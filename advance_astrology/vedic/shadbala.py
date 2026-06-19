"""Ṣaḍbala — the six-source planetary strength system (in virūpas; 60 = 1 rūpa).

Computes the full profile for the seven grahas (Sun..Saturn):

* **Sthāna bala**  — Uccha, Saptavargaja, Oja-Yugma, Kendrādi, Drekkāṇa
* **Dig bala**     — directional strength
* **Kāla bala**    — Nathonnata, Pakṣa, Tribhāga, Varṣa/Māsa/Vāra/Horā, Ayana
* **Cheṣṭā bala**  — motional strength (retrogression / relative speed)
* **Naisargika bala** — fixed natural strength
* **Dṛg bala**     — net aspectual strength (benefic − malefic)

plus Iṣṭa-phala / Kaṣṭa-phala (benefic vs. malefic yield).

Some components that classically require mean-longitude machinery (Cheṣṭā kendra,
year/month lords) use documented, standard approximations; they are noted in
the relevant function docstrings.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import timedelta

from ..angles import norm180, norm360, to_zodiac
from ..constants import RULERSHIPS, SIGNS, Planet
from .dignities import EXALTATION, MOOLATRIKONA, OWN_SIGNS, compound_relationship
from .nature import natural_benefic
from .vargas import divisional_sign

SHADBALA_PLANETS = [Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
                    Planet.JUPITER, Planet.VENUS, Planet.SATURN]

# Minimum Ṣaḍbala (in rūpas) a planet should reach to be considered strong.
REQUIRED_RUPAS = {
    Planet.SUN: 6.5, Planet.MOON: 6.0, Planet.MARS: 5.0, Planet.MERCURY: 7.0,
    Planet.JUPITER: 6.5, Planet.VENUS: 5.5, Planet.SATURN: 5.0,
}

# Naisargika bala (fixed), brightest to dimmest.
NAISARGIKA = {
    Planet.SUN: 60.0, Planet.MOON: 51.43, Planet.VENUS: 42.86,
    Planet.JUPITER: 34.29, Planet.MERCURY: 25.71, Planet.MARS: 17.14,
    Planet.SATURN: 8.57,
}

# Mean daily motion (deg/day) for the Cheṣṭā approximation.
_MEAN_SPEED = {
    Planet.MARS: 0.524, Planet.MERCURY: 1.383, Planet.JUPITER: 0.0831,
    Planet.VENUS: 1.2, Planet.SATURN: 0.0335,
}


# --------------------------------------------------------------------------- #
# Sthāna bala
# --------------------------------------------------------------------------- #

def uccha_bala(planet: Planet, longitude: float) -> float:
    """Exaltation strength: 60 at deep exaltation, 0 at deep debilitation."""
    ex_sign, ex_deg = EXALTATION[planet]
    exalt_lon = SIGNS.index(ex_sign) * 30.0 + ex_deg
    deb_lon = norm360(exalt_lon + 180.0)
    arc = abs(norm180(longitude - deb_lon))   # 0 at debilitation, 180 at exalt
    return arc / 3.0


def _saptavargaja_value(planet: Planet, varga_sign: int,
                        d1_signs: dict[Planet, int]) -> float:
    """Dignity virūpa for a planet in one divisional sign."""
    sign_name = SIGNS[varga_sign]
    deg_none = 0.0  # moolatrikona check needs degree; handled only in D1 below
    if planet in MOOLATRIKONA and MOOLATRIKONA[planet][0] == sign_name:
        return 45.0
    if sign_name in OWN_SIGNS.get(planet, []):
        return 30.0
    dispositor = RULERSHIPS[sign_name]
    if dispositor == planet:
        return 30.0
    rel = compound_relationship(planet, d1_signs[planet],
                                dispositor, d1_signs[dispositor])
    return {
        "Great Friend": 22.5, "Friend": 15.0, "Neutral": 7.5,
        "Enemy": 3.75, "Great Enemy": 1.875, "Self": 30.0,
    }.get(rel, 7.5)


def saptavargaja_bala(planet: Planet, longitudes: dict[Planet, float]) -> float:
    """Strength from dignity across seven vargas (D1, D2, D3, D7, D9, D12, D30)."""
    d1_signs = {p: to_zodiac(l).sign_index for p, l in longitudes.items()}
    total = 0.0
    for varga in (1, 2, 3, 7, 9, 12, 30):
        vs = divisional_sign(longitudes[planet], varga)
        total += _saptavargaja_value(planet, vs, d1_signs)
    return total


# Planets that gain strength in odd (oja) vs even (yugma) signs.
_ODD_PLANETS = {Planet.SUN, Planet.MARS, Planet.MERCURY, Planet.JUPITER,
                Planet.SATURN}
_EVEN_PLANETS = {Planet.MOON, Planet.VENUS}


def oja_yugma_bala(planet: Planet, longitude: float) -> float:
    """Odd/even sign strength in the Rāśi (D1) and Navāṃśa (D9), 15 each."""
    total = 0.0
    for varga in (1, 9):
        s = divisional_sign(longitude, varga)
        odd = (s % 2 == 0)   # 0-based even index = odd-numbered sign
        if (odd and planet in _ODD_PLANETS) or (not odd and planet in _EVEN_PLANETS):
            total += 15.0
    return total


def kendradi_bala(house: int) -> float:
    """Quadrant strength: kendra 60, panapara 30, apoklima 15."""
    if house in (1, 4, 7, 10):
        return 60.0
    if house in (2, 5, 8, 11):
        return 30.0
    return 15.0


_MALE = {Planet.SUN, Planet.MARS, Planet.JUPITER}
_NEUTER = {Planet.MERCURY, Planet.SATURN}
_FEMALE = {Planet.MOON, Planet.VENUS}


def drekkana_bala(planet: Planet, longitude: float) -> float:
    """15 virūpas in the matching drekkāṇa: male 1st, neuter 2nd, female 3rd."""
    deg = to_zodiac(longitude).degree_in_sign
    drekkana = int(deg // 10.0)   # 0, 1, 2
    if drekkana == 0 and planet in _MALE:
        return 15.0
    if drekkana == 1 and planet in _NEUTER:
        return 15.0
    if drekkana == 2 and planet in _FEMALE:
        return 15.0
    return 0.0


# --------------------------------------------------------------------------- #
# Dig bala
# --------------------------------------------------------------------------- #

# Planet -> house whose cusp is its point of *zero* directional strength.
_DIG_WEAK_ANGLE = {
    Planet.SUN: "ic", Planet.MARS: "ic",          # strong in 10th (South)
    Planet.JUPITER: "desc", Planet.MERCURY: "desc",  # strong in 1st (East)
    Planet.SATURN: "asc",                          # strong in 7th (West)
    Planet.MOON: "mc", Planet.VENUS: "mc",         # strong in 4th (North)
}


def dig_bala(planet: Planet, longitude: float, angles: dict[str, float]) -> float:
    """Directional strength: 0 at the weak angle, 60 opposite it."""
    weak = angles[_DIG_WEAK_ANGLE[planet]]
    arc = abs(norm180(longitude - weak))   # 0..180
    return arc / 3.0


# --------------------------------------------------------------------------- #
# Kāla bala
# --------------------------------------------------------------------------- #

_DAY_PLANETS = {Planet.SUN, Planet.JUPITER, Planet.VENUS}
_NIGHT_PLANETS = {Planet.MOON, Planet.MARS, Planet.SATURN}


def nathonnatha_bala(planet: Planet, sun_hour_angle: float) -> float:
    """Diurnal/nocturnal strength from the Sun's hour angle (deg, 0 at noon)."""
    h = abs(norm180(sun_hour_angle))       # 0 (noon) .. 180 (midnight)
    natha = 60.0 * h / 180.0               # night strength
    unnata = 60.0 - natha                  # day strength
    if planet is Planet.MERCURY:
        return 60.0
    return unnata if planet in _DAY_PLANETS else natha


