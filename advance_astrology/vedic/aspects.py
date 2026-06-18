"""Vedic aspects: graha drishti (planetary) and rashi drishti (sign)."""

from __future__ import annotations

from dataclasses import dataclass

from ..constants import SIGNS, Planet

# Special full-aspect distances (1 = the sign the planet occupies).
# Every planet aspects the 7th; some have extra special aspects.
SPECIAL_ASPECTS = {
    Planet.MARS: [4, 7, 8],
    Planet.JUPITER: [5, 7, 9],
    Planet.SATURN: [3, 7, 10],
    # Nodes are commonly given Jupiter-like 5/7/9 aspects (convention varies).
    Planet.RAHU: [5, 7, 9],
    Planet.KETU: [5, 7, 9],
}
DEFAULT_ASPECT = [7]


def graha_aspect_houses(planet: Planet) -> list[int]:
    """House distances a planet aspects (inclusive counting, 1 = own sign)."""
    return SPECIAL_ASPECTS.get(planet, DEFAULT_ASPECT)


def aspects_sign(planet: Planet, planet_sign: int, target_sign: int) -> bool:
    """Whether `planet` (in `planet_sign`) casts a graha drishti on target."""
    distance = (target_sign - planet_sign) % 12 + 1
    return distance in graha_aspect_houses(planet)


@dataclass(frozen=True)
class GrahaDrishti:
    planet: Planet
    from_sign: int
    to_sign: int
    distance: int

    def __str__(self) -> str:
        return (f"{self.planet.value} aspects {SIGNS[self.to_sign]} "
                f"({self.distance}th)")


def all_graha_aspects(
    planet_signs: dict[Planet, int]
) -> list[GrahaDrishti]:
    """Every graha drishti among the placed planets (planet-to-occupied-sign)."""
    occupied = {}
    for p, s in planet_signs.items():
        occupied.setdefault(s, []).append(p)

    out: list[GrahaDrishti] = []
    for planet, src in planet_signs.items():
        for dist in graha_aspect_houses(planet):
            tgt = (src + dist - 1) % 12
            out.append(GrahaDrishti(planet, src, tgt, dist))
    return out


def planets_aspecting_sign(
    sign: int, planet_signs: dict[Planet, int]
) -> list[Planet]:
    """Which planets cast a graha drishti onto a given sign."""
    return [p for p, s in planet_signs.items() if aspects_sign(p, s, sign)]


# --------------------------------------------------------------------------- #
# Rashi drishti (sign aspects, Jaimini)
# --------------------------------------------------------------------------- #

# Offsets aspected by each modality: movable->fixed, fixed->movable, dual->dual.
_RASHI_OFFSETS = {
    0: [4, 7, 10],   # movable signs (s % 3 == 0) aspect the fixed signs
    1: [2, 5, 8],    # fixed signs aspect the movable signs
    2: [3, 6, 9],    # dual signs aspect the other dual signs
}


def rashi_aspects(from_sign: int) -> list[int]:
    """Signs receiving rashi drishti from the given sign."""
    offsets = _RASHI_OFFSETS[from_sign % 3]
    return [(from_sign + o) % 12 for o in offsets]


def rashi_aspects_sign(from_sign: int, to_sign: int) -> bool:
    return to_sign in rashi_aspects(from_sign)
