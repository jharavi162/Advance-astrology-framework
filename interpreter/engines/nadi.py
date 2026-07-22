"""Nāḍī (Bhṛgu-Nandi) engine — DATA ONLY.

Planets AS kārakas, houses secondary. Reports the BNN reading data: the matter's
descriptor kāraka, the timing kāraka(s), the kāraka-saṅga nature, the natal
degree-ordered CHAIN (the Nāḍī chronology), the Bhṛgu Bindu, and the transit
windows where slow movers (Guru-jeeva / Śani-sanction) hold a golden relation to
the kārakas or the Bhṛgu Bindu. No score, no verdict — the AI narrates the story.

Sources: R.G. Rao (Bhṛgu Nandi Nādi); Satyanarayana Naik. Golden relation =
conjunction or the 1/5/9 trine only (not the 7th). A retrograde (vakri) planet is
reckoned one sign back; nodes at their actual sign. Self-contained — depends on
`advance_astrology` only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from advance_astrology import Planet
from advance_astrology.constants import SIGNS

# Matter → its Nāḍī descriptor kāraka. "kalatra" is gender-aware (♂ Venus / ♀ Mars).
NADI_KARAKAS = {
    "marriage": "kalatra", "divorce": "kalatra",
    "career": Planet.SATURN, "children": Planet.JUPITER,
    "education": Planet.MERCURY, "wealth": Planet.VENUS,
    "mother": Planet.MOON, "father": Planet.SUN,
    "illness": Planet.SATURN, "relocation": Planet.RAHU,
    "foreign": Planet.RAHU, "property": Planet.MARS,
}

_NADI_REL = {0, 4, 8}     # conjunction + 1/5/9 trine — the golden relations
_CHAIN_BODIES = (Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
                 Planet.JUPITER, Planet.VENUS, Planet.SATURN,
                 Planet.RAHU, Planet.KETU)
_SIGNIF = {
    Planet.SUN: "authority/govt/father; influential, ego-driven",
    Planet.MOON: "emotions/instability; caring but changeable",
    Planet.MARS: "husband(♀)/passion/drive; the cutter & executor",
    Planet.MERCURY: "communication/business; witty, younger-seeming",
    Planet.JUPITER: "jeeva/blessing/expansion; mature, fortunate",
    Planet.VENUS: "spouse(♂)/love/quality-of-marriage; comfort, romance",
    Planet.SATURN: "delay/karma/cold; older/serious, karmic bond",
    Planet.RAHU: "foreign/inter-caste/unconventional; sharp",
    Planet.KETU: "cut/break/detachment; separation, disinterest",
}


def _spec(profile):
    return NADI_KARAKAS.get(profile.name) or \
        NADI_KARAKAS.get(getattr(profile, "base_domain", None) or "")


def _descriptor_karaka(v, profile) -> Planet:
    spec = _spec(profile)
    if spec == "kalatra":
        g = (getattr(v, "gender", "") or "").lower()
        return Planet.MARS if g.startswith("f") else Planet.VENUS
    return spec or profile.natural_karaka or Planet.JUPITER


def _timing_karakas(v, profile) -> list:
    """Kārakas whose transit-activation TIMES the event. Venus is the universal
    marriage event-kāraka; a female chart additionally reads Mars (R.G. Rao)."""
    if _spec(profile) == "kalatra":
        g = (getattr(v, "gender", "") or "").lower()
        return [Planet.VENUS, Planet.MARS] if g.startswith("f") else [Planet.VENUS]
    return [_descriptor_karaka(v, profile)]


def _retro(v, p) -> bool:
    try:
        return bool(v.natal.placements[p].retrograde) and p not in (Planet.RAHU, Planet.KETU)
    except Exception:
        return False


def _nadi_sign(lon, retro=False) -> int:
    s = int(lon // 30)
    return (s - 1) % 12 if retro else s


@dataclass(frozen=True)
class ChainMember:
    planet: str
    degree: float
    relation: str          # conjunction | trine-5th | trine-9th
    retrograde: bool
    when: str              # HERO | before/already | after/follows (degree chronology)
    signifies: str


@dataclass(frozen=True)
class NadiReport:
    domain: str
    descriptor_karaka: str            # spouse/matter descriptor
    timing_karakas: tuple[str, ...]   # event timers
    nature: tuple[str, ...]           # kāraka-saṅga flavour notes
    chain: tuple[ChainMember, ...]    # degree-ordered BNN chronology
    bhrigu_bindu_sign: str
    jeeva_windows: tuple[tuple[datetime, datetime, str], ...]   # transit Jupiter golden→kāraka
    sanction_windows: tuple[tuple[datetime, datetime, str], ...] # transit Saturn golden→kāraka
    bb_windows: tuple[tuple[datetime, datetime, str], ...]       # slow mover on Bhṛgu Bindu


def _nature(v, profile) -> list:
    nk = _descriptor_karaka(v, profile)
    s = v.signs[nk]
    trines = {s, (s + 4) % 12, (s + 8) % 12}
    notes = []
    if v.signs[Planet.RAHU] in trines:
        notes.append("Rāhu-saṅga → sudden/unconventional (love/inter-community)")
    if v.signs[Planet.KETU] in trines:
        notes.append("Ketu-saṅga → delay / talks-break / vairāgya")
    if _retro(v, nk):
        notes.append("vakri kāraka → repeat/revisit pattern")
    return notes


def _chain(v, profile) -> list:
    hero = _descriptor_karaka(v, profile)
    hero_lon = float(v.longitudes[hero])
    hero_sign = _nadi_sign(hero_lon, _retro(v, hero))
    hero_deg = hero_lon % 30.0
    rows = []
    for p in _CHAIN_BODIES:
        lon = float(v.longitudes[p])
        retro = _retro(v, p)
        off = (_nadi_sign(lon, retro) - hero_sign) % 12
        if off not in _NADI_REL:
            continue
        deg = lon % 30.0
        rel = "conjunction" if off == 0 else "trine-5th" if off == 4 else "trine-9th"
        when = ("HERO (kāraka — the pivot)" if p == hero
                else "before / already (pre-existing)" if deg < hero_deg
                else "after (post-event / follows)")
        rows.append(ChainMember(p.value, round(deg, 1), rel, retro, when,
                                _SIGNIF.get(p, "")))
    rows.sort(key=lambda r: r.degree)
    return rows


def _golden_windows(tr, transit, natal_lon, start, end, label, orb=9.0):
    out = []
    for ang in (0.0, 120.0, 240.0):
        for w in tr.conjunction_windows(transit, (natal_lon + ang) % 360.0,
                                        start, end, orb=orb, step_days=10.0):
            out.append((w.start, w.end, label))
    return out


class NadiEngine:
    name = "nadi"

    def evaluate(self, v, profile, start: datetime, end: datetime) -> NadiReport:
        tr = v.transits()
        timers = _timing_karakas(v, profile)
        jeeva, sanction = [], []
        for k in timers:
            nl = float(v.longitudes[k])
            jeeva += _golden_windows(tr, Planet.JUPITER, nl, start, end,
                                     f"Guru-jeeva → {k.value}")
            sanction += _golden_windows(tr, Planet.SATURN, nl, start, end,
                                        f"Śani-sanction → {k.value}")
        bb = v.bhrigu_bindu()
        bb_windows = []
        for slow in (Planet.JUPITER, Planet.SATURN):
            for w in tr.conjunction_windows(slow, bb, start, end, orb=4.0, step_days=10.0):
                bb_windows.append((w.start, w.end, f"{slow.value} on Bhṛgu Bindu"))
        jeeva.sort(); sanction.sort(); bb_windows.sort()

        return NadiReport(
            domain=profile.name,
            descriptor_karaka=_descriptor_karaka(v, profile).value,
            timing_karakas=tuple(k.value for k in timers),
            nature=tuple(_nature(v, profile)),
            chain=tuple(_chain(v, profile)),
            bhrigu_bindu_sign=SIGNS[int(bb // 30)],
            jeeva_windows=tuple(jeeva), sanction_windows=tuple(sanction),
            bb_windows=tuple(bb_windows))
