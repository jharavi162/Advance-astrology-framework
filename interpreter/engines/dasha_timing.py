"""Daśā timing engine — DATA ONLY.

The event clock, per the corrected division of labour: this engine reports
*which event-significators are running* in the Vimśottari and Jaimini-Chara
daśās over a span, plus the Gochara double-transit windows — and nothing else.
It computes **no score and no verdict**. The AI reads the data and times the
event (e.g. "the 7th-lord's antardaśā opens here → marriage window").

Why this engine, not KP, for timing (established by blind test): KP's cuspal
sub-lord is a promise/quality instrument; the *clock* is the daśā of the event's
own significators — the 7th-lord and its dispositor for marriage, confirmed by
the Jupiter+Saturn double-transit on the bhāva and its lord.

Significators are derived transparently from the domain (house-lords + their
dispositors + kāraka + Darakaraka) — domain-general, never a hard-coded native.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from advance_astrology import Planet
from advance_astrology.constants import RULERSHIPS, SIGNS


@dataclass(frozen=True)
class Significator:
    label: str                 # "7th-lord", "disp(7th-lord)", "kāraka:Venus", "Darakaraka"
    planet: Planet


@dataclass(frozen=True)
class VimPeriod:
    """One Vimśottari antardaśā, annotated with which significators are its
    MD or AD lord. `onset` marks the AD's start — events cluster at AD onsets."""
    start: datetime
    end: datetime
    md: str
    ad: str
    active: tuple[str, ...]    # significator LABELS running as MD or AD lord


@dataclass(frozen=True)
class CharaPeriod:
    start: datetime
    end: datetime
    sign: str
    roles: tuple[str, ...]     # classical marriage-timing roles this sign plays


@dataclass(frozen=True)
class SeventhLordTrineData:
    """Phaladeepika X.14 raw inputs: the 7th-lord's rāśi and navāṃśa, the lords
    of both (pair 1) and Venus/Moon (pair 2) with their Ṣaḍbala, the signs in
    trine (1/5/9) to either, and every Jupiter transit span through one of them.
    The śloka times marriage in the daśā of the stronger planet while Jupiter
    crosses such a sign — the AI makes that call; no window is ranked here."""
    seventh_lord: str
    rasi_sign: str
    navamsa_sign: str
    rasi_lord: str
    navamsa_lord: str
    shadbala_ratio: dict          # planet → total_rupa / required_rupa
    stronger_of_lords: str        # of (rasi_lord, navamsa_lord), by ratio
    stronger_of_venus_moon: str
    trine_signs: dict             # sign → ("1st from 7L-rāśi", "5th from 7L-navāṃśa", …)
    jupiter_windows: tuple[tuple[datetime, datetime, str, tuple[str, ...]], ...]


@dataclass(frozen=True)
class DashaTimingReport:
    domain: str
    significators: tuple[Significator, ...]
    vimshottari: tuple[VimPeriod, ...]
    chara: tuple[CharaPeriod, ...]
    transit_triggers: tuple[tuple[datetime, datetime, str], ...]  # (start, end, what)
    seventh_lord_trines: SeventhLordTrineData | None = None   # marriage family only

    def active_windows(self, label: str) -> list[VimPeriod]:
        """Convenience for the AI: every antardaśā in which `label` is running."""
        return [p for p in self.vimshottari if label in p.active]


def _dispositor(v, planet: Planet) -> Planet:
    return RULERSHIPS[SIGNS[v.signs[planet]]]


def _significators(v, profile) -> list[Significator]:
    """Derive the event's timing significators from the domain, transparently.
    Marriage-class matters also carry the spouse kārakas (Darakaraka; Jupiter is
    the husband-kāraka for a female, Venus the wife-kāraka)."""
    sig: list[Significator] = []
    seen: set = set()

    def add(label, planet):
        if planet and (label, planet) not in seen:
            seen.add((label, planet))
            sig.append(Significator(label, planet))

    for h in profile.houses:
        lord = v.house_lord(h)
        add(f"{_ord(h)}-lord", lord)
        add(f"disp({_ord(h)}-lord)", _dispositor(v, lord))
    if profile.natural_karaka:
        add(f"kāraka:{profile.natural_karaka.value}", profile.natural_karaka)
    # spouse matters: Darakaraka + gender-aware partner kāraka
    is_marriage = (profile.base_domain or profile.name) in ("marriage", "divorce")
    if is_marriage or 7 in profile.houses:
        dk = v.chara_karakas().get("Darakaraka")
        add("Darakaraka", dk)
        g = (getattr(v, "gender", "") or "").lower()
        add("kāraka:Jupiter(spouse)" if g.startswith("f") else "kāraka:Venus(spouse)",
            Planet.JUPITER if g.startswith("f") else Planet.VENUS)
    return sig