_PAKSHA_BENEFIC = {Planet.JUPITER, Planet.VENUS, Planet.MERCURY}
_PAKSHA_MALEFIC = {Planet.SUN, Planet.MARS, Planet.SATURN}


def paksha_bala(planet: Planet, sun_long: float, moon_long: float) -> float:
    """Lunar-phase strength; benefics wax-strong, malefics wane-strong."""
    elong = norm360(moon_long - sun_long)
    m = elong if elong <= 180 else 360 - elong   # 0 (new) .. 180 (full)
    benefic_val = m / 3.0
    if planet is Planet.MOON:
        return benefic_val * 2.0
    if planet in _PAKSHA_BENEFIC:
        return benefic_val
    return 60.0 - benefic_val


def tribhaga_bala(planet: Planet, is_day: bool, third: int) -> float:
    """Strength to the lord of the active 1/3 of day or night; Jupiter always 60."""
    if planet is Planet.JUPITER:
        return 60.0
    day_lords = [Planet.MERCURY, Planet.SUN, Planet.SATURN]
    night_lords = [Planet.MOON, Planet.VENUS, Planet.MARS]
    lord = (day_lords if is_day else night_lords)[third]
    return 60.0 if planet is lord else 0.0


_VARA_LORDS = [Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
               Planet.JUPITER, Planet.VENUS, Planet.SATURN]


