"""Isolated paddhati engines behind one standardized contract.

Each engine is a self-contained evaluator: same `evaluate(v, profile, start,
end)` signature, same `EngineResult` output, no engine aware of any other. This
is the per-engine-observability foundation — see every school's standalone
testimony first, validate each in isolation, THEN build the Samanvaya fan-in on
top of trustworthy parts.
"""

from interpreter.engines.base import Engine, EngineResult, TimelinePoint
from interpreter.engines.kp_engine import KPEngine, kp_window_grade
from interpreter.engines.dasha_timing import DashaTimingEngine, DashaTimingReport
from interpreter.engines.jaimini import JaiminiEngine, JaiminiReport
from interpreter.engines.tajika import TajikaEngine, TajikaReport
from interpreter.engines.samanvaya import assemble, SamanvayaBundle
from interpreter.engines.router import classify, route

# Registry of isolated per-school engines behind one contract. Each is data-only
# (or, for KP, promise/quality) — none carries a verdict; the AI interprets.
ENGINES: dict[str, object] = {
    "kp": KPEngine(),                     # promise / quality / yes-no
    "dasha_timing": DashaTimingEngine(),  # event clock (Vimśottari + Chara + transit)
    "jaimini": JaiminiEngine(),           # Arudha / UL / chara-kāraka / Chara rāśi
    "tajika": TajikaEngine(),             # annual Varṣaphal / Muntha / Sāham
}


def samanvaya(v, profile, start, end, *, intent=None, question=None):
    """Route the question and bundle every engine's raw data for the AI."""
    return assemble(ENGINES, v, profile, start, end, intent=intent, question=question)


__all__ = [
    "Engine", "EngineResult", "TimelinePoint",
    "KPEngine", "kp_window_grade",
    "DashaTimingEngine", "DashaTimingReport",
    "JaiminiEngine", "JaiminiReport",
    "TajikaEngine", "TajikaReport",
    "SamanvayaBundle", "assemble", "samanvaya",
    "classify", "route", "ENGINES",
]
