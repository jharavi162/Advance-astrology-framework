"""VedicChart — a high-level Jyotish chart wrapping the sidereal NatalChart.

Exposes vargas, all dasha systems, Jaimini tools, arudhas, ashtakavarga,
panchanga, special lagnas, upagrahas, yogas and avasthas through one object.
"""

from __future__ import annotations

from datetime import datetime, timezone
from functools import cached_property

from ..angles import norm360, to_zodiac
from ..chart import NatalChart
from ..constants import RULERSHIPS, SIGNS, VEDIC_GRAHAS, Planet
from ..dasha import DashaPeriod, current_dasha
from . import (
    arudha,
    ashtakavarga,
    avastha,
    compatibility,
    dashas as dasha_systems,
    jaimini,
    panchanga as panchanga_mod,
    special_lagnas,
    upagrahas,
    yogas as yoga_mod,
)
from .aspects import all_graha_aspects, planets_aspecting_sign, rashi_aspects
from .dignities import dignity
from .vargas import VARGA_NAMES, build_varga


class VedicChart:
    """A sidereal (Vedic) chart with the full Jyotish toolkit attached."""

    def __init__(self, natal: NatalChart):
        if natal.zodiac != "sidereal":
            raise ValueError("VedicChart requires a sidereal NatalChart")
        self.natal = natal
        self.when_utc = natal.when_utc
        self.ayanamsa = natal.ayanamsa_value

        # Sidereal longitudes and sign indices for every charted body.
        self.longitudes: dict[Planet, float] = {
            p: pl.sidereal_longitude for p, pl in natal.placements.items()
        }
        self.signs: dict[Planet, int] = {
            p: to_zodiac(l).sign_index for p, l in self.longitudes.items()
        }
        self.ascendant = natal.angles.ascendant
        self.ascendant_sign = to_zodiac(self.ascendant).sign_index

    # ------------------------------------------------------------------ #
    @classmethod
    def create(cls, when: datetime, latitude: float, longitude: float, *,
               name: str = "", ayanamsa: str = "lahiri",
               house_system: str = "whole_sign", **kwargs) -> "VedicChart":
        natal = NatalChart.create(
            when=when, latitude=latitude, longitude=longitude, name=name,
            zodiac="sidereal", ayanamsa=ayanamsa, house_system=house_system,
            **kwargs,
        )
        return cls(natal)

    # -- Houses --------------------------------------------------------- #
    def house_of(self, planet: Planet) -> int:
        return (self.signs[planet] - self.ascendant_sign) % 12 + 1

    def planets_in_house(self, house: int) -> list[Planet]:
        target = (self.ascendant_sign + house - 1) % 12
        return [p for p, s in self.signs.items() if s == target]

    def house_lord(self, house: int) -> Planet:
        """Parāśarī lord of a whole-sign house (sign on the house → its ruler)."""
        return RULERSHIPS[SIGNS[(self.ascendant_sign + house - 1) % 12]]

    def house_lords(self) -> dict[int, Planet]:
        """Lords of all twelve houses, keyed 1..12."""
        return {h: self.house_lord(h) for h in range(1, 13)}

    # -- Nakshatra & Naamakshara ---------------------------------------- #
    def nakshatra(self, planet: Planet):
        """Nakshatra/pada (with Naamakshara syllable) of a planet."""
        from ..nakshatra import nakshatra_of
        return nakshatra_of(self.longitudes[planet])

    def naamakshara(self, planet: Planet) -> str:
        """Name-syllable (Naamakshara) of a planet's nakshatra-pada."""
        return self.nakshatra(planet).syllable

    # -- Dignities ------------------------------------------------------ #
    def dignity(self, planet: Planet):
        return dignity(planet, self.longitudes[planet])

    # -- Vargas --------------------------------------------------------- #
    def varga(self, division: int):
        """Build a divisional chart (e.g. ``chart.varga(9)`` for Navamsha)."""
        return build_varga(division, self.ascendant, self.longitudes)

    @cached_property
    def navamsha(self):
        return self.varga(9)

    def all_vargas(self, divisions=None) -> dict[int, object]:
        from .vargas import SHODASHAVARGA
        divisions = divisions or SHODASHAVARGA
        return {d: self.varga(d) for d in divisions}

    # -- Dashas --------------------------------------------------------- #
    def dasha(self, system: str = "vimshottari", **kwargs) -> list[DashaPeriod]:
        moon = self.longitudes[Planet.MOON]
        return dasha_systems.compute_dasha(system, moon, self.when_utc, **kwargs)

    def current_dasha(self, system: str = "vimshottari",
                      when: datetime | None = None,
                      levels: int | None = None) -> list[DashaPeriod]:
        """Active dasha chain at *when*. ``levels`` overrides the default depth —
        e.g. ``levels=5`` drills Vimśottari to Sūkṣma/Prāṇa for event-day timing."""
        when = when or datetime.now(timezone.utc)
        if levels is None:
            levels = 3 if system in ("vimshottari", "ashtottari", "yogini") else 1
        # Project enough cycles for short dashas (e.g. Yogini's 36 years) to
        # reach the requested date.
        cycles = 1
        periods = self.dasha(system, levels=levels, cycles=cycles)
        while periods and periods[-1].end < when and cycles < 10:
            cycles += 1
            periods = self.dasha(system, levels=levels, cycles=cycles)
        return current_dasha(periods, when)

    def chara_dasha(self, **kwargs) -> list[DashaPeriod]:
        return jaimini.chara_dasha(self.ascendant_sign, self.signs,
                                   self.when_utc, **kwargs)

    def narayana_dasha(self, **kwargs) -> list[DashaPeriod]:
        return jaimini.narayana_dasha(self.ascendant_sign, self.signs,
                                      self.longitudes, self.when_utc, **kwargs)

    def sudasa_dasha(self, **kwargs) -> list[DashaPeriod]:
        sree_sign = int(self.special_lagnas()["sree"] // 30)
        return jaimini.sudasa_dasha(sree_sign, self.signs,
                                    self.when_utc, **kwargs)

    # -- Jaimini -------------------------------------------------------- #
    def chara_karakas(self, scheme: int = 8) -> dict[str, Planet]:
        return jaimini.chara_karakas(self.longitudes, scheme)

    def atmakaraka(self, scheme: int = 8) -> Planet:
        return jaimini.atmakaraka(self.longitudes, scheme)

    def karakamsha(self, scheme: int = 8) -> int:
        return jaimini.karakamsha(self.longitudes, self.navamsha.signs, scheme)

    def argala(self, house: int = 1):
        ref = (self.ascendant_sign + house - 1) % 12
        return jaimini.argala_on_sign(ref, self.signs)

    # -- Arudhas -------------------------------------------------------- #
    def arudhas(self) -> dict[str, int]:
        return arudha.all_arudhas(self.ascendant_sign, self.signs)

    def arudha_lagna(self) -> int:
        return arudha.arudha_lagna(self.ascendant_sign, self.signs)

    # -- Ashtakavarga --------------------------------------------------- #
    def bhinnashtakavarga(self, planet: Planet) -> list[int]:
        return ashtakavarga.bhinnashtakavarga(planet, self.signs,
                                              self.ascendant_sign)

    def sarvashtakavarga(self) -> list[int]:
        return ashtakavarga.sarvashtakavarga(self.signs, self.ascendant_sign)

    # -- Aspects -------------------------------------------------------- #
    def graha_aspects(self):
        return all_graha_aspects(self.signs)

    def planets_aspecting(self, house: int) -> list[Planet]:
        sign = (self.ascendant_sign + house - 1) % 12
        return planets_aspecting_sign(sign, self.signs)

    def rashi_aspects_from(self, house: int) -> list[int]:
        sign = (self.ascendant_sign + house - 1) % 12
        return rashi_aspects(sign)

    # -- Panchanga ------------------------------------------------------ #
    def panchanga(self):
        sun = self.natal.get(Planet.SUN)
        moon = self.natal.get(Planet.MOON)
        return panchanga_mod.panchanga(
            sun.tropical_longitude, moon.tropical_longitude,
            sun.sidereal_longitude, moon.sidereal_longitude, self.when_utc,
        )

    # -- Special lagnas & upagrahas ------------------------------------- #
    def calculated_upagrahas(self) -> dict[str, float]:
        return upagrahas.calculated_upagrahas(self.longitudes[Planet.SUN])

    def special_lagnas(self) -> dict[str, float]:
        """Bhava/Hora/Ghati (sunrise-based) and Sree lagna longitudes."""
        eph = self.natal._ephemeris
        rise, _, _, _ = eph.day_portions(
            self.when_utc, self.natal.latitude, self.natal.longitude
        )
        out: dict[str, float] = {}
        if rise is not None:
            ghatis = special_lagnas._ghatis_since_sunrise(self.when_utc, rise)
            t_sr = eph.time(rise)
            sun_sr = norm360(eph.position(Planet.SUN, t_sr).longitude - self.ayanamsa)
            out["bhava"] = special_lagnas.bhava_lagna(sun_sr, ghatis)
            out["hora"] = special_lagnas.hora_lagna(sun_sr, ghatis)
            out["ghati"] = special_lagnas.ghati_lagna(sun_sr, ghatis)
        out["sree"] = special_lagnas.sree_lagna(
            self.ascendant, self.longitudes[Planet.MOON]
        )
        return out

    def indu_lagna(self) -> int:
        return special_lagnas.indu_lagna(
            self.ascendant_sign, self.signs[Planet.MOON], self.signs
        )

    # -- Strengths ------------------------------------------------------ #
    def shadbala(self):
        """Full Ṣaḍbala profile for the seven grahas."""
        from .shadbala import compute_shadbala
        return compute_shadbala(self)

    def ishta_kashta(self):
        """Iṣṭa-phala (benefic yield) vs Kaṣṭa-phala (malefic yield)."""
        from .shadbala import compute_ishta_kashta
        return compute_ishta_kashta(self)

    def vaiseshikamsa(self, planet: Planet) -> str:
        """Varga-dignity tier (Pārijāta … Bhāsvath) across the Ṣoḍaśavarga."""
        from .strength import vaiseshikamsa
        return vaiseshikamsa(planet, self.longitudes)

    # -- Planetary nature ----------------------------------------------- #
    def functional_nature(self) -> dict[Planet, str]:
        from .nature import functional_nature
        return functional_nature(self.ascendant_sign)

    def marakas(self) -> list[Planet]:
        from .nature import marakas
        return marakas(self.ascendant_sign)

    # -- Sensitive points ----------------------------------------------- #
    def bhrigu_bindu(self) -> float:
        """Bhṛgu Bindu — the midpoint of Rahu and the Moon."""
        from ..angles import norm180
        rahu = self.longitudes[Planet.RAHU]
        moon = self.longitudes[Planet.MOON]
        return norm360(rahu + norm180(moon - rahu) / 2.0)

    # -- Bhava-Chalit, KP, Kakshya, Transits ---------------------------- #
    def bhava_chalit(self):
        """Rāśi vs Placidus (Chalit) house placement, with shift detection."""
        from .chalit import bhava_chalit
        return bhava_chalit(self)

    def kp_chain(self, planet: Planet):
        """KP sign/star/sub/sub-sub lord chain for a planet."""
        from .kp import kp_chain
        return kp_chain(self.longitudes[planet])

    def kp_significators(self):
        """KP significator engine (house & planet significators)."""
        from .kp import KPSignificators
        return KPSignificators(self)

    def kakshya_lord(self, planet: Planet):
        from .kakshya import kakshya_lord
        return kakshya_lord(self.longitudes[planet])

    def transits(self):
        """Gochara calculator bound to this natal chart."""
        from .transits import Transits
        return Transits(self)

    def triangulate(self, start: datetime, end: datetime):
        """Multi-paddhati convergence analysis over a time window.

        Returns a :class:`~.triangulate.Triangulation` ranking activated
        life-event domains with texture, confidence and candidate timing.
        """
        from .triangulate import Triangulator
        return Triangulator(self, start, end).run()

    def triangulate_timeline(self, start: datetime, end: datetime,
                             width_days: int = 183, step_days: int = 30,
                             timing: bool = True):
        """Slide a short window across [start, end] and detect when each
        life-event theme peaks — discrete, dated events with precise gochara
        triggers. The time-localization layer over :meth:`triangulate`.
        """
        from .triangulate import Triangulator
        tl = Triangulator(self, start, end).timeline(width_days, step_days)
        return tl.with_timing() if timing else tl

    def varshaphal(self, year: int):
        """Tājika annual chart for *year*: solar-return Varṣa lagna + Muntha."""
        from .varshaphal import annual_chart
        return annual_chart(self, year)

    # -- Yogas & avasthas ----------------------------------------------- #
    def yogas(self):
        return yoga_mod.detect_yogas(self.ascendant_sign, self.signs,
                                     self.longitudes)

    def avasthas(self, planet: Planet) -> dict[str, str]:
        sun = self.longitudes[Planet.SUN]
        return avastha.all_avasthas(planet, self.longitudes[planet],
                                    sun_longitude=sun)

    # -- Compatibility -------------------------------------------------- #
    @staticmethod
    def compatibility(boy: "VedicChart", girl: "VedicChart"):
        return compatibility.guna_milan(
            boy.longitudes[Planet.MOON], girl.longitudes[Planet.MOON]
        )

    # -- Presentation --------------------------------------------------- #
    def summary(self) -> str:
        lines = [f"Vedic Chart — {self.when_utc:%Y-%m-%d %H:%M UTC}",
                 f"  Ayanamsa: {self.natal.ayanamsa_name} ({self.ayanamsa:.3f}°)",
                 f"  Lagna: {to_zodiac(self.ascendant)} ({SIGNS[self.ascendant_sign]})",
                 ""]
        for p in VEDIC_GRAHAS:
            if p not in self.longitudes:
                continue
            pos = to_zodiac(self.longitudes[p])
            dig = self.dignity(p)
            lines.append(f"  {p.value:<8} {pos}  H{self.house_of(p)}  "
                         f"[{dig.state}]")
        return "\n".join(lines)
