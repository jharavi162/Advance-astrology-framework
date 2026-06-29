"""Bhāva-Chalit — cusp-based house placement and Rāśi→Chalit shift detection.

The Rāśi chart places a planet in the whole sign it occupies (house counted
from the lagna sign). The Bhāva-Chalit chart instead uses unequal Placidus
cusps: a planet can fall into the adjacent bhāva even while remaining in its
Rāśi sign. The playbook uses this to separate a planet's *environment* (Rāśi
house) from its *physical results* (Chalit house).
"""

from __future__ import annotations

from dataclasses import dataclass

from ..angles import norm360, to_zodiac
from ..constants import Planet
from ..houses import compute_cusps, house_of


@dataclass
class ChalitPlacement:
    planet: Planet
    rashi_house: int      # whole-sign house from the lagna
    chalit_house: int     # Placidus cusp-based house
    shifted: bool

    def __str__(self) -> str:
        arrow = f" → H{self.chalit_house}" if self.shifted else ""
        return f"{self.planet.value:<8} Rāśi H{self.rashi_house}{arrow}"


def sidereal_cusps(chart, system: str = "placidus") -> dict[int, float]:
    """Sidereal house cusps for a VedicChart in any supported house system
    (placidus, whole_sign, equal, porphyry, regiomontanus)."""
    natal = chart.natal
    system_n = system.lower().replace("-", "_").replace(" ", "_")
    if system_n == "whole_sign":
        # Whole-sign snaps to sign boundaries, which must happen in the SIDEREAL
        # zodiac — so build from the sidereal ascendant, not tropical-then-shift.
        from ..houses import ascendant, whole_sign_cusps
        asc_sid = norm360(ascendant(natal.ramc, natal.obliquity, natal.latitude)
                          - chart.ayanamsa)
        return whole_sign_cusps(asc_sid)
    cusps, _ = compute_cusps(system, natal.ramc, natal.obliquity, natal.latitude)
    return {h: norm360(c - chart.ayanamsa) for h, c in cusps.items()}


def placidus_cusps_sidereal(chart) -> dict[int, float]:
    """Sidereal Placidus cusps for a VedicChart (KP uses Placidus by doctrine)."""
    return sidereal_cusps(chart, "placidus")


def bhava_chalit(chart) -> dict[Planet, ChalitPlacement]:
    """Compare each body's Rāśi house with its Placidus (Chalit) house."""
    cusps = placidus_cusps_sidereal(chart)
    out: dict[Planet, ChalitPlacement] = {}
    for planet, lon in chart.longitudes.items():
        rashi_house = (to_zodiac(lon).sign_index - chart.ascendant_sign) % 12 + 1
        chalit = house_of(lon, cusps)
        out[planet] = ChalitPlacement(
            planet=planet,
            rashi_house=rashi_house,
            chalit_house=chalit,
            shifted=(rashi_house != chalit),
        )
    return out


def shifted_planets(chart) -> list[Planet]:
    """Bodies whose physical results anchor to a different (Chalit) house."""
    return [p for p, c in bhava_chalit(chart).items() if c.shifted]
