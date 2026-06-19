"""Arudha padas (Jaimini).

The arudha of a house is the "reflection" of the house through its lord: count
from the house to its lord, then the same count onward from the lord. Two
exceptions keep the arudha from coinciding with the house itself or its 7th.

  * Arudha Lagna (AL) = arudha of the 1st house
  * Upapada Lagna (UL) = arudha of the 12th house
  * A1 .. A12 = arudhas of houses 1 .. 12
"""

from __future__ import annotations

from ..constants import RULERSHIPS, SIGNS, Planet

# Sign lords including the standard (non-nodal) rulerships used for arudhas.
_LORD = {i: RULERSHIPS[SIGNS[i]] for i in range(12)}


def _lord_of(sign_index: int) -> Planet:
    return _LORD[sign_index]


def arudha_of_sign(house_sign: int, lord_sign: int) -> int:
    """Arudha pada sign index for a house at `house_sign` whose lord is in
    `lord_sign`."""
    a = (2 * lord_sign - house_sign) % 12
    # Exception: an arudha may not fall in the house itself (1st) or its 7th;
    # in those cases take the 10th sign from the computed pada.
    if (a - house_sign) % 12 in (0, 6):
        a = (a + 9) % 12
    return a


def all_arudhas(
    ascendant_sign: int,
    planet_signs: dict[Planet, int],
) -> dict[str, int]:
    """Compute A1..A12 (keyed 'A1'..'A12') plus 'AL' and 'UL'.

    `planet_signs` must include the seven sign lords (Sun..Saturn) so each
    house lord's position is known.
    """
    arudhas: dict[str, int] = {}
    for house in range(1, 13):
        house_sign = (ascendant_sign + house - 1) % 12
        lord = _lord_of(house_sign)
        lord_sign = planet_signs[lord]
        arudhas[f"A{house}"] = arudha_of_sign(house_sign, lord_sign)
    arudhas["AL"] = arudhas["A1"]
    arudhas["UL"] = arudhas["A12"]
    return arudhas


def arudha_lagna(ascendant_sign: int, planet_signs: dict[Planet, int]) -> int:
    lord = _lord_of(ascendant_sign)
    return arudha_of_sign(ascendant_sign, planet_signs[lord])


def upapada_lagna(ascendant_sign: int, planet_signs: dict[Planet, int]) -> int:
    twelfth = (ascendant_sign + 11) % 12
    lord = _lord_of(twelfth)
    return arudha_of_sign(twelfth, planet_signs[lord])
