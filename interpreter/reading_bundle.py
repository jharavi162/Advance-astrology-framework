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


def _h(lines: list, title: str) -> None:
    lines.append("")
    lines.append(f"## {title}")


def build_bundle(when_local: datetime, lat: float, lon: float, *, place: str = "",
                 gender: str = "", ayanamsa: str = "lahiri",
                 as_of: datetime | None = None) -> str:
    """The full engine bundle for a native, as of *as_of* (default: now)."""
    tz = when_local.tzinfo
    now = as_of or datetime.now(timezone.utc)
    v = VedicChart.create(when=when_local, latitude=lat, longitude=lon,
                          ayanamsa=ayanamsa)
    v.gender = gender
    tr = v.transits()
    A = int(v.ascendant_sign)
    house = lambda sign: (int(sign) - A) % 12 + 1

    L = [build_matrix(when_local, lat, lon, place, gender, "", ayanamsa, 3)]
    L.append("")
    L.append(f"# AS-OF DATE: {_d(now, tz)}")

    # -- Gulika / Mandi ------------------------------------------------------
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

    # -- Vimśottari to sūkṣma -------------------------------------------------
    _h(L, "Vimshottari — running chain (to Sukshma/Prana) and the periods around it")
    ch = v.current_dasha("vimshottari", now, levels=5)
    names = ["MD", "AD", "PD", "SD", "PrD"]
    for i, p in enumerate(ch):
        L.append(f"  {names[i]} {p.lord.value}: {_d(p.start, tz)} → {_d(p.end, tz)}")
    if len(ch) >= 1:
        L.append("  ADs of the running MD: " + "; ".join(
            f"{p.lord.value} {_d(p.start, tz)}→{_d(p.end, tz)}" for p in ch[0].sub_periods))
    if len(ch) >= 2:
        L.append("  PDs of the running AD: " + "; ".join(
            f"{p.lord.value} {_d(p.start, tz)}→{_d(p.end, tz)}" for p in ch[1].sub_periods))
    if len(ch) >= 3:
        L.append("  Sukshmas of the running PD: " + "; ".join(
            f"{p.lord.value} {_d(p.start, tz)}" for p in ch[2].sub_periods))
    nxt_md = [p for p in v.dasha("vimshottari", levels=1) if p.start > now][:2]
    L.append("  Next MDs: " + "; ".join(f"{p.lord.value} from {_d(p.start, tz)}" for p in nxt_md))
    # The AD after the running one, with its PDs (the next chapter).
    nxt_ad = [p for p in (ch[0].sub_periods if ch else []) if p.start >= ch[1].end][:1] \
        if len(ch) >= 2 else []
    if nxt_ad:
        later = v.current_dasha("vimshottari", nxt_ad[0].start + timedelta(days=1), levels=3)
        if len(later) >= 2:
            L.append(f"  Next AD {later[1].lord.value} PDs: " + "; ".join(
                f"{p.lord.value} {_d(p.start, tz)}→{_d(p.end, tz)}" for p in later[1].sub_periods))

    # -- Jaimini & other daśās ------------------------------------------------
    _h(L, "Jaimini rashi dashas, Yogini, Ashtottari, Mudda, Sudarshana")
    for nm, ps in (("Chara", v.chara_dasha(levels=2, cycles=1)),
                   ("Narayana", v.narayana_dasha(levels=2)),
                   ("Sudasa", v.sudasa_dasha(levels=2))):
        cur = current_dasha(ps, now)
        if not cur:
            continue
        L.append(f"  {nm}: " + " › ".join(f"{p.note or p.lord.value} ({_d(p.start, tz)}→{_d(p.end, tz)})"
                                           for p in cur))
        L.append(f"    {nm} ADs: " + "; ".join(f"{p.note} {_d(p.start, tz)}" for p in cur[0].sub_periods))
    for s in ("yogini", "ashtottari"):
        L.append(f"  {s.title()}: " + " › ".join(
            f"{p.lord.value} ({_d(p.start, tz)}→{_d(p.end, tz)})" for p in v.current_dasha(s, now)))
    try:
        L.append("  Mudda (annual Vimshottari): " + " › ".join(
            f"{p.lord.value} ({_d(p.start, tz)}→{_d(p.end, tz)})"
            for p in v.current_mudda_dasha(now, levels=2)))
    except Exception as e:                                   # pragma: no cover
        L.append(f"  Mudda: unavailable ({type(e).__name__})")
    su = v.sudarshana(now)
    L.append(f"  Sudarshana year signs — Lagna wheel {SIGNS[su.lagna_year_sign]}, "
             f"Moon wheel {SIGNS[su.moon_year_sign]}, Sun wheel {SIGNS[su.sun_year_sign]}; "
             f"month signs {SIGNS[su.lagna_month_sign]} / {SIGNS[su.moon_month_sign]} / "
             f"{SIGNS[su.sun_month_sign]} (years elapsed {su.years_elapsed})")

    # -- Varṣaphal ------------------------------------------------------------
    _h(L, "Varshaphal (Tajika annual chart) running now")
    from advance_astrology.vedic.varshaphal import solar_return_time
    y = now.year if now >= solar_return_time(v, now.year) else now.year - 1
    ac = v.varshaphal(y)
    c = ac.chart
    L.append(f"  Year {y}: solar return {_d(ac.solar_return, tz)}; Varsha lagna "
             f"{SIGNS[ac.varsha_lagna_sign]} (= natal H{house(ac.varsha_lagna_sign)}); "
             f"Muntha {SIGNS[ac.muntha_sign]} (natal H{ac.muntha_house}), Muntha lord "
             f"{ac.muntha_lord.value}; year lord {ac.lagna_lord.value}")
    L.append("  Annual positions: " + "; ".join(
        f"{p.value} {_z(c.longitudes[p])} aH{(int(c.signs[p]) - int(c.ascendant_sign)) % 12 + 1}"
        for p in VEDIC_GRAHAS))

    # -- Sahams, vargas, avasthas, KP ----------------------------------------
    _h(L, "Sahams (with natal house)")
    L.append("  " + "; ".join(f"{k} {_z(s.longitude)} H{house(int(float(s.longitude) // 30) % 12)}"
                              for k, s in v.sahams().items()))
    _h(L, "Key vargas (graha → sign)")
    for dv in (9, 7, 10, 30, 60):
        vc = v.varga(dv)
        L.append(f"  D{dv} asc {SIGNS[vc.ascendant_sign]}: " + ", ".join(
            f"{p.value} {SIGNS[s]}" for p, s in vc.signs.items() if p in VEDIC_GRAHAS))
    _h(L, "Avasthas (all grahas)")
    for p in VEDIC_GRAHAS:
        try:
            L.append(f"  {p.value}: {v.avasthas(p)}")
        except Exception:
            pass
    _h(L, "KP — houses each graha signifies")
    k = v.kp_significators()
    L.append("  " + "; ".join(f"{p.value} {k.planet_signifies(p)}" for p in VEDIC_GRAHAS))

    # -- Gochara now ----------------------------------------------------------
    _h(L, f"Gochara on {_d(now, tz)} (houses from each reference; tara from janma nakshatra)")
    snap = tr.snapshot(now)
    L.append(f"  Reference signs: " + ", ".join(f"{k_}={SIGNS[s]}" for k_, s in snap["references"].items()))
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
    sb = tr.sarvatobhadra(now)
    L.append(f"  Sarvatobhadra janma points: {sb['janma']}")
    for p, x in sb["planets"].items():
        if x["hits"]:
            L.append(f"    {p.value} in {x['nakshatra']} ({x['motion']}, predominant "
                     f"{x['predominant']}): hits {x['hits']}")

    # -- What changes next ----------------------------------------------------
    end = now + timedelta(days=548)
    _h(L, f"Ingresses and stations {_d(now, tz)} → {_d(end, tz)}")
    for p in TIMED:
        L.append(f"  {p.value} rashi: " + "; ".join(
            f"{_d(x['when'], tz)} → {SIGNS[x['to_sign']]} (H{x['house_from_lagna']} lagna/"
            f"H{x['house_from_moon']} moon{', vakri' if x['retrograde'] else ''})"
            for x in tr.sign_ingresses(p, now, end)))
        L.append(f"  {p.value} nakshatra: " + "; ".join(
            f"{_d(x['when'], tz)} → {x['tara']['name']} tara (to idx {x['to_nakshatra']})"
            for x in tr.nakshatra_ingresses(p, now, end)))
        st = tr.stations(p, now, end)
        if st:
            L.append(f"  {p.value} stations: " + "; ".join(
                f"{_d(x['when'], tz)} {x['turns']}" for x in st))

    _h(L, "Degree (BNN) windows of slow grahas over natal points, past 18 months → next 18 months")
    pts = {p.value: v.longitudes[p] for p in VEDIC_GRAHAS}
    pts["Lagna"] = v.ascendant
    for tp in SLOW:
        for nm, lon_ in pts.items():
            for w in tr.conjunction_windows(tp, lon_, now - timedelta(days=548), end, orb=2):
                L.append(f"  {tp.value} over natal {nm}: {_d(w.start, tz)} → {_d(w.end, tz)}")

    _h(L, "Jupiter+Saturn double transit per house (from lagna), next 4 years")
    for hno in range(1, 13):
        ws = tr.double_transit_windows(hno, now, now + timedelta(days=4 * 365))
        L.append(f"  H{hno}: " + ("; ".join(f"{_d(w.start, tz)}→{_d(w.end, tz)}" for w in ws) or "—"))

    # -- Samanvaya engines per domain -----------------------------------------
    _h(L, "Samanvaya engine reports per domain (KP / dasha_timing / jaimini / tajika / nadi)")
    from interpreter.domains import DOMAIN_PROFILES
    from interpreter.engines import ENGINES
    start, stop = now - timedelta(days=180), now + timedelta(days=2 * 365)
    for name, prof in DOMAIN_PROFILES.items():
        L.append(f"### {name}")
        for en, eng in ENGINES.items():
            try:
                L.append(f"  {en}: {eng.evaluate(v, prof, start, stop)}")
            except Exception as e:                           # pragma: no cover
                L.append(f"  {en}: unavailable ({type(e).__name__}: {e})")
    return "\n".join(L)
