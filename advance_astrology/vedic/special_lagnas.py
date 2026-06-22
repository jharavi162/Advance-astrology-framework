"""Special ascendants (vishesha lagnas).

Bhava, Hora and Ghati lagnas advance from the Sun's sunrise longitude at fixed
rates with elapsed time; Sree Lagna derives from the Moon's nakshatra progress;
Indu Lagna from the kala values of the 9th lords.
"""

from __future__ import annotations

from datetime import datetime

from ..angles import norm360, to_zodiac
from ..constants import NAKSHATRA_ARC, RULERSHIPS, SIGNS, Planet
from ..nakshatra import nakshatra_of


def _ghatis_since_sunrise(birth_utc: datetime, sunrise: datetime) -> float:
    """Elapsed time from sunrise in ghatis (1 ghati = 24 minutes)."""
    seconds = (birth_utc - sunrise).total_seconds()
    return seconds / 60.0 / 24.0


def bhava_lagna(sun_long_at_sunrise: float, ghatis: float) -> float:
    """Bhava Lagna: advances one sign per 5 ghatis (i.e. 6° per ghati)."""
    return norm360(sun_long_at_sunrise + ghatis * (30.0 / 5.0))


def hora_lagna(sun_long_at_sunrise: float, ghatis: float) -> float:
    """Hora Lagna: advances one sign per 2.5 ghatis (12° per ghati)."""
    return norm360(sun_long_at_sunrise + ghatis * (30.0 / 2.5))


def ghati_lagna(sun_long_at_sunrise: float, ghatis: float) -> float:
    """Ghati (Ghatika) Lagna: advances one sign per ghati (30° per ghati)."""
    return norm360(sun_long_at_sunrise + ghatis * 30.0)


def sree_lagna(ascendant: float, moon_sid_long: float) -> float:
    """Sree Lagna from the Moon's progress through its nakshatra.

    The fraction of the nakshatra the Moon has traversed is mapped onto a full
    sign (30°) and added to the ascendant.
    """
    nak = nakshatra_of(moon_sid_long)
    progress = (moon_sid_long % NAKSHATRA_ARC) / NAKSHATRA_ARC
    return norm360(ascendant + progress * 30.0 * 9.0)


# Kala (light units) of the planets for Indu Lagna.
INDU_KALA = {
    Planet.SUN: 30, Planet.MOON: 16, Planet.MARS: 6, Planet.MERCURY: 8,
    Planet.JUPITER: 10, Planet.VENUS: 12, Planet.SATURN: 1,
}


def indu_lagna(ascendant_sign: int, moon_sign: int,
               planet_signs: dict[Planet, int]) -> int:
    """Indu Lagna sign index.

    Sum the kalas of the lords of the 9th house from the ascendant and from the
    Moon, take the remainder mod 12, and count that many signs from the Moon.
    """
    ninth_from_asc = (ascendant_sign + 8) % 12
    ninth_from_moon = (moon_sign + 8) % 12
    lord_a = RULERSHIPS[SIGNS[ninth_from_asc]]
    lord_m = RULERSHIPS[SIGNS[ninth_from_moon]]
    total = INDU_KALA[lord_a] + INDU_KALA[lord_m]
    rem = total % 12
    if rem == 0:
        rem = 12
    return (moon_sign + rem - 1) % 12
