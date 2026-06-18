"""Planetary states (avasthas)."""

from __future__ import annotations

from ..angles import to_zodiac
from ..constants import Planet
from .dignities import dignity

# Baladi (five-fold) states by 6° segment within a sign.
BALADI_STATES = ["Bala", "Kumara", "Yuva", "Vriddha", "Mrita"]
# Relative strength weight traditionally assigned to each baladi state.
BALADI_STRENGTH = {"Bala": 0.25, "Kumara": 0.5, "Yuva": 1.0,
                   "Vriddha": 0.75, "Mrita": 0.0}


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


def deeptadi_avastha(planet: Planet, longitude: float) -> str:
    """Nine-fold state (simplified to the dignity-driven principal states)."""
    dig = dignity(planet, longitude)
    if dig.is_exalted:
        return "Deepta"        # radiant
    if dig.is_own or dig.is_moolatrikona:
        return "Swastha"       # comfortable
    if dig.is_debilitated:
        return "Khala"         # wicked / distressed
    return "Shanta"            # peaceful (neutral placement)


def all_avasthas(planet: Planet, longitude: float) -> dict[str, str]:
    return {
        "baladi": baladi_avastha(longitude),
        "jagradadi": jagradadi_avastha(planet, longitude),
        "deeptadi": deeptadi_avastha(planet, longitude),
    }