def _ord(h: int) -> str:
    return {1: "1st", 2: "2nd", 3: "3rd"}.get(h, f"{h}th")


def _overlaps(a_start, a_end, b_start, b_end) -> bool:
    return a_start < b_end and b_start < a_end


class DashaTimingEngine:
    """Data-only event-clock engine (the `Engine` contract's `evaluate`, but the
    result is raw daśā DATA, not a scored timeline)."""

    name = "dasha_timing"

    def evaluate(self, v, profile, start: datetime, end: datetime) -> DashaTimingReport:
        sig = _significators(v, profile)
        by_planet: dict = {}
        for s in sig:
            by_planet.setdefault(s.planet, []).append(s.label)

        # --- Vimśottari MD>AD, annotated with running significators ---------- #
        vim: list[VimPeriod] = []
        for md in v.dasha("vimshottari", levels=2):
            if not _overlaps(md.start, md.end, start, end):
                continue
            for ad in (md.sub_periods or []):
                if not _overlaps(ad.start, ad.end, start, end):
                    continue
                labels = []
                for lord in (md.lord, ad.lord):
                    labels += by_planet.get(lord, [])
                vim.append(VimPeriod(ad.start, ad.end, md.lord.value, ad.lord.value,
                                     tuple(dict.fromkeys(labels))))

        # --- Jaimini Chara rāśi daśā, tagged by the DOMAIN's own rāśi roles ----
        # Domain-general (never marriage-only): a rāśi period matters when its
        # sign is one of the matter's bhāva-signs (Hth-from-Lagna for each house)
        # or holds the matter's chara-kāraka (Darakaraka / Amātyakāraka / …) or
        # its natural kāraka. The AI reads which role is active for the question.
        asc = v.ascendant_sign
        ck = v.chara_karakas()
        house_signs = {SIGNS[(asc + h - 1) % 12]: _ord(h) for h in profile.houses}
        karaka_signs: dict = {}
        for kname in profile.karakas:                      # e.g. Darakaraka, Amatyakaraka
            kp = ck.get(kname)
            if kp:
                karaka_signs.setdefault(SIGNS[v.signs[kp]], []).append(kname)
        if profile.natural_karaka:
            karaka_signs.setdefault(SIGNS[v.signs[profile.natural_karaka]], []).append(
                f"kāraka:{profile.natural_karaka.value}")
        chara: list[CharaPeriod] = []
        for cp in _chara_periods(v):
            if not _overlaps(cp["start"], cp["end"], start, end):
                continue
            roles = []
            if cp["sign"] in house_signs:
                roles.append(f"{house_signs[cp['sign']]}-from-Lagna")
            for k in karaka_signs.get(cp["sign"], []):
                roles.append(f"holds {k}")
            chara.append(CharaPeriod(cp["start"], cp["end"], cp["sign"], tuple(roles)))

        # --- Gochara double-transit triggers on the bhāva and its lord ------- #
        tr = v.transits()
        triggers: list = []
        for h in profile.houses:
            for w in tr.double_transit_windows(h, start, end):
                triggers.append((w.start, w.end, f"double-transit on H{h}"))
            lord = v.house_lord(h)
            lord_house = (v.signs[lord] - asc) % 12 + 1
            for w in tr.double_transit_windows(lord_house, start, end):
                triggers.append((w.start, w.end,
                                 f"double-transit on {_ord(h)}-lord ({lord.value}, H{lord_house})"))
        triggers.sort()

        is_marriage = not profile.rupture_matter and \
            (profile.base_domain or profile.name) == "marriage"
        return DashaTimingReport(
            domain=profile.name, significators=tuple(sig),
            vimshottari=tuple(vim), chara=tuple(chara),
            transit_triggers=tuple(triggers),
            seventh_lord_trines=_seventh_lord_trines(v, tr, start, end)
            if is_marriage else None)


