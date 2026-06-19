"""Nakshatras (lunar mansions) and their padas."""

from __future__ import annotations

from dataclasses import dataclass

from .angles import norm360
from .constants import (
    NAKSHATRA_ARC,
    NAKSHATRA_LORDS,
    NAKSHATRAS,
    Planet,
)

PADA_ARC = NAKSHATRA_ARC / 4.0  # 3°20'


@dataclass(frozen=True)
class NakshatraPosition:
    index: int            # 0..26
    name: str
    lord: Planet          # Vimshottari dasha lord
    pada: int             # 1..4
    degree_in_nakshatra: float
    fraction_traversed: float  # [0, 1) progress through the nakshatra

    def __str__(self) -> str:
        return f"{self.name} (pada {self.pada}, lord {self.lord.value})"


def nakshatra_of(sidereal_longitude: float) -> NakshatraPosition:
    """Resolve a sidereal ecliptic longitude into its nakshatra and pada."""
    lon = norm360(sidereal_longitude)
    index = int(lon // NAKSHATRA_ARC)
    degree_in = lon - index * NAKSHATRA_ARC
    pada = int(degree_in // PADA_ARC) + 1
    return NakshatraPosition(
        index=index,
        name=NAKSHATRAS[index],
        lord=NAKSHATRA_LORDS[index],
        pada=pada,
        degree_in_nakshatra=degree_in,
        fraction_traversed=degree_in / NAKSHATRA_ARC,
    )
