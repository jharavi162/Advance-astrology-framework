"""Yoga detection — recognisable planetary combinations.

Covers the most consequential classical yogas: the Pancha Mahapurusha set,
lunar yogas (Gajakesari, Sunapha/Anapha/Durudhara, Kemadruma), conjunction
yogas (Budha-Aditya, Chandra-Mangala), Raja and Dhana yogas from house-lord
associations, Viparita Raja yoga, and Kala Sarpa.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..constants import RULERSHIPS, SIGNS, Planet
from .dignities import EXALTATION, OWN_SIGNS

KENDRAS = (1, 4, 7, 10)
TRIKONAS = (1, 5, 9)
DUSTHANAS = (6, 8, 12)

# The seven "true" planets used for most yoga rules.
_GRAHAS = [Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
           Planet.JUPITER, Planet.VENUS, Planet.SATURN]

MAHAPURUSHA = {
    Planet.MARS: "Ruchaka", Planet.MERCURY: "Bhadra", Planet.JUPITER: "Hamsa",
    Planet.VENUS: "Malavya", Planet.SATURN: "Shasha",
}


@dataclass
class Yoga:
    name: str
    kind: str                 # category, e.g. "Mahapurusha", "Raja", "Lunar"
    planets: list[Planet]
    description: str

    def __str__(self) -> str:
        who = ", ".join(p.value for p in self.planets)
        return f"{self.name} ({self.kind}): {self.description}" + (
            f" [{who}]" if who else ""
        )


def _house_of(planet_sign: int, asc_sign: int) -> int:
    return (planet_sign - asc_sign) % 12 + 1


def _house_lord(house: int, asc_sign: int) -> Planet:
    return RULERSHIPS[SIGNS[(asc_sign + house - 1) % 12]]


def _lord_house(lord: Planet, asc_sign: int, planet_signs: dict[Planet, int]) -> int:
    return _house_of(planet_signs[lord], asc_sign)


def detect_yogas(
    asc_sign: int,
    planet_signs: dict[Planet, int],
    planet_longitudes: dict[Planet, float],
) -> list[Yoga]:
    yogas: list[Yoga] = []
    house = {p: _house_of(s, asc_sign) for p, s in planet_signs.items()}
    by_sign: dict[int, list[Planet]] = {}
    for p, s in planet_signs.items():
        by_sign.setdefault(s, []).append(p)

    # --- Pancha Mahapurusha ------------------------------------------------ #
    for planet, yname in MAHAPURUSHA.items():
        sign = SIGNS[planet_signs[planet]]
        dignified = sign in OWN_SIGNS.get(planet, []) or sign == EXALTATION[planet][0]
        if dignified and house[planet] in KENDRAS:
            yogas.append(Yoga(
                f"{yname} Yoga", "Mahapurusha", [planet],
                f"{planet.value} dignified in a kendra ({sign}, house {house[planet]})",
            ))

    # --- Gajakesari (Jupiter in a kendra from the Moon) -------------------- #
    moon_sign = planet_signs[Planet.MOON]
    jup_from_moon = (planet_signs[Planet.JUPITER] - moon_sign) % 12 + 1
    if jup_from_moon in KENDRAS:
        yogas.append(Yoga(
            "Gajakesari Yoga", "Lunar", [Planet.MOON, Planet.JUPITER],
            "Jupiter in a kendra from the Moon",
        ))

    # --- Sunapha / Anapha / Durudhara / Kemadruma -------------------------- #
    second = (moon_sign + 1) % 12
    twelfth = (moon_sign - 1) % 12
    # Only the five non-luminary classical grahas qualify for lunar yogas.
    _LUNAR_YOGA_GRAHAS = (Planet.MARS, Planet.MERCURY, Planet.JUPITER,
                          Planet.VENUS, Planet.SATURN)
    others = lambda s: [p for p in by_sign.get(s, []) if p in _LUNAR_YOGA_GRAHAS]
    in2, in12 = others(second), others(twelfth)
    if in2 and in12:
        yogas.append(Yoga("Durudhara Yoga", "Lunar", in2 + in12,
                          "Planets flank the Moon in both 2nd and 12th"))
    elif in2:
        yogas.append(Yoga("Sunapha Yoga", "Lunar", in2,
                          "Planet(s) in the 2nd from the Moon"))
    elif in12:
        yogas.append(Yoga("Anapha Yoga", "Lunar", in12,
                          "Planet(s) in the 12th from the Moon"))
    else:
        # Kemadruma also requires no planet conjunct the Moon (besides nodes).
        with_moon = others(moon_sign)
        if not with_moon:
            yogas.append(Yoga("Kemadruma Yoga", "Lunar", [Planet.MOON],
                              "Moon isolated (no planets in 2nd/12th/conjunct)"))

    # --- Conjunction yogas ------------------------------------------------- #
    if planet_signs[Planet.SUN] == planet_signs[Planet.MERCURY]:
        yogas.append(Yoga("Budha-Aditya Yoga", "Conjunction",
                          [Planet.SUN, Planet.MERCURY],
                          "Sun and Mercury conjunct"))
    if planet_signs[Planet.MOON] == planet_signs[Planet.MARS]:
        yogas.append(Yoga("Chandra-Mangala Yoga", "Conjunction",
                          [Planet.MOON, Planet.MARS],
                          "Moon and Mars conjunct"))

    # --- Raja yoga: kendra lord with trikona lord ------------------------- #
    kendra_lords = {_house_lord(h, asc_sign) for h in KENDRAS}
    trikona_lords = {_house_lord(h, asc_sign) for h in TRIKONAS}
    for kl in kendra_lords:
        for tl in trikona_lords:
            if kl == tl:
                continue
            if planet_signs[kl] == planet_signs[tl]:
                yogas.append(Yoga(
                    "Raja Yoga", "Raja", [kl, tl],
                    f"Kendra lord {kl.value} conjunct trikona lord {tl.value}",
                ))

    # --- Viparita Raja yoga: dusthana lords in dusthanas ------------------ #
    for h in DUSTHANAS:
        lord = _house_lord(h, asc_sign)
        if house[lord] in DUSTHANAS:
            yogas.append(Yoga(
                "Viparita Raja Yoga", "Raja", [lord],
                f"{h}th lord {lord.value} placed in a dusthana (house {house[lord]})",
            ))

    # --- Dhana yoga: wealth-house lords associated ------------------------ #
    wealth_lords = {h: _house_lord(h, asc_sign) for h in (2, 5, 9, 11)}
    seen = set()
    for h1, l1 in wealth_lords.items():
        for h2, l2 in wealth_lords.items():
            if h1 >= h2 or l1 == l2:
                continue
            key = frozenset({l1, l2})
            if key in seen:
                continue
            if planet_signs[l1] == planet_signs[l2]:
                seen.add(key)
                yogas.append(Yoga(
                    "Dhana Yoga", "Dhana", [l1, l2],
                    f"Wealth lords {l1.value} and {l2.value} conjunct",
                ))

    # --- Kala Sarpa: all grahas between the Rahu-Ketu axis ----------------- #
    if Planet.RAHU in planet_signs:
        yogas.extend(_kala_sarpa(planet_signs))

    return yogas


def _kala_sarpa(planet_signs: dict[Planet, int]) -> list[Yoga]:
    rahu = planet_signs[Planet.RAHU]
    ketu = planet_signs[Planet.KETU]
    # Arc from Rahu forward to Ketu.
    span = (ketu - rahu) % 12
    inside = outside = False
    for p in _GRAHAS:
        d = (planet_signs[p] - rahu) % 12
        if 0 < d < span:
            inside = True
        elif d > span or d == 0:
            outside = True
    if inside and not outside:
        return [Yoga("Kala Sarpa Yoga", "Special",
                     [Planet.RAHU, Planet.KETU],
                     "All planets hemmed within the Rahu-Ketu axis")]
    return []
