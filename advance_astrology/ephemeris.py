"""Skyfield / JPL ephemeris wrapper.

Provides geocentric apparent ecliptic longitudes (tropical, equinox of date)
for the planets, plus sidereal time, obliquity, and the mean lunar node — the
raw astronomical inputs every chart is built from.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from skyfield.api import load, load_file

from .angles import norm360
from .constants import Planet, SKYFIELD_BODY

# Default ephemeris shipped with the package.
_DATA_DIR = Path(__file__).resolve().parent / "data"
_DEFAULT_BSP = _DATA_DIR / "de421.bsp"


@dataclass(frozen=True)
class BodyPosition:
    """Geocentric apparent position of a body at one instant."""

    planet: Planet
    longitude: float          # tropical ecliptic longitude, deg [0, 360)
    latitude: float           # ecliptic latitude, deg
    distance_au: float        # geocentric distance, AU (0 for nodes)
    speed: float              # longitude rate, deg/day (negative = retrograde)

    @property
    def retrograde(self) -> bool:
        return self.speed < 0.0


class Ephemeris:
    """Thin wrapper around a Skyfield ephemeris kernel.

    Parameters
    ----------
    bsp_path:
        Path to a JPL ``.bsp`` kernel. Defaults to the bundled de421
        (1899-2053). Override with the ``ASTRO_EPHEMERIS`` environment
        variable or by passing a path to use a wider kernel (e.g. de440).
    """

    def __init__(self, bsp_path: str | os.PathLike | None = None):
        if bsp_path is None:
            bsp_path = os.environ.get("ASTRO_EPHEMERIS", str(_DEFAULT_BSP))
        self.bsp_path = str(bsp_path)
        self._eph = load_file(self.bsp_path)
        self._ts = load.timescale()
        self._earth = self._eph["earth"]

    # ------------------------------------------------------------------ #
    # Time handling
    # ------------------------------------------------------------------ #

    def time(self, dt_utc: datetime):
        """Build a Skyfield time from a timezone-aware UTC datetime."""
        if dt_utc.tzinfo is None:
            raise ValueError("datetime must be timezone-aware (UTC)")
        dt_utc = dt_utc.astimezone(timezone.utc)
        return self._ts.from_datetime(dt_utc)

    @staticmethod
    def julian_day(t) -> float:
        """Terrestrial-Time Julian Date for a Skyfield time."""
        return t.tt

    # ------------------------------------------------------------------ #
    # Core astronomical quantities
    # ------------------------------------------------------------------ #

    def obliquity(self, t) -> float:
        """Mean obliquity of the ecliptic in degrees (Meeus / IAU 1980)."""
        tc = (t.tt - 2451545.0) / 36525.0
        seconds = (
            84381.448
            - 46.8150 * tc
            - 0.00059 * tc * tc
            + 0.001813 * tc * tc * tc
        )
        return seconds / 3600.0

    def gast_hours(self, t) -> float:
        """Greenwich apparent sidereal time in hours."""
        return t.gast

    def local_sidereal_time(self, t, longitude_east: float) -> float:
        """Local apparent sidereal time in degrees for an east longitude."""
        lst_hours = (t.gast + longitude_east / 15.0) % 24.0
        return lst_hours * 15.0

    # ------------------------------------------------------------------ #
    # Body positions
    # ------------------------------------------------------------------ #

    def _ecliptic_lonlat(self, t, body_key: str) -> tuple[float, float, float]:
        body = self._eph[body_key]
        astrometric = self._earth.at(t).observe(body).apparent()
        lat, lon, distance = astrometric.ecliptic_latlon(epoch=t)
        return norm360(lon.degrees), lat.degrees, distance.au

    def position(self, planet: Planet, t) -> BodyPosition:
        """Geocentric apparent position of a single body."""
        if planet in (Planet.RAHU, Planet.KETU):
            return self._node_position(planet, t)

        body_key = SKYFIELD_BODY[planet]
        lon, lat, dist = self._ecliptic_lonlat(t, body_key)

        # Central finite difference for daily longitude motion.
        dt = 0.5  # days
        t1 = self._ts.tt_jd(t.tt - dt)
        t2 = self._ts.tt_jd(t.tt + dt)
        lon1, _, _ = self._ecliptic_lonlat(t1, body_key)
        lon2, _, _ = self._ecliptic_lonlat(t2, body_key)
        speed = _delta_lon(lon1, lon2) / (2 * dt)

        return BodyPosition(planet, lon, lat, dist, speed)

    def _node_position(self, planet: Planet, t) -> BodyPosition:
        """Mean lunar node (Rahu = ascending, Ketu = descending)."""
        node = mean_lunar_node(t.tt)
        if planet is Planet.KETU:
            node = norm360(node + 180.0)
        # The mean node regresses at a near-constant rate.
        node1 = mean_lunar_node(t.tt - 0.5)
        node2 = mean_lunar_node(t.tt + 0.5)
        speed = _delta_lon(norm360(node1), norm360(node2))
        return BodyPosition(planet, node, 0.0, 0.0, speed)

    def positions(self, planets, t) -> dict[Planet, BodyPosition]:
        return {p: self.position(p, t) for p in planets}


def _delta_lon(lon1: float, lon2: float) -> float:
    """Signed longitude change lon2 - lon1, handling 0/360 wrap (-180, 180]."""
    d = (lon2 - lon1 + 180.0) % 360.0 - 180.0
    return d


def mean_lunar_node(jd_tt: float) -> float:
    """Tropical longitude of the Moon's mean ascending node (deg), Meeus."""
    t = (jd_tt - 2451545.0) / 36525.0
    omega = (
        125.0445479
        - 1934.1362891 * t
        + 0.0020754 * t * t
        + t * t * t / 467441.0
        - t * t * t * t / 60616000.0
    )
    return norm360(omega)


@lru_cache(maxsize=4)
def get_ephemeris(bsp_path: str | None = None) -> Ephemeris:
    """Return a cached Ephemeris instance (kernels are expensive to load)."""
    return Ephemeris(bsp_path)
