"""Varṣaphal (Tājika annual chart).

For a given year, finds the solar return (Sun's return to its natal *sidereal*
longitude), casts the annual chart (Varṣa lagna) for the birth place, and
derives the Muntha (the progressed point advancing one sign per year of age).
These feed the convergence engine as a year-resolution dynamic witness.

Full Tājika lord-of-the-year (Pañcādhikārī / Pañca-vargīya bala) and the Muddā
daśā are deferred; the robust, unambiguous outputs (Varṣa lagna, Muntha house,
Muntha/lagna lords) are exposed and logged for later extension.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from ..constants import RULERSHIPS, SIGNS, Planet


@dataclass
class AnnualChart:
    year: int
    solar_return: datetime
    varsha_lagna_sign: int
    muntha_sign: int
    muntha_house: int            # house of the Muntha from the natal lagna
    muntha_lord: Planet
    lagna_lord: Planet           # lord of the Varṣa lagna
    chart: object                # the VedicChart cast for the solar-return moment


def solar_return_time(chart, year: int, tol_deg: float = 1e-3) -> datetime:
    """Moment in *year* when the transiting Sun regains its natal sidereal
    longitude (Nirayana solar return). Bisected to high precision."""
    natal_sun = chart.longitudes[Planet.SUN]
    tr = chart.transits()

    def diff(t: datetime) -> float:
        lon = tr.positions(t, [Planet.SUN])[Planet.SUN]
        return ((lon - natal_sun + 180.0) % 360.0) - 180.0

    base = chart.when_utc
    guess = datetime(year, base.month, min(base.day, 28),
                     tzinfo=timezone.utc)
    lo, hi = guess - timedelta(days=4), guess + timedelta(days=4)
    flo, fhi = diff(lo), diff(hi)
    tries = 0
    while flo * fhi > 0 and tries < 8:        # widen until the return is bracketed
        lo -= timedelta(days=3)
        hi += timedelta(days=3)
        flo, fhi = diff(lo), diff(hi)
        tries += 1
    for _ in range(50):
        mid = lo + (hi - lo) / 2
        fm = diff(mid)
        if abs(fm) < tol_deg:
            return mid
        if flo * fm <= 0:
            hi, fhi = mid, fm
        else:
            lo, flo = mid, fm
    return lo + (hi - lo) / 2


def annual_chart(chart, year: int) -> AnnualChart:
    """Cast the Varṣaphal chart for *year* at the native's birth place."""
    from .chart import VedicChart
    sr = solar_return_time(chart, year)
    ann = VedicChart.create(when=sr, latitude=chart.natal.latitude,
                            longitude=chart.natal.longitude,
                            ayanamsa=chart.natal.ayanamsa_name)
    age = year - chart.when_utc.year                 # completed years at return
    natal_lagna = chart.ascendant_sign
    muntha = (natal_lagna + age) % 12
    muntha_house = (age % 12) + 1                     # = (muntha − lagna) + 1
    return AnnualChart(
        year=year, solar_return=sr,
        varsha_lagna_sign=ann.ascendant_sign,
        muntha_sign=muntha, muntha_house=muntha_house,
        muntha_lord=RULERSHIPS[SIGNS[muntha]],
        lagna_lord=RULERSHIPS[SIGNS[ann.ascendant_sign]],
        chart=ann,
    )
