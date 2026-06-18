"""Aspect detection between bodies."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from .angles import angular_separation, signed_difference
from .constants import ASPECTS, MAJOR_ASPECTS, Planet


@dataclass(frozen=True)
class Aspect:
    body1: Planet
    body2: Planet
    name: str
    angle: float          # exact angle of the aspect (e.g. 120 for a trine)
    separation: float     # actual angular separation between the two bodies
    orb: float            # |separation - angle|, how far from exact
    applying: bool        # True if the aspect is tightening (approaching exact)

    def __str__(self) -> str:
        kind = "applying" if self.applying else "separating"
        return (
            f"{self.body1.value} {self.name} {self.body2.value} "
            f"(orb {self.orb:.2f}°, {kind})"
        )


def _is_applying(
    lon1: float, speed1: float, lon2: float, speed2: float, angle: float
) -> bool:
    """Whether the aspect is applying (separation moving toward exact)."""
    diff = signed_difference(lon1, lon2)
    sep = abs(diff)
    # Rate of change of the separation as the faster body moves.
    rel_speed = speed1 - speed2
    # Derivative of |diff - angle| sign tells us applying vs separating.
    target = angle if diff >= 0 else -angle
    delta = diff - target
    return (delta * rel_speed) < 0


def find_aspects(
    positions: dict[Planet, "object"],
    aspect_set: dict[str, tuple[float, float]] | None = None,
    only: list[str] | None = None,
    orb_factor: float = 1.0,
) -> list[Aspect]:
    """Find all aspects among the given body positions.

    Parameters
    ----------
    positions:
        Mapping of Planet -> object exposing ``.longitude`` and ``.speed``.
    aspect_set:
        Mapping of aspect name -> (angle, orb). Defaults to all built-ins.
    only:
        Restrict to these aspect names (e.g. the five major aspects).
    orb_factor:
        Scale every orb (e.g. 0.5 for tighter, 2.0 for looser aspects).
    """
    aspect_set = aspect_set or ASPECTS
    if only is not None:
        aspect_set = {k: v for k, v in aspect_set.items() if k in only}

    results: list[Aspect] = []
    for p1, p2 in combinations(positions.keys(), 2):
        pos1, pos2 = positions[p1], positions[p2]
        sep = angular_separation(pos1.longitude, pos2.longitude)
        for name, (angle, orb) in aspect_set.items():
            allowed = orb * orb_factor
            delta = abs(sep - angle)
            if delta <= allowed:
                applying = _is_applying(
                    pos1.longitude, getattr(pos1, "speed", 0.0),
                    pos2.longitude, getattr(pos2, "speed", 0.0),
                    angle,
                )
                results.append(
                    Aspect(p1, p2, name, angle, sep, delta, applying)
                )
                break  # one aspect per pair (the tightest matching angle)
    results.sort(key=lambda a: a.orb)
    return results


def find_major_aspects(positions, orb_factor: float = 1.0) -> list[Aspect]:
    return find_aspects(positions, only=MAJOR_ASPECTS, orb_factor=orb_factor)
