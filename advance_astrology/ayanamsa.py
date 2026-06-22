"""Ayanamsa models.

The ayanamsa is the angular offset between the tropical zodiac (measured from
the moving vernal equinox) and a sidereal zodiac (fixed against the stars).

    sidereal_longitude = tropical_longitude - ayanamsa

Each model is pinned by its value at J2000.0 and propagated with an IAU-style
general-precession-in-longitude polynomial. This is accurate to well within an
arc-minute over the de421 date range (1900-2050), which is far finer than the
13°20' width of a nakshatra.
"""

from __future__ import annotations

J2000 = 2451545.0  # Julian Date of the J2000.0 epoch (TT)

# General precession in longitude relative to J2000, in arc-seconds, with
# T in Julian centuries (IAU 1976 / Lieske coefficients, leading terms).
_PREC_LINEAR = 5028.796195
_PREC_QUAD = 1.1054348

# Value of each ayanamsa at J2000.0, in degrees.
_J2000_VALUES = {
    "lahiri": 23.85294,        # Chitrapaksha — Indian government standard
    "raman": 22.46888,         # B. V. Raman
    "krishnamurti": 23.71614,  # K. S. Krishnamurti (KP)
    "fagan_bradley": 24.73620, # Fagan/Bradley (Western sidereal)
    "yukteshwar": 22.46163,    # Sri Yukteshwar
}

# Friendly aliases.
_ALIASES = {
    "kp": "krishnamurti",
    "chitrapaksha": "lahiri",
    "fagan": "fagan_bradley",
    "fagan-bradley": "fagan_bradley",
}


def available_models() -> list[str]:
    return sorted(_J2000_VALUES)


def _precession_offset(jd_tt: float) -> float:
    """Accumulated general precession in longitude since J2000, in degrees."""
    t = (jd_tt - J2000) / 36525.0
    arcsec = _PREC_LINEAR * t + _PREC_QUAD * t * t
    return arcsec / 3600.0


def ayanamsa(jd_tt: float, model: str = "lahiri") -> float:
    """Return the ayanamsa in degrees for a Julian Date (TT) and model name."""
    key = model.lower().replace(" ", "_")
    key = _ALIASES.get(key, key)
    if key not in _J2000_VALUES:
        raise ValueError(
            f"Unknown ayanamsa '{model}'. Available: {available_models()}"
        )
    return _J2000_VALUES[key] + _precession_offset(jd_tt)
