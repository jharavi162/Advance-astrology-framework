"""Blind-backtest harness for an isolated engine.

Given a chart and a KNOWN event date, it reports WHERE that event falls in the
engine's own timeline — did the engine's standalone testimony point there? It
measures; it never tunes. No engine parameter is changed from the result
(CLAUDE.md: the blind past-event test detects coverage/logic bugs, never fits
the native's history). Engine-generic: works for KP today, every school later.

Metrics per (chart, event, engine):
  • verdict / promised       — the engine's standing answer, on its own
  • nearest_score            — the engine's score at the window closest to the event
  • nearest_percentile       — how that window ranks among all the engine's windows
                               (1.0 = the engine's strongest window IS the event window)
  • best_gap_days            — days between the event and the engine's single top window
  • hit                      — event within `tol_days` of a top-quantile window
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

UTC = timezone.utc


@dataclass(frozen=True)
class BacktestResult:
    engine: str
    domain: str
    event_date: datetime
    verdict: str
    promised: bool | None
    nearest_window: datetime | None
    nearest_score: float
    nearest_percentile: float          # rank of the nearest window's score in [0,1]
    best_window: datetime | None
    best_score: float
    best_gap_days: int | None          # |event − best window|
    hit: bool

    def summary(self) -> str:
        nd = f"{self.nearest_window:%Y-%m-%d}" if self.nearest_window else "—"
        bd = f"{self.best_window:%Y-%m-%d}" if self.best_window else "—"
        return (f"[{self.engine}/{self.domain}] event {self.event_date:%Y-%m-%d} → "
                f"verdict={self.verdict} | nearest window {nd} "
                f"score={self.nearest_score:.2f} pct={self.nearest_percentile:.0%} | "
                f"top window {bd} gap={self.best_gap_days}d | "
                f"{'HIT' if self.hit else 'miss'}")


def backtest_engine(engine, v, profile, event_date: datetime, *,
                    window_years: int = 2, tol_days: int = 60,
                    top_q: float = 0.75) -> BacktestResult:
    """Run `engine` over a span bracketing `event_date` and locate the event in
    its timeline. `top_q` sets the quantile a window must beat to count as the
    engine 'firing'; `tol_days` is how close the event must fall to such a window
    to score a hit."""
    if event_date.tzinfo is None:
        event_date = event_date.replace(tzinfo=UTC)
    start = event_date - timedelta(days=365 * window_years)
    end = event_date + timedelta(days=365 * window_years)
    res = engine.evaluate(v, profile, start, end)
    pts = list(res.timeline)

    if not pts:
        return BacktestResult(engine.name, profile.name, event_date,
                              res.verdict, res.promised, None, 0.0, 0.0,
                              None, 0.0, None, False)

    scores = sorted(p.score for p in pts)
    # window closest in time to the actual event
    nearest = min(pts, key=lambda p: abs((p.when - event_date).days))
    # percentile rank of that window's score among all windows (fraction ≤ it)
    le = sum(1 for s in scores if s <= nearest.score)
    nearest_pct = le / len(scores)
    # the engine's single strongest window
    best = max(pts, key=lambda p: p.score)
    best_gap = abs((best.when - event_date).days)

    # HIT = a window scoring in the top quantile lies within tol_days of the event
    q_idx = max(0, int(top_q * (len(scores) - 1)))
    threshold = scores[q_idx]
    hit = any(p.score >= threshold and abs((p.when - event_date).days) <= tol_days
              for p in pts)

    return BacktestResult(
        engine.name, profile.name, event_date, res.verdict, res.promised,
        nearest.when, nearest.score, nearest_pct,
        best.when, best.score, best_gap, hit)


def backtest_batch(engine, cases) -> list[BacktestResult]:
    """`cases` = iterable of (VedicChart, DomainProfile, event_date). Returns one
    result per case; caller aggregates (hit-rate, mean percentile) across a
    PANEL of public charts — the honest way to read an engine's accuracy."""
    return [backtest_engine(engine, v, prof, ev) for v, prof, ev in cases]