def varshamasa_bala(planet: Planet, abda_lord: Planet, masa_lord: Planet,
                    vara_lord: Planet, hora_lord: Planet) -> float:
    """Year (15), month (30), day (45) and hour (60) lordship bonuses."""
    total = 0.0
    if planet is abda_lord:
        total += 15.0
    if planet is masa_lord:
        total += 30.0
    if planet is vara_lord:
        total += 45.0
    if planet is hora_lord:
        total += 60.0
    return total


_AYANA_NORTH = {Planet.SUN, Planet.MARS, Planet.JUPITER, Planet.VENUS,
                Planet.MERCURY}


def ayana_bala(planet: Planet, declination: float,
               double_sun: bool = True) -> float:
    """Declination-based strength; Sun's value is doubled for Kāla bala.

    Pass ``double_sun=False`` when feeding Cheṣṭā / Iṣṭa-phala, which use the
    undoubled value so the yield stays within 0..60.
    """
    if planet in _AYANA_NORTH:
        val = 60.0 * (23.45 + declination) / 46.9
    else:   # Moon, Saturn favour southern declination
        val = 60.0 * (23.45 - declination) / 46.9
    val = max(0.0, min(60.0, val))
    return val * 2.0 if (planet is Planet.SUN and double_sun) else val


# --------------------------------------------------------------------------- #
# Cheṣṭā bala
# --------------------------------------------------------------------------- #

def cheshta_bala(planet: Planet, speed: float, retrograde: bool,
                 sun_ayana: float, moon_paksha: float) -> float:
    """Motional strength.

    The Sun's cheṣṭā equals its ayana bala and the Moon's equals its pakṣa bala
    (classical convention). For the five star-planets a documented approximation
    is used: retrogression yields near-maximal strength, fast direct motion
    little, scaled by speed relative to the mean.
    """
    if planet is Planet.SUN:
        return sun_ayana
    if planet is Planet.MOON:
        return moon_paksha
    if retrograde:
        return 60.0
    mean = _MEAN_SPEED.get(planet, 1.0)
    ratio = max(0.0, min(1.0, abs(speed) / mean)) if mean else 0.5
    # Slow (near station) -> high; fast direct -> low.
    return 60.0 * (1.0 - 0.75 * ratio)


# --------------------------------------------------------------------------- #
# Dṛg bala (aspectual)
# --------------------------------------------------------------------------- #

def _drishti_virupa(aspecting: Planet, src: float, tgt: float) -> float:
    """Parashari graded aspect amount (virūpas) cast from src onto tgt."""
    house = int(norm360(to_zodiac(tgt).sign_index - to_zodiac(src).sign_index)) % 12 + 1
    # Special full aspects.
    specials = {Planet.MARS: (4, 8), Planet.JUPITER: (5, 9),
                Planet.SATURN: (3, 10)}
    if house == 7:
        return 60.0
    if house in specials.get(aspecting, ()):
        return 60.0
    # Standard graded aspects for all planets.
    quarter = {3: 15.0, 10: 15.0, 5: 30.0, 9: 30.0, 4: 45.0, 8: 45.0}
    return quarter.get(house, 0.0)


