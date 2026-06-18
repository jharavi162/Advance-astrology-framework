"""Ashtakavarga — Bhinnashtakavarga (BAV) and Sarvashtakavarga (SAV).

Each planet earns benefic points (bindus) in every sign, contributed by the
eight reference points (the seven grahas plus the Lagna) according to the
classical Parashara tables. The per-planet totals are 48/49/39/54/56/52/39
(Sun..Saturn), summing to 337 across the Sarvashtakavarga.
"""

from __future__ import annotations

from ..constants import SIGNS, Planet

# For each planet, the benefic houses (1 = the contributor's own sign) counted
# from each contributor. Order of contributors: Sun, Moon, Mars, Mercury,
# Jupiter, Venus, Saturn, Lagna.
_CONTRIBUTORS = [Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
                 Planet.JUPITER, Planet.VENUS, Planet.SATURN, "Lagna"]

BENEFIC_PLACES = {
    Planet.SUN: {
        Planet.SUN: [1, 2, 4, 7, 8, 9, 10, 11],
        Planet.MOON: [3, 6, 10, 11],
        Planet.MARS: [1, 2, 4, 7, 8, 9, 10, 11],
        Planet.MERCURY: [3, 5, 6, 9, 10, 11, 12],
        Planet.JUPITER: [5, 6, 9, 11],
        Planet.VENUS: [6, 7, 12],
        Planet.SATURN: [1, 2, 4, 7, 8, 9, 10, 11],
        "Lagna": [3, 4, 6, 10, 11, 12],
    },
    Planet.MOON: {
        Planet.SUN: [3, 6, 7, 8, 10, 11],
        Planet.MOON: [1, 3, 6, 7, 10, 11],
        Planet.MARS: [2, 3, 5, 6, 9, 10, 11],
        Planet.MERCURY: [1, 3, 4, 5, 7, 8, 10, 11],
        Planet.JUPITER: [1, 4, 7, 8, 10, 11, 12],
        Planet.VENUS: [3, 4, 5, 7, 9, 10, 11],
        Planet.SATURN: [3, 5, 6, 11],
        "Lagna": [3, 6, 10, 11],
    },
    Planet.MARS: {
        Planet.SUN: [3, 5, 6, 10, 11],
        Planet.MOON: [3, 6, 11],
        Planet.MARS: [1, 2, 4, 7, 8, 10, 11],
        Planet.MERCURY: [3, 5, 6, 11],
        Planet.JUPITER: [6, 10, 11, 12],
        Planet.VENUS: [6, 8, 11, 12],
        Planet.SATURN: [1, 4, 7, 8, 9, 10, 11],
        "Lagna": [1, 3, 6, 10, 11],
    },
    Planet.MERCURY: {
        Planet.SUN: [5, 6, 9, 11, 12],
        Planet.MOON: [2, 4, 6, 8, 10, 11],
        Planet.MARS: [1, 2, 4, 7, 8, 9, 10, 11],
        Planet.MERCURY: [1, 3, 5, 6, 9, 10, 11, 12],
        Planet.JUPITER: [6, 8, 11, 12],
        Planet.VENUS: [1, 2, 3, 4, 5, 8, 9, 11],
        Planet.SATURN: [1, 2, 4, 7, 8, 9, 10, 11],
        "Lagna": [1, 2, 4, 6, 8, 10, 11],
    },
    Planet.JUPITER: {
        Planet.SUN: [1, 2, 3, 4, 7, 8, 9, 10, 11],
        Planet.MOON: [2, 5, 7, 9, 11],
        Planet.MARS: [1, 2, 4, 7, 8, 10, 11],
        Planet.MERCURY: [1, 2, 4, 5, 6, 9, 10, 11],
        Planet.JUPITER: [1, 2, 3, 4, 7, 8, 10, 11],
        Planet.VENUS: [2, 5, 6, 9, 10, 11],
        Planet.SATURN: [3, 5, 6, 12],
        "Lagna": [1, 2, 4, 5, 6, 7, 9, 10, 11],
    },
    Planet.VENUS: {
        Planet.SUN: [8, 11, 12],
        Planet.MOON: [1, 2, 3, 4, 5, 8, 9, 11, 12],
        Planet.MARS: [3, 5, 6, 9, 11, 12],
        Planet.MERCURY: [3, 5, 6, 9, 11],
        Planet.JUPITER: [5, 8, 9, 10, 11],
        Planet.VENUS: [1, 2, 3, 4, 5, 8, 9, 10, 11],
        Planet.SATURN: [3, 4, 5, 8, 9, 10, 11],
        "Lagna": [1, 2, 3, 4, 5, 8, 9, 11],
    },
    Planet.SATURN: {
        Planet.SUN: [1, 2, 4, 7, 8, 10, 11],
        Planet.MOON: [3, 6, 11],
        Planet.MARS: [3, 5, 6, 10, 11, 12],
        Planet.MERCURY: [6, 8, 9, 10, 11, 12],
        Planet.JUPITER: [5, 6, 11, 12],
        Planet.VENUS: [6, 11, 12],
        Planet.SATURN: [3, 5, 6, 11],
        "Lagna": [1, 3, 4, 6, 10, 11],
    },
}

ASHTAKAVARGA_PLANETS = [Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
                        Planet.JUPITER, Planet.VENUS, Planet.SATURN]


def bhinnashtakavarga(
    planet: Planet,
    planet_signs: dict[Planet, int],
    ascendant_sign: int,
) -> list[int]:
    """BAV for a planet: 12-length list of bindus indexed by sign (0=Aries)."""
    bindus = [0] * 12
    table = BENEFIC_PLACES[planet]
    for contributor in _CONTRIBUTORS:
        ref_sign = ascendant_sign if contributor == "Lagna" else planet_signs[contributor]
        for house in table[contributor]:
            sign = (ref_sign + house - 1) % 12
            bindus[sign] += 1
    return bindus


def sarvashtakavarga(
    planet_signs: dict[Planet, int],
    ascendant_sign: int,
) -> list[int]:
    """SAV: total bindus per sign across all seven planetary BAVs."""
    total = [0] * 12
    for planet in ASHTAKAVARGA_PLANETS:
        bav = bhinnashtakavarga(planet, planet_signs, ascendant_sign)
        for i in range(12):
            total[i] += bav[i]
    return total


def all_bhinnashtakavarga(
    planet_signs: dict[Planet, int],
    ascendant_sign: int,
) -> dict[Planet, list[int]]:
    return {
        p: bhinnashtakavarga(p, planet_signs, ascendant_sign)
        for p in ASHTAKAVARGA_PLANETS
    }


def format_ashtakavarga(bindus: list[int], title: str = "") -> str:
    head = "  ".join(f"{s[:3]}" for s in SIGNS)
    vals = "  ".join(f"{b:>3}" for b in bindus)
    return f"{title}\n  {head}\n  {vals}  (total {sum(bindus)})"
