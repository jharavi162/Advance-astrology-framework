"""Panchanga — the five limbs of the Vedic almanac.

Tithi, Vara, Nakshatra, Yoga and Karana, plus the planetary hora. Tithi and
karana depend only on the Moon-Sun elongation (ayanamsa-independent); yoga and
nakshatra use sidereal (nirayana) longitudes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..angles import norm360
from ..constants import NAKSHATRA_ARC, Planet
from ..nakshatra import nakshatra_of

# --------------------------------------------------------------------------- #
# Names
# --------------------------------------------------------------------------- #

TITHI_NAMES = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi",
    "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi",
    "Trayodashi", "Chaturdashi", "Purnima",
]

YOGA_NAMES = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda",
    "Sukarma", "Dhriti", "Shoola", "Ganda", "Vriddhi", "Dhruva", "Vyaghata",
    "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyana", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma", "Indra", "Vaidhriti",
]

MOVABLE_KARANAS = ["Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija",
                   "Vishti"]
FIXED_KARANAS = ["Kimstughna", "Shakuni", "Chatushpada", "Naga"]

VARA_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday",
              "Friday", "Saturday"]
VARA_LORDS = [Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
              Planet.JUPITER, Planet.VENUS, Planet.SATURN]

# Order of planetary lords governing successive horas.
HORA_ORDER = [Planet.SUN, Planet.VENUS, Planet.MERCURY, Planet.MOON,
              Planet.SATURN, Planet.JUPITER, Planet.MARS]


@dataclass(frozen=True)
class Tithi:
    number: int           # 1..30
    name: str             # e.g. "Shukla Panchami"
    paksha: str           # "Shukla" or "Krishna"
    fraction: float       # progress through the tithi [0, 1)


@dataclass(frozen=True)
class Panchanga:
    tithi: Tithi
    vara: str
    vara_lord: Planet
    nakshatra: str
    nakshatra_lord: Planet
    yoga_number: int
    yoga: str
    karana: str

    def __str__(self) -> str:
        return (f"Tithi: {self.tithi.name}\n"
                f"Vara: {self.vara} ({self.vara_lord.value})\n"
                f"Nakshatra: {self.nakshatra} ({self.nakshatra_lord.value})\n"
                f"Yoga: {self.yoga}\n"
                f"Karana: {self.karana}")


def tithi(sun_long: float, moon_long: float) -> Tithi:
    elong = norm360(moon_long - sun_long)
    idx = int(elong // 12.0)           # 0..29
    frac = (elong - idx * 12.0) / 12.0
    number = idx + 1
    if number <= 15:
        paksha, name = "Shukla", TITHI_NAMES[idx]
    else:
        paksha = "Krishna"
        name = TITHI_NAMES[idx - 15] if number < 30 else "Amavasya"
    return Tithi(number, f"{paksha} {name}", paksha, frac)


def yoga(sun_sid_long: float, moon_sid_long: float) -> tuple[int, str]:
    total = norm360(sun_sid_long + moon_sid_long)
    idx = int(total // NAKSHATRA_ARC)   # 0..26
    return idx + 1, YOGA_NAMES[idx]


def karana(sun_long: float, moon_long: float) -> str:
    elong = norm360(moon_long - sun_long)
    k = int(elong // 6.0)               # 0..59
    if k == 0:
        return "Kimstughna"
    if k <= 56:
        return MOVABLE_KARANAS[(k - 1) % 7]
    return ["Shakuni", "Chatushpada", "Naga"][k - 57]


def vara(dt_local: datetime) -> tuple[str, Planet]:
    """Weekday and its lord. (Civil weekday; the Vedic vara starts at sunrise.)"""
    wd = (dt_local.weekday() + 1) % 7    # Python Mon=0 -> Sun=0 indexing
    return VARA_NAMES[wd], VARA_LORDS[wd]


def hora_lord(dt_local: datetime, sunrise_hour: float = 6.0) -> Planet:
    """Planetary lord of the hora (planetary hour) at a local time.

    Each civil day has 24 horas starting at sunrise; the first hora is ruled by
    the lord of the weekday, then the lords cycle in Chaldean order.
    """
    _, day_lord = vara(dt_local)
    hours_since = (dt_local.hour + dt_local.minute / 60.0) - sunrise_hour
    hora_index = int(hours_since) % 24
    start = HORA_ORDER.index(day_lord)
    return HORA_ORDER[(start + hora_index) % 7]


def panchanga(
    sun_long: float, moon_long: float,
    sun_sid_long: float, moon_sid_long: float,
    dt_local: datetime,
) -> Panchanga:
    """Assemble the full panchanga.

    `sun_long`/`moon_long` may be tropical (only their difference matters for
    tithi/karana); `*_sid_long` must be sidereal for nakshatra and yoga.
    """
    t = tithi(sun_long, moon_long)
    v, vlord = vara(dt_local)
    nak = nakshatra_of(moon_sid_long)
    ynum, yname = yoga(sun_sid_long, moon_sid_long)
    return Panchanga(
        tithi=t, vara=v, vara_lord=vlord,
        nakshatra=nak.name, nakshatra_lord=nak.lord,
        yoga_number=ynum, yoga=yname, karana=karana(sun_long, moon_long),
    )
