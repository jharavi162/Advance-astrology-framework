"""Planetary states (avasthas)."""

from __future__ import annotations

from ..angles import angular_separation, to_zodiac
from ..constants import Planet
from .dignities import dignity

# Baladi (five-fold) states by 6° segment within a sign.
BALADI_STATES = ["Bala", "Kumara", "Yuva", "Vriddha", "Mrita"]
# Relative strength weight traditionally assigned to each baladi state.
BALADI_STRENGTH = {"Bala": 0.25, "Kumara": 0.5, "Yuva": 1.0,
                   "Vriddha": 0.75, "Mrita": 0.0}

# Combustion (astangata) orbs from the Sun, in degrees.
COMBUSTION_ORB = {
    Planet.MOON: 12.0, Planet.MARS: 17.0, Planet.MERCURY: 14.0,
    Planet.JUPITER: 11.0, Planet.VENUS: 10.0, Planet.SATURN: 15.0,
}


def baladi_avastha(longitude: float) -> str:
    """Infant→dead state from the degree within the sign (reversed for even
    signs)."""
    pos = to_zodiac(longitude)
    seg = int(pos.degree_in_sign // 6.0)        # 0..4
    if pos.sign_index % 2 == 1:                 # even-numbered sign -> reversed
        seg = 4 - seg
    return BALADI_STATES[seg]


def jagradadi_avastha(planet: Planet, longitude: float) -> str:
    """Three-fold wakefulness state from sign dignity.

    Jagrat (awake) in own/exaltation, Swapna (dreaming) in friendly/neutral,
    Sushupti (sleeping) in enemy/debilitation.
    """
    dig = dignity(planet, longitude)
    if dig.is_exalted or dig.is_own or dig.is_moolatrikona:
        return "Jagrat"
    if dig.is_debilitated:
        return "Sushupti"
    return "Swapna"


def is_combust(planet: Planet, longitude: float, sun_longitude: float) -> bool:
    """Whether a planet is combust (astangata) — too close to the Sun."""
    if planet not in COMBUSTION_ORB:
        return False
    return angular_separation(longitude, sun_longitude) <= COMBUSTION_ORB[planet]


def deeptadi_avastha(planet: Planet, longitude: float,
                     sun_longitude: float | None = None) -> str:
    """Temperamental mood (Dīptādi) — the fuller eight-state scheme.

    Dīpta (exalted), Svastha (own), Pramudita (great-friend), Śānta
    (friend/neutral), Dīna (enemy), Khala (great-enemy), Vikala (combust),
    Duḥkhita (debilitated). Combustion overrides to Vikala.
    """
    if sun_longitude is not None and is_combust(planet, longitude, sun_longitude):
        return "Vikala"
    dig = dignity(planet, longitude)
    if dig.is_debilitated:
        return "Duhkhita"
    if dig.is_exalted:
        return "Dipta"
    if dig.is_own or dig.is_moolatrikona:
        return "Svastha"
    # Fall back to the dispositor relationship for the remaining moods.
    from ..constants import RULERSHIPS, SIGNS
    from .dignities import natural_relationship
    sign = SIGNS[to_zodiac(longitude).sign_index]
    dispositor = RULERSHIPS[sign]
    rel = natural_relationship(planet, dispositor)
    return {"Friend": "Pramudita", "Neutral": "Shanta", "Enemy": "Dina"}.get(
        rel, "Shanta")


def all_avasthas(planet: Planet, longitude: float,
                 sun_longitude: float | None = None) -> dict[str, str]:
    return {
        "baladi": baladi_avastha(longitude),
        "jagradadi": jagradadi_avastha(planet, longitude),
        "deeptadi": deeptadi_avastha(planet, longitude, sun_longitude),
        "combust": "Yes" if (sun_longitude is not None
                             and is_combust(planet, longitude, sun_longitude))
                   else "No",
    }
