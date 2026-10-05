"""Upagrahas (sub-planets / shadow points).

Two families:

* **Calculated upagrahas** derived directly from the Sun's longitude — Dhuma,
  Vyatipata, Parivesha, Indrachapa and Upaketu.
* **Time-based upagrahas** — Gulika and Mandi — found from the ascendant rising
  at the start of Saturn's eighth-part of the day or night.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from ..angles import norm360
from ..constants import Planet

# --------------------------------------------------------------------------- #
# Calculated upagrahas (from the Sun)
# --------------------------------------------------------------------------- #

def calculated_upagrahas(sun_longitude: float) -> dict[str, float]:
    """Longitudes of the five Sun-derived upagrahas."""
    dhuma = norm360(sun_longitude + 133.0 + 20.0 / 60.0)        # +133°20'
    vyatipata = norm360(360.0 - dhuma)
    parivesha = norm360(vyatipata + 180.0)
    indrachapa = norm360(360.0 - parivesha)
    upaketu = norm360(indrachapa + 16.0 + 40.0 / 60.0)          # +16°40'
    return {
        "Dhuma": dhuma,
        "Vyatipata": vyatipata,
        "Parivesha": parivesha,
        "Indrachapa": indrachapa,
        "Upaketu": upaketu,
    }


# --------------------------------------------------------------------------- #
# Gulika / Mandi (time based)
# --------------------------------------------------------------------------- #

# The day (sunrise->sunset) is split into 8 parts ruled, in order, starting
# from the weekday lord's sequence. The part index ruled by Saturn gives the
# Gulika segment. These are the classical Saturn-portion indices (0-based) for
# the eight weekday parts, day and night.
_GULIKA_DAY_PART = {
    "Sunday": 6, "Monday": 5, "Tuesday": 4, "Wednesday": 3,
    "Thursday": 2, "Friday": 1, "Saturday": 0,
}
_GULIKA_NIGHT_PART = {
    "Sunday": 2, "Monday": 1, "Tuesday": 0, "Wednesday": 6,
    "Thursday": 5, "Friday": 4, "Saturday": 3,
}

_WEEKDAY = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
            "Saturday", "Sunday"]


def vedic_weekday(preceding_sunrise_utc: datetime, longitude: float) -> str:
    """Weekday (vāra) of the Vedic day, which runs sunrise-to-sunrise.

    Taken from the local-mean-time date of the sunrise that opened the day, so
    a pre-sunrise birth belongs to the PREVIOUS civil weekday, and a sunrise
    that falls on the previous UTC date (far-east longitudes) is still read in
    local time.
    """
    local = preceding_sunrise_utc + timedelta(hours=longitude / 15.0)
    return _WEEKDAY[local.weekday()]


def _saturn_portion(
    birth_utc: datetime,
    sunrise: datetime,
    sunset: datetime,
    next_sunrise: datetime,
    *,
    use_night: bool | None = None,
    weekday: str | None = None,
) -> tuple[datetime, timedelta]:
    """(start, length) of Saturn's eighth-part of the birth day or night."""
    weekday = weekday or _WEEKDAY[sunrise.weekday()]
    is_night = use_night
    if is_night is None:
        is_night = not (sunrise <= birth_utc < sunset)

    if not is_night:
        segment = (sunset - sunrise) / 8.0
        return sunrise + _GULIKA_DAY_PART[weekday] * segment, segment
    segment = (next_sunrise - sunset) / 8.0
    return sunset + _GULIKA_NIGHT_PART[weekday] * segment, segment


def gulika_time(
    birth_utc: datetime,
    sunrise: datetime,
    sunset: datetime,
    next_sunrise: datetime,
    *,
    use_night: bool | None = None,
    weekday: str | None = None,
) -> datetime:
    """Time at which the Gulika segment (Saturn's portion) begins.

    The ascendant computed for this instant is the longitude of Gulika.
    `sunrise` is the sunrise that opened the Vedic day containing the birth;
    pass `weekday` (see :func:`vedic_weekday`) to fix the vāra explicitly,
    otherwise the sunrise's UTC weekday is used.
    """
    start, _ = _saturn_portion(birth_utc, sunrise, sunset, next_sunrise,
                               use_night=use_night, weekday=weekday)
    return start


def mandi_time(
    birth_utc: datetime,
    sunrise: datetime,
    sunset: datetime,
    next_sunrise: datetime,
    *,
    use_night: bool | None = None,
    weekday: str | None = None,
) -> datetime:
    """Time at the MIDDLE of Saturn's portion; its ascendant is Mandi.

    Gulika rises at the start of Saturn's eighth-part and Mandi at its middle
    (the BPHS Upagraha-adhyāya reading followed by Jagannātha Horā). Where a
    tradition treats the two as one point, read Gulika.
    """
    start, segment = _saturn_portion(birth_utc, sunrise, sunset, next_sunrise,
                                     use_night=use_night, weekday=weekday)
    return start + segment / 2.0


def gulika_longitude(ascendant_fn, gulika_dt: datetime) -> float:
    """Longitude of Gulika = ascendant at the Gulika instant.

    `ascendant_fn(dt) -> longitude` should return the (sidereal) ascendant at a
    given UTC datetime.
    """
    return norm360(ascendant_fn(gulika_dt))
