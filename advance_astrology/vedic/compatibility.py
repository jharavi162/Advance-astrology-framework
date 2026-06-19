"""Ashtakoota (Guna Milan) marriage compatibility — the 36-point system.

The eight kootas and their maxima: Varna 1, Vashya 2, Tara 3, Yoni 4,
Graha Maitri 5, Gana 6, Bhakoot 7, Nadi 8.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..constants import RULERSHIPS, SIGNS, Planet
from ..nakshatra import nakshatra_of
from . import nakshatra_attributes as na
from .dignities import natural_relationship, FRIEND, ENEMY, NEUTRAL

# --------------------------------------------------------------------------- #
# Varna (1)
# --------------------------------------------------------------------------- #

# Moon-sign varna, ranked Brahmin(4) > Kshatriya(3) > Vaishya(2) > Shudra(1).
_VARNA_RANK = {
    "Cancer": 4, "Scorpio": 4, "Pisces": 4,            # Brahmin (water)
    "Aries": 3, "Leo": 3, "Sagittarius": 3,            # Kshatriya (fire)
    "Taurus": 2, "Virgo": 2, "Capricorn": 2,           # Vaishya (earth)
    "Gemini": 1, "Libra": 1, "Aquarius": 1,            # Shudra (air)
}


def varna_koota(boy_sign: int, girl_sign: int) -> float:
    boy = _VARNA_RANK[SIGNS[boy_sign]]
    girl = _VARNA_RANK[SIGNS[girl_sign]]
    return 1.0 if boy >= girl else 0.0


# --------------------------------------------------------------------------- #
# Vashya (2)
# --------------------------------------------------------------------------- #

# Signs each sign holds vashya (control) over (whole-sign approximation).
_VASHYA = {
    "Aries": {"Leo", "Scorpio"}, "Taurus": {"Cancer", "Libra"},
    "Gemini": {"Virgo"}, "Cancer": {"Scorpio", "Sagittarius"},
    "Leo": {"Libra"}, "Virgo": {"Pisces", "Gemini"},
    "Libra": {"Capricorn", "Virgo"}, "Scorpio": {"Cancer"},
    "Sagittarius": {"Pisces"}, "Capricorn": {"Aries", "Aquarius"},
    "Aquarius": {"Aries"}, "Pisces": {"Capricorn"},
}


def vashya_koota(boy_sign: int, girl_sign: int) -> float:
    boy, girl = SIGNS[boy_sign], SIGNS[girl_sign]
    score = 0.0
    if girl in _VASHYA[boy]:
        score += 1.0
    if boy in _VASHYA[girl]:
        score += 1.0
    return min(score, 2.0)


# --------------------------------------------------------------------------- #
# Tara / Dina (3)
# --------------------------------------------------------------------------- #

def _tara_good(source_nak: int, target_nak: int) -> bool:
    count = (target_nak - source_nak) % 27 + 1
    tara = count % 9
    if tara == 0:
        tara = 9
    return tara not in (3, 5, 7)   # Vipat, Pratyari, Vadha are inauspicious


def tara_koota(boy_nak: int, girl_nak: int) -> float:
    score = 0.0
    if _tara_good(boy_nak, girl_nak):
        score += 1.5
    if _tara_good(girl_nak, boy_nak):
        score += 1.5
    return score


# --------------------------------------------------------------------------- #
# Yoni (4)
# --------------------------------------------------------------------------- #

_YONI_ENEMIES = {
    frozenset({"Horse", "Buffalo"}), frozenset({"Elephant", "Lion"}),
    frozenset({"Sheep", "Monkey"}), frozenset({"Serpent", "Mongoose"}),
    frozenset({"Dog", "Deer"}), frozenset({"Cat", "Rat"}),
    frozenset({"Cow", "Tiger"}),
}


def yoni_koota(boy_nak: int, girl_nak: int) -> float:
    a, b = na.YONI[boy_nak], na.YONI[girl_nak]
    if a == b:
        return 4.0
    if frozenset({a, b}) in _YONI_ENEMIES:
        return 0.0
    return 2.0   # friendly/neutral (simplified from the full 14x14 matrix)


# --------------------------------------------------------------------------- #
# Graha Maitri (5)
# --------------------------------------------------------------------------- #

def graha_maitri_koota(boy_sign: int, girl_sign: int) -> float:
    boy_lord = RULERSHIPS[SIGNS[boy_sign]]
    girl_lord = RULERSHIPS[SIGNS[girl_sign]]
    if boy_lord == girl_lord:
        return 5.0
    r1 = natural_relationship(boy_lord, girl_lord)
    r2 = natural_relationship(girl_lord, boy_lord)
    pair = {r1, r2}
    if pair == {FRIEND}:
        return 5.0
    if pair == {FRIEND, NEUTRAL}:
        return 4.0
    if pair == {NEUTRAL}:
        return 3.0
    if pair == {FRIEND, ENEMY}:
        return 1.0
    if pair == {NEUTRAL, ENEMY}:
        return 0.5
    return 0.0   # mutual enemies


# --------------------------------------------------------------------------- #
# Gana (6)
# --------------------------------------------------------------------------- #

_GANA_SCORE = {
    ("Deva", "Deva"): 6, ("Deva", "Manushya"): 6, ("Deva", "Rakshasa"): 1,
    ("Manushya", "Deva"): 5, ("Manushya", "Manushya"): 6,
    ("Manushya", "Rakshasa"): 0,
    ("Rakshasa", "Deva"): 1, ("Rakshasa", "Manushya"): 0,
    ("Rakshasa", "Rakshasa"): 6,
}


def gana_koota(boy_nak: int, girl_nak: int) -> float:
    return float(_GANA_SCORE[(na.GANA[boy_nak], na.GANA[girl_nak])])


# --------------------------------------------------------------------------- #
# Bhakoot (7)
# --------------------------------------------------------------------------- #

def bhakoot_koota(boy_sign: int, girl_sign: int) -> float:
    d1 = (girl_sign - boy_sign) % 12 + 1
    d2 = (boy_sign - girl_sign) % 12 + 1
    pair = {d1, d2}
    if pair in ({2, 12}, {5, 9}, {6, 8}):
        return 0.0
    return 7.0


# --------------------------------------------------------------------------- #
# Nadi (8)
# --------------------------------------------------------------------------- #

def nadi_koota(boy_nak: int, girl_nak: int) -> float:
    return 0.0 if na.NADI[boy_nak] == na.NADI[girl_nak] else 8.0


# --------------------------------------------------------------------------- #
# Aggregate
# --------------------------------------------------------------------------- #

@dataclass
class GunaMilan:
    scores: dict[str, float]
    total: float
    maximum: float = 36.0

    @property
    def percentage(self) -> float:
        return round(100.0 * self.total / self.maximum, 1)

    @property
    def verdict(self) -> str:
        pct = self.percentage
        if pct >= 75:
            return "Excellent"
        if pct >= 50:           # 18/36 is the traditional minimum to match
            return "Good"
        if pct >= 25:
            return "Average"
        return "Poor"

    def __str__(self) -> str:
        rows = [f"  {k:<14} {v:>4}" for k, v in self.scores.items()]
        return ("Ashtakoota (Guna Milan)\n" + "\n".join(rows) +
                f"\n  {'TOTAL':<14} {self.total:>4} / 36  "
                f"({self.percentage}% — {self.verdict})")


def guna_milan(
    boy_moon_sidereal: float,
    girl_moon_sidereal: float,
) -> GunaMilan:
    """Compute the full 36-point Ashtakoota from both Moons' sidereal longitudes."""
    from ..angles import to_zodiac
    bs = to_zodiac(boy_moon_sidereal).sign_index
    gs = to_zodiac(girl_moon_sidereal).sign_index
    bn = nakshatra_of(boy_moon_sidereal).index
    gn = nakshatra_of(girl_moon_sidereal).index

    scores = {
        "Varna": varna_koota(bs, gs),
        "Vashya": vashya_koota(bs, gs),
        "Tara": tara_koota(bn, gn),
        "Yoni": yoni_koota(bn, gn),
        "Graha Maitri": graha_maitri_koota(bs, gs),
        "Gana": gana_koota(bn, gn),
        "Bhakoot": bhakoot_koota(bs, gs),
        "Nadi": nadi_koota(bn, gn),
    }
    return GunaMilan(scores=scores, total=round(sum(scores.values()), 1))
