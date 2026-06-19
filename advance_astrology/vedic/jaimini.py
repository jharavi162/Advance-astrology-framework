"""Jaimini astrology: Chara Karakas, Karakamsha, Argala and Chara dasha."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from ..angles import to_zodiac
from ..constants import RULERSHIPS, SIGNS, Planet
from ..dasha import DAYS_PER_YEAR, DashaPeriod

# --------------------------------------------------------------------------- #
# Chara Karakas
# --------------------------------------------------------------------------- #

# Eight-karaka scheme (includes Rahu); seven-karaka drops Rahu and merges
# Pitri/Matri into a single Matrikaraka.
KARAKAS_8 = ["Atmakaraka", "Amatyakaraka", "Bhratrikaraka", "Matrikaraka",
             "Pitrikaraka", "Putrakaraka", "Gnatikaraka", "Darakaraka"]
KARAKAS_7 = ["Atmakaraka", "Amatyakaraka", "Bhratrikaraka", "Matrikaraka",
             "Putrakaraka", "Gnatikaraka", "Darakaraka"]

KARAKA_ABBR = {
    "Atmakaraka": "AK", "Amatyakaraka": "AmK", "Bhratrikaraka": "BK",
    "Matrikaraka": "MK", "Pitrikaraka": "PiK", "Putrakaraka": "PK",
    "Gnatikaraka": "GK", "Darakaraka": "DK",
}


def chara_karakas(
    planet_longitudes: dict[Planet, float],
    scheme: int = 8,
) -> dict[str, Planet]:
    """Assign Chara Karakas by descending degree-within-sign.

    Rahu (used only in the 8-karaka scheme) is counted in reverse, i.e. by
    ``30 - degree``, because it is retrograde.
    """
    if scheme == 8:
        bodies = [Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
                  Planet.JUPITER, Planet.VENUS, Planet.SATURN, Planet.RAHU]
        names = KARAKAS_8
    else:
        bodies = [Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
                  Planet.JUPITER, Planet.VENUS, Planet.SATURN]
        names = KARAKAS_7

    degrees = {}
    for p in bodies:
        d = to_zodiac(planet_longitudes[p]).degree_in_sign
        degrees[p] = (30.0 - d) if p is Planet.RAHU else d

    ranked = sorted(bodies, key=lambda p: degrees[p], reverse=True)
    return {name: planet for name, planet in zip(names, ranked)}


def atmakaraka(planet_longitudes: dict[Planet, float], scheme: int = 8) -> Planet:
    return chara_karakas(planet_longitudes, scheme)["Atmakaraka"]


# --------------------------------------------------------------------------- #
# Karakamsha
# --------------------------------------------------------------------------- #

def karakamsha(
    planet_longitudes: dict[Planet, float],
    navamsha_signs: dict[Planet, int],
    scheme: int = 8,
) -> int:
    """Sign of the Atmakaraka in the navamsha (the Karakamsha lagna)."""
    ak = atmakaraka(planet_longitudes, scheme)
    return navamsha_signs[ak]


# --------------------------------------------------------------------------- #
# Argala (intervention) and Virodhargala (counter-intervention)
# --------------------------------------------------------------------------- #

# Primary argala houses and the house that counters each.
ARGALA_HOUSES = {2: 12, 4: 10, 11: 3, 5: 9}


@dataclass
class Argala:
    house: int            # the argala-causing house (from the reference sign)
    causers: list[Planet]
    counter_house: int
    counterers: list[Planet]

    @property
    def effective(self) -> bool:
        """Argala holds when its causers outnumber the counterers."""
        return len(self.causers) > len(self.counterers)


def argala_on_sign(
    reference_sign: int,
    planet_signs: dict[Planet, int],
) -> list[Argala]:
    """Compute argalas acting on a sign from occupying planets."""
    by_sign: dict[int, list[Planet]] = {}
    for p, s in planet_signs.items():
        by_sign.setdefault(s, []).append(p)

    out: list[Argala] = []
    for arg_h, ctr_h in ARGALA_HOUSES.items():
        arg_sign = (reference_sign + arg_h - 1) % 12
        ctr_sign = (reference_sign + ctr_h - 1) % 12
        out.append(Argala(
            house=arg_h,
            causers=by_sign.get(arg_sign, []),
            counter_house=ctr_h,
            counterers=by_sign.get(ctr_sign, []),
        ))
    return out


# --------------------------------------------------------------------------- #
# Chara dasha (Jaimini sign dasha, Parashara / KN Rao method)
# --------------------------------------------------------------------------- #

def _co_lord_sign(sign: int, planet_signs: dict[Planet, int]) -> Planet:
    """Lord of a sign, resolving Scorpio/Aquarius co-lordship by placement.

    For Scorpio the stronger of Mars/Ketu and for Aquarius of Saturn/Rahu is
    taken; here we use the conventional primary lord, but prefer the node when
    it occupies the sign (a common strength heuristic).
    """
    name = SIGNS[sign]
    if name == "Scorpio":
        return Planet.KETU if planet_signs.get(Planet.KETU) == sign else Planet.MARS
    if name == "Aquarius":
        return Planet.RAHU if planet_signs.get(Planet.RAHU) == sign else Planet.SATURN
    return RULERSHIPS[name]


def chara_dasha_years(sign: int, planet_signs: dict[Planet, int]) -> int:
    """Duration (years) of a sign's Chara dasha.

    Count from the sign to its lord — forward for odd signs, backward for even
    signs. Years = (count − 1); if the lord sits in its own sign, 12 years.
    """
    lord = _co_lord_sign(sign, planet_signs)
    lord_sign = planet_signs[lord]
    odd = sign % 2 == 0   # odd-numbered sign (Aries, Gemini, ...)
    if odd:
        count = (lord_sign - sign) % 12 + 1
    else:
        count = (sign - lord_sign) % 12 + 1
    years = count - 1
    return 12 if years == 0 else years


def _rashi_strength(sign: int, planet_signs: dict[Planet, int]) -> float:
    """Simplified Jaimini rashi bala for seeding Narayana dasha.

    Counts occupants, a bonus if the sign holds its own lord, and a bonus for an
    aspect from Jupiter. (Full Jaimini rashi bala is more elaborate; this is a
    deterministic, documented approximation for the 1st-vs-7th seed choice.)
    """
    from .aspects import rashi_aspects
    occupants = sum(1 for s in planet_signs.values() if s == sign)
    strength = float(occupants)
    lord = _co_lord_sign(sign, planet_signs)
    if planet_signs.get(lord) == sign:
        strength += 1.0
    jup = planet_signs.get(Planet.JUPITER)
    if jup is not None and sign in rashi_aspects(jup):
        strength += 0.5
    return strength


def narayana_dasha(
    ascendant_sign: int,
    planet_signs: dict[Planet, int],
    planet_longitudes: dict[Planet, float],
    birth: datetime,
    cycles: int = 1,
) -> list[DashaPeriod]:
    """Nārāyaṇa (Padakrama) Daśā — Parashari Jaimini rashi dasha.

    Seeds from the stronger of the Lagna and the 7th house; progresses
    zodiacally for an odd seed sign and reverse for an even one. Each sign's
    span is (signs to its lord − 1), counted directly for odd signs and in
    reverse for even ones, adjusted ±1 year for an exalted/debilitated lord.
    """
    seventh = (ascendant_sign + 6) % 12
    seed = (ascendant_sign
            if _rashi_strength(ascendant_sign, planet_signs)
            >= _rashi_strength(seventh, planet_signs)
            else seventh)
    direct = seed % 2 == 0
    order = [((seed + i) if direct else (seed - i)) % 12 for i in range(12)]

    periods: list[DashaPeriod] = []
    cursor = birth
    for _ in range(cycles):
        for s in order:
            years = narayana_years(s, planet_signs, planet_longitudes)
            end = cursor + timedelta(days=years * DAYS_PER_YEAR)
            lord = _co_lord_sign(s, planet_signs)
            periods.append(DashaPeriod(lord, cursor, end, level=1, note=SIGNS[s]))
            cursor = end
    return periods


def narayana_years(sign: int, planet_signs: dict[Planet, int],
                   planet_longitudes: dict[Planet, float]) -> int:
    """Duration (years) of a sign's Narayana dasha."""
    from .dignities import dignity
    lord = _co_lord_sign(sign, planet_signs)
    lord_sign = planet_signs[lord]
    odd = sign % 2 == 0
    count = ((lord_sign - sign) if odd else (sign - lord_sign)) % 12 + 1
    base = count - 1
    if base == 0:
        base = 12
    dig = dignity(lord, planet_longitudes[lord])
    if dig.is_exalted:
        base = min(12, base + 1)
    elif dig.is_debilitated:
        base = max(1, base - 1)
    return base


def chara_dasha(
    ascendant_sign: int,
    planet_signs: dict[Planet, int],
    birth: datetime,
    cycles: int = 1,
) -> list[DashaPeriod]:
    """Jaimini Chara (rashi) dasha sequence beginning from the lagna.

    Progression is zodiacal when the lagna is an odd sign and reverse when it
    is even. Each period's lord is recorded as the sign ruler; the sign name is
    stored in ``DashaPeriod.note``.
    """
    direct = ascendant_sign % 2 == 0   # odd lagna -> direct
    order = []
    for i in range(12):
        s = (ascendant_sign + i) % 12 if direct else (ascendant_sign - i) % 12
        order.append(s)

    periods: list[DashaPeriod] = []
    cursor = birth
    for _ in range(cycles):
        for s in order:
            years = chara_dasha_years(s, planet_signs)
            end = cursor + timedelta(days=years * DAYS_PER_YEAR)
            lord = _co_lord_sign(s, planet_signs)
            period = DashaPeriod(lord, cursor, end, level=1, note=SIGNS[s])
            periods.append(period)
            cursor = end
    return periods
