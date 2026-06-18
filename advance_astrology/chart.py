"""The natal chart — the central object of the framework.

Ties together the ephemeris, zodiac, houses, aspects and (for sidereal work)
nakshatras and dashas into one computed chart.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from .angles import ZodiacPosition, norm360, to_zodiac
from .aspects import Aspect, find_aspects
from .ayanamsa import ayanamsa as compute_ayanamsa
from .constants import (
    DEFAULT_PLANETS,
    Planet,
    sign_element,
    sign_modality,
)
from .dasha import DashaPeriod, current_dasha, vimshottari_dasha
from .ephemeris import Ephemeris, get_ephemeris
from .houses import Angles, compute_cusps, house_of
from .nakshatra import NakshatraPosition, nakshatra_of


@dataclass(frozen=True)
class PlanetPlacement:
    planet: Planet
    longitude: float                  # in the chart's chosen zodiac
    tropical_longitude: float
    sidereal_longitude: float
    position: ZodiacPosition          # sign/deg breakdown in chosen zodiac
    latitude: float
    distance_au: float
    speed: float
    retrograde: bool
    house: int
    nakshatra: NakshatraPosition      # always from the sidereal longitude

    @property
    def sign(self) -> str:
        return self.position.sign

    @property
    def element(self) -> str:
        return sign_element(self.position.sign)

    @property
    def modality(self) -> str:
        return sign_modality(self.position.sign)

    def __str__(self) -> str:
        rx = " ℞" if self.retrograde else ""
        return f"{self.planet.value:<8} {self.position}{rx}  H{self.house}"


@dataclass
class NatalChart:
    when_utc: datetime
    latitude: float
    longitude: float
    zodiac: str                       # "tropical" | "sidereal"
    house_system: str
    ayanamsa_name: str
    ayanamsa_value: float
    obliquity: float
    ramc: float
    angles: Angles
    cusps: dict[int, float]
    placements: dict[Planet, PlanetPlacement]
    name: str = ""
    _ephemeris: Ephemeris | None = field(default=None, repr=False)

    # ------------------------------------------------------------------ #
    # Construction
    # ------------------------------------------------------------------ #

    @classmethod
    def create(
        cls,
        when: datetime,
        latitude: float,
        longitude: float,
        *,
        name: str = "",
        zodiac: str = "tropical",
        house_system: str = "placidus",
        ayanamsa: str = "lahiri",
        planets: list[Planet] | None = None,
        ephemeris: Ephemeris | None = None,
    ) -> "NatalChart":
        """Compute a natal chart.

        Parameters
        ----------
        when:
            Timezone-aware birth datetime. Naive datetimes are rejected — make
            the timezone explicit so the UTC instant is unambiguous.
        latitude, longitude:
            Geographic coordinates in degrees; east longitude and north
            latitude are positive.
        zodiac:
            ``"tropical"`` (Western default) or ``"sidereal"`` (Vedic).
        house_system:
            ``placidus``, ``whole_sign``, ``equal`` or ``porphyry``.
        ayanamsa:
            Sidereal offset model (used for sidereal charts and for all
            nakshatra/dasha calculations regardless of zodiac).
        """
        if when.tzinfo is None:
            raise ValueError(
                "`when` must be timezone-aware so the UTC instant is unambiguous"
            )
        when_utc = when.astimezone(timezone.utc)
        zodiac = zodiac.lower()
        if zodiac not in ("tropical", "sidereal"):
            raise ValueError("zodiac must be 'tropical' or 'sidereal'")

        eph = ephemeris or get_ephemeris()
        t = eph.time(when_utc)

        obliquity = eph.obliquity(t)
        ayan = compute_ayanamsa(eph.julian_day(t), ayanamsa)
        ramc = eph.local_sidereal_time(t, longitude)

        # House cusps and angles are computed in the tropical frame, then
        # shifted into the sidereal frame if requested.
        cusps_trop, angles_trop = compute_cusps(
            house_system, ramc, obliquity, latitude
        )

        def shift(lon: float) -> float:
            return norm360(lon - ayan) if zodiac == "sidereal" else lon

        cusps = {h: shift(v) for h, v in cusps_trop.items()}
        angles = Angles(
            ascendant=shift(angles_trop.ascendant),
            midheaven=shift(angles_trop.midheaven),
            descendant=shift(angles_trop.descendant),
            imum_coeli=shift(angles_trop.imum_coeli),
            vertex=shift(angles_trop.vertex) if angles_trop.vertex is not None else None,
        )

        planet_list = planets or DEFAULT_PLANETS
        raw = eph.positions(planet_list, t)

        placements: dict[Planet, PlanetPlacement] = {}
        for planet, bp in raw.items():
            trop = bp.longitude
            sid = norm360(trop - ayan)
            chosen = sid if zodiac == "sidereal" else trop
            placements[planet] = PlanetPlacement(
                planet=planet,
                longitude=chosen,
                tropical_longitude=trop,
                sidereal_longitude=sid,
                position=to_zodiac(chosen),
                latitude=bp.latitude,
                distance_au=bp.distance_au,
                speed=bp.speed,
                retrograde=bp.retrograde,
                house=house_of(chosen, cusps),
                nakshatra=nakshatra_of(sid),
            )

        return cls(
            when_utc=when_utc,
            latitude=latitude,
            longitude=longitude,
            zodiac=zodiac,
            house_system=house_system,
            ayanamsa_name=ayanamsa,
            ayanamsa_value=ayan,
            obliquity=obliquity,
            ramc=ramc,
            angles=angles,
            cusps=cusps,
            placements=placements,
            name=name,
            _ephemeris=eph,
        )

    # ------------------------------------------------------------------ #
    # Derived data
    # ------------------------------------------------------------------ #

    def get(self, planet: Planet) -> PlanetPlacement:
        return self.placements[planet]

    @property
    def ascendant(self) -> ZodiacPosition:
        return to_zodiac(self.angles.ascendant)

    @property
    def midheaven(self) -> ZodiacPosition:
        return to_zodiac(self.angles.midheaven)

    def aspects(self, **kwargs) -> list[Aspect]:
        """All aspects between charted bodies (see :func:`find_aspects`)."""
        return find_aspects(self.placements, **kwargs)

    def planets_in_sign(self, sign: str) -> list[PlanetPlacement]:
        return [p for p in self.placements.values() if p.sign == sign]

    # -- Western extensions --------------------------------------------- #

    @property
    def is_day_chart(self) -> bool:
        """Day chart when the Sun is above the horizon (houses 7-12)."""
        return self.placements[Planet.SUN].house in (7, 8, 9, 10, 11, 12)

    def lots(self) -> dict[str, float]:
        """Arabic Parts / Hellenistic Lots (Fortune, Spirit, ...)."""
        from .western.lots import all_lots
        lon = {p: pl.longitude for p, pl in self.placements.items()}
        return all_lots(lon, self.angles.ascendant, self.is_day_chart)

    def declinations(self) -> dict[Planet, float]:
        from .western.declination import declination
        return {
            p: declination(pl.longitude, pl.latitude, self.obliquity)
            for p, pl in self.placements.items()
        }

    def essential_dignity(self, planet: Planet):
        from .western.dignities import essential_dignity
        return essential_dignity(
            self.placements[planet].longitude, self.is_day_chart
        )

    def to_vedic(self):
        """Return a :class:`VedicChart` view (requires a sidereal chart)."""
        from .vedic import VedicChart
        return VedicChart(self)

    def planets_in_house(self, house: int) -> list[PlanetPlacement]:
        return [p for p in self.placements.values() if p.house == house]

    def element_balance(self) -> dict[str, int]:
        balance = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
        for p in self.placements.values():
            balance[p.element] += 1
        return balance

    def modality_balance(self) -> dict[str, int]:
        balance = {"Cardinal": 0, "Fixed": 0, "Mutable": 0}
        for p in self.placements.values():
            balance[p.modality] += 1
        return balance

    # -- Vedic ---------------------------------------------------------- #

    def vimshottari_dasha(self, levels: int = 2, cycles: int = 1) -> list[DashaPeriod]:
        """Vimshottari dasha timeline anchored to the natal Moon."""
        moon_sid = self.placements[Planet.MOON].sidereal_longitude
        return vimshottari_dasha(moon_sid, self.when_utc, levels=levels, cycles=cycles)

    def current_dasha(self, when: datetime | None = None) -> list[DashaPeriod]:
        """Active dasha chain (maha → antar → …) on a given date (default now)."""
        when = when or datetime.now(timezone.utc)
        periods = self.vimshottari_dasha(levels=3, cycles=1)
        return current_dasha(periods, when)

    # ------------------------------------------------------------------ #
    # Presentation
    # ------------------------------------------------------------------ #

    def summary(self) -> str:
        lines = []
        title = self.name or "Natal Chart"
        lines.append(f"{title}  —  {self.when_utc:%Y-%m-%d %H:%M UTC}")
        lines.append(
            f"  {self.latitude:.4f}°, {self.longitude:.4f}°   "
            f"{self.zodiac} / {self.house_system}"
        )
        if self.zodiac == "sidereal":
            lines.append(
                f"  Ayanamsa: {self.ayanamsa_name} ({self.ayanamsa_value:.4f}°)"
            )
        lines.append("")
        lines.append(f"  Ascendant  {self.ascendant}")
        lines.append(f"  Midheaven  {self.midheaven}")
        lines.append("")
        for planet in self.placements:
            lines.append("  " + str(self.placements[planet]))
        return "\n".join(lines)
