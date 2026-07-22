"""Engine contract — the one shape every paddhati engine shares.

Each engine is a self-contained evaluator with the SAME entry point,
``evaluate(v, profile, start, end)``, returning that school's own **data**
report (KPReport, DashaTimingReport, JaiminiReport, TajikaReport). No engine
returns a score or a verdict — the interpretation is the AI's, per
``docs/AI_EVENT_TIMING_GUIDE.md``. The orchestrator (Samanvaya) calls engines
through this signature without knowing any engine's internal rules.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class Engine(Protocol):
    """What every paddhati engine implements. `name` identifies the school;
    `evaluate` is the single decoupled entry point the orchestrator calls and
    returns the engine's own data report."""
    name: str

    def evaluate(self, v, profile, start: datetime, end: datetime):
        ...
