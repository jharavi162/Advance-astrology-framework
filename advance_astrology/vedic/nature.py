"""Planetary nature: natural benefic/malefic and functional (per-lagna) status.

Natural (naisargika) nature is intrinsic; functional (tatkalika/bhava-adhipati)
nature depends on the houses a planet rules from a given ascendant, yielding
the Śubha (benefic) / Krūra (malefic) / Taṭastha (neutral) classification plus
Yogakāraka and Maraka flags the playbook relies on.
"""

from __future__ import annotations

from ..constants import RULERSHIPS, SIGNS, Planet

NATURAL_BENEFICS = {Planet.JUPITER, Planet.VENUS}
NATURAL_MALEFICS = {Planet.SUN, Planet.MARS, Planet.SATURN,
                    Planet.RAHU, Planet.KETU}


def natural_benefic(planet: Planet, *, moon_waxing: bool = True,
                    mercury_with_malefic: bool = False) -> bool:
    """Whether a planet is a natural benefic.

    The Moon is benefic when waxing; Mercury is benefic unless joined by a
    malefic.
    """
    if planet in NATURAL_BENEFICS:
        return True
    if planet is Planet.MOON:
        return moon_waxing
    if planet is Planet.MERCURY:
        return not mercury_with_malefic
    return False


# Houses ruled (1..12) by each planet for a given ascendant sign.
def houses_ruled(planet: Planet, asc_sign: int) -> list[int]:
    out = []
    for house in range(1, 13):
        sign = SIGNS[(asc_sign + house - 1) % 12]
        if RULERSHIPS[sign] == planet:
            out.append(house)
    return out


KENDRAS = (1, 4, 7, 10)
TRIKONAS = (1, 5, 9)
DUSTHANAS = (6, 8, 12)
MARAKA_HOUSES = (2, 7)

# Classification labels.
YOGAKARAKA = "Yogakaraka"
BENEFIC = "Benefic"
MALEFIC = "Malefic"
NEUTRAL = "Neutral"


def functional_nature(asc_sign: int) -> dict[Planet, str]:
    """Functional benefic/malefic/neutral for each of the seven grahas.

    Parashari rules: trikona lords are benefic; kendra lordship grants malefics
    benefic capacity but afflicts natural benefics (kendradhipati dosha);
    owning a kendra *and* a trikona makes a Yogakaraka; 3/6/8/11/12 lordship
    leans malefic.
    """
    nature: dict[Planet, str] = {}
    for planet in (Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
                   Planet.JUPITER, Planet.VENUS, Planet.SATURN):
        houses = houses_ruled(planet, asc_sign)
        owns_trikona = any(h in (5, 9) for h in houses)
        owns_kendra = any(h in (4, 7, 10) for h in houses)
        owns_dusthana = any(h in DUSTHANAS for h in houses)
        owns_growth = any(h in (3, 11) for h in houses)
        is_lagna_lord = 1 in houses

        if owns_kendra and (owns_trikona or is_lagna_lord):
            nature[planet] = YOGAKARAKA
        elif owns_trikona or is_lagna_lord:
            nature[planet] = BENEFIC
        elif owns_dusthana or owns_growth:
            nature[planet] = MALEFIC
        elif owns_kendra:
            # Kendradhipati dosha: benefics neutralised, malefics empowered.
            nature[planet] = NEUTRAL if natural_benefic(planet) else BENEFIC
        else:
            nature[planet] = NEUTRAL
    return nature


def marakas(asc_sign: int) -> list[Planet]:
    """Maraka (death-inflicting) lords — rulers of the 2nd and 7th houses."""
    out = []
    for house in MARAKA_HOUSES:
        sign = SIGNS[(asc_sign + house - 1) % 12]
        lord = RULERSHIPS[sign]
        if lord not in out:
            out.append(lord)
    return out


def yogakarakas(asc_sign: int) -> list[Planet]:
    return [p for p, n in functional_nature(asc_sign).items() if n == YOGAKARAKA]
