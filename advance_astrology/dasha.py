"""Vimshottari dasha — the principal Vedic timing system.

The 120-year cycle is anchored to the Moon's nakshatra at birth: the fraction
of the nakshatra already traversed by the Moon sets how much of the first major
period (mahadasha) has elapsed, after which the lords proceed in their fixed
order. Each period subdivides among all nine lords in the same proportions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .constants import Planet
from .nakshatra import nakshatra_of

# Mahadasha length in years for each lord.
DASHA_YEARS = {
    Planet.KETU: 7,
    Planet.VENUS: 20,
    Planet.SUN: 6,
    Planet.MOON: 10,
    Planet.MARS: 7,
    Planet.RAHU: 18,
    Planet.JUPITER: 16,
    Planet.SATURN: 19,
    Planet.MERCURY: 17,
}

# The fixed cyclic order of dasha lords.
DASHA_ORDER = [
    Planet.KETU, Planet.VENUS, Planet.SUN, Planet.MOON, Planet.MARS,
    Planet.RAHU, Planet.JUPITER, Planet.SATURN, Planet.MERCURY,
]

TOTAL_YEARS = 120
DAYS_PER_YEAR = 365.25


@dataclass
class DashaPeriod:
    lord: Planet
    start: datetime
    end: datetime
    level: int                       # 1 = maha, 2 = antar, 3 = pratyantar
    sub_periods: list["DashaPeriod"] = field(default_factory=list)
    note: str = ""                   # optional label (e.g. sign for Kalachakra)

    @property
    def years(self) -> float:
        return (self.end - self.start).total_seconds() / 86400.0 / DAYS_PER_YEAR

    def __str__(self) -> str:
        return (
            f"{self.lord.value}: {self.start:%Y-%m-%d} → {self.end:%Y-%m-%d} "
            f"({self.years:.2f}y)"
        )


def _order_from(lord: Planet) -> list[Planet]:
    i = DASHA_ORDER.index(lord)
    return DASHA_ORDER[i:] + DASHA_ORDER[:i]


def _subdivide(
    parent_lord: Planet,
    start: datetime,
    total_days: float,
    level: int,
    max_level: int,
) -> list[DashaPeriod]:
    """Divide a span among all nine lords, weighted by their dasha years."""
    periods: list[DashaPeriod] = []
    cursor = start
    for lord in _order_from(parent_lord):
        span = total_days * DASHA_YEARS[lord] / TOTAL_YEARS
        end = cursor + timedelta(days=span)
        period = DashaPeriod(lord, cursor, end, level)
        if level < max_level:
            period.sub_periods = _subdivide(
                lord, cursor, span, level + 1, max_level
            )
        periods.append(period)
        cursor = end
    return periods


def vimshottari_dasha(
    moon_sidereal_longitude: float,
    birth: datetime,
    levels: int = 2,
    cycles: int = 1,
) -> list[DashaPeriod]:
    """Build the Vimshottari mahadasha timeline from the birth Moon.

    Parameters
    ----------
    moon_sidereal_longitude:
        The Moon's sidereal longitude at birth, in degrees.
    birth:
        Birth datetime (any timezone; periods are returned in the same frame).
    levels:
        1 = mahadashas only, 2 = + antardashas, 3 = + pratyantardashas.
    cycles:
        How many 120-year cycles to project (1 covers a normal lifetime).

    The returned mahadashas span the full nakshatra of birth, so the first
    period begins *before* the birth date by the already-elapsed portion — its
    sub-periods are therefore correctly placed in time. Use
    :func:`current_dasha` to find the active chain on any date.
    """
    nak = nakshatra_of(moon_sidereal_longitude)
    start_lord = nak.lord

    # How far the Moon has already moved through its nakshatra.
    elapsed_days = nak.fraction_traversed * DASHA_YEARS[start_lord] * DAYS_PER_YEAR
    notional_start = birth - timedelta(days=elapsed_days)

    periods: list[DashaPeriod] = []
    cursor = notional_start
    order = _order_from(start_lord)
    for c in range(cycles):
        for lord in order:
            span = DASHA_YEARS[lord] * DAYS_PER_YEAR
            end = cursor + timedelta(days=span)
            maha = DashaPeriod(lord, cursor, end, level=1)
            if levels >= 2:
                maha.sub_periods = _subdivide(lord, cursor, span, 2, levels)
            periods.append(maha)
            cursor = end
    return periods


def current_dasha(
    periods: list[DashaPeriod], when: datetime
) -> list[DashaPeriod]:
    """Return the active period chain (maha, antar, ...) at a given moment."""
    chain: list[DashaPeriod] = []
    level = periods
    while level:
        active = next((p for p in level if p.start <= when < p.end), None)
        if active is None:
            break
        chain.append(active)
        level = active.sub_periods
    return chain