def drik_bala(planet: Planet, longitudes: dict[Planet, float],
              benefic_flags: dict[Planet, bool]) -> float:
    """Net aspectual strength: (benefic drishti − malefic drishti) / 4."""
    tgt = longitudes[planet]
    net = 0.0
    for other, lon in longitudes.items():
        if other is planet or other in (Planet.RAHU, Planet.KETU):
            continue
        amount = _drishti_virupa(other, lon, tgt)
        if amount:
            net += amount if benefic_flags.get(other, False) else -amount
    return net / 4.0


# --------------------------------------------------------------------------- #
# Aggregate result
# --------------------------------------------------------------------------- #

@dataclass
class PlanetShadbala:
    planet: Planet
    sthana: float
    dig: float
    kala: float
    cheshta: float
    naisargika: float
    drik: float
    components: dict[str, float] = field(default_factory=dict)

    @property
    def total_virupa(self) -> float:
        return (self.sthana + self.dig + self.kala + self.cheshta
                + self.naisargika + self.drik)

    @property
    def total_rupa(self) -> float:
        return self.total_virupa / 60.0

    @property
    def required_rupa(self) -> float:
        return REQUIRED_RUPAS[self.planet]

    @property
    def ratio(self) -> float:
        """Strength relative to the required minimum (>=1 is strong)."""
        return self.total_rupa / self.required_rupa

    @property
    def is_strong(self) -> bool:
        return self.total_rupa >= self.required_rupa

    def __str__(self) -> str:
        return (f"{self.planet.value:<8} {self.total_rupa:5.2f} rūpa "
                f"({self.ratio*100:5.1f}% of req)  "
                f"[Sth {self.sthana:5.1f} Dig {self.dig:5.1f} "
                f"Kāl {self.kala:5.1f} Che {self.cheshta:5.1f} "
                f"Nai {self.naisargika:5.1f} Dṛg {self.drik:+5.1f}]")


@dataclass
class IshtaKashta:
    planet: Planet
    ishta: float    # benefic yield 0..60
    kashta: float   # malefic yield 0..60

    def __str__(self) -> str:
        return (f"{self.planet.value:<8} Iṣṭa {self.ishta:5.2f} | "
                f"Kaṣṭa {self.kashta:5.2f}")


def ishta_kashta(uccha: float, cheshta: float) -> tuple[float, float]:
    """Iṣṭa = √(uccha·cheṣṭā); Kaṣṭa = √((60−uccha)·(60−cheṣṭā))."""
    ishta = math.sqrt(max(0.0, uccha) * max(0.0, cheshta))
    kashta = math.sqrt(max(0.0, 60 - uccha) * max(0.0, 60 - cheshta))
    return ishta, kashta


# --------------------------------------------------------------------------- #
# Orchestrator (operates on a VedicChart)
# --------------------------------------------------------------------------- #

def _abda_masa_lords(chart) -> tuple[Planet, Planet]:
    """Approximate year (abda) and month (masa) lords from the solar position."""
    sun_sid = chart.longitudes[Planet.SUN]
    mean_speed = 360.0 / 365.2425
    days_into_year = sun_sid / mean_speed
    days_into_month = (sun_sid % 30.0) / mean_speed
    year_start = chart.when_utc - timedelta(days=days_into_year)
    month_start = chart.when_utc - timedelta(days=days_into_month)
    abda = _VARA_LORDS[(year_start.weekday() + 1) % 7]
    masa = _VARA_LORDS[(month_start.weekday() + 1) % 7]
    return abda, masa


