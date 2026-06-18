"""Angle utilities and zodiac sign/degree helpers."""

from __future__ import annotations

from dataclasses import dataclass

from .constants import SIGNS


def norm360(deg: float) -> float:
    """Normalise an angle to [0, 360)."""
    return deg % 360.0


def norm180(deg: float) -> float:
    """Normalise an angle to (-180, 180]."""
    d = (deg + 180.0) % 360.0 - 180.0
    return d + 360.0 if d <= -180.0 else d


def angular_separation(a: float, b: float) -> float:
    """Smallest unsigned separation between two ecliptic longitudes (0..180)."""
    return abs(norm180(a - b))


def signed_difference(a: float, b: float) -> float:
    """Signed difference a - b normalised to (-180, 180]."""
    return norm180(a - b)


@dataclass(frozen=True)
class ZodiacPosition:
    """A longitude expressed in sign / degree / minute / second terms."""

    longitude: float          # absolute ecliptic longitude [0, 360)
    sign: str                 # zodiac sign name
    sign_index: int           # 0 = Aries .. 11 = Pisces
    degree: int               # whole degrees within the sign (0..29)
    minute: int               # arc-minutes (0..59)
    second: float             # arc-seconds (0..60)
    degree_in_sign: float     # fractional degrees within the sign [0, 30)

    def __str__(self) -> str:
        return f"{self.degree:02d}°{self.minute:02d}'{self.second:05.2f}\" {self.sign}"

    @property
    def dms(self) -> str:
        return str(self)


def to_zodiac(longitude: float) -> ZodiacPosition:
    """Convert an absolute ecliptic longitude into a sign/degree breakdown."""
    lon = norm360(longitude)
    sign_index = int(lon // 30.0)
    degree_in_sign = lon - sign_index * 30.0

    deg = int(degree_in_sign)
    minute_full = (degree_in_sign - deg) * 60.0
    minute = int(minute_full)
    second = (minute_full - minute) * 60.0

    return ZodiacPosition(
        longitude=lon,
        sign=SIGNS[sign_index],
        sign_index=sign_index,
        degree=deg,
        minute=minute,
        second=second,
        degree_in_sign=degree_in_sign,
    )


def format_longitude(longitude: float) -> str:
    """Human readable 'DD°MM' Sign' string."""
    pos = to_zodiac(longitude)
    return f"{pos.degree:02d}°{pos.minute:02d}' {pos.sign}"
