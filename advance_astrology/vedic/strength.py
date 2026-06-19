"""Vaiśeṣikāṃśa — the named varga-dignity strength tiers.

A planet that occupies its own, friendly or exalted sign in many divisional
charts earns a higher tier. Counting such dignified placements across the
Ṣoḍaśavarga (16 divisions) maps to the classical named scales:

  2 → Pārijāta, 3 → Uttama, 4 → Gopura, 5 → Siṃhāsana, 6 → Pāravata,
  7 → Devaloka, 8 → Brahmaloka, 9 → Airāvata, 10+ → Śrīdhāma.
"""

from __future__ import annotations

from ..constants import SIGNS, Planet
from .dignities import EXALTATION, MOOLATRIKONA, OWN_SIGNS, natural_relationship
from .vargas import SHODASHAVARGA, divisional_sign

VAISESHIKAMSA_TIERS = [
    (2, "Parijata"), (3, "Uttama"), (4, "Gopura"), (5, "Simhasana"),
    (6, "Paravata"), (7, "Devaloka"), (8, "Brahmaloka"), (9, "Airavata"),
    (10, "Sridhama"),
]


def _is_dignified(planet: Planet, sign_index: int) -> bool:
    sign = SIGNS[sign_index]
    if sign in OWN_SIGNS.get(planet, []):
        return True
    if sign == EXALTATION[planet][0]:
        return True
    if planet in MOOLATRIKONA and MOOLATRIKONA[planet][0] == sign:
        return True
    from ..constants import RULERSHIPS
    return natural_relationship(planet, RULERSHIPS[sign]) == "Friend"


def dignified_varga_count(planet: Planet, longitude: float,
                          divisions=None) -> int:
    """How many of the chosen vargas the planet is dignified in."""
    divisions = divisions or SHODASHAVARGA
    return sum(
        _is_dignified(planet, divisional_sign(longitude, v))
        for v in divisions
    )


def vaiseshikamsa(planet: Planet, longitudes: dict[Planet, float],
                  divisions=None) -> str:
    """Named strength tier for a planet across the divisional charts."""
    count = dignified_varga_count(planet, longitudes[planet], divisions)
    tier = "Adhama"   # below Parijata
    for threshold, name in VAISESHIKAMSA_TIERS:
        if count >= threshold:
            tier = name
    return tier
