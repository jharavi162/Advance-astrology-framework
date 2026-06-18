"""Arabic Parts / Hellenistic Lots.

Each lot is a longitude derived from three points (usually Ascendant + a
significator − another), with the formula reflected between day and night
charts for the sect-sensitive lots.
"""

from __future__ import annotations

from ..angles import norm360
from ..constants import Planet

# A lot is defined by the three terms for a DAY chart: (a, b, c) -> a + b - c.
# Sect-sensitive lots swap b and c at night.
_LOTS = {
    # name: (a, b, c, sect_sensitive)
    "Fortune": ("Asc", Planet.MOON, Planet.SUN, True),
    "Spirit": ("Asc", Planet.SUN, Planet.MOON, True),
    "Eros": ("Asc", Planet.VENUS, "Spirit", True),
    "Necessity": ("Asc", "Fortune", Planet.MERCURY, True),
    "Victory": ("Asc", Planet.JUPITER, "Spirit", True),
    "Courage": ("Asc", "Fortune", Planet.MARS, True),
    "Nemesis": ("Asc", "Fortune", Planet.SATURN, True),
    "Marriage": ("Asc", Planet.VENUS, Planet.SATURN, False),
    "Children": ("Asc", Planet.JUPITER, Planet.SATURN, False),
    "Father": ("Asc", Planet.SUN, Planet.SATURN, True),
    "Mother": ("Asc", Planet.MOON, Planet.VENUS, True),
}


def is_day_chart(sun_house: int) -> bool:
    """Day chart when the Sun is above the horizon (houses 7-12)."""
    return sun_house in (7, 8, 9, 10, 11, 12)


def _resolve(term, positions, asc, is_day, _depth=0):
    if term == "Asc":
        return asc
    if isinstance(term, Planet):
        return positions[term]
    # A lot referenced by name (e.g. Spirit inside Eros).
    if _depth > 5:
        raise ValueError("lot reference cycle")
    return compute_lot(term, positions, asc, is_day, _depth + 1)


def compute_lot(name: str, positions: dict[Planet, float], asc: float,
                is_day: bool, _depth: int = 0) -> float:
    if name not in _LOTS:
        raise ValueError(f"Unknown lot '{name}'. Available: {sorted(_LOTS)}")
    a, b, c, sect = _LOTS[name]
    if sect and not is_day:
        b, c = c, b
    av = _resolve(a, positions, asc, is_day, _depth)
    bv = _resolve(b, positions, asc, is_day, _depth)
    cv = _resolve(c, positions, asc, is_day, _depth)
    return norm360(av + bv - cv)


def all_lots(positions: dict[Planet, float], asc: float,
             is_day: bool) -> dict[str, float]:
    return {name: compute_lot(name, positions, asc, is_day) for name in _LOTS}


def part_of_fortune(positions, asc, is_day) -> float:
    return compute_lot("Fortune", positions, asc, is_day)
