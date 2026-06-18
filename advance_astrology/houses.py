"""House systems and chart angles.

All functions take the Right Ascension of the Midheaven (RAMC), the obliquity
of the ecliptic, and the geographic latitude — everything else derives from
those three quantities plus the chosen division scheme.

Returns ecliptic longitudes (degrees) for the twelve house cusps, indexed
1..12, where cusp 1 is the Ascendant and cusp 10 is the Midheaven.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .angles import norm360, to_zodiac

_DEG = math.pi / 180.0


@dataclass(frozen=True)
class Angles:
    ascendant: float
    midheaven: float
    descendant: float
    imum_coeli: float
    vertex: float | None = None


def midheaven(ramc: float, obliquity: float) -> float:
    """Ecliptic longitude of the MC (the ecliptic point on the meridian)."""
    ramc_r = ramc * _DEG
    eps_r = obliquity * _DEG
    mc = math.atan2(math.sin(ramc_r), math.cos(ramc_r) * math.cos(eps_r))
    return norm360(mc / _DEG)


def ascendant(ramc: float, obliquity: float, latitude: float) -> float:
    """Ecliptic longitude of the Ascendant (rising point of the ecliptic)."""
    ramc_r = ramc * _DEG
    eps_r = obliquity * _DEG
    lat_r = latitude * _DEG
    y = math.cos(ramc_r)
    x = -(math.sin(ramc_r) * math.cos(eps_r) + math.tan(lat_r) * math.sin(eps_r))
    return norm360(math.atan2(y, x) / _DEG)


def vertex(ramc: float, obliquity: float, latitude: float) -> float:
    """The Vertex — the ascendant computed for the co-latitude in the west."""
    co_lat = 90.0 - abs(latitude)
    return ascendant(norm360(ramc + 180.0), obliquity, co_lat)


# --------------------------------------------------------------------------- #
# Whole-sign and equal houses (closed form)
# --------------------------------------------------------------------------- #

def whole_sign_cusps(asc: float) -> dict[int, float]:
    """Each house occupies one whole sign; cusp 1 = 0° of the rising sign."""
    start = to_zodiac(asc).sign_index * 30.0
    return {i + 1: norm360(start + 30.0 * i) for i in range(12)}


def equal_cusps(asc: float) -> dict[int, float]:
    """Twelve 30° houses starting exactly from the Ascendant degree."""
    return {i + 1: norm360(asc + 30.0 * i) for i in range(12)}


def porphyry_cusps(asc: float, mc: float) -> dict[int, float]:
    """Trisect each ecliptic quadrant between the angles."""
    ic = norm360(mc + 180.0)
    dsc = norm360(asc + 180.0)

    q1 = norm360(asc - mc)        # MC -> ASC arc (10th to 1st)
    q2 = norm360(ic - asc)        # ASC -> IC arc (1st to 4th)

    cusps = {
        1: asc,
        10: mc,
        4: ic,
        7: dsc,
        11: norm360(mc + q1 / 3.0),
        12: norm360(mc + 2.0 * q1 / 3.0),
        2: norm360(asc + q2 / 3.0),
        3: norm360(asc + 2.0 * q2 / 3.0),
    }
    # Opposite cusps are 180° away.
    for h in (11, 12, 2, 3):
        cusps[(h + 5) % 12 + 1] = norm360(cusps[h] + 180.0)
    return {h: cusps[h] for h in range(1, 13)}


# --------------------------------------------------------------------------- #
# Placidus (time-based, iterative)
# --------------------------------------------------------------------------- #

def placidus_cusps(
    ramc: float, obliquity: float, latitude: float
) -> dict[int, float]:
    """Placidus cusps via semi-arc trisection.

    Falls back to Porphyry near the polar circles, where Placidus is undefined
    (the required semi-arc condition has no solution).
    """
    eps = obliquity * _DEG
    phi = latitude * _DEG
    asc = ascendant(ramc, obliquity, latitude)
    mc = midheaven(ramc, obliquity)

    # Placidus breaks down when the ascendant's declination exceeds the
    # co-latitude; use Porphyry as a graceful fallback.
    if abs(latitude) >= 66.0:
        return porphyry_cusps(asc, mc)

    def cusp(fraction: float, nocturnal: bool) -> float | None:
        # Initial RA guess steps 30° per intermediate cusp from the MC.
        ra = ramc + (fraction * 90.0 if not nocturnal else 90.0 + fraction * 90.0)
        for _ in range(100):
            ra_r = ra * _DEG
            lam = math.atan2(math.sin(ra_r), math.cos(ra_r) * math.cos(eps))
            decl = math.asin(math.sin(eps) * math.sin(lam))
            cos_sa = -math.tan(phi) * math.tan(decl)
            if abs(cos_sa) > 1.0:
                return None
            sa = math.acos(cos_sa) / _DEG  # semidiurnal arc, degrees
            if nocturnal:
                na = 180.0 - sa
                ra_new = ramc + sa + (fraction - 1.0) * na
            else:
                ra_new = ramc + fraction * sa
            if abs(((ra_new - ra + 180.0) % 360.0) - 180.0) < 1e-9:
                ra = ra_new
                break
            ra = ra_new
        ra_r = ra * _DEG
        lam = math.atan2(math.sin(ra_r), math.cos(ra_r) * math.cos(eps))
        return norm360(lam / _DEG)

    # Fractions of the semidiurnal (11,12) and seminocturnal (2,3) arcs.
    c11 = cusp(1.0 / 3.0, nocturnal=False)
    c12 = cusp(2.0 / 3.0, nocturnal=False)
    c2 = cusp(4.0 / 3.0, nocturnal=True)
    c3 = cusp(5.0 / 3.0, nocturnal=True)

    if None in (c11, c12, c2, c3):
        return porphyry_cusps(asc, mc)

    cusps = {
        1: asc, 10: mc,
        4: norm360(mc + 180.0), 7: norm360(asc + 180.0),
        11: c11, 12: c12, 2: c2, 3: c3,
    }
    cusps[5] = norm360(c11 + 180.0)
    cusps[6] = norm360(c12 + 180.0)
    cusps[8] = norm360(c2 + 180.0)
    cusps[9] = norm360(c3 + 180.0)
    return {h: cusps[h] for h in range(1, 13)}


# --------------------------------------------------------------------------- #
# Dispatch
# --------------------------------------------------------------------------- #

HOUSE_SYSTEMS = {
    "placidus", "whole_sign", "equal", "porphyry",
}


def compute_cusps(
    system: str, ramc: float, obliquity: float, latitude: float
) -> tuple[dict[int, float], Angles]:
    """Compute house cusps and chart angles for the named system."""
    system = system.lower().replace("-", "_").replace(" ", "_")
    asc = ascendant(ramc, obliquity, latitude)
    mc = midheaven(ramc, obliquity)
    angles = Angles(
        ascendant=asc,
        midheaven=mc,
        descendant=norm360(asc + 180.0),
        imum_coeli=norm360(mc + 180.0),
        vertex=vertex(ramc, obliquity, latitude),
    )

    if system == "placidus":
        cusps = placidus_cusps(ramc, obliquity, latitude)
    elif system == "whole_sign":
        cusps = whole_sign_cusps(asc)
    elif system == "equal":
        cusps = equal_cusps(asc)
    elif system == "porphyry":
        cusps = porphyry_cusps(asc, mc)
    else:
        raise ValueError(
            f"Unknown house system '{system}'. Available: {sorted(HOUSE_SYSTEMS)}"
        )
    return cusps, angles


def house_of(longitude: float, cusps: dict[int, float]) -> int:
    """Return the house number (1..12) containing the given longitude."""
    lon = norm360(longitude)
    for h in range(1, 13):
        start = cusps[h]
        end = cusps[h % 12 + 1]
        span = norm360(end - start)
        offset = norm360(lon - start)
        if offset < span or (span == 0 and offset == 0):
            return h
    return 12