def _seventh_lord_trines(v, tr, start: datetime, end: datetime) -> SeventhLordTrineData:
    """Phaladeepika X.14 (and the 7th-lord-in-transit family of JP XIV): the
    rāśi/navāṃśa of the Lagna's 7th lord, their lords, Venus/Moon, and Jupiter's
    passage through any sign trine to either reference."""
    l7 = v.house_lord(7)
    rasi = v.signs[l7]
    nav = v.varga(9).signs[l7]
    rasi_lord, nav_lord = RULERSHIPS[SIGNS[rasi]], RULERSHIPS[SIGNS[nav]]
    sb = v.shadbala()
    ratio = {p.value: round(sb[p].ratio, 3)
             for p in dict.fromkeys((rasi_lord, nav_lord, Planet.VENUS, Planet.MOON))}

    def stronger(a: Planet, b: Planet) -> str:
        return a.value if ratio[a.value] >= ratio[b.value] else b.value

    trines: dict = {}
    for ref, base in (("7L-rāśi", rasi), ("7L-navāṃśa", nav)):
        for n, off in ((1, 0), (5, 4), (9, 8)):
            trines.setdefault(SIGNS[(base + off) % 12], []).append(f"{_ord(n)} from {ref}")
    windows = tuple((s, e, SIGNS[sign], tuple(trines[SIGNS[sign]]))
                    for s, e, sign in _sign_spans(tr, Planet.JUPITER, start, end)
                    if SIGNS[sign] in trines)
    return SeventhLordTrineData(
        seventh_lord=l7.value, rasi_sign=SIGNS[rasi], navamsa_sign=SIGNS[nav],
        rasi_lord=rasi_lord.value, navamsa_lord=nav_lord.value,
        shadbala_ratio=ratio, stronger_of_lords=stronger(rasi_lord, nav_lord),
        stronger_of_venus_moon=stronger(Planet.VENUS, Planet.MOON),
        trine_signs={k: tuple(r) for k, r in trines.items()},
        jupiter_windows=windows)


def _sign_spans(tr, planet: Planet, start: datetime, end: datetime,
                step_days: int = 7) -> list[tuple[datetime, datetime, int]]:
    """Contiguous (start, end, sign) spans of a transit planet's whole sign.
    The step must stay below the shortest retrograde re-entry (~3 weeks)."""
    step, one_day = timedelta(days=step_days), timedelta(days=1)
    spans: list = []
    s0, sign = start, tr.transit_sign(start, planet)
    d = start
    while d < end:
        nxt = min(d + step, end)
        s2 = tr.transit_sign(nxt, planet)
        if s2 != sign:
            lo, hi = d, nxt
            while hi - lo > one_day:
                mid = lo + (hi - lo) / 2
                if tr.transit_sign(mid, planet) == sign:
                    lo = mid
                else:
                    hi = mid
            spans.append((s0, hi, sign))
            s0, sign = hi, s2
        d = nxt
    spans.append((s0, end, sign))
    return spans


def _chara_periods(v) -> list[dict]:
    """Chara antardaśā-level rāśi periods (sign + span), robust to sub_periods
    absence — falls back to MD-level rāśi periods."""
    out = []
    tops = v.chara_dasha(levels=2)
    for md in tops:
        subs = getattr(md, "sub_periods", None)
        if subs:
            for ad in subs:
                out.append(dict(sign=_sign_of(ad), start=ad.start, end=ad.end))
        else:
            out.append(dict(sign=_sign_of(md), start=md.start, end=md.end))
    return out


def _sign_of(period) -> str:
    """Chara periods carry the sign name in `.note`; fall back to `.lord`."""
    note = getattr(period, "note", None)
    if isinstance(note, str) and note in SIGNS:
        return note
    lord = getattr(period, "lord", None)
    return getattr(lord, "value", str(note))
