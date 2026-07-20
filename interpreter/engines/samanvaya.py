"""Samanvaya — assemble every routed engine's DATA into one bundle for the AI.

This is deliberately NOT the old convergence math. It runs no scoring, casts no
vote, and reaches no verdict. It simply routes the question to the right engines,
runs each, and hands back a dict of `{engine_name: engine_report}` plus the
intent and the significators in play. The AI reads the bundle, interprets each
school per `docs/AI_EVENT_TIMING_GUIDE.md` / `AI_TRIANGULATION_PROMPT.md`, and
states its own triangulated confidence. Confidence is a JUDGMENT, not a number
this layer computes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from interpreter.engines.router import classify, route


@dataclass
class SamanvayaBundle:
    domain: str
    intent: str
    engines_run: list                       # engine names, in routing order
    reports: dict = field(default_factory=dict)   # {engine_name: report}

    def get(self, engine: str):
        return self.reports.get(engine)


def assemble(registry, v, profile, start: datetime, end: datetime, *,
             intent: str | None = None, question: str | None = None) -> SamanvayaBundle:
    """Route → run each engine → bundle the raw reports. `registry` is the
    `{name: engine}` map (interpreter.engines.ENGINES). `intent` may be given
    explicitly or inferred from `question`."""
    intent = intent or (classify(question) if question else "timing")
    names = [n for n in route(intent) if n in registry]
    reports = {}
    for name in names:
        reports[name] = registry[name].evaluate(v, profile, start, end)
    return SamanvayaBundle(domain=profile.name, intent=intent,
                           engines_run=names, reports=reports)
