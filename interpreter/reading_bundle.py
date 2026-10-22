"""Reading bundle — every engine datum a reading prompt needs, as one text block.

Read-only consumer of the engine (like ``build_matrix``): it computes nothing
the engine does not already expose and reaches no verdict. It gathers the
Phase-I matrix plus the period and transit data a current-life reading uses —
the running daśā chain to sūkṣma, Chara / Nārāyaṇa / Sudasā, Yoginī,
Aṣṭottarī, Muddā, Sudarśana, the running Varṣaphal, Sāhams, Gulika/Mandi,
key vargas, avasthās, KP significations, the gochara snapshot (houses from
Lagna/Moon/Sun/AL/UL/Kārakāṁśa, nakṣatra, tārā, Vedha, SAV, Kakṣyā), Saturn
from the Moon, Sarvatobhadra hits, the next ingresses and stations, degree
(BNN) windows of the slow grahas over natal points, Jupiter+Saturn double
transits per house, and every registered domain's Samanvaya engine reports.

The bundle is fed to the AI as ground truth; interpretation stays in the
prompt (see docs/AI_TRIANGULATION_PROMPT.md).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from advance_astrology import Planet, VedicChart
from advance_astrology.constants import SIGNS, VEDIC_GRAHAS
from advance_astrology.dasha import current_dasha
from advance_astrology.vedic import upagrahas

from interpreter.build_matrix import build_matrix

SLOW = (Planet.SATURN, Planet.JUPITER, Planet.RAHU, Planet.KETU)
TIMED = (Planet.SATURN, Planet.JUPITER, Planet.RAHU, Planet.KETU, Planet.MARS)


def _d(x: datetime, tz) -> str:
    return x.astimezone(tz).strftime("%Y-%m-%d")


def _z(lon: float) -> str:
    lon = float(lon) % 360
    return f"{SIGNS[int(lon // 30)]} {lon % 30:.2f}°"


def _fmt(x, tz) -> str:
    """Compact text for an engine report: the same fields and values as its
    repr, without the Python noise (datetime(...), <Planet.X: 'X'>, quotes,
    microseconds). Instants are shown to the minute in the native's zone."""
    import dataclasses
    import enum
    if dataclasses.is_dataclass(x) and not isinstance(x, type):
        return f"{type(x).__name__}(" + ", ".join(
            f"{f.name}={_fmt(getattr(x, f.name), tz)}" for f in dataclasses.fields(x)) + ")"
    if isinstance(x, datetime):
        return x.astimezone(tz).strftime("%Y-%m-%d %H:%M")
    if isinstance(x, enum.Enum):
        return str(x.value)
    if isinstance(x, (list, tuple)):
        return "[" + ", ".join(_fmt(i, tz) for i in x) + "]"
    if isinstance(x, dict):
        return "{" + ", ".join(f"{_fmt(k, tz)}: {_fmt(v, tz)}" for k, v in x.items()) + "}"
    if isinstance(x, float):
        return f"{x:.3f}".rstrip("0").rstrip(".")
    if isinstance(x, str):
        return repr(x) if any(c in x for c in ",=[]{}():") else x
    return str(x)


def _h(lines: list, title: str) -> None:
    lines.append("")
    lines.append(f"## {title}")


