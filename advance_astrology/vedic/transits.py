"""Gochara (transits) against a natal chart.

Computes sidereal transit positions for any date and maps them onto the natal
frame: transit sign/house, degree-to-degree conjunctions with natal points,
the natal SAV of the transited sign, Kakṣyā activity, and Sade Sati.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

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


@dataclass(frozen=True)
class ActivationWindow:
    """A contiguous date range during which a timing condition holds."""
    start: datetime
    end: datetime
    label: str

    @property
    def days(self) -> int:
        return (self.end - self.start).days

    def __str__(self) -> str:
        return (f"{self.start:%Y-%m-%d}→{self.end:%Y-%m-%d} "
                f"({self.days}d): {self.label}")


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

    # ------------------------------------------------------------------ #
    # Forward activation-window scanner (Section 3 Step-3 timing engine)
    # ------------------------------------------------------------------ #
    def scan_windows(self, predicate, start: datetime, end: datetime,
                     step_days: float = 5.0, label: str = ""
                     ) -> list[ActivationWindow]:
        """Contiguous windows in [start, end] where ``predicate(when)`` is True.

        Coarse-steps by ``step_days`` then bisects each True/False flip to ~1-day
        resolution. ``step_days`` must be smaller than the shortest activation to
        be resolved (e.g. ≤2 for tight conjunction orbs, ≤1 for Kakṣyā zones).
        """
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        step = timedelta(days=step_days)
        one_day = timedelta(days=1)

        def boundary(lo: datetime, hi: datetime, prev: bool) -> datetime:
            while (hi - lo) > one_day:
                mid = lo + (hi - lo) / 2
                if predicate(mid) == prev:
                    lo = mid
                else:
                    hi = mid
            return hi

        windows: list[ActivationWindow] = []
        d = start
        state = predicate(d)
        win_start = start if state else None
        while d < end:
            nxt = min(d + step, end)
            s2 = predicate(nxt)
            if s2 != state:
                edge = boundary(d, nxt, state)
                if s2:
                    win_start = edge
                else:
                    windows.append(ActivationWindow(win_start, edge, label))
                    win_start = None
                state = s2
            d = nxt
        if state and win_start is not None:
            windows.append(ActivationWindow(win_start, end, label))
        return windows

    def conjunction_windows(self, transit: Planet, natal_longitude: float,
                            start: datetime, end: datetime, orb: float = 1.0,
                            step_days: float = 2.0) -> list[ActivationWindow]:
        """Windows where a transit is within ``orb`` of a natal longitude.

        The Bhrigu-Nandi-Nāḍī degree-to-degree trigger (§3 Step-3.3).
        """
        def pred(when: datetime) -> bool:
            lon = self.positions(when, [transit])[transit]
            return angular_separation(lon, natal_longitude) <= orb
        lbl = f"{transit.value} within {orb}° of {natal_longitude:.2f}°"
        return self.scan_windows(pred, start, end, step_days, lbl)

    def house_windows(self, planet: Planet, house: int, start: datetime,
                      end: datetime, reference: str = "lagna",
                      step_days: float = 5.0) -> list[ActivationWindow]:
        """Windows where a planet transits a given natal house (whole-sign)."""
        def pred(when: datetime) -> bool:
            return self.transit_house(when, planet, reference) == house
        lbl = f"{planet.value} transiting H{house} (from {reference})"
        return self.scan_windows(pred, start, end, step_days, lbl)

    def kakshya_windows(self, planet: Planet, start: datetime, end: datetime,
                        step_days: float = 1.0) -> list[ActivationWindow]:
        """Windows where a transit is in a fruitful Kakṣyā (§3 Step-3.4)."""
        def pred(when: datetime) -> bool:
            return self.kakshya_active(when, planet)
        lbl = f"{planet.value} in a bindu-bearing Kakṣyā"
        return self.scan_windows(pred, start, end, step_days, lbl)

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
