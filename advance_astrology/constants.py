"""Core astrological constants: zodiac signs, planets, aspects, nakshatras.

All longitudes in this framework are measured in degrees [0, 360) along the
ecliptic, increasing eastward, with 0 deg at the vernal equinox (tropical) or
the chosen sidereal origin (sidereal).
"""

from __future__ import annotations

from enum import Enum

# --------------------------------------------------------------------------- #
# Zodiac signs
# --------------------------------------------------------------------------- #

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

SIGN_GLYPHS = {
    "Aries": "♈", "Taurus": "♉", "Gemini": "♊", "Cancer": "♋",
    "Leo": "♌", "Virgo": "♍", "Libra": "♎", "Scorpio": "♏",
    "Sagittarius": "♐", "Capricorn": "♑", "Aquarius": "♒", "Pisces": "♓",
}

# Element and modality (quality) of each sign.
ELEMENTS = {
    "Fire": ["Aries", "Leo", "Sagittarius"],
    "Earth": ["Taurus", "Virgo", "Capricorn"],
    "Air": ["Gemini", "Libra", "Aquarius"],
    "Water": ["Cancer", "Scorpio", "Pisces"],
}

MODALITIES = {
    "Cardinal": ["Aries", "Cancer", "Libra", "Capricorn"],
    "Fixed": ["Taurus", "Leo", "Scorpio", "Aquarius"],
    "Mutable": ["Gemini", "Virgo", "Sagittarius", "Pisces"],
}

POLARITIES = {
    "Positive": ["Aries", "Gemini", "Leo", "Libra", "Sagittarius", "Aquarius"],
    "Negative": ["Taurus", "Cancer", "Virgo", "Scorpio", "Capricorn", "Pisces"],
}


def sign_element(sign: str) -> str:
    for element, signs in ELEMENTS.items():
        if sign in signs:
            return element
    raise ValueError(f"Unknown sign: {sign}")


def sign_modality(sign: str) -> str:
    for modality, signs in MODALITIES.items():
        if sign in signs:
            return modality
    raise ValueError(f"Unknown sign: {sign}")


def sign_polarity(sign: str) -> str:
    for polarity, signs in POLARITIES.items():
        if sign in signs:
            return polarity
    raise ValueError(f"Unknown sign: {sign}")


# --------------------------------------------------------------------------- #
# Planets / points
# --------------------------------------------------------------------------- #

class Planet(str, Enum):
    SUN = "Sun"
    MOON = "Moon"
    MERCURY = "Mercury"
    VENUS = "Venus"
    MARS = "Mars"
    JUPITER = "Jupiter"
    SATURN = "Saturn"
    URANUS = "Uranus"
    NEPTUNE = "Neptune"
    PLUTO = "Pluto"
    RAHU = "Rahu"      # North lunar node (Mean)
    KETU = "Ketu"      # South lunar node (Mean)


# The classical seven plus modern + nodes. Default set used for natal charts.
DEFAULT_PLANETS = [
    Planet.SUN, Planet.MOON, Planet.MERCURY, Planet.VENUS, Planet.MARS,
    Planet.JUPITER, Planet.SATURN, Planet.URANUS, Planet.NEPTUNE, Planet.PLUTO,
    Planet.RAHU, Planet.KETU,
]

# The seven traditional / Vedic grahas (no outer planets, includes nodes).
VEDIC_GRAHAS = [
    Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY, Planet.JUPITER,
    Planet.VENUS, Planet.SATURN, Planet.RAHU, Planet.KETU,
]

PLANET_GLYPHS = {
    Planet.SUN: "☉", Planet.MOON: "☽", Planet.MERCURY: "☿",
    Planet.VENUS: "♀", Planet.MARS: "♂", Planet.JUPITER: "♃",
    Planet.SATURN: "♄", Planet.URANUS: "♅", Planet.NEPTUNE: "♆",
    Planet.PLUTO: "♇", Planet.RAHU: "☊", Planet.KETU: "☋",
}

# Skyfield body keys for bodies present in a JPL ephemeris (DE-series).
# Nodes (Rahu/Ketu) are computed analytically and are not listed here.
SKYFIELD_BODY = {
    Planet.SUN: "sun",
    Planet.MOON: "moon",
    Planet.MERCURY: "mercury",
    Planet.VENUS: "venus",
    Planet.MARS: "mars",
    Planet.JUPITER: "jupiter barycenter",
    Planet.SATURN: "saturn barycenter",
    Planet.URANUS: "uranus barycenter",
    Planet.NEPTUNE: "neptune barycenter",
    Planet.PLUTO: "pluto barycenter",
}

# Domicile (rulership) — traditional rulerships used by Vedic and classical work.
RULERSHIPS = {
    "Aries": Planet.MARS, "Taurus": Planet.VENUS, "Gemini": Planet.MERCURY,
    "Cancer": Planet.MOON, "Leo": Planet.SUN, "Virgo": Planet.MERCURY,
    "Libra": Planet.VENUS, "Scorpio": Planet.MARS, "Sagittarius": Planet.JUPITER,
    "Capricorn": Planet.SATURN, "Aquarius": Planet.SATURN, "Pisces": Planet.JUPITER,
}

# Modern rulerships (outer planets) — used by most Western astrologers.
MODERN_RULERSHIPS = dict(RULERSHIPS)
MODERN_RULERSHIPS.update({
    "Scorpio": Planet.PLUTO, "Aquarius": Planet.URANUS, "Pisces": Planet.NEPTUNE,
})


# --------------------------------------------------------------------------- #
# Aspects
# --------------------------------------------------------------------------- #

# name -> (exact angle, default orb in degrees)
ASPECTS = {
    "Conjunction": (0.0, 8.0),
    "Opposition": (180.0, 8.0),
    "Trine": (120.0, 7.0),
    "Square": (90.0, 7.0),
    "Sextile": (60.0, 6.0),
    "Quincunx": (150.0, 3.0),
    "Semisextile": (30.0, 2.0),
    "Semisquare": (45.0, 2.0),
    "Sesquiquadrate": (135.0, 2.0),
    "Quintile": (72.0, 1.5),
    "Biquintile": (144.0, 1.5),
}

ASPECT_GLYPHS = {
    "Conjunction": "☌", "Opposition": "☍", "Trine": "△",
    "Square": "□", "Sextile": "✱", "Quincunx": "⚻",
}

MAJOR_ASPECTS = ["Conjunction", "Opposition", "Trine", "Square", "Sextile"]


# --------------------------------------------------------------------------- #
# Nakshatras (lunar mansions) — 27 divisions of the sidereal zodiac.
# Each spans 13 deg 20 min = 13.3333... degrees.
# --------------------------------------------------------------------------- #

NAKSHATRA_ARC = 360.0 / 27.0  # 13.3333... degrees

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada",
    "Revati",
]

# Vimshottari dasha lords for each nakshatra (repeating cycle of 9).
NAKSHATRA_LORDS = [
    Planet.KETU, Planet.VENUS, Planet.SUN, Planet.MOON, Planet.MARS,
    Planet.RAHU, Planet.JUPITER, Planet.SATURN, Planet.MERCURY,
] * 3
