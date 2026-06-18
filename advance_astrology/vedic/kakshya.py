"""Kakṣyā — the eight 3°45' sub-zones of each sign for micro-timing transits.

Each 30° sign is split into eight kakṣyās of 3°45', ruled in a fixed order by
Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon and the Lagna. A transiting
planet delivers its result while crossing a kakṣyā whose lord contributed a
bindu to that planet's Bhinnāṣṭakavarga in the sign — narrowing an event to a
few days.
"""

from __future__ import annotations

from ..angles import to_zodiac
from ..constants import Planet
from .ashtakavarga import contributor_gives_bindu

KAKSHYA_ARC = 30.0 / 8.0   # 3°45'

# Kakṣyā lords in order from 0° of each sign.
KAKSHYA_LORDS = [Planet.SATURN, Planet.JUPITER, Planet.MARS, Planet.SUN,
                 Planet.VENUS, Planet.MERCURY, Planet.MOON, "Lagna"]


def kakshya_index(longitude: float) -> int:
    """Kakṣyā number 0..7 within the sign."""
    deg = to_zodiac(longitude).degree_in_sign
    return int(deg // KAKSHYA_ARC)


def kakshya_lord(longitude: float):
    """The planet (or 'Lagna') ruling the kakṣyā at this longitude."""
    return KAKSHYA_LORDS[kakshya_index(longitude)]


def transit_active(
    transit_planet: Planet,
    transit_longitude: float,
    planet_signs: dict[Planet, int],
    ascendant_sign: int,
) -> bool:
    """Whether a transit delivers results in its current kakṣyā.

    True when the kakṣyā lord contributed a bindu to the transiting planet's
    BAV in the sign being transited.
    """
    lord = kakshya_lord(transit_longitude)
    sign = to_zodiac(transit_longitude).sign_index
    return contributor_gives_bindu(transit_planet, lord, sign,
                                   planet_signs, ascendant_sign)
