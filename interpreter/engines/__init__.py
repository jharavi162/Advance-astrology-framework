"""Isolated paddhati engines behind one standardized contract.

Each engine is a self-contained evaluator: same `evaluate(v, profile, start,
end)` signature, same `EngineResult` output, no engine aware of any other. This
is the per-engine-observability foundation — see every school's standalone
testimony first, validate each in isolation, THEN build the Samanvaya fan-in on
top of trustworthy parts.
"""

from interpreter.engines.base import Engine, EngineResult, TimelinePoint
from interpreter.engines.kp_engine import KPEngine, kp_window_grade

# Registry of isolated engines (grows one entry per school as they're pulled out).
ENGINES: dict[str, Engine] = {
    "kp": KPEngine(),
}

__all__ = [
    "Engine", "EngineResult", "TimelinePoint",
    "KPEngine", "kp_window_grade", "ENGINES",
]
