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


def gulika_time(
    birth_utc: datetime,
    sunrise: datetime,
    sunset: datetime,
    next_sunrise: datetime,
    *,
    use_night: bool | None = None,
) -> datetime:
    """Time at which the Gulika segment begins.

    The ascendant computed for this instant is the longitude of Gulika.
    """
    weekday = _WEEKDAY[birth_utc.weekday()]
    is_night = use_night
    if is_night is None:
        is_night = not (sunrise <= birth_utc < sunset)

    if not is_night:
        part = _GULIKA_DAY_PART[weekday]
        segment = (sunset - sunrise) / 8.0
        return sunrise + part * segment
    else:
        part = _GULIKA_NIGHT_PART[weekday]
        segment = (next_sunrise - sunset) / 8.0
        return sunset + part * segment


def gulika_longitude(ascendant_fn, gulika_dt: datetime) -> float:
    """Longitude of Gulika = ascendant at the Gulika instant.

    `ascendant_fn(dt) -> longitude` should return the (sidereal) ascendant at a
    given UTC datetime.
    """
    return norm360(ascendant_fn(gulika_dt))
