"""Divisional charts (Vargas / Amshas) per Parashara (BPHS).

Implements the sixteen Shodasavarga divisions. Each function maps a sidereal
longitude to the sign (rashi) it occupies in that divisional chart; a
``VargaChart`` applies the mapping to every body and the ascendant.

Varga sign indices follow the project convention: 0 = Aries .. 11 = Pisces.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..angles import norm360, to_zodiac
from ..constants import SIGNS, Planet

# Sign-nature helpers (s = 0..11, Aries..Pisces).
def _is_odd(s: int) -> bool:        # odd-numbered sign (Aries, Gemini, ...)
    return s % 2 == 0

def _is_movable(s: int) -> bool:    # chara: Aries, Cancer, Libra, Capricorn
    return s % 3 == 0

def _is_fixed(s: int) -> bool:      # sthira: Taurus, Leo, Scorpio, Aquarius
    return s % 3 == 1

def _is_dual(s: int) -> bool:       # dvisvabhava: Gemini, Virgo, Sag, Pisces
    return s % 3 == 2

def _element(s: int) -> int:        # 0 fire, 1 earth, 2 air, 3 water
    return s % 4


def _split(longitude: float) -> tuple[int, float]:
    pos = to_zodiac(longitude)
    return pos.sign_index, pos.degree_in_sign


# --------------------------------------------------------------------------- #
# Individual divisional mappings -> sign index (0..11)
# --------------------------------------------------------------------------- #

def d1(longitude: float) -> int:
    s, _ = _split(longitude)
    return s


def d2_hora(longitude: float) -> int:
    s, d = _split(longitude)
    first_half = d < 15.0
    # Odd sign: 1st half -> Leo (Sun), 2nd -> Cancer (Moon). Even: reversed.
    if _is_odd(s):
        return 4 if first_half else 3        # Leo / Cancer
    return 3 if first_half else 4            # Cancer / Leo


def d3_drekkana(longitude: float) -> int:
    s, d = _split(longitude)
    part = int(d // 10.0)                    # 0,1,2
    return (s + 4 * part) % 12               # same, 5th, 9th


def d4_chaturthamsha(longitude: float) -> int:
    s, d = _split(longitude)
    part = int(d // 7.5)                     # 0..3
    return (s + 3 * part) % 12               # same, 4th, 7th, 10th


def d7_saptamsha(longitude: float) -> int:
    s, d = _split(longitude)
    part = int(d // (30.0 / 7))              # 0..6
    start = s if _is_odd(s) else (s + 6) % 12
    return (start + part) % 12


def d9_navamsha(longitude: float) -> int:
    s, d = _split(longitude)
    part = int(d // (30.0 / 9))              # 0..8
    if _is_movable(s):
        start = s
    elif _is_fixed(s):
        start = (s + 8) % 12                 # 9th
    else:
        start = (s + 4) % 12                 # 5th
    return (start + part) % 12


def d10_dashamsha(longitude: float) -> int:
    s, d = _split(longitude)
    part = int(d // 3.0)                     # 0..9
    start = s if _is_odd(s) else (s + 8) % 12
    return (start + part) % 12


def d12_dwadashamsha(longitude: float) -> int:
    s, d = _split(longitude)
    part = int(d // 2.5)                     # 0..11
    return (s + part) % 12                   # count from same sign


def d16_shodashamsha(longitude: float) -> int:
    s, d = _split(longitude)
    part = int(d // (30.0 / 16))             # 0..15
    start = {0: 0, 1: 4, 2: 8}[s % 3]        # movable Aries / fixed Leo / dual Sag
    return (start + part) % 12


def d20_vimshamsha(longitude: float) -> int:
    s, d = _split(longitude)
    part = int(d // 1.5)                      # 0..19
    start = {0: 0, 1: 8, 2: 4}[s % 3]         # movable Aries / fixed Sag / dual Leo
    return (start + part) % 12


def d24_chaturvimshamsha(longitude: float) -> int:
    s, d = _split(longitude)
    part = int(d // 1.25)                     # 0..23
    start = 4 if _is_odd(s) else 3            # odd Leo / even Cancer
    return (start + part) % 12


def d27_bhamsha(longitude: float) -> int:
    s, d = _split(longitude)
    part = int(d // (30.0 / 27))              # 0..26
    start = {0: 0, 1: 3, 2: 6, 3: 9}[_element(s)]  # fire/earth/air/water
    return (start + part) % 12


def d30_trimshamsha(longitude: float) -> int:
    s, d = _split(longitude)
    if _is_odd(s):
        # Mars, Saturn, Jupiter, Mercury, Venus
        if d < 5:    return 0    # Aries
        if d < 10:   return 10   # Aquarius
        if d < 18:   return 8    # Sagittarius
        if d < 25:   return 2    # Gemini
        return 6                 # Libra
    else:
        # Venus, Mercury, Jupiter, Saturn, Mars
        if d < 5:    return 1    # Taurus
        if d < 12:   return 5    # Virgo
        if d < 20:   return 11   # Pisces
        if d < 25:   return 9    # Capricorn
        return 7                 # Scorpio


def d40_khavedamsha(longitude: float) -> int:
    s, d = _split(longitude)
    part = int(d // 0.75)                     # 0..39
    start = 0 if _is_odd(s) else 6            # odd Aries / even Libra
    return (start + part) % 12


def d45_akshavedamsha(longitude: float) -> int:
    s, d = _split(longitude)
    part = int(d // (30.0 / 45))              # 0..44
    start = {0: 0, 1: 4, 2: 8}[s % 3]         # movable Aries / fixed Leo / dual Sag
    return (start + part) % 12


def d60_shashtiamsha(longitude: float) -> int:
    s, d = _split(longitude)
    part = int(d // 0.5)                       # 0..59
    return (s + part) % 12                     # count from same sign


# --------------------------------------------------------------------------- #
# Registry & dispatch
# --------------------------------------------------------------------------- #

VARGA_FUNCS = {
    1: d1, 2: d2_hora, 3: d3_drekkana, 4: d4_chaturthamsha, 7: d7_saptamsha,
    9: d9_navamsha, 10: d10_dashamsha, 12: d12_dwadashamsha,
    16: d16_shodashamsha, 20: d20_vimshamsha, 24: d24_chaturvimshamsha,
    27: d27_bhamsha, 30: d30_trimshamsha, 40: d40_khavedamsha,
    45: d45_akshavedamsha, 60: d60_shashtiamsha,
}

VARGA_NAMES = {
    1: "Rashi (D1)", 2: "Hora (D2)", 3: "Drekkana (D3)",
    4: "Chaturthamsha (D4)", 7: "Saptamsha (D7)", 9: "Navamsha (D9)",
    10: "Dashamsha (D10)", 12: "Dwadashamsha (D12)", 16: "Shodashamsha (D16)",
    20: "Vimshamsha (D20)", 24: "Chaturvimshamsha (D24)", 27: "Bhamsha (D27)",
    30: "Trimshamsha (D30)", 40: "Khavedamsha (D40)",
    45: "Akshavedamsha (D45)", 60: "Shashtiamsha (D60)",
}

# Standard varga groupings.
SHADVARGA = [1, 2, 3, 9, 12, 30]
SAPTAVARGA = [1, 2, 3, 7, 9, 12, 30]
DASHAVARGA = [1, 2, 3, 7, 9, 10, 12, 16, 30, 60]
SHODASHAVARGA = [1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]

# Vimshopaka bala weights (sum 20) for the Shadvarga and Dashavarga schemes.
VIMSHOPAKA_SHADVARGA = {1: 6, 2: 2, 3: 4, 9: 5, 12: 2, 30: 1}
VIMSHOPAKA_DASHAVARGA = {1: 3, 2: 1, 3: 1, 7: 1, 9: 3, 10: 1,
                         12: 2, 16: 2, 30: 3, 60: 3}
VIMSHOPAKA_SHODASHAVARGA = {
    1: 3.5, 2: 1, 3: 1, 4: 0.5, 7: 0.5, 9: 3, 10: 0.5, 12: 0.5,
    16: 2, 20: 0.5, 24: 0.5, 27: 0.5, 30: 1, 40: 0.5, 45: 0.5, 60: 4,
}


def divisional_sign(longitude: float, varga: int) -> int:
    """Sign index (0..11) of a longitude in the given divisional chart."""
    if varga not in VARGA_FUNCS:
        raise ValueError(
            f"Unsupported varga D{varga}. Available: {sorted(VARGA_FUNCS)}"
        )
    return VARGA_FUNCS[varga](longitude)


@dataclass
class VargaChart:
    varga: int
    name: str
    ascendant_sign: int
    signs: dict[Planet, int]          # planet -> sign index in this varga

    def house_of(self, planet: Planet) -> int:
        """Bhava (1..12) of a planet, counted from the varga ascendant."""
        return (self.signs[planet] - self.ascendant_sign) % 12 + 1

    def planets_in_sign(self, sign_index: int) -> list[Planet]:
        return [p for p, s in self.signs.items() if s == sign_index]

    def __str__(self) -> str:
        rows = [f"{self.name}  (Asc: {SIGNS[self.ascendant_sign]})"]
        for p, s in self.signs.items():
            rows.append(f"  {p.value:<8} {SIGNS[s]:<12} H{self.house_of(p)}")
        return "\n".join(rows)


def build_varga(
    varga: int,
    ascendant_longitude: float,
    planet_longitudes: dict[Planet, float],
) -> VargaChart:
    """Build a divisional chart from sidereal longitudes."""
    asc_sign = divisional_sign(ascendant_longitude, varga)
    signs = {p: divisional_sign(lon, varga) for p, lon in planet_longitudes.items()}
    return VargaChart(varga, VARGA_NAMES[varga], asc_sign, signs)


def vimshopaka_bala(
    planet: Planet,
    ascendant_longitude: float,
    planet_longitudes: dict[Planet, float],
    scheme: str = "shadvarga",
) -> float:
    """Vimshopaka strength (out of 20): rewards dignity across many vargas.

    A simplified-but-standard scoring: each varga contributes its weight when
    the planet falls in its own / friendly / exalted sign, scaled by the
    quality of that placement.
    """
    from .dignities import EXALTATION, OWN_SIGNS, debilitation_sign

    weights = {
        "shadvarga": VIMSHOPAKA_SHADVARGA,
        "dashavarga": VIMSHOPAKA_DASHAVARGA,
        "shodashavarga": VIMSHOPAKA_SHODASHAVARGA,
    }[scheme]

    total = 0.0
    for v, w in weights.items():
        sign_idx = divisional_sign(planet_longitudes[planet], v)
        sign = SIGNS[sign_idx]
        if sign == EXALTATION[planet][0] or sign in OWN_SIGNS.get(planet, []):
            total += w
        elif sign == debilitation_sign(planet):
            total += 0.0
        else:
            total += w * 0.5
    return round(total, 3)
