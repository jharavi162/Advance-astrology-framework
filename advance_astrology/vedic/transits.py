"""Gochara (transits) against a natal chart.

Computes sidereal transit positions for any date and maps them onto the natal
frame: transit sign/house, degree-to-degree conjunctions with natal points,
the natal SAV of the transited sign, Kakṣyā activity, and Sade Sati.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from ..angles import angular_separation, norm360, to_zodiac
from ..ayanamsa import ayanamsa as compute_ayanamsa
from ..constants import DEFAULT_PLANETS, SIGNS, Planet
from . import kakshya as kakshya_mod
from .ashtakavarga import sarvashtakavarga


@dataclass(frozen=True)
class TransitHit:
    transit: Planet
    natal: Planet
    orb: float

    def __str__(self) -> str:
        return (f"transit {self.transit.value} conjunct natal "
                f"{self.natal.value} (orb {self.orb:.2f}°)")


class Transits:
    """Transit calculator bound to a natal :class:`VedicChart`."""

    def __init__(self, chart):
        self.chart = chart
        self._eph = chart.natal._ephemeris
        self._ayanamsa_name = chart.natal.ayanamsa_name
        self.natal_signs = chart.signs
        self.natal_moon_sign = chart.signs[Planet.MOON]
        self.asc_sign = chart.ascendant_sign
        self._sav = sarvashtakavarga(chart.signs, self.asc_sign)

    # ------------------------------------------------------------------ #
    def positions(self, when: datetime,
                  planets=None) -> dict[Planet, float]:
        """Sidereal transit longitudes (ayanamsa of the transit date)."""
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        planets = planets or DEFAULT_PLANETS
        t = self._eph.time(when)
        ayan = compute_ayanamsa(self._eph.julian_day(t), self._ayanamsa_name)
        return {
            p: norm360(self._eph.position(p, t).longitude - ayan)
            for p in planets
        }

    def transit_sign(self, when: datetime, planet: Planet) -> int:
        return to_zodiac(self.positions(when, [planet])[planet]).sign_index

    def transit_house(self, when: datetime, planet: Planet,
                      reference: str = "lagna") -> int:
        """Whole-sign house of a transit from the natal lagna or Moon."""
        sign = self.transit_sign(when, planet)
        base = self.asc_sign if reference == "lagna" else self.natal_moon_sign
        return (sign - base) % 12 + 1

    def conjunctions(self, when: datetime, orb: float = 1.0,
                     planets=None) -> list[TransitHit]:
        """Degree-to-degree transit→natal conjunctions within orb."""
        tpos = self.positions(when, planets)
        hits = []
        for tp, tlon in tpos.items():
            for np_, nlon in self.chart.longitudes.items():
                sep = angular_separation(tlon, nlon)
                if sep <= orb:
                    hits.append(TransitHit(tp, np_, sep))
        hits.sort(key=lambda h: h.orb)
        return hits

    def sav_of_transit(self, when: datetime, planet: Planet) -> int:
        """Natal SAV bindus of the sign a planet is transiting."""
        return self._sav[self.transit_sign(when, planet)]

    def kakshya_active(self, when: datetime, planet: Planet) -> bool:
        """Whether the transit is in a fruitful kakṣyā (BAV bindu present)."""
        lon = self.positions(when, [planet])[planet]
        return kakshya_mod.transit_active(planet, lon, self.natal_signs,
                                          self.asc_sign)

    def sade_sati(self, when: datetime) -> dict:
        """Saturn's Sade Sati status relative to the natal Moon."""
        sat_sign = self.transit_sign(when, Planet.SATURN)
        rel = (sat_sign - self.natal_moon_sign) % 12
        phases = {11: "Rising (12th)", 0: "Peak (Janma)", 1: "Setting (2nd)"}
        return {
            "active": rel in (11, 0, 1),
            "phase": phases.get(rel, "—"),
            "saturn_sign": SIGNS[sat_sign],
        }

    def slow_movers(self, when: datetime) -> dict[Planet, dict]:
        """Sign/house summary for the structural heavyweights."""
        out = {}
        for p in (Planet.SATURN, Planet.JUPITER, Planet.RAHU, Planet.KETU):
            sign = self.transit_sign(when, p)
            out[p] = {
                "sign": SIGNS[sign],
                "house_from_lagna": (sign - self.asc_sign) % 12 + 1,
                "house_from_moon": (sign - self.natal_moon_sign) % 12 + 1,
                "sav": self._sav[sign],
            }
        return out
