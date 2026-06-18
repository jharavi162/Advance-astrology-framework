"""Planetary dignities and relationships (Jyotish).

Covers exaltation/debilitation (with deep-exaltation degrees), moolatrikona,
own-sign, and the three-tier relationship scheme — natural (naisargika),
temporal (tatkalika) and the combined five-fold (panchadha) relationship.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..angles import norm360, to_zodiac
from ..constants import SIGNS, Planet

# Sign index helper: 0 = Aries .. 11 = Pisces.
_SIGN_IDX = {name: i for i, name in enumerate(SIGNS)}


# --------------------------------------------------------------------------- #
# Exaltation / debilitation / moolatrikona / own-sign
# --------------------------------------------------------------------------- #

# planet -> (sign, deep-exaltation degree within sign)
EXALTATION = {
    Planet.SUN: ("Aries", 10.0),
    Planet.MOON: ("Taurus", 3.0),
    Planet.MARS: ("Capricorn", 28.0),
    Planet.MERCURY: ("Virgo", 15.0),
    Planet.JUPITER: ("Cancer", 5.0),
    Planet.VENUS: ("Pisces", 27.0),
    Planet.SATURN: ("Libra", 20.0),
    # Node exaltation is disputed between texts; Taurus/Scorpio is a common set.
    Planet.RAHU: ("Taurus", 20.0),
    Planet.KETU: ("Scorpio", 20.0),
}


def debilitation_sign(planet: Planet) -> str:
    sign, _ = EXALTATION[planet]
    return SIGNS[(_SIGN_IDX[sign] + 6) % 12]


# planet -> (sign, start_deg, end_deg)
MOOLATRIKONA = {
    Planet.SUN: ("Leo", 0.0, 20.0),
    Planet.MOON: ("Taurus", 3.0, 30.0),
    Planet.MARS: ("Aries", 0.0, 12.0),
    Planet.MERCURY: ("Virgo", 15.0, 20.0),
    Planet.JUPITER: ("Sagittarius", 0.0, 10.0),
    Planet.VENUS: ("Libra", 0.0, 15.0),
    Planet.SATURN: ("Aquarius", 0.0, 20.0),
}

# planet -> list of own signs (swakshetra)
OWN_SIGNS = {
    Planet.SUN: ["Leo"],
    Planet.MOON: ["Cancer"],
    Planet.MARS: ["Aries", "Scorpio"],
    Planet.MERCURY: ["Gemini", "Virgo"],
    Planet.JUPITER: ["Sagittarius", "Pisces"],
    Planet.VENUS: ["Taurus", "Libra"],
    Planet.SATURN: ["Capricorn", "Aquarius"],
    Planet.RAHU: ["Aquarius"],   # co-lord conventions vary
    Planet.KETU: ["Scorpio"],
}


# --------------------------------------------------------------------------- #
# Natural (naisargika) relationships
# --------------------------------------------------------------------------- #

# planet -> {"friend": [...], "enemy": [...]}; everything else is neutral.
_NATURAL = {
    Planet.SUN: {"friend": [Planet.MOON, Planet.MARS, Planet.JUPITER],
                 "enemy": [Planet.VENUS, Planet.SATURN]},
    Planet.MOON: {"friend": [Planet.SUN, Planet.MERCURY],
                  "enemy": []},
    Planet.MARS: {"friend": [Planet.SUN, Planet.MOON, Planet.JUPITER],
                  "enemy": [Planet.MERCURY]},
    Planet.MERCURY: {"friend": [Planet.SUN, Planet.VENUS],
                     "enemy": [Planet.MOON]},
    Planet.JUPITER: {"friend": [Planet.SUN, Planet.MOON, Planet.MARS],
                     "enemy": [Planet.MERCURY, Planet.VENUS]},
    Planet.VENUS: {"friend": [Planet.MERCURY, Planet.SATURN],
                   "enemy": [Planet.SUN, Planet.MOON]},
    Planet.SATURN: {"friend": [Planet.MERCURY, Planet.VENUS],
                    "enemy": [Planet.SUN, Planet.MOON, Planet.MARS]},
    # Node relationships (commonly used; treat like their dispositors).
    Planet.RAHU: {"friend": [Planet.VENUS, Planet.SATURN, Planet.MERCURY],
                  "enemy": [Planet.SUN, Planet.MOON, Planet.MARS]},
    Planet.KETU: {"friend": [Planet.MARS, Planet.VENUS, Planet.SATURN],
                  "enemy": [Planet.SUN, Planet.MOON]},
}

FRIEND, NEUTRAL, ENEMY = "Friend", "Neutral", "Enemy"
GREAT_FRIEND, GREAT_ENEMY = "Great Friend", "Great Enemy"


def natural_relationship(of: Planet, towards: Planet) -> str:
    """Naisargika relationship of `of` toward `towards`."""
    if of == towards:
        return "Self"
    rel = _NATURAL.get(of, {"friend": [], "enemy": []})
    if towards in rel["friend"]:
        return FRIEND
    if towards in rel["enemy"]:
        return ENEMY
    return NEUTRAL


def temporal_relationship(of_sign_idx: int, towards_sign_idx: int) -> str:
    """Tatkalika relationship from house distance.

    Planets in the 2nd, 3rd, 4th, 10th, 11th or 12th sign from a planet are its
    temporal friends; the rest (1,5,6,7,8,9) are temporal enemies.
    """
    distance = (towards_sign_idx - of_sign_idx) % 12 + 1  # 1..12
    return FRIEND if distance in (2, 3, 4, 10, 11, 12) else ENEMY


def compound_relationship(of: Planet, of_sign_idx: int,
                          towards: Planet, towards_sign_idx: int) -> str:
    """Five-fold (panchadha) relationship combining natural + temporal."""
    if of == towards:
        return "Self"
    nat = natural_relationship(of, towards)
    tmp = temporal_relationship(of_sign_idx, towards_sign_idx)
    table = {
        (FRIEND, FRIEND): GREAT_FRIEND,
        (FRIEND, ENEMY): NEUTRAL,
        (NEUTRAL, FRIEND): FRIEND,
        (NEUTRAL, ENEMY): ENEMY,
        (ENEMY, FRIEND): NEUTRAL,
        (ENEMY, ENEMY): GREAT_ENEMY,
    }
    return table[(nat, tmp)]


# --------------------------------------------------------------------------- #
# Sign-based dignity of a placed planet
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Dignity:
    planet: Planet
    sign: str
    state: str               # Exalted / Debilitated / Moolatrikona / Own / ...
    is_exalted: bool
    is_debilitated: bool
    is_moolatrikona: bool
    is_own: bool

    def __str__(self) -> str:
        return f"{self.planet.value} in {self.sign}: {self.state}"


def dignity(planet: Planet, longitude: float,
            dispositor_relationships: dict | None = None) -> Dignity:
    """Classify a planet's dignity from its sidereal longitude.

    The strongest applicable state is reported (exalt > moolatrikona > own >
    relationship-based). `dispositor_relationships` optionally supplies the
    compound relationship of the planet toward each sign lord for the
    great-friend/.../great-enemy classifications.
    """
    pos = to_zodiac(longitude)
    sign = pos.sign
    deg = pos.degree_in_sign

    ex_sign, _ = EXALTATION[planet]
    deb_sign = debilitation_sign(planet)

    is_exalted = sign == ex_sign
    is_debilitated = sign == deb_sign

    mt = MOOLATRIKONA.get(planet)
    is_mt = bool(mt and sign == mt[0] and mt[1] <= deg < mt[2])
    is_own = sign in OWN_SIGNS.get(planet, [])

    if is_exalted:
        state = "Exalted"
    elif is_debilitated:
        state = "Debilitated"
    elif is_mt:
        state = "Moolatrikona"
    elif is_own:
        state = "Own Sign"
    elif dispositor_relationships is not None:
        state = dispositor_relationships.get(sign, NEUTRAL)
    else:
        state = NEUTRAL

    return Dignity(
        planet=planet, sign=sign, state=state,
        is_exalted=is_exalted, is_debilitated=is_debilitated,
        is_moolatrikona=is_mt, is_own=is_own,
    )


def exaltation_longitude(planet: Planet) -> float:
    """Absolute sidereal longitude of a planet's deep exaltation point."""
    sign, deg = EXALTATION[planet]
    return norm360(_SIGN_IDX[sign] * 30.0 + deg)
