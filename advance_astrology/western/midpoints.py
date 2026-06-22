"""Midpoints and harmonic charts."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from ..angles import angular_separation, norm360, norm180
from ..constants import Planet


def midpoint(a: float, b: float) -> float:
    """Nearer midpoint of two longitudes (the one on the short arc)."""
    return norm360(a + norm180(b - a) / 2.0)


def far_midpoint(a: float, b: float) -> float:
    return norm360(midpoint(a, b) + 180.0)


@dataclass(frozen=True)
class Midpoint:
    body1: Planet
    body2: Planet
    longitude: float


def all_midpoints(longitudes: dict[Planet, float]) -> list[Midpoint]:
    return [
        Midpoint(p1, p2, midpoint(longitudes[p1], longitudes[p2]))
        for p1, p2 in combinations(longitudes, 2)
    ]


def midpoint_trees(
    longitudes: dict[Planet, float], orb: float = 1.5
) -> list[tuple[Planet, Planet, Planet, float]]:
    """Find planets sitting on a midpoint (direct or 90°/180° hard contacts)."""
    out = []
    mids = all_midpoints(longitudes)
    for m in mids:
        for p, lon in longitudes.items():
            if p in (m.body1, m.body2):
                continue
            for harmonic in (0.0, 90.0, 180.0, 45.0, 135.0):
                target = norm360(m.longitude + harmonic)
                sep = angular_separation(lon, target)
                if sep <= orb:
                    out.append((p, m.body1, m.body2, sep))
                    break
    return out


def harmonic_chart(longitudes: dict[Planet, float], n: int) -> dict[Planet, float]:
    """Nth-harmonic positions: each longitude multiplied by n (mod 360)."""
    return {p: norm360(lon * n) for p, lon in longitudes.items()}
