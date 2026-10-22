"""KP (Krishnamurti Paddhati) engine — DATA ONLY.

KP is the promise / denial / quality instrument (never the timing clock — that's
the daśā engine). This engine reports the KP *data* and lets the AI draw the
yes/no: the primary cusp's sub-lord and everything it signifies, split into the
fulfilment vs negation houses it touches, plus the running daśā-chain's
fulfil/negate counts per window. No verdict, no score — the interpretation
("sub-lord signifies 6/12 alongside 7 → marries but separative") is the AI's.

Reads KP significators on the KP ayanāṃśa + Placidus sub-chart. Wraps existing
computation (never recomputes a number); the Vimśottari spine and KP view come
from `interpreter.engines._shared`, so this engine has no tie to the legacy
`event_evidence` monolith.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from advance_astrology.constants import VEDIC_GRAHAS, Planet
from advance_astrology.vedic.kp import kp_chain
from interpreter.engines._shared import (
    chain_lords, kp_score, kp_view, pratyantar_midpoints,
)


@dataclass(frozen=True)
class KPWindow:
    """A pratyantar date with the running chain's fulfil/negate counts — raw
    data; the AI reads whether the daśā-lords signify the matter."""
    when: datetime
    chain: tuple[str, ...]
    fulfil: int
    negate: int


@dataclass(frozen=True)
class KPReport:
    domain: str
    cusp_sublord: str                 # the primary cusp's sub-lord (KP's arbiter)
    cusp_signifies: tuple[int, ...]   # every house it signifies
    hits_fulfil: tuple[int, ...]      # of those, the fulfilment houses (raw)
    hits_negate: tuple[int, ...]      # of those, the negation houses (raw)
    windows: tuple[KPWindow, ...]     # running-chain fulfil/negate per pratyantar
    plurality: dict | None = None     # marriage family: KSK more-than-one-marriage data
    # the matter's secondary houses (houses[1:]): (house, cusp sub-lord, signifies)
    other_cusps: tuple[tuple[int, str, tuple[int, ...]], ...] = ()


_DUAL_SIGNS = frozenset({2, 5, 8, 11})   # Gemini, Virgo, Sagittarius, Pisces
_CLASSICAL = frozenset(VEDIC_GRAHAS)      # the nine grahas (no outer planets)


def plurality_data(vkp, kps) -> dict:
    """KP Reader IV (KSK) raw tests for more than one marriage — DATA, no verdict.
    p.84: "if the sublord of 7th cusp is either Mercury or any planet occupying
    dual Sign, more than one wife"; p.~153: "if it is in any manner connected
    with a dual sign or a dual planet, second marriage is shown" (his example:
    7th sub-lord Venus conjoined Mercury); p.~147: 2nd-cusp sub-lord connected
    with 7 → legal second marriage, with 11 only → attachment, not marriage."""
    csl =kp_chain(kps.cusps[7]).sub_lord
    star = kps.star_lord[csl]
    conj = sorted(p.value for p, s in vkp.signs.items()
                  if p != csl and p in _CLASSICAL and s == vkp.signs[csl])
    csl2 = kp_chain(kps.cusps[2]).sub_lord
    sig2 = set(kps.planet_signifies(csl2))
    return {
        "csl7": csl.value,
        "csl7_is_mercury": csl == Planet.MERCURY,
        "csl7_in_dual_sign": vkp.signs[csl] in _DUAL_SIGNS,
        "csl7_star_lord": star.value,
        "csl7_star_lord_dual": star == Planet.MERCURY or vkp.signs[star] in _DUAL_SIGNS,
        "csl7_conjoined": tuple(conj),
        "csl7_conjoined_dual": any(
            p == Planet.MERCURY.value or vkp.signs[Planet(p)] in _DUAL_SIGNS
            for p in conj),
        "csl2": csl2.value,
        "csl2_signifies_7": 7 in sig2,
        "csl2_signifies_11": 11 in sig2,
    }


def _is_marriage_family(profile) -> bool:
    return not profile.rupture_matter and \
        (profile.base_domain or profile.name) == "marriage"


class KPEngine:
    """Isolated KP paddhati — emits data, casts no verdict."""

    name = "kp"

    def evaluate(self, v, profile, start: datetime, end: datetime) -> KPReport:
        vkp, kps = kp_view(v)
        primary = profile.houses[0]
        cusp_sub = kp_chain(kps.cusps[primary]).sub_lord
        sig = kps.planet_signifies(cusp_sub)
        sset = set(sig)

        windows = []
        for d in pratyantar_midpoints(v, start, end):
            chain = chain_lords(v, d, levels=3)
            fulfil = negate = 0
            for lord in chain:
                a, b = kp_score(kps, lord, profile)
                fulfil += a
                negate += b
            windows.append(KPWindow(d, tuple(c.value[:2] for c in chain),
                                    fulfil, negate))

        return KPReport(
            domain=profile.name,
            cusp_sublord=cusp_sub.value,
            cusp_signifies=tuple(sig),
            hits_fulfil=tuple(sorted(sset & profile.fulfil_houses)),
            hits_negate=tuple(sorted(sset & profile.negate_houses)),
            windows=tuple(windows),
            plurality=plurality_data(vkp, kps) if _is_marriage_family(profile) else None,
            other_cusps=tuple(
                (h, sl.value, tuple(kps.planet_signifies(sl)))
                for h in profile.houses[1:]
                for sl in (kp_chain(kps.cusps[h]).sub_lord,)))
