"""Engine contract — the standardized, decoupled output interface every
paddhati (KP, Jaimini, Parāśari, Tājika, Nāḍī) must implement.

This is the in-process realisation of "each engine is a self-contained
evaluator with a visible, standalone output": an orchestrator can call any
engine through the SAME `evaluate(...)` signature and read back the SAME
`EngineResult` shape, without knowing the engine's internal rules. No network,
no serialization — the isolation is at the interface, not the deployment.

An `EngineResult` carries two independent things per matter:
  • a STANDING verdict — does this engine, on its own, judge the matter promised?
  • a TIMELINE — one normalized point per evaluation date, `score ∈ [0.0, 1.0]`,
    "how strongly does THIS engine alone say the matter delivers here?".

Aggregation across engines (the Samanvaya layer) is deliberately NOT here — an
engine never sees another engine. It only reports its own testimony.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class TimelinePoint:
    """One evaluation date's normalized testimony from a single engine."""
    when: datetime
    score: float                       # normalized [0.0, 1.0] — engine's own reading
    chain: tuple[str, ...] = ()         # daśā chain lords at `when` (transparency)
    detail: dict = field(default_factory=dict)   # engine-specific raw evidence

    def __post_init__(self):
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"score {self.score} outside [0,1] — contract breach")


@dataclass(frozen=True)
class EngineResult:
    """The complete, standalone testimony of one engine on one matter."""
    engine: str                        # "kp", "jaimini", …
    domain: str                        # the matter's name
    verdict: str                       # "YES" | "NO" | "UNCERTAIN" (promise, this engine alone)
    promised: bool | None              # engine's boolean promise (None = can't say)
    timeline: tuple[TimelinePoint, ...]
    notes: tuple[str, ...] = ()

    def best(self) -> TimelinePoint | None:
        """The window this engine alone points to most strongly."""
        return max(self.timeline, key=lambda p: p.score, default=None)

    def as_rows(self) -> list[tuple]:
        """The strict `[date, factor_id, score]` normalized-array view (the data
        contract the Samanvaya spec asks for). `factor_id` = the engine name, so a
        fan-in layer can stack every engine's rows into one matrix."""
        return [(p.when, self.engine, p.score) for p in self.timeline]


@runtime_checkable
class Engine(Protocol):
    """What every paddhati engine implements. `name` identifies the school;
    `evaluate` is the single decoupled entry point the orchestrator calls."""
    name: str

    def evaluate(self, v, profile, start: datetime, end: datetime) -> EngineResult:
        ...
