"""KP (Krishnamurti Paddhati) engine — the first isolated paddhati.

KP judged in isolation, emitting the standardized `EngineResult`. It answers two
questions with KP doctrine ALONE (no other school consulted):

  • PROMISE (standing) — the sub-lord of the matter's primary cusp is KP's final
    arbiter. If it signifies a fulfilment house the matter is promised; if it
    signifies only negation houses it is denied. (KP Readers III & VI.)

  • TIMING (per window) — a period delivers when the running Vimśottari daśā
    chain (MD>AD>PD) lords SIGNIFY the fulfilment houses and fulfilment ≥
    negation. Each evaluation date is scored to a normalized [0,1] grade.

The engine WRAPS existing computation — it never recomputes a number the engine
already owns (CLAUDE.md). Raw significators come from
`advance_astrology.vedic.kp`; the KP sub-chart (KP ayanāṃśa + Placidus) and the
shared Vimśottari timing spine are reused from `event_evidence`. The KP-specific
interpretation (promise, fulfil/negate scoring, grade) lives HERE, so this file
alone defines "what KP says" and can be validated on doctrine alone.
"""

from __future__ import annotations

from datetime import datetime

from advance_astrology.vedic.kp import kp_chain
from interpreter.engines.base import EngineResult, TimelinePoint

# Shared, KP-agnostic infrastructure (the Vimśottari timing spine + KP sub-chart).
# Reused, not reimplemented, so this engine can never drift from the canonical
# evaluation grid. A later refactor promotes these to a neutral `timing` module.
from interpreter.event_evidence import (
    _chain_lords, _kp_score, _kp_view, _pratyantar_midpoints,
)


def kp_window_grade(fulfil: int, negate: int) -> float:
    """Normalize a window's KP significator counts to a [0,1] delivery grade.

    Anchored to the graded discriminator KP timing already uses (fulfil ≥
    negation ⇒ full weight; some fulfilment but out-weighed ⇒ contested; chain
    silent ⇒ weak-neutral), extended with an explicit ADVERSE band for the KP
    denial signature (chain-lords signify ONLY negation). Pure and total — a
    named function precisely so the mapping is testable without any event date.
    """
    if fulfil == 0 and negate == 0:
        return 0.30                       # chain silent on the matter — neutral
    if fulfil >= max(1, negate):
        return 1.00                       # fulfilment signified and dominant
    if fulfil >= 1:
        return 0.60                       # fulfilment present but out-weighed — contested
    return 0.15                           # only negation signified — KP denial signature


class KPEngine:
    """Isolated KP paddhati implementing the `Engine` contract."""

    name = "kp"

    def evaluate(self, v, profile, start: datetime, end: datetime) -> EngineResult:
        # KP MUST be read on its own ayanāṃśa + Placidus cusps, not the main chart.
        _, kps = _kp_view(v)

        # --- STANDING: promise by the primary cusp's sub-lord --------------- #
        primary = profile.houses[0]
        cusp_sub = kp_chain(kps.cusps[primary]).sub_lord
        sig = set(kps.planet_signifies(cusp_sub))
        promised = bool(sig & profile.fulfil_houses)
        denied = (not promised) and bool(sig & profile.negate_houses)
        verdict = "NO" if denied else "YES" if promised else "UNCERTAIN"
        notes = [
            f"primary cusp H{primary} sub-lord = {cusp_sub.value}; "
            f"signifies {sorted(sig)} "
            f"(fulfil={sorted(profile.fulfil_houses)}, "
            f"negate={sorted(profile.negate_houses)})",
        ]
        if denied:
            notes.append("sub-lord signifies ONLY negation → KP denies the matter")

        # --- TIMING: fulfil-vs-negate of the running daśā chain per window --- #
        points = []
        for d in _pratyantar_midpoints(v, start, end):
            chain = _chain_lords(v, d, levels=3)
            fulfil = negate = 0
            for lord in chain:
                a, b = _kp_score(kps, lord, profile)
                fulfil += a
                negate += b
            points.append(TimelinePoint(
                when=d,
                score=kp_window_grade(fulfil, negate),
                chain=tuple(c.value[:2] for c in chain),
                detail={"fulfil": fulfil, "negate": negate,
                        "chain_lords": [c.value for c in chain]},
            ))

        return EngineResult(
            engine=self.name, domain=profile.name, verdict=verdict,
            promised=promised, timeline=tuple(points), notes=tuple(notes),
        )
