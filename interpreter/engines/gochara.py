"""Gochara (transit) engine — DATA ONLY.

Answers "what are the CURRENT transits doing to this chart?" in three layers the
AI then interprets (never scored, never judged here):

  1. **Transit ↔ natal** — every transiting graha's contact with a natal graha
     (conjunction / graha-dṛṣṭi, with the degree gap), so the personal pattern
     is explicit.
  2. **Transit ↔ bhāva** — which natal houses each transit occupies/aspects,
     reckoned BOTH from Lagna and from the Moon (Janma-rāśi gochara), with the
     sign's SAV bindus and kakṣyā fruitfulness, Sade-Sati, the Jupiter+Saturn
     double-transit, and Saturn/Jupiter returns.
  3. **Sky-only (independent of the native)** — mutual transit-to-transit
     conjunctions, retrogrades, and the slow movers' upcoming sign ingresses:
     the collective weather, true for everyone.

Wraps existing computation (`VedicChart.transits()`); recomputes nothing.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from advance_astrology import Planet
from advance_astrology.constants import SIGNS
from advance_astrology.nakshatra import nakshatra_of
from advance_astrology.vedic.aspects import graha_aspect_houses

UTC = timezone.utc

GRAHAS = (Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY, Planet.JUPITER,
          Planet.VENUS, Planet.SATURN, Planet.RAHU, Planet.KETU)
SLOW = (Planet.SATURN, Planet.JUPITER, Planet.RAHU, Planet.KETU)
# Nodes never retrograde in the ordinary sense; luminaries never do.
_NEVER_RETRO = (Planet.SUN, Planet.MOON, Planet.RAHU, Planet.KETU)


@dataclass(frozen=True)
class TransitPosition:
    planet: str
    sign: str
    degree: float
    nakshatra: str
    retrograde: bool
    house_from_lagna: int
    house_from_moon: int
    sav_bindus: int              # natal SAV of the sign being transited
    kakshya_fruitful: bool       # transit in a bindu-bearing kakṣyā (BAV)


@dataclass(frozen=True)
class NatalContact:
    transit_planet: str
    natal_planet: str
    relation: str                # "conjunction" | "aspect (Nth)"
    orb: float                   # degree gap (conjunction) or 0.0 for sign-aspect
    degree_lock: bool            # within 3° — the tight, event-grade contact


@dataclass(frozen=True)
class HouseActivation:
    house: int
    reference: str               # "lagna" | "moon"
    occupied_by: tuple[str, ...]
    aspected_by: tuple[str, ...]


@dataclass(frozen=True)
class Ingress:
    planet: str
    from_sign: str
    to_sign: str
    on: datetime


@dataclass(frozen=True)
class GocharaReport:
    as_of: datetime
    positions: tuple[TransitPosition, ...]
    natal_contacts: tuple[NatalContact, ...]
    house_activation: tuple[HouseActivation, ...]
    sade_sati: dict
    double_transit_houses: tuple[int, ...]      # houses lit by BOTH Jupiter & Saturn
    returns: tuple[str, ...]                    # e.g. "Saturn return (3.1° from natal)"
    sky_conjunctions: tuple[str, ...]           # transit-to-transit (native-independent)
    retrogrades: tuple[str, ...]
    upcoming_ingresses: tuple[Ingress, ...]


def _is_retrograde(tr, when: datetime, planet: Planet) -> bool:
    """Retrograde = sidereal longitude decreasing across a ±1-day bracket."""
    if planet in _NEVER_RETRO:
        return False
    a = float(tr.positions(when - timedelta(days=1), [planet])[planet])
    b = float(tr.positions(when + timedelta(days=1), [planet])[planet])
    # bool(...) — the ephemeris yields numpy scalars, whose comparison is a
    # numpy.bool_ that json.dumps cannot serialize downstream.
    return bool(((b - a + 540.0) % 360.0) - 180.0 < 0)


def _sep(a: float, b: float) -> float:
    """Smallest angular separation between two longitudes."""
    return float(abs(((float(a) - float(b) + 180.0) % 360.0) - 180.0))


class GocharaEngine:
    name = "gochara"

    def evaluate(self, v, profile=None, start: datetime | None = None,
                 end: datetime | None = None) -> GocharaReport:
        """`profile` is unused (gochara is chart-wide, not domain-scoped) but kept
        so the engine matches the shared contract. `start` doubles as the as-of
        instant; `end` bounds the ingress look-ahead (default: +12 months)."""
        when = start or datetime.now(UTC)
        horizon = end or (when + timedelta(days=365))
        tr = v.transits()
        asc, moon_sign = v.ascendant_sign, v.signs[Planet.MOON]
        pos = tr.positions(when, list(GRAHAS))

        # ---- layer 1+2 groundwork: where every graha sits right now ---------- #
        positions = []
        for p in GRAHAS:
            lon = float(pos[p])
            sign = int(lon // 30) % 12
            try:
                kak = bool(tr.kakshya_active(when, p))
            except Exception:
                kak = False
            try:
                sav = int(tr.sav_of_transit(when, p))
            except Exception:
                sav = 0
            positions.append(TransitPosition(
                planet=p.value, sign=SIGNS[sign], degree=round(lon % 30, 2),
                nakshatra=nakshatra_of(lon).name,
                retrograde=_is_retrograde(tr, when, p),
                house_from_lagna=(sign - asc) % 12 + 1,
                house_from_moon=(sign - moon_sign) % 12 + 1,
                sav_bindus=sav, kakshya_fruitful=kak))

        # ---- layer 1: transit ↔ NATAL graha contacts ------------------------- #
        contacts = []
        for tp in GRAHAS:
            t_lon = float(pos[tp])
            t_sign = int(t_lon // 30) % 12
            aspected = {(t_sign + d - 1) % 12: d for d in graha_aspect_houses(tp)}
            for np_ in GRAHAS:
                n_lon = float(v.longitudes[np_])
                n_sign = int(n_lon // 30) % 12
                if t_sign == n_sign:
                    gap = _sep(t_lon, n_lon)
                    contacts.append(NatalContact(
                        tp.value, np_.value, "conjunction",
                        round(gap, 2), gap <= 3.0))
                elif n_sign in aspected:
                    contacts.append(NatalContact(
                        tp.value, np_.value, f"aspect ({aspected[n_sign]}th)",
                        0.0, False))
        contacts.sort(key=lambda c: (not c.degree_lock, c.orb))

        # ---- layer 2: bhāva activation from Lagna AND from the Moon ---------- #
        activation = []
        for ref, base in (("lagna", asc), ("moon", moon_sign)):
            asp_map = tr.transit_aspects(when, reference=ref, planets=list(GRAHAS))
            for h in range(1, 13):
                occ = tuple(p.value for p in GRAHAS
                            if (int(float(pos[p]) // 30) - base) % 12 + 1 == h)
                ap = tuple(p.value for p, hs in asp_map.items() if h in hs)
                if occ or ap:
                    activation.append(HouseActivation(h, ref, occ, ap))

        # ---- double transit (Jupiter AND Saturn on the same bhāva) ----------- #
        dt_houses = tuple(
            int(h) for h in range(1, 13)
            if {Planet.JUPITER, Planet.SATURN} <= set(tr.slow_activators(when, h)))

        # ---- returns (a slow graha back on its own natal degree) ------------- #
        returns = []
        for p in (Planet.SATURN, Planet.JUPITER, Planet.RAHU):
            gap = _sep(float(pos[p]), float(v.longitudes[p]))
            if gap <= 8.0:
                returns.append(f"{p.value} return (within {gap:.1f}° of its natal degree)")

        # ---- layer 3: SKY-ONLY patterns (true for everyone) ------------------ #
        sky = []
        pl = list(GRAHAS)
        for i, a in enumerate(pl):
            for b in pl[i + 1:]:
                gap = _sep(float(pos[a]), float(pos[b]))
                if gap <= 8.0:
                    sky.append(f"{a.value} ☌ {b.value} ({gap:.1f}°)")
        retro = tuple(tp.planet for tp in positions if tp.retrograde)

        # ---- slow-mover sign ingresses inside the horizon -------------------- #
        ingress = []
        for p in SLOW:
            cur = int(float(pos[p]) // 30) % 12
            probe, last = when, cur
            while probe < horizon:
                probe += timedelta(days=5)
                s = int(float(tr.positions(probe, [p])[p]) // 30) % 12
                if s != last:
                    ingress.append(Ingress(p.value, SIGNS[last], SIGNS[s], probe))
                    last = s
        ingress.sort(key=lambda x: x.on)

        return GocharaReport(
            as_of=when, positions=tuple(positions),
            natal_contacts=tuple(contacts), house_activation=tuple(activation),
            # normalise numpy scalars → plain Python so the report is JSON-safe
            sade_sati={k: (bool(x) if isinstance(x, bool) or hasattr(x, "item")
                           and isinstance(x.item(), bool) else x)
                       for k, x in tr.sade_sati(when).items()},
            double_transit_houses=dt_houses, returns=tuple(returns),
            sky_conjunctions=tuple(sky), retrogrades=retro,
            upcoming_ingresses=tuple(ingress))