def compute_shadbala(chart) -> dict[Planet, PlanetShadbala]:
    """Full Ṣaḍbala for the seven grahas of a :class:`VedicChart`."""
    longs = chart.longitudes
    natal = chart.natal
    eps = natal.obliquity
    decls = natal.declinations()

    # Chart angles (sidereal) for dig bala.
    angles = {
        "asc": chart.ascendant,
        "desc": norm360(chart.ascendant + 180.0),
        "mc": natal.angles.midheaven,
        "ic": norm360(natal.angles.midheaven + 180.0),
    }

    sun_long = longs[Planet.SUN]
    moon_long = longs[Planet.MOON]

    # Sun's hour angle for nathonnatha (RAMC - RA_sun).
    ra_sun = math.degrees(math.atan2(
        math.sin(math.radians(natal.get(Planet.SUN).tropical_longitude))
        * math.cos(math.radians(eps)),
        math.cos(math.radians(natal.get(Planet.SUN).tropical_longitude)),
    ))
    sun_ha = norm180(natal.ramc - ra_sun)

    # Day/night and tribhaga third.
    rise, setting, next_rise, is_day = natal._ephemeris.day_portions(
        chart.when_utc, natal.latitude, natal.longitude)
    third = 0
    if rise and setting and next_rise:
        if is_day:
            frac = (chart.when_utc - rise) / (setting - rise)
        else:
            ref = setting if chart.when_utc >= setting else rise
            span = (next_rise - setting)
            frac = (chart.when_utc - setting) / span if chart.when_utc >= setting else 0.0
        third = min(2, max(0, int(frac * 3)))

    abda_lord, masa_lord = _abda_masa_lords(chart)
    vara_lord = _VARA_LORDS[(chart.when_utc.weekday() + 1) % 7]
    from .panchanga import hora_lord as _hora
    sunrise_hour = (rise.hour + rise.minute / 60.0) if rise else 6.0
    hora_lord = _hora(chart.when_utc, sunrise_hour)

    moon_waxing = norm360(moon_long - sun_long) <= 180.0
    benefic_flags = {p: natural_benefic(p, moon_waxing=moon_waxing)
                     for p in SHADBALA_PLANETS}

    results: dict[Planet, PlanetShadbala] = {}
    for p in SHADBALA_PLANETS:
        lon = longs[p]
        house = chart.house_of(p)

        ub = uccha_bala(p, lon)
        svb = saptavargaja_bala(p, longs)
        oyb = oja_yugma_bala(p, lon)
        kdb = kendradi_bala(house)
        drk = drekkana_bala(p, lon)
        sthana = ub + svb + oyb + kdb + drk

        dig = dig_bala(p, lon, angles)

        nb = nathonnatha_bala(p, sun_ha)
        pb = paksha_bala(p, sun_long, moon_long)
        tb = tribhaga_bala(p, is_day if is_day is not None else True, third)
        vmb = varshamasa_bala(p, abda_lord, masa_lord, vara_lord, hora_lord)
        ab = ayana_bala(p, decls[p])
        kala = nb + pb + tb + vmb + ab

        sun_ayana = ayana_bala(Planet.SUN, decls[Planet.SUN], double_sun=False)
        moon_paksha = paksha_bala(Planet.MOON, sun_long, moon_long)
        ch = cheshta_bala(p, natal.get(p).speed, natal.get(p).retrograde,
                          sun_ayana, moon_paksha)

        nai = NAISARGIKA[p]
        dg = drik_bala(p, longs, benefic_flags)

        results[p] = PlanetShadbala(
            planet=p, sthana=sthana, dig=dig, kala=kala, cheshta=ch,
            naisargika=nai, drik=dg,
            components={
                "uccha": ub, "saptavargaja": svb, "oja_yugma": oyb,
                "kendradi": kdb, "drekkana": drk,
                "nathonnatha": nb, "paksha": pb, "tribhaga": tb,
                "varshamasa": vmb, "ayana": ab,
            },
        )
    return results


def compute_ishta_kashta(chart) -> dict[Planet, IshtaKashta]:
    longs = chart.longitudes
    natal = chart.natal
    decls = natal.declinations()
    sun_ayana = ayana_bala(Planet.SUN, decls[Planet.SUN], double_sun=False)
    moon_paksha = paksha_bala(Planet.MOON, longs[Planet.SUN], longs[Planet.MOON])
    out = {}
    for p in SHADBALA_PLANETS:
        ub = uccha_bala(p, longs[p])
        ch = cheshta_bala(p, natal.get(p).speed, natal.get(p).retrograde,
                          sun_ayana, moon_paksha)
        i, k = ishta_kashta(ub, ch)
        out[p] = IshtaKashta(p, i, k)
    return out
