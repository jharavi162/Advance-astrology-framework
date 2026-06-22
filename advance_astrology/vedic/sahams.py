"""Tājika Sahams — sensitive longitudes (Arabic-parts analogues) used in
Tājika/Varṣaphal for event sensitivity, marriage among them.

A Saham is a derived point ``A − B + Lagna`` (by a day birth) with ``A`` and
``B`` swapped for a night birth. The point and its rāśi lord become active
timers: an event tends to fire when the Saham's dispositor runs in the daśā or
when a slow transit (esp. the Jupiter+Saturn double-transit) lights up the
Saham's sign.

Only well-attested formulas are exposed as primary; textual variants are noted.
These are pure calculators — they take longitudes and return points; the
interpretation/triangulation is done by the caller.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..angles import norm360, to_zodiac
from ..constants import RULERSHIPS, SIGNS, Planet

# Houses above the horizon (Descendant → MC → Ascendant). Used to decide a
# day vs night birth without re-deriving sunrise: the Sun is above the horizon
# during the day.
_ABOVE_HORIZON = {7, 8, 9, 10, 11, 12}


@dataclass(frozen=True)
class Saham:
    name: str
    longitude: float

    @property
    def sign_index(self) -> int:
        return to_zodiac(self.longitude).sign_index

    @property
    def sign(self) -> str:
        return SIGNS[self.sign_index]

    @property
    def lord(self) -> Planet:
        return RULERSHIPS[SIGNS[self.sign_index]]

    def __str__(self) -> str:
        return f"{self.name}: {to_zodiac(self.longitude)} (lord {self.lord.value})"


def _saham(a_lon: float, b_lon: float, asc_lon: float, is_day: bool) -> float:
    """Core Tājika saham: ``A − B + Lagna`` by day, ``B − A + Lagna`` by night."""
    val = (a_lon - b_lon) if is_day else (b_lon - a_lon)
    return norm360(val + asc_lon)


def is_day_birth(chart) -> bool:
    """Day birth ⇔ the Sun is above the horizon (whole-sign houses 7–12)."""
    return chart.house_of(Planet.SUN) in _ABOVE_HORIZON


def vivaha_saham(longitudes: dict[Planet, float], asc_lon: float,
                 is_day: bool) -> Saham:
    """Vivāha (marriage) Saham = Venus − Saturn + Lagna (reversed at night).

    The standard Tājika marriage point; its rāśi lord and the double-transit on
    its sign are prime marriage timers.
    """
    lon = _saham(longitudes[Planet.VENUS], longitudes[Planet.SATURN],
                 asc_lon, is_day)
    return Saham("Vivaha", lon)


def punarvivaha_saham(longitudes: dict[Planet, float], asc_lon: float,
                      is_day: bool) -> Saham:
    """Punar-vivāha (re-marriage) Saham — *documented variant*.

    Punarvivāha is not in the classical 36-Saham core; here we use the
    commonly-cited reverse of the Vivāha formula (Saturn − Venus + Lagna by
    day), read as the sensitive point of a second union. Treat as a secondary,
    corroborating timer — not a sole authority.
    """
    lon = _saham(longitudes[Planet.SATURN], longitudes[Planet.VENUS],
                 asc_lon, is_day)
    return Saham("Punarvivaha", lon)


def compute_sahams(chart) -> dict[str, Saham]:
    """All exposed Sahams for a :class:`VedicChart` (natal frame)."""
    day = is_day_birth(chart)
    lon = chart.longitudes
    asc = chart.ascendant
    return {
        "Vivaha": vivaha_saham(lon, asc, day),
        "Punarvivaha": punarvivaha_saham(lon, asc, day),
    }
