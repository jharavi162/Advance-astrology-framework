"""Declinations, antiscia and parallels."""

from __future__ import annotations

import math
from dataclasses import dataclass

from ..angles import norm360, signed_difference
from ..constants import Planet

_DEG = math.pi / 180.0


def declination(longitude: float, latitude: float, obliquity: float) -> float:
    """Declination (deg) from ecliptic longitude, latitude and obliquity."""
    lam, beta, eps = longitude * _DEG, latitude * _DEG, obliquity * _DEG
    sin_dec = (math.sin(beta) * math.cos(eps)
               + math.cos(beta) * math.sin(eps) * math.sin(lam))
    return math.asin(max(-1.0, min(1.0, sin_dec))) / _DEG


def antiscion(longitude: float) -> float:
    """Antiscion: reflection across the Cancer-Capricorn (solstitial) axis."""
    return norm360(180.0 - longitude)


def contra_antiscion(longitude: float) -> float:
    return norm360(antiscion(longitude) + 180.0)


@dataclass(frozen=True)
class DeclinationAspect:
    body1: Planet
    body2: Planet
    kind: str             # "parallel" or "contra-parallel"
    orb: float


def declination_aspects(
    declinations: dict[Planet, float], orb: float = 1.0
) -> list[DeclinationAspect]:
    """Find parallels (same declination) and contra-parallels (opposite)."""
    from itertools import combinations
    out: list[DeclinationAspect] = []
    for p1, p2 in combinations(declinations, 2):
        d1, d2 = declinations[p1], declinations[p2]
        if abs(d1 - d2) <= orb:
            out.append(DeclinationAspect(p1, p2, "parallel", abs(d1 - d2)))
        elif abs(d1 + d2) <= orb:
            out.append(DeclinationAspect(p1, p2, "contra-parallel", abs(d1 + d2)))
    return out


def antiscia_contacts(
    longitudes: dict[Planet, float], orb: float = 1.0
) -> list[tuple[Planet, Planet, str, float]]:
    """Find bodies in antiscia / contra-antiscia contact."""
    from itertools import combinations
    out = []
    for p1, p2 in combinations(longitudes, 2):
        a = antiscion(longitudes[p1])
        d_anti = abs(signed_difference(a, longitudes[p2]))
        d_contra = abs(signed_difference(contra_antiscion(longitudes[p1]),
                                         longitudes[p2]))
        if d_anti <= orb:
            out.append((p1, p2, "antiscia", d_anti))
        elif d_contra <= orb:
            out.append((p1, p2, "contra-antiscia", d_contra))
    return out
