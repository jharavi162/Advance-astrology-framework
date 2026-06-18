"""Advance Astrology Framework.

A Python astrology engine built on the Skyfield / JPL ephemeris. Computes natal
charts for both the Western tropical and Vedic sidereal systems: planetary
positions, house cusps, chart angles, aspects, nakshatras and Vimshottari
dashas.

Quick start
-----------
>>> from datetime import datetime
>>> from zoneinfo import ZoneInfo
>>> from advance_astrology import NatalChart
>>> chart = NatalChart.create(
...     when=datetime(1990, 5, 15, 14, 30, tzinfo=ZoneInfo("America/New_York")),
...     latitude=40.7128, longitude=-74.0060, name="Example",
... )
>>> print(chart.summary())
"""

from __future__ import annotations

from .angles import ZodiacPosition, format_longitude, to_zodiac
from .aspects import Aspect, find_aspects, find_major_aspects
from .ayanamsa import ayanamsa, available_models as ayanamsa_models
from .chart import NatalChart, PlanetPlacement
from .vedic import VedicChart
from .constants import (
    ASPECTS,
    DEFAULT_PLANETS,
    NAKSHATRAS,
    SIGNS,
    VEDIC_GRAHAS,
    Planet,
)
from .dasha import DashaPeriod, current_dasha, vimshottari_dasha
from .ephemeris import BodyPosition, Ephemeris, get_ephemeris
from .houses import Angles, compute_cusps, house_of
from .nakshatra import NakshatraPosition, nakshatra_of

__version__ = "0.1.0"

__all__ = [
    "NatalChart",
    "VedicChart",
    "PlanetPlacement",
    "Planet",
    "Ephemeris",
    "BodyPosition",
    "get_ephemeris",
    "Aspect",
    "find_aspects",
    "find_major_aspects",
    "Angles",
    "compute_cusps",
    "house_of",
    "ZodiacPosition",
    "to_zodiac",
    "format_longitude",
    "ayanamsa",
    "ayanamsa_models",
    "NakshatraPosition",
    "nakshatra_of",
    "DashaPeriod",
    "vimshottari_dasha",
    "current_dasha",
    "SIGNS",
    "ASPECTS",
    "NAKSHATRAS",
    "DEFAULT_PLANETS",
    "VEDIC_GRAHAS",
    "__version__",
]