class Reading:
    """One native's chart, as of a date, with each bundle section on demand.

    Sections are the unit both consumers use: ``build_bundle`` joins all of
    them, and ``interpreter.engine_tools`` hands them to Claude one tool call
    at a time.
    """

    SECTIONS = ("strengths", "gulika", "vimshottari", "rashi_dashas", "varshaphal", "sahams",
                "vargas", "avasthas", "kp", "gochara_now", "ingresses",
                "bnn_windows", "double_transit")

    def __init__(self, when_local: datetime, lat: float, lon: float, *,
                 place: str = "", gender: str = "", ayanamsa: str = "lahiri",
                 as_of: datetime | None = None):
        self.when_local, self.lat, self.lon = when_local, lat, lon
        self.place, self.gender, self.ayanamsa = place, gender, ayanamsa
        self.tz = when_local.tzinfo
        self.now = as_of or datetime.now(timezone.utc)
        self.v = VedicChart.create(when=when_local, latitude=lat, longitude=lon,
                                   ayanamsa=ayanamsa)
        self.v.gender = gender
        self.tr = self.v.transits()
        self.A = int(self.v.ascendant_sign)

    def house(self, sign) -> int:
        return (int(sign) - self.A) % 12 + 1

    def d(self, x: datetime) -> str:
        return _d(x, self.tz)

    def matrix(self) -> str:
        return (build_matrix(self.when_local, self.lat, self.lon, self.place, self.gender,
                             "", self.ayanamsa, 3)
                + f"\n\n# AS-OF DATE: {self.d(self.now)}")

    def section(self, name: str) -> str:
        if name not in self.SECTIONS:
            raise KeyError(name)
        L: list = []
        getattr(self, "_" + name)(L)
        return "\n".join(L).strip("\n")

    # -- sections -------------------------------------------------------------
    def _strengths(self, L):
        v = self.v
        _h(L, "Shadbala by component (virupas; 60 = 1 rupa) and Ishta/Kashta")
        ik = v.ishta_kashta()
        for p, x in v.shadbala().items():
            c = ", ".join(f"{k} {val:.1f}" for k, val in x.components.items())
            L.append(f"  {p.value}: total {x.total_rupa:.2f} rupa (needs {x.required_rupa}, "
                     f"ratio {x.ratio:.2f}) = sthana {x.sthana:.1f} + dig {x.dig:.1f} + kala "
                     f"{x.kala:.1f} + cheshta {x.cheshta:.1f} + naisargika {x.naisargika:.1f} + "
                     f"drik {x.drik:+.1f}; parts: {c}; ishta {ik[p].ishta:.1f}, kashta "
                     f"{ik[p].kashta:.1f}")
        _h(L, "Bhava Bala (Raman ch. IX, Sripati madhyas): adhipati + dig + drishti")
        for x in v.bhava_bala().values():
            L.append(f"  {x}")

    def _gulika(self, L):
        v, house, lat, lon, ayanamsa = self.v, self.house, self.lat, self.lon, self.ayanamsa
        _h(L, "Gulika / Mandi (time-based upagrahas)")
        eph = v.natal._ephemeris
        rise, sset, nrise, _ = eph.day_portions(v.when_utc, lat, lon)
        if rise is not None:
            is_day = rise <= v.when_utc < sset
            gt = upagrahas.gulika_time(v.when_utc, rise, sset, nrise)
            seg = ((sset - rise) if is_day else (nrise - sset)) / 8
            gl = VedicChart.create(when=gt, latitude=lat, longitude=lon, ayanamsa=ayanamsa).ascendant
            md = VedicChart.create(when=gt + seg / 2, latitude=lat, longitude=lon,
                                   ayanamsa=ayanamsa).ascendant
            L.append(f"  Birth in {'day' if is_day else 'night'} portion. "
                     f"Gulika (start of Saturn segment): {_z(gl)} = H{house(int(gl // 30) % 12)}; "
                     f"Mandi (middle of segment): {_z(md)} = H{house(int(md // 30) % 12)}")
        for k, x in v.calculated_upagrahas().items():
            L.append(f"  {k}: {_z(x)} = H{house(int(float(x) // 30) % 12)}")

    def _vimshottari(self, L, at: datetime | None = None):
        v, d = self.v, self.d
        at = at or self.now
        _h(L, f"Vimshottari — running chain on {d(at)} (to Sukshma/Prana) and the periods around it")
        ch = v.current_dasha("vimshottari", at, levels=5)
        names = ["MD", "AD", "PD", "SD", "PrD"]
        for i, p in enumerate(ch):
            L.append(f"  {names[i]} {p.lord.value}: {d(p.start)} → {d(p.end)}")
        if len(ch) >= 1:
            L.append("  ADs of the running MD: " + "; ".join(
                f"{p.lord.value} {d(p.start)}→{d(p.end)}" for p in ch[0].sub_periods))
        if len(ch) >= 2:
            L.append("  PDs of the running AD: " + "; ".join(
                f"{p.lord.value} {d(p.start)}→{d(p.end)}" for p in ch[1].sub_periods))
        if len(ch) >= 3:
            L.append("  Sukshmas of the running PD: " + "; ".join(
                f"{p.lord.value} {d(p.start)}" for p in ch[2].sub_periods))
        nxt_md = [p for p in v.dasha("vimshottari", levels=1) if p.start > at][:2]
        L.append("  Next MDs: " + "; ".join(f"{p.lord.value} from {d(p.start)}" for p in nxt_md))
        # The AD after the running one, with its PDs (the next chapter).
        nxt_ad = [p for p in (ch[0].sub_periods if ch else []) if p.start >= ch[1].end][:1] \
            if len(ch) >= 2 else []
        if nxt_ad:
            later = v.current_dasha("vimshottari", nxt_ad[0].start + timedelta(days=1), levels=3)
            if len(later) >= 2:
                L.append(f"  Next AD {later[1].lord.value} PDs: " + "; ".join(
                    f"{p.lord.value} {d(p.start)}→{d(p.end)}" for p in later[1].sub_periods))

    def _rashi_dashas(self, L, at: datetime | None = None):
        v, d = self.v, self.d
        at = at or self.now
        _h(L, f"Jaimini rashi dashas, Yogini, Ashtottari, Mudda, Sudarshana on {d(at)}")
        for nm, ps in (("Chara", v.chara_dasha(levels=2, cycles=1)),
                       ("Narayana", v.narayana_dasha(levels=2)),
                       ("Sudasa", v.sudasa_dasha(levels=2))):
            cur = current_dasha(ps, at)
            if not cur:
                continue
            L.append(f"  {nm}: " + " › ".join(f"{p.note or p.lord.value} ({d(p.start)}→{d(p.end)})"
                                               for p in cur))
            L.append(f"    {nm} ADs: " + "; ".join(f"{p.note} {d(p.start)}" for p in cur[0].sub_periods))
        for s in ("yogini", "ashtottari"):
            L.append(f"  {s.title()}: " + " › ".join(
                f"{p.lord.value} ({d(p.start)}→{d(p.end)})" for p in v.current_dasha(s, at)))
        try:
            L.append("  Mudda (annual Vimshottari): " + " › ".join(
                f"{p.lord.value} ({d(p.start)}→{d(p.end)})"
                for p in v.current_mudda_dasha(at, levels=2)))
        except Exception as e:                               # pragma: no cover
            L.append(f"  Mudda: unavailable ({type(e).__name__})")
        su = v.sudarshana(at)
        L.append(f"  Sudarshana year signs — Lagna wheel {SIGNS[su.lagna_year_sign]}, "
                 f"Moon wheel {SIGNS[su.moon_year_sign]}, Sun wheel {SIGNS[su.sun_year_sign]}; "
                 f"month signs {SIGNS[su.lagna_month_sign]} / {SIGNS[su.moon_month_sign]} / "
                 f"{SIGNS[su.sun_month_sign]} (years elapsed {su.years_elapsed})")

    def _varshaphal(self, L, year: int | None = None):
        from advance_astrology.vedic.varshaphal import solar_return_time
        v, d, house, now = self.v, self.d, self.house, self.now
        if year is None:
            year = now.year if now >= solar_return_time(v, now.year) else now.year - 1
        _h(L, f"Varshaphal (Tajika annual chart), year {year}")
        ac = v.varshaphal(year)
        c = ac.chart
        L.append(f"  Year {year}: solar return {d(ac.solar_return)}; Varsha lagna "
                 f"{SIGNS[ac.varsha_lagna_sign]} (= natal H{house(ac.varsha_lagna_sign)}); "
                 f"Muntha {SIGNS[ac.muntha_sign]} (natal H{ac.muntha_house}), Muntha lord "
                 f"{ac.muntha_lord.value}; year lord {ac.lagna_lord.value}")
        L.append("  Annual positions: " + "; ".join(
            f"{p.value} {_z(c.longitudes[p])} aH{(int(c.signs[p]) - int(c.ascendant_sign)) % 12 + 1}"
            for p in VEDIC_GRAHAS))

    def _sahams(self, L):
        _h(L, "Sahams (with natal house)")
        L.append("  " + "; ".join(f"{k} {_z(s.longitude)} H{self.house(int(float(s.longitude) // 30) % 12)}"
                                  for k, s in self.v.sahams().items()))

    def _vargas(self, L, divisions=(9, 7, 10, 30, 60)):
        _h(L, "Vargas (graha → sign; house counted from the varga lagna)")
        for dv in divisions:
            vc = self.v.varga(dv)
            va = int(vc.ascendant_sign)
            L.append(f"  D{dv} asc {SIGNS[va]}: " + ", ".join(
                f"{p.value} {SIGNS[s]} vH{(int(s) - va) % 12 + 1}"
                for p, s in vc.signs.items() if p in VEDIC_GRAHAS))

    def _avasthas(self, L):
        _h(L, "Avasthas (all grahas)")
        for p in VEDIC_GRAHAS:
            try:
                L.append(f"  {p.value}: {self.v.avasthas(p)}")
            except Exception:
                pass

    def _kp(self, L):
        _h(L, "KP — houses each graha signifies")
        k = self.v.kp_significators()
        L.append("  " + "; ".join(f"{p.value} {k.planet_signifies(p)}" for p in VEDIC_GRAHAS))

    def _gochara_now(self, L, at: datetime | None = None):
        tr, d = self.tr, self.d
        at = at or self.now
        _h(L, f"Gochara on {d(at)} (houses from each reference; tara from janma nakshatra)")
        snap = tr.snapshot(at)
        L.append("  Reference signs: " + ", ".join(f"{k_}={SIGNS[s]}" for k_, s in snap["references"].items()))
        for p, x in snap["planets"].items():
            vd = x["vedha"]
            L.append(f"  {p.value}: {_z(x['longitude'])} {x['nakshatra_name']} p{x['pada']} "
                     f"({'vakri' if x['retrograde'] else 'margi'}); houses {x['houses']}; "
                     f"SAV {x['sav']}; kakshya {x['kakshya_active']}; tara {x['tara']['name']} "
                     f"({x['tara']['quality']}); aspects from lagna {x['aspects_from_lagna']}, "
                     f"from moon {x['aspects_from_moon']}; vedha good={vd['good']} "
                     f"obstructed_by={[q.value for q in vd['obstructed_by']]} "
                     f"vipareeta_by={[q.value for q in vd['vipareeta_by']]}")
        L.append(f"  Saturn from Moon: {snap['saturn']}")
        sb = tr.sarvatobhadra(at)
        L.append(f"  Sarvatobhadra janma points: {sb['janma']}")
        for p, x in sb["planets"].items():
            if x["hits"]:
                L.append(f"    {p.value} in {x['nakshatra']} ({x['motion']}, predominant "
                         f"{x['predominant']}): hits {x['hits']}")

    def _ingresses(self, L, start: datetime | None = None, end: datetime | None = None,
                   planets=TIMED):
        tr, d = self.tr, self.d
        start = start or self.now
        end = end or start + timedelta(days=548)
        _h(L, f"Ingresses and stations {d(start)} → {d(end)}")
        for p in planets:
            L.append(f"  {p.value} rashi: " + "; ".join(
                f"{d(x['when'])} → {SIGNS[x['to_sign']]} (H{x['house_from_lagna']} lagna/"
                f"H{x['house_from_moon']} moon{', vakri' if x['retrograde'] else ''})"
                for x in tr.sign_ingresses(p, start, end)))
            L.append(f"  {p.value} nakshatra: " + "; ".join(
                f"{d(x['when'])} → {x['tara']['name']} tara (to idx {x['to_nakshatra']})"
                for x in tr.nakshatra_ingresses(p, start, end)))
            st = tr.stations(p, start, end)
            if st:
                L.append(f"  {p.value} stations: " + "; ".join(
                    f"{d(x['when'])} {x['turns']}" for x in st))

    def _bnn_windows(self, L):
        v, tr, d, now = self.v, self.tr, self.d, self.now
        _h(L, "Degree (BNN) windows of slow grahas over natal points, past 18 months → next 18 months")
        pts = {p.value: v.longitudes[p] for p in VEDIC_GRAHAS}
        pts["Lagna"] = v.ascendant
        for tp in SLOW:
            for nm, lon_ in pts.items():
                for w in tr.conjunction_windows(tp, lon_, now - timedelta(days=548),
                                                now + timedelta(days=548), orb=2):
                    L.append(f"  {tp.value} over natal {nm}: {d(w.start)} → {d(w.end)}")

    def _double_transit(self, L):
        tr, d, now = self.tr, self.d, self.now
        _h(L, "Jupiter+Saturn double transit per house (from lagna), next 4 years")
        for hno in range(1, 13):
            ws = tr.double_transit_windows(hno, now, now + timedelta(days=4 * 365))
            L.append(f"  H{hno}: " + ("; ".join(f"{d(w.start)}→{d(w.end)}" for w in ws) or "—"))

    def samanvaya(self, domain: str, prof=None) -> str:
        """Every Samanvaya engine's report for one domain (DomainProfile)."""
        from interpreter.engines import ENGINES
        if prof is None:
            from interpreter.domains import DOMAIN_PROFILES
            prof = DOMAIN_PROFILES.get(domain)
            if prof is None:
                from interpreter.significators import resolve
                prof = resolve(domain)
        start, stop = self.now - timedelta(days=180), self.now + timedelta(days=2 * 365)
        name = getattr(prof, "name", domain)
        L = [f"### {domain}" + (f" (resolved to domain '{name}', houses {tuple(prof.houses)})"
                                if name != domain else "")]
        for en, eng in ENGINES.items():
            try:
                L.append(f"  {en}: {_fmt(eng.evaluate(self.v, prof, start, stop), self.tz)}")
            except Exception as e:                           # pragma: no cover
                L.append(f"  {en}: unavailable ({type(e).__name__}: {e})")
        return "\n".join(L)


def build_bundle(when_local: datetime, lat: float, lon: float, *, place: str = "",
                 gender: str = "", ayanamsa: str = "lahiri",
                 as_of: datetime | None = None) -> str:
    """The full engine bundle for a native, as of *as_of* (default: now)."""
    r = Reading(when_local, lat, lon, place=place, gender=gender, ayanamsa=ayanamsa,
                as_of=as_of)
    L = [r.matrix()]
    for s in Reading.SECTIONS:
        L.append("")
        L.append(r.section(s))
    L.append("")
    L.append("## Samanvaya engine reports per domain (KP / dasha_timing / jaimini / tajika / nadi)")
    from interpreter.domains import DOMAIN_PROFILES
    for name, prof in DOMAIN_PROFILES.items():
        L.append(r.samanvaya(name, prof))
    return "\n".join(L)
