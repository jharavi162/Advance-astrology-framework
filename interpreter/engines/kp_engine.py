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


class KPEngine:
    """Isolated KP paddhati — emits data, casts no verdict."""

    name = "kp"

    def evaluate(self, v, profile, start: datetime, end: datetime) -> KPReport:
        _, kps = kp_view(v)
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
            windows=tuple(windows))
