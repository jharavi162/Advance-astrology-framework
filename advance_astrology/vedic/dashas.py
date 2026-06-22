"""Nakshatra-based dasha systems.

A single generic engine powers every nakshatra dasha: each system supplies an
ordered ring of (lord, years), the index of the starting lord, and the fraction
of that first period already elapsed at birth. Sub-periods (antardasha and
deeper) subdivide each period among the same ring, weighted by years.

Systems implemented here:
  * Vimshottari (120 years) — the default and most widely used
  * Ashtottari (108 years)
  * Yogini (36 years)
  * Kalachakra (navamsha-based, variable)

Jaimini's sign-based Chara dasha lives in :mod:`advance_astrology.vedic.jaimini`.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from ..constants import NAKSHATRA_ARC, Planet
from ..dasha import DAYS_PER_YEAR, DashaPeriod
from ..nakshatra import nakshatra_of

# --------------------------------------------------------------------------- #
# Generic ring engine
# --------------------------------------------------------------------------- #

def _subdivide(ring, ring_start: int, total_years: float,
               start: datetime, total_days: float, level: int,
               max_level: int) -> list[DashaPeriod]:
    n = len(ring)
    periods: list[DashaPeriod] = []
    cursor = start
    for k in range(n):
        lord, years = ring[(ring_start + k) % n]
        span = total_days * years / total_years
        end = cursor + timedelta(days=span)
        period = DashaPeriod(lord, cursor, end, level)
        if level < max_level:
            period.sub_periods = _subdivide(
                ring, (ring_start + k) % n, total_years,
                cursor, span, level + 1, max_level,
            )
        periods.append(period)
        cursor = end
    return periods


def build_ring_dasha(
    ring: list[tuple[Planet, float]],
    start_index: int,
    elapsed_fraction: float,
    birth: datetime,
    levels: int = 2,
    cycles: int = 1,
) -> list[DashaPeriod]:
    """Generic nakshatra-dasha builder.

    ``ring`` is the cyclic list of (lord, years); ``start_index`` selects the
    birth mahadasha; ``elapsed_fraction`` is how much of it had already passed.
    The first period therefore notionally begins before birth so its
    sub-periods land at the correct dates.
    """
    n = len(ring)
    total_years = sum(y for _, y in ring)

    start_lord, start_years = ring[start_index]
    elapsed_days = elapsed_fraction * start_years * DAYS_PER_YEAR
    cursor = birth - timedelta(days=elapsed_days)

    periods: list[DashaPeriod] = []
    for c in range(cycles):
        for k in range(n):
            idx = (start_index + k) % n
            lord, years = ring[idx]
            span = years * DAYS_PER_YEAR
            end = cursor + timedelta(days=span)
            maha = DashaPeriod(lord, cursor, end, level=1)
            if levels >= 2:
                maha.sub_periods = _subdivide(
                    ring, idx, total_years, cursor, span, 2, levels
                )
            periods.append(maha)
            cursor = end
    return periods


# --------------------------------------------------------------------------- #
# Vimshottari (120 years)
# --------------------------------------------------------------------------- #

VIMSHOTTARI_RING = [
    (Planet.KETU, 7), (Planet.VENUS, 20), (Planet.SUN, 6), (Planet.MOON, 10),
    (Planet.MARS, 7), (Planet.RAHU, 18), (Planet.JUPITER, 16),
    (Planet.SATURN, 19), (Planet.MERCURY, 17),
]


def vimshottari(moon_sidereal_longitude: float, birth: datetime,
                levels: int = 2, cycles: int = 1) -> list[DashaPeriod]:
    nak = nakshatra_of(moon_sidereal_longitude)
    start_index = nak.index % 9
    return build_ring_dasha(
        VIMSHOTTARI_RING, start_index, nak.fraction_traversed,
        birth, levels, cycles,
    )


# --------------------------------------------------------------------------- #
# Ashtottari (108 years)
# --------------------------------------------------------------------------- #

# Lord ring in dasha order with years.
ASHTOTTARI_RING = [
    (Planet.SUN, 6), (Planet.MOON, 15), (Planet.MARS, 8), (Planet.MERCURY, 17),
    (Planet.SATURN, 10), (Planet.JUPITER, 19), (Planet.RAHU, 12),
    (Planet.VENUS, 21),
]

# Each lord owns a contiguous block of nakshatras (0-based indices), counted
# from Ardra. Sizes: 3,4,3,4,3,4,3,3 = 27.
ASHTOTTARI_GROUPS = [
    (Planet.SUN, [5, 6, 7]),                  # Ardra, Punarvasu, Pushya
    (Planet.MOON, [8, 9, 10, 11]),            # Ashlesha..U.Phalguni
    (Planet.MARS, [12, 13, 14]),              # Hasta, Chitra, Swati
    (Planet.MERCURY, [15, 16, 17, 18]),       # Vishakha..Mula
    (Planet.SATURN, [19, 20, 21]),            # P.Ashadha..Shravana
    (Planet.JUPITER, [22, 23, 24, 25]),       # Dhanishta..U.Bhadrapada
    (Planet.RAHU, [26, 0, 1]),                # Revati, Ashwini, Bharani
    (Planet.VENUS, [2, 3, 4]),                # Krittika, Rohini, Mrigashira
]


def ashtottari(moon_sidereal_longitude: float, birth: datetime,
               levels: int = 2, cycles: int = 1) -> list[DashaPeriod]:
    nak = nakshatra_of(moon_sidereal_longitude)
    # Locate the lord-group containing the Moon, and the fraction through it.
    for ring_idx, (lord, members) in enumerate(ASHTOTTARI_GROUPS):
        if nak.index in members:
            pos_in_group = members.index(nak.index)
            arc = len(members) * NAKSHATRA_ARC
            traversed = pos_in_group * NAKSHATRA_ARC + (
                nak.fraction_traversed * NAKSHATRA_ARC
            )
            elapsed_fraction = traversed / arc
            return build_ring_dasha(
                ASHTOTTARI_RING, ring_idx, elapsed_fraction,
                birth, levels, cycles,
            )
    raise RuntimeError("nakshatra not mapped to an Ashtottari group")


# --------------------------------------------------------------------------- #
# Yogini (36 years)
# --------------------------------------------------------------------------- #

YOGINI_NAMES = [
    "Mangala", "Pingala", "Dhanya", "Bhramari",
    "Bhadrika", "Ulka", "Siddha", "Sankata",
]

YOGINI_RING = [
    (Planet.MOON, 1), (Planet.SUN, 2), (Planet.JUPITER, 3), (Planet.MARS, 4),
    (Planet.MERCURY, 5), (Planet.SATURN, 6), (Planet.VENUS, 7), (Planet.RAHU, 8),
]


def yogini(moon_sidereal_longitude: float, birth: datetime,
           levels: int = 2, cycles: int = 1) -> list[DashaPeriod]:
    nak = nakshatra_of(moon_sidereal_longitude)
    nak_num = nak.index + 1                    # 1..27
    r = (nak_num + 3) % 8
    start_index = (r - 1) % 8                  # 0-based into the ring
    return build_ring_dasha(
        YOGINI_RING, start_index, nak.fraction_traversed,
        birth, levels, cycles,
    )


def yogini_name(period: DashaPeriod) -> str:
    """Name of the yogini governing a period (by its lord)."""
    for name, (lord, _) in zip(YOGINI_NAMES, YOGINI_RING):
        if lord == period.lord:
            return name
    return ""


# --------------------------------------------------------------------------- #
# Kalachakra dasha (navamsha-based)
# --------------------------------------------------------------------------- #

# Paramayush (full dasha span) per sign group and the deha/jeeva sign sequence
# differ for savya (direct) and apasavya (reverse) nakshatra pada groups.
# Years assigned to each sign in the Kalachakra scheme:
KALACHAKRA_SIGN_YEARS = {
    "Aries": 7, "Taurus": 16, "Gemini": 9, "Cancer": 21, "Leo": 5, "Virgo": 9,
    "Libra": 16, "Scorpio": 7, "Sagittarius": 10, "Capricorn": 4,
    "Aquarius": 4, "Pisces": 10,
}

# Savya (clockwise) and apasavya (anticlockwise) sign sequences for the four
# padas, keyed by the nakshatra's "group" (each group = 9 nakshatras).
_SAVYA = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
          "Scorpio", "Sagittarius"]
_APASAVYA = ["Sagittarius", "Scorpio", "Libra", "Virgo", "Leo", "Cancer",
             "Gemini", "Taurus", "Aries"]


def kalachakra(moon_sidereal_longitude: float, birth: datetime,
               levels: int = 1, cycles: int = 1) -> list[DashaPeriod]:
    """Kalachakra dasha (standard Parashari form).

    The mahadasha sequence of signs is selected from the Moon's navamsha pada;
    each sign's span follows :data:`KALACHAKRA_SIGN_YEARS`. This is the core
    deha/jeeva progression; conventions differ between texts, so treat the
    sign order as the standard savya/apasavya scheme.

    Returned ``DashaPeriod`` objects carry the *sign ruler* as ``lord`` (the
    sign itself is recorded in ``DashaPeriod.note`` via the lord's sign).
    """
    from ..constants import RULERSHIPS
    nak = nakshatra_of(moon_sidereal_longitude)
    pada = int((moon_sidereal_longitude % NAKSHATRA_ARC) // (NAKSHATRA_ARC / 4))
    group = nak.index % 9
    # Savya for nakshatra groups 0,2 (and similar); apasavya otherwise.
    savya = (nak.index // 9) % 2 == 0
    base = _SAVYA if savya else _APASAVYA
    # Rotate the sequence to begin at the pada offset.
    seq = base[pada:] + base[:pada] + base  # ensure full coverage
    seq = seq[:9]

    periods: list[DashaPeriod] = []
    cursor = birth
    for sign in seq:
        years = KALACHAKRA_SIGN_YEARS[sign]
        end = cursor + timedelta(days=years * DAYS_PER_YEAR)
        period = DashaPeriod(RULERSHIPS[sign], cursor, end, level=1)
        period.note = sign  # type: ignore[attr-defined]
        periods.append(period)
        cursor = end
    return periods


# --------------------------------------------------------------------------- #
# Sudarśana Chakra dasha (tri-wheel progression)
# --------------------------------------------------------------------------- #

from dataclasses import dataclass as _dataclass  # local alias, avoid top churn
from ..constants import SIGNS as _SIGNS


@_dataclass(frozen=True)
class SudarshanaState:
    """Active signs of the three Sudarśana wheels at a moment.

    The chakra advances one house per *year* of life from each of the three
    references (Lagna, Moon, Sun) and, within a year, one house per *month*.
    A theme is highlighted when the same house/sign lights up on two or three
    wheels at once — a fast corroborating layer over the slower dashas.
    """
    years_elapsed: int
    month_index: int                 # 0..11 within the running year
    lagna_year_sign: int
    moon_year_sign: int
    sun_year_sign: int
    lagna_month_sign: int
    moon_month_sign: int
    sun_month_sign: int

    def year_signs(self) -> dict[str, str]:
        return {"lagna": _SIGNS[self.lagna_year_sign],
                "moon": _SIGNS[self.moon_year_sign],
                "sun": _SIGNS[self.sun_year_sign]}

    def month_signs(self) -> dict[str, str]:
        return {"lagna": _SIGNS[self.lagna_month_sign],
                "moon": _SIGNS[self.moon_month_sign],
                "sun": _SIGNS[self.sun_month_sign]}


def sudarshana_chakra(ascendant_sign: int, moon_sign: int, sun_sign: int,
                      birth: datetime, when: datetime) -> SudarshanaState:
    """Sudarśana Chakra daśā state at *when* (year + month wheels)."""
    days = (when - birth).total_seconds() / 86400.0
    years_elapsed = int(days // DAYS_PER_YEAR)
    frac_year = (days - years_elapsed * DAYS_PER_YEAR) / DAYS_PER_YEAR
    month_index = min(11, int(frac_year * 12))

    def yr(base: int) -> int:
        return (base + years_elapsed) % 12

    def mo(year_sign: int) -> int:
        return (year_sign + month_index) % 12

    ly, my, sy = yr(ascendant_sign), yr(moon_sign), yr(sun_sign)
    return SudarshanaState(
        years_elapsed=years_elapsed, month_index=month_index,
        lagna_year_sign=ly, moon_year_sign=my, sun_year_sign=sy,
        lagna_month_sign=mo(ly), moon_month_sign=mo(my), sun_month_sign=mo(sy),
    )


# --------------------------------------------------------------------------- #
# Registry
# --------------------------------------------------------------------------- #

DASHA_SYSTEMS = {
    "vimshottari": vimshottari,
    "ashtottari": ashtottari,
    "yogini": yogini,
    "kalachakra": kalachakra,
}


def compute_dasha(system: str, moon_sidereal_longitude: float,
                  birth: datetime, **kwargs) -> list[DashaPeriod]:
    system = system.lower()
    if system not in DASHA_SYSTEMS:
        raise ValueError(
            f"Unknown dasha '{system}'. Available: {sorted(DASHA_SYSTEMS)}"
        )
    return DASHA_SYSTEMS[system](moon_sidereal_longitude, birth, **kwargs)
