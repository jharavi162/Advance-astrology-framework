"""Essential dignities (Ptolemaic) and the almuten of a degree.

Domicile, exaltation, triplicity (Dorothean), Egyptian terms and Chaldean faces,
scored 5/4/3/2/1 respectively to find the almuten (the most dignified planet)
at any ecliptic degree.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..angles import to_zodiac
from ..constants import SIGNS, Planet

# Traditional domicile rulers.
DOMICILE = {
    "Aries": Planet.MARS, "Taurus": Planet.VENUS, "Gemini": Planet.MERCURY,
    "Cancer": Planet.MOON, "Leo": Planet.SUN, "Virgo": Planet.MERCURY,
    "Libra": Planet.VENUS, "Scorpio": Planet.MARS, "Sagittarius": Planet.JUPITER,
    "Capricorn": Planet.SATURN, "Aquarius": Planet.SATURN, "Pisces": Planet.JUPITER,
}

# Exaltation ruler and the degree of deepest exaltation (Western values).
EXALTATION = {
    "Aries": (Planet.SUN, 19), "Taurus": (Planet.MOON, 3),
    "Cancer": (Planet.JUPITER, 15), "Virgo": (Planet.MERCURY, 15),
    "Libra": (Planet.SATURN, 21), "Capricorn": (Planet.MARS, 28),
    "Pisces": (Planet.VENUS, 27),
}

# Dorothean triplicity rulers: (day, night, participating) per element.
TRIPLICITY = {
    "Fire": (Planet.SUN, Planet.JUPITER, Planet.SATURN),
    "Earth": (Planet.VENUS, Planet.MOON, Planet.MARS),
    "Air": (Planet.SATURN, Planet.MERCURY, Planet.JUPITER),
    "Water": (Planet.MARS, Planet.MARS, Planet.MOON),
}
_ELEMENT = {s: e for e, signs in {
    "Fire": ["Aries", "Leo", "Sagittarius"],
    "Earth": ["Taurus", "Virgo", "Capricorn"],
    "Air": ["Gemini", "Libra", "Aquarius"],
    "Water": ["Cancer", "Scorpio", "Pisces"],
}.items() for s in signs}

# Egyptian terms (bounds): per sign, list of (ruler, upper_bound_degree).
TERMS = {
    "Aries": [(Planet.JUPITER, 6), (Planet.VENUS, 12), (Planet.MERCURY, 20),
              (Planet.MARS, 25), (Planet.SATURN, 30)],
    "Taurus": [(Planet.VENUS, 8), (Planet.MERCURY, 14), (Planet.JUPITER, 22),
               (Planet.SATURN, 27), (Planet.MARS, 30)],
    "Gemini": [(Planet.MERCURY, 6), (Planet.JUPITER, 12), (Planet.VENUS, 17),
               (Planet.MARS, 24), (Planet.SATURN, 30)],
    "Cancer": [(Planet.MARS, 7), (Planet.VENUS, 13), (Planet.MERCURY, 19),
               (Planet.JUPITER, 26), (Planet.SATURN, 30)],
    "Leo": [(Planet.JUPITER, 6), (Planet.VENUS, 11), (Planet.SATURN, 18),
            (Planet.MERCURY, 24), (Planet.MARS, 30)],
    "Virgo": [(Planet.MERCURY, 7), (Planet.VENUS, 17), (Planet.JUPITER, 21),
              (Planet.MARS, 28), (Planet.SATURN, 30)],
    "Libra": [(Planet.SATURN, 6), (Planet.MERCURY, 14), (Planet.JUPITER, 21),
              (Planet.VENUS, 28), (Planet.MARS, 30)],
    "Scorpio": [(Planet.MARS, 7), (Planet.VENUS, 11), (Planet.MERCURY, 19),
                (Planet.JUPITER, 24), (Planet.SATURN, 30)],
    "Sagittarius": [(Planet.JUPITER, 12), (Planet.VENUS, 17),
                    (Planet.MERCURY, 21), (Planet.SATURN, 26), (Planet.MARS, 30)],
    "Capricorn": [(Planet.MERCURY, 7), (Planet.JUPITER, 14), (Planet.VENUS, 22),
                  (Planet.SATURN, 26), (Planet.MARS, 30)],
    "Aquarius": [(Planet.MERCURY, 7), (Planet.VENUS, 13), (Planet.JUPITER, 20),
                 (Planet.MARS, 25), (Planet.SATURN, 30)],
    "Pisces": [(Planet.VENUS, 12), (Planet.JUPITER, 16), (Planet.MERCURY, 19),
               (Planet.MARS, 28), (Planet.SATURN, 30)],
}

# Chaldean order for the 36 faces (decans), starting at 0° Aries.
_CHALDEAN = [Planet.MARS, Planet.SUN, Planet.VENUS, Planet.MERCURY,
             Planet.MOON, Planet.SATURN, Planet.JUPITER]

DIGNITY_SCORES = {"domicile": 5, "exaltation": 4, "triplicity": 3,
                  "term": 2, "face": 1}


def term_ruler(longitude: float) -> Planet:
    pos = to_zodiac(longitude)
    for ruler, bound in TERMS[pos.sign]:
        if pos.degree_in_sign < bound:
            return ruler
    return TERMS[pos.sign][-1][0]


def face_ruler(longitude: float) -> Planet:
    pos = to_zodiac(longitude)
    decan_index = pos.sign_index * 3 + int(pos.degree_in_sign // 10.0)
    return _CHALDEAN[decan_index % 7]


def triplicity_ruler(sign: str, is_day: bool, participating: bool = False) -> Planet:
    day, night, partic = TRIPLICITY[_ELEMENT[sign]]
    if participating:
        return partic
    return day if is_day else night


@dataclass
class EssentialDignity:
    longitude: float
    sign: str
    domicile: Planet
    exaltation: Planet | None
    triplicity: Planet
    term: Planet
    face: Planet

    def scores(self) -> dict[Planet, int]:
        tally: dict[Planet, int] = {}
        tally[self.domicile] = tally.get(self.domicile, 0) + DIGNITY_SCORES["domicile"]
        if self.exaltation:
            tally[self.exaltation] = tally.get(self.exaltation, 0) + DIGNITY_SCORES["exaltation"]
        tally[self.triplicity] = tally.get(self.triplicity, 0) + DIGNITY_SCORES["triplicity"]
        tally[self.term] = tally.get(self.term, 0) + DIGNITY_SCORES["term"]
        tally[self.face] = tally.get(self.face, 0) + DIGNITY_SCORES["face"]
        return tally

    def almuten(self) -> Planet:
        return max(self.scores().items(), key=lambda kv: kv[1])[0]


def essential_dignity(longitude: float, is_day: bool = True) -> EssentialDignity:
    pos = to_zodiac(longitude)
    exalt = EXALTATION.get(pos.sign)
    return EssentialDignity(
        longitude=longitude,
        sign=pos.sign,
        domicile=DOMICILE[pos.sign],
        exaltation=exalt[0] if exalt else None,
        triplicity=triplicity_ruler(pos.sign, is_day),
        term=term_ruler(longitude),
        face=face_ruler(longitude),
    )
