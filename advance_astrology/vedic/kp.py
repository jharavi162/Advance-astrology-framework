"""Krishnamurti Paddhati (KP) — star/sub/sub-sub lords and significators.

Each point carries a chain: Sign lord → Star lord (nakshatra) → Sub lord →
Sub-sub lord, the sub being a Vimśottari-proportional division of the nakshatra.
The Sub lord is KP's final arbiter of whether a matter fructifies. House and
planet significators are built from occupation, ownership and star-lordship,
using Placidus cusps for house boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..angles import norm360, to_zodiac
from ..constants import NAKSHATRA_ARC, RULERSHIPS, SIGNS, Planet
from ..houses import house_of
from ..nakshatra import nakshatra_of
from .chalit import placidus_cusps_sidereal
from .dashas import VIMSHOTTARI_RING

_RING = VIMSHOTTARI_RING            # [(lord, years), ...] starting at Ketu
_TOTAL = sum(y for _, y in _RING)   # 120


def _ring_from(lord: Planet):
    i = [p for p, _ in _RING].index(lord)
    return _RING[i:] + _RING[:i]


def _subdivide(start: float, length: float, first_lord: Planet):
    """Vimśottari-proportional sub-segments of an arc, starting at first_lord."""
    segs = []
    cursor = start
    for lord, years in _ring_from(first_lord):
        width = length * years / _TOTAL
        segs.append((lord, cursor, cursor + width))
        cursor += width
    return segs


@dataclass(frozen=True)
class KPChain:
    longitude: float
    sign_lord: Planet
    star_lord: Planet
    sub_lord: Planet
    sub_sub_lord: Planet

    def __str__(self) -> str:
        return (f"{to_zodiac(self.longitude)} — "
                f"{self.sign_lord.value} / {self.star_lord.value} / "
                f"{self.sub_lord.value} / {self.sub_sub_lord.value}")


def kp_chain(longitude: float) -> KPChain:
    """Full sign/star/sub/sub-sub lord chain for a longitude."""
    lon = norm360(longitude)
    sign_lord = RULERSHIPS[SIGNS[to_zodiac(lon).sign_index]]
    nak = nakshatra_of(lon)
    star_lord = nak.lord
    nak_start = nak.index * NAKSHATRA_ARC

    subs = _subdivide(nak_start, NAKSHATRA_ARC, star_lord)
    sub_lord, s0, s1 = next((s for s in subs if s[1] <= lon < s[2]), subs[-1])

    subsubs = _subdivide(s0, s1 - s0, sub_lord)
    sub_sub_lord = next((s[0] for s in subsubs if s[1] <= lon < s[2]),
                        subsubs[-1][0])

    return KPChain(lon, sign_lord, star_lord, sub_lord, sub_sub_lord)


def sub_lord(longitude: float) -> Planet:
    return kp_chain(longitude).sub_lord


# --------------------------------------------------------------------------- #
# Significators (using Placidus house boundaries)
# --------------------------------------------------------------------------- #

class KPSignificators:
    """Builds KP house/planet significators for a VedicChart."""

    def __init__(self, chart):
        self.chart = chart
        self.cusps = placidus_cusps_sidereal(chart)
        # House each planet occupies (Placidus).
        self.planet_house = {
            p: house_of(lon, self.cusps) for p, lon in chart.longitudes.items()
        }
        # Star (nakshatra) lord of each planet.
        self.star_lord = {
            p: nakshatra_of(lon).lord for p, lon in chart.longitudes.items()
        }
        # Owner of each house = lord of the sign on its cusp.
        self.house_owner = {
            h: RULERSHIPS[SIGNS[to_zodiac(self.cusps[h]).sign_index]]
            for h in range(1, 13)
        }

    def occupants(self, house: int) -> list[Planet]:
        return [p for p, h in self.planet_house.items() if h == house]

    def owners(self, house: int) -> list[Planet]:
        return [self.house_owner[house]]

    def planet_signifies(self, planet: Planet) -> list[int]:
        """Houses a planet signifies (star-lord houses are primary)."""
        houses: list[int] = []
        star = self.star_lord[planet]
        # Primary: houses occupied & owned by the star lord.
        houses.append(self.planet_house[star])
        houses += [h for h, o in self.house_owner.items() if o == star]
        # Secondary: the planet's own occupation & ownership.
        houses.append(self.planet_house[planet])
        houses += [h for h, o in self.house_owner.items() if o == planet]
        # De-duplicate, preserve order.
        seen, out = set(), []
        for h in houses:
            if h not in seen:
                seen.add(h)
                out.append(h)
        return out

    def house_significators(self, house: int) -> list[Planet]:
        """Planets signifying a house in KP strength order."""
        occ = self.occupants(house)
        own = self.owners(house)
        in_star_of_occ = [p for p in self.chart.longitudes
                          if self.star_lord[p] in occ]
        in_star_of_own = [p for p in self.chart.longitudes
                          if self.star_lord[p] in own]
        ordered = in_star_of_occ + occ + in_star_of_own + own
        seen, out = set(), []
        for p in ordered:
            if p not in seen:
                seen.add(p)
                out.append(p)
        return out

    def signifies_any(self, planet: Planet, houses) -> bool:
        return bool(set(self.planet_signifies(planet)) & set(houses))


def ruling_planets(chart) -> dict[str, Planet]:
    """Natal ruling planets: lagna & Moon sign/star lords plus the day lord."""
    from .panchanga import vara
    asc = chart.ascendant
    moon = chart.longitudes[Planet.MOON]
    _, day_lord = vara(chart.when_utc)
    return {
        "lagna_sign_lord": RULERSHIPS[SIGNS[to_zodiac(asc).sign_index]],
        "lagna_star_lord": nakshatra_of(asc).lord,
        "moon_sign_lord": RULERSHIPS[SIGNS[to_zodiac(moon).sign_index]],
        "moon_star_lord": nakshatra_of(moon).lord,
        "day_lord": day_lord,
    }
