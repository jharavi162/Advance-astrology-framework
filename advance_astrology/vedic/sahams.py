"""Tājika Sahams — sensitive longitudes (Arabic-parts analogues) used in
Tājika/Varṣaphal for event sensitivity across every life domain.

A Saham is a derived point ``A − B + Lagna`` (for a day birth) with ``A`` and
``B`` swapped for a night birth. The point and its rāśi lord become active
timers: an event tends to fire when the Saham's dispositor runs in the daśā or
when a slow transit (esp. the Jupiter+Saturn double-transit) lights up the
Saham's sign.

These are pure calculators — they take longitudes and return points; the
interpretation/triangulation is done by the caller. The formulas follow the
common Tājika tradition (Tājika-Nīlakaṇṭhī / B. V. Raman, *Varshaphal*);
textual variants exist and are noted per function.
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


# --------------------------------------------------------------------------- #
# Marriage Sahams
# --------------------------------------------------------------------------- #

def vivaha_saham(longitudes: dict[Planet, float], asc_lon: float,
                 is_day: bool) -> Saham:
    """Vivāha (marriage) Saham = Venus − Saturn + Lagna (reversed at night)."""
    return Saham("Vivaha", _saham(longitudes[Planet.VENUS],
                                  longitudes[Planet.SATURN], asc_lon, is_day))


def punarvivaha_saham(longitudes: dict[Planet, float], asc_lon: float,
                      is_day: bool) -> Saham:
    """Punar-vivāha (re-marriage) Saham — *documented variant* = Saturn − Venus
    + Lagna (reverse of Vivāha). Not in the classical 36-core; secondary timer.
    """
    return Saham("Punarvivaha", _saham(longitudes[Planet.SATURN],
                                       longitudes[Planet.VENUS], asc_lon, is_day))


# --------------------------------------------------------------------------- #
# General-domain Sahams (career, children, wealth, illness, fortune, …)
# --------------------------------------------------------------------------- #

def punya_saham(longitudes: dict[Planet, float], asc_lon: float,
                is_day: bool) -> Saham:
    """Puṇya (merit / overall fortune) = Moon − Sun + Lagna (reversed night).
    The seed point from which several other Sahams (e.g. Yaśas) are derived."""
    return Saham("Punya", _saham(longitudes[Planet.MOON],
                                 longitudes[Planet.SUN], asc_lon, is_day))


def vidya_saham(longitudes: dict[Planet, float], asc_lon: float,
                is_day: bool) -> Saham:
    """Vidyā (education) = Sun − Moon + Lagna (reversed night)."""
    return Saham("Vidya", _saham(longitudes[Planet.SUN],
                                 longitudes[Planet.MOON], asc_lon, is_day))


def karma_saham(longitudes: dict[Planet, float], asc_lon: float,
                is_day: bool) -> Saham:
    """Karma (career / action) = Mars − Mercury + Lagna (reversed night)."""
    return Saham("Karma", _saham(longitudes[Planet.MARS],
                                 longitudes[Planet.MERCURY], asc_lon, is_day))


def yasas_saham(longitudes: dict[Planet, float], asc_lon: float,
                is_day: bool) -> Saham:
    """Yaśas (fame / repute) = Jupiter − Puṇya-Saham + Lagna (reversed night)."""
    punya = punya_saham(longitudes, asc_lon, is_day).longitude
    return Saham("Yasas", _saham(longitudes[Planet.JUPITER], punya,
                                 asc_lon, is_day))


def putra_saham(longitudes: dict[Planet, float], asc_lon: float,
                is_day: bool) -> Saham:
    """Putra / Santāna (children) = Jupiter − Moon + Lagna (reversed night)."""
    return Saham("Putra", _saham(longitudes[Planet.JUPITER],
                                 longitudes[Planet.MOON], asc_lon, is_day))


def roga_saham(longitudes: dict[Planet, float], asc_lon: float,
               is_day: bool) -> Saham:
    """Roga (illness / health) = Saturn − Moon + Lagna (reversed night)."""
    return Saham("Roga", _saham(longitudes[Planet.SATURN],
                                longitudes[Planet.MOON], asc_lon, is_day))


def artha_saham(longitudes: dict[Planet, float], asc_lon: float,
                is_day: bool, lord1_lon: float, lord2_lon: float) -> Saham:
    """Artha (wealth) = lord(1) − lord(2) + Lagna (reversed night).

    Uses the longitudes of the 1st- and 2nd-house lords, supplied by the
    caller (they depend on the lagna sign)."""
    return Saham("Artha", _saham(lord1_lon, lord2_lon, asc_lon, is_day))


def mrityu_saham(longitudes: dict[Planet, float], asc_lon: float,
                 is_day: bool, eighth_cusp_lon: float) -> Saham:
    """Mṛtyu (longevity / mortality) = Moon − 8th-cusp + Lagna (reversed night).

    The 8th cusp is supplied by the caller (whole-sign proxy: the lagna degree
    carried to the 8th sign)."""
    return Saham("Mrityu", _saham(longitudes[Planet.MOON], eighth_cusp_lon,
                                  asc_lon, is_day))


# --------------------------------------------------------------------------- #
# Aggregate
# --------------------------------------------------------------------------- #

def compute_sahams(chart) -> dict[str, Saham]:
    """All exposed Sahams for a :class:`VedicChart` (natal frame)."""
    day = is_day_birth(chart)
    lon = chart.longitudes
    asc = chart.ascendant
    lord1 = lon[chart.house_lord(1)]
    lord2 = lon[chart.house_lord(2)]
    eighth_cusp = norm360(asc + 210.0)        # lagna degree carried to 8th sign
    return {
        "Vivaha": vivaha_saham(lon, asc, day),
        "Punarvivaha": punarvivaha_saham(lon, asc, day),
        "Punya": punya_saham(lon, asc, day),
        "Vidya": vidya_saham(lon, asc, day),
        "Karma": karma_saham(lon, asc, day),
        "Yasas": yasas_saham(lon, asc, day),
        "Putra": putra_saham(lon, asc, day),
        "Artha": artha_saham(lon, asc, day, lord1, lord2),
        "Roga": roga_saham(lon, asc, day),
        "Mrityu": mrityu_saham(lon, asc, day, eighth_cusp),
    }
