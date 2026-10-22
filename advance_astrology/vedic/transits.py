"""Gochara (transits) against a natal chart.

Computes sidereal transit positions for any date and maps them onto the natal
frame: transit sign/house, degree-to-degree conjunctions with natal points,
the natal SAV of the transited sign, Kakṣyā activity, and Sade Sati. Also the
nakṣatra-level gochara (nakṣatra, pada, tārā), sign and nakṣatra ingresses,
retrograde stations, Vedha, Ḍhaiyā, ingress Murti, and houses counted from any
reference point (Lagna, Moon, Sun, Arudha Lagna, Upapada, Kārakāṁśa). The
doctrine tables live in :mod:`.gochara`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from ..angles import angular_separation, norm360, to_zodiac
from ..ayanamsa import ayanamsa as compute_ayanamsa
from ..constants import DEFAULT_PLANETS, NAKSHATRA_ARC, SIGNS, VEDIC_GRAHAS, Planet
from ..nakshatra import nakshatra_of
from . import gochara
from . import sarvatobhadra as sbc
from . import kakshya as kakshya_mod
from .aspects import graha_aspect_houses
from .ashtakavarga import sarvashtakavarga


@dataclass(frozen=True)
class TransitHit:
    transit: Planet
    natal: Planet
    orb: float

    def __str__(self) -> str:
        return (f"transit {self.transit.value} conjunct natal "
                f"{self.natal.value} (orb {self.orb:.2f}°)")


@dataclass(frozen=True)
class ActivationWindow:
    """A contiguous date range during which a timing condition holds."""
    start: datetime
    end: datetime
    label: str

    @property
    def days(self) -> int:
        return (self.end - self.start).days

    def __str__(self) -> str:
        return (f"{self.start:%Y-%m-%d}→{self.end:%Y-%m-%d} "
                f"({self.days}d): {self.label}")


class Transits:
    """Transit calculator bound to a natal :class:`VedicChart`."""

    def __init__(self, chart):
        self.chart = chart
        self._eph = chart.natal._ephemeris
        self._ayanamsa_name = chart.natal.ayanamsa_name
        self.natal_signs = chart.signs
        self.natal_moon_sign = chart.signs[Planet.MOON]
        self.asc_sign = chart.ascendant_sign
        self._sav = sarvashtakavarga(chart.signs, self.asc_sign)
        # Memoized sidereal longitudes keyed by (when, planet). Timing scans
        # (double-transit / Kakṣyā / BNN / the candidate ledger) ask for the SAME
        # instants repeatedly across nodes; the ephemeris call dominates their
        # runtime, and the cached value is exactly what would be recomputed.
        self._pos_cache: dict = {}

    # ------------------------------------------------------------------ #
    def positions(self, when: datetime,
                  planets=None) -> dict[Planet, float]:
        """Sidereal transit longitudes (ayanamsa of the transit date)."""
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        planets = planets or DEFAULT_PLANETS
        missing = [p for p in planets if (when, p) not in self._pos_cache]
        if missing:
            t = self._eph.time(when)
            ayan = compute_ayanamsa(self._eph.julian_day(t), self._ayanamsa_name)
            for p in missing:
                self._pos_cache[(when, p)] = norm360(
                    self._eph.position(p, t).longitude - ayan)
        return {p: self._pos_cache[(when, p)] for p in planets}

    def transit_sign(self, when: datetime, planet: Planet) -> int:
        return to_zodiac(self.positions(when, [planet])[planet]).sign_index

    def transit_house(self, when: datetime, planet: Planet,
                      reference: str = "lagna") -> int:
        """Whole-sign house of a transit from the natal lagna or Moon."""
        sign = self.transit_sign(when, planet)
        base = self.asc_sign if reference == "lagna" else self.natal_moon_sign
        return (sign - base) % 12 + 1

    def conjunctions(self, when: datetime, orb: float = 1.0,
                     planets=None) -> list[TransitHit]:
        """Degree-to-degree transit→natal conjunctions within orb."""
        tpos = self.positions(when, planets)
        hits = []
        for tp, tlon in tpos.items():
            for np_, nlon in self.chart.longitudes.items():
                sep = angular_separation(tlon, nlon)
                if sep <= orb:
                    hits.append(TransitHit(tp, np_, sep))
        hits.sort(key=lambda h: h.orb)
        return hits

    def sav_of_transit(self, when: datetime, planet: Planet) -> int:
        """Natal SAV bindus of the sign a planet is transiting."""
        return self._sav[self.transit_sign(when, planet)]

    def kakshya_active(self, when: datetime, planet: Planet) -> bool:
        """Whether the transit is in a fruitful kakṣyā (BAV bindu present)."""
        lon = self.positions(when, [planet])[planet]
        return kakshya_mod.transit_active(planet, lon, self.natal_signs,
                                          self.asc_sign)

    def sade_sati(self, when: datetime) -> dict:
        """Saturn's Sade Sati status relative to the natal Moon."""
        sat_sign = self.transit_sign(when, Planet.SATURN)
        rel = (sat_sign - self.natal_moon_sign) % 12
        phases = {11: "Rising (12th)", 0: "Peak (Janma)", 1: "Setting (2nd)"}
        return {
            "active": rel in (11, 0, 1),
            "phase": phases.get(rel, "—"),
            "saturn_sign": SIGNS[sat_sign],
        }

    # ------------------------------------------------------------------ #
    # Forward activation-window scanner (Section 3 Step-3 timing engine)
    # ------------------------------------------------------------------ #
    def scan_windows(self, predicate, start: datetime, end: datetime,
                     step_days: float = 5.0, label: str = ""
                     ) -> list[ActivationWindow]:
        """Contiguous windows in [start, end] where ``predicate(when)`` is True.

        Coarse-steps by ``step_days`` then bisects each True/False flip to ~1-day
        resolution. ``step_days`` must be smaller than the shortest activation to
        be resolved (e.g. ≤2 for tight conjunction orbs, ≤1 for Kakṣyā zones).
        """
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        step = timedelta(days=step_days)
        one_day = timedelta(days=1)

        def boundary(lo: datetime, hi: datetime, prev: bool) -> datetime:
            while (hi - lo) > one_day:
                mid = lo + (hi - lo) / 2
                if predicate(mid) == prev:
                    lo = mid
                else:
                    hi = mid
            return hi

        windows: list[ActivationWindow] = []
        d = start
        state = predicate(d)
        win_start = start if state else None
        while d < end:
            nxt = min(d + step, end)
            s2 = predicate(nxt)
            if s2 != state:
                edge = boundary(d, nxt, state)
                if s2:
                    win_start = edge
                else:
                    windows.append(ActivationWindow(win_start, edge, label))
                    win_start = None
                state = s2
            d = nxt
        if state and win_start is not None:
            windows.append(ActivationWindow(win_start, end, label))
        return windows

    def conjunction_windows(self, transit: Planet, natal_longitude: float,
                            start: datetime, end: datetime, orb: float = 1.0,
                            step_days: float = 2.0) -> list[ActivationWindow]:
        """Windows where a transit is within ``orb`` of a natal longitude.

        The Bhrigu-Nandi-Nāḍī degree-to-degree trigger (§3 Step-3.3).
        """
        def pred(when: datetime) -> bool:
            lon = self.positions(when, [transit])[transit]
            return angular_separation(lon, natal_longitude) <= orb
        lbl = f"{transit.value} within {orb}° of {natal_longitude:.2f}°"
        return self.scan_windows(pred, start, end, step_days, lbl)

    def house_windows(self, planet: Planet, house: int, start: datetime,
                      end: datetime, reference: str = "lagna",
                      step_days: float = 5.0) -> list[ActivationWindow]:
        """Windows where a planet transits a given natal house (whole-sign)."""
        def pred(when: datetime) -> bool:
            return self.transit_house(when, planet, reference) == house
        lbl = f"{planet.value} transiting H{house} (from {reference})"
        return self.scan_windows(pred, start, end, step_days, lbl)

    def kakshya_windows(self, planet: Planet, start: datetime, end: datetime,
                        step_days: float = 1.0) -> list[ActivationWindow]:
        """Windows where a transit is in a fruitful Kakṣyā (§3 Step-3.4)."""
        def pred(when: datetime) -> bool:
            return self.kakshya_active(when, planet)
        lbl = f"{planet.value} in a bindu-bearing Kakṣyā"
        return self.scan_windows(pred, start, end, step_days, lbl)

    def transit_aspects(self, when: datetime, reference: str = "lagna",
                        planets=None) -> dict[Planet, list[int]]:
        """Gochar dṛṣṭi: houses each transiting planet ASPECTS (not just occupies).

        Uses Parāśarī special aspects, so e.g. a transit Jupiter aspects the 5th/
        7th/9th from itself — it need not bodily enter a house to act on it.
        """
        planets = planets or DEFAULT_PLANETS
        base = self.asc_sign if reference == "lagna" else self.natal_moon_sign
        out: dict[Planet, list[int]] = {}
        for p in planets:
            sign = self.transit_sign(when, p)
            houses = set()
            for dist in graha_aspect_houses(p):
                target_sign = (sign + dist - 1) % 12
                houses.add((target_sign - base) % 12 + 1)
            out[p] = sorted(houses)
        return out

    def aspects_house(self, when: datetime, house: int,
                      reference: str = "lagna", planets=None) -> list[Planet]:
        """Which transiting planets cast a graha-dṛṣṭi on a given natal house."""
        return [p for p, hs in self.transit_aspects(when, reference, planets).items()
                if house in hs]

    # ------------------------------------------------------------------ #
    # Double Transit (Gochara of Jupiter + Saturn) — the classic pinpoint
    # discriminator. An event fructifies only when BOTH the slow benefic
    # (Jupiter) and the slow karmic mover (Saturn) simultaneously activate
    # the bhava and/or its lord — by occupation OR by graha-dṛṣṭi.
    # ------------------------------------------------------------------ #
    def slow_activators(self, when: datetime, house: int,
                        reference: str = "lagna",
                        planets=(Planet.JUPITER, Planet.SATURN)) -> set:
        """Which of *planets* activate a whole-sign house (occupy OR aspect)."""
        base = self.asc_sign if reference == "lagna" else self.natal_moon_sign
        asp = self.transit_aspects(when, reference, planets)
        out = set()
        for p in planets:
            h_occ = (self.transit_sign(when, p) - base) % 12 + 1
            if h_occ == house or house in asp.get(p, []):
                out.add(p)
        return out

    def double_transit_windows(self, house: int, start: datetime,
                               end: datetime, reference: str = "lagna",
                               required=(Planet.JUPITER, Planet.SATURN),
                               step_days: float = 10.0
                               ) -> list[ActivationWindow]:
        """Windows where *all* ``required`` slow planets activate ``house``.

        The Double-Transit (Gochara) rule: marriage/career/etc. peaks when
        Jupiter AND Saturn together transit or aspect the matter's house.
        """
        req = set(required)
        def pred(when: datetime) -> bool:
            return req.issubset(
                self.slow_activators(when, house, reference, tuple(req)))
        lbl = (f"double-transit ({'+'.join(p.value for p in required)}) "
               f"on H{house} from {reference}")
        return self.scan_windows(pred, start, end, step_days, lbl)

    def double_transit_on_sign(self, sign: int, start: datetime,
                               end: datetime,
                               required=(Planet.JUPITER, Planet.SATURN),
                               step_days: float = 10.0
                               ) -> list[ActivationWindow]:
        """Double-transit windows on a fixed natal sign (e.g. the Upapada sign
        or the 7th-lord's sign), evaluated from the lagna."""
        house = (sign - self.asc_sign) % 12 + 1
        return self.double_transit_windows(house, start, end, "lagna",
                                           required, step_days)

    def slow_movers(self, when: datetime) -> dict[Planet, dict]:
        """Sign/house summary for the structural heavyweights."""
        out = {}
        for p in (Planet.SATURN, Planet.JUPITER, Planet.RAHU, Planet.KETU):
            sign = self.transit_sign(when, p)
            out[p] = {
                "sign": SIGNS[sign],
                "house_from_lagna": (sign - self.asc_sign) % 12 + 1,
                "house_from_moon": (sign - self.natal_moon_sign) % 12 + 1,
                "sav": self._sav[sign],
            }
        return out

    # ------------------------------------------------------------------ #
    # Nakṣatra-level gochara, ingresses, stations, Vedha, Murti, references
    # ------------------------------------------------------------------ #
    # Coarse scan step (days) per planet. At the planet's fastest motion one
    # step covers well under half a nakṣatra (13°20'), so no nakṣatra or sign
    # can be skipped between two samples: Mercury/Venus ≤1.6°/day → 4 d,
    # Sun ≤1.02°/day → 5 d, Mars ≤0.8°/day → 6 d, Jupiter ≤0.25°/day → 12 d,
    # Saturn ≤0.13°/day → 20 d, mean node ≈0.053°/day → 40 d, Moon → 0.25 d.
    _STEP = {Planet.MOON: 0.25, Planet.SUN: 5.0, Planet.MERCURY: 4.0,
             Planet.VENUS: 4.0, Planet.MARS: 6.0, Planet.JUPITER: 12.0,
             Planet.SATURN: 20.0, Planet.RAHU: 40.0, Planet.KETU: 40.0}

    def motion(self, when: datetime, planet: Planet) -> dict:
        """Daily motion (deg/day) and whether the planet is vakri (retrograde).
        Rāhu/Ketu use the mean node, which is always retrograde."""
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        speed = float(self._eph.position(planet, self._eph.time(when)).speed)
        return dict(speed=speed, retrograde=speed < 0.0)

    def reference_signs(self) -> dict[str, int]:
        """Natal signs that gochara can be counted from: Lagna, Moon and Sun
        (the Sudarśana triad) and the Jaimini points AL, UL and Kārakāṁśa."""
        ar = self.chart.arudhas()
        return dict(lagna=int(self.asc_sign), moon=int(self.natal_moon_sign),
                    sun=int(self.natal_signs[Planet.SUN]), al=int(ar["AL"]),
                    ul=int(ar["UL"]), karakamsha=int(self.chart.karakamsha()))

    def houses_from(self, when: datetime, reference_sign: int,
                    planets=None) -> dict[Planet, int]:
        """Whole-sign house of each transit counted from any natal sign."""
        planets = planets or VEDIC_GRAHAS
        return {p: (self.transit_sign(when, p) - reference_sign) % 12 + 1
                for p in planets}

    def _sidereal_lons(self, planet: Planet, whens: list) -> list[float]:
        """Sidereal longitudes of *planet* at many instants (one vectorised
        ephemeris call; same value :meth:`positions` would give)."""
        lons, tts = self._eph.longitudes(planet, whens)
        return [norm360(lon - compute_ayanamsa(tt, self._ayanamsa_name))
                for lon, tt in zip(lons, tts)]

    def _changes(self, planet: Planet, start: datetime, end: datetime,
                 key, step_days=None) -> list[tuple]:
        """Instants in [start, end] where ``key(longitude)`` changes value, to
        ≤ 1 hour. Samples a coarse grid in one vectorised call, then refines
        each changing step 24-fold until the change is pinned to an hour.
        Returns (when, old_value, new_value)."""
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        step = timedelta(days=step_days or self._STEP.get(planet, 1.0))
        grid = [start]
        while grid[-1] < end:
            grid.append(min(grid[-1] + step, end))
        vals = [key(lon) for lon in self._sidereal_lons(planet, grid)]
        hour = timedelta(hours=1)

        def refine(lo, hi, v_lo, v_hi):
            # Split a changing interval into 24 parts (one vectorised call) and
            # recurse into the parts that change, until they are ≤ 1 hour.
            if hi - lo <= hour:
                return [(hi, v_lo, v_hi)]
            pts = [lo + (hi - lo) * k / 24 for k in range(25)]
            pv = [v_lo] + [key(lon) for lon in
                           self._sidereal_lons(planet, pts[1:-1])] + [v_hi]
            found = []
            for k in range(24):
                if pv[k + 1] != pv[k]:
                    found += refine(pts[k], pts[k + 1], pv[k], pv[k + 1])
            return found

        out = []
        for i in range(len(grid) - 1):
            if vals[i + 1] != vals[i]:
                out += refine(grid[i], grid[i + 1], vals[i], vals[i + 1])
        return out

    def _retro_flags(self, planet: Planet, whens: list) -> list[bool]:
        """Vakri flag at each instant from a ±12 h longitude difference (one
        vectorised call for all instants; same rule as :meth:`motion`)."""
        if not whens:
            return []
        if planet in (Planet.RAHU, Planet.KETU):
            return [True] * len(whens)   # mean node: always retrograde
        half = timedelta(hours=12)
        pts = [w + d for w in whens for d in (-half, half)]
        lons = self._sidereal_lons(planet, pts)
        return [((lons[2 * k + 1] - lons[2 * k] + 180.0) % 360.0 - 180.0) < 0.0
                for k in range(len(whens))]

    def sign_ingresses(self, planet: Planet, start: datetime,
                       end: datetime) -> list[dict]:
        """Rāśi parivartan: every sign change of *planet* in [start, end], with
        the house it enters (from Lagna and Moon) and the ingress Murti."""
        ch = self._changes(planet, start, end, lambda lon: int(lon // 30) % 12)
        whens = [c[0] for c in ch]
        retro = self._retro_flags(planet, whens)
        moon = self._sidereal_lons(Planet.MOON, whens) if whens else []
        out = []
        for (when, old, new), r, mlon in zip(ch, retro, moon):
            moon_h = (int(mlon // 30) % 12 - self.natal_moon_sign) % 12 + 1
            out.append(dict(planet=planet, when=when, from_sign=old,
                            to_sign=new,
                            house_from_lagna=(new - self.asc_sign) % 12 + 1,
                            house_from_moon=(new - self.natal_moon_sign) % 12 + 1,
                            retrograde=r, murti=gochara.murti(moon_h)))
        return out

    def nakshatra_ingresses(self, planet: Planet, start: datetime,
                            end: datetime) -> list[dict]:
        """Nakṣatra parivartan: every nakṣatra change of *planet* in
        [start, end], with the new nakṣatra's lord and its tārā from the janma
        nakṣatra."""
        janma = nakshatra_of(self.chart.longitudes[Planet.MOON]).index
        ch = self._changes(planet, start, end,
                           lambda lon: int(lon // NAKSHATRA_ARC) % 27)
        retro = self._retro_flags(planet, [c[0] for c in ch])
        out = []
        for (when, old, new), r in zip(ch, retro):
            nk = nakshatra_of((new + 0.5) * NAKSHATRA_ARC)
            out.append(dict(planet=planet, when=when, from_nakshatra=old,
                            to_nakshatra=new, lord=nk.lord, retrograde=r,
                            tara=gochara.tara(janma, new)))
        return out

    def stations(self, planet: Planet, start: datetime,
                 end: datetime) -> list[dict]:
        """Vakri / mārgī stations of *planet* in [start, end], to ≤ 1 hour.
        Empty for the mean nodes, which never station.

        Samples the vakri flag every 3 days (a retrograde spell lasts at least
        ~3 weeks, so none can be missed) in one vectorised call, then refines
        each flip 24-fold like :meth:`_changes`."""
        if planet in (Planet.RAHU, Planet.KETU):
            return []
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        step, hour = timedelta(days=3), timedelta(hours=1)
        grid = [start]
        while grid[-1] < end:
            grid.append(min(grid[-1] + step, end))
        flags = self._retro_flags(planet, grid)

        def refine(lo, hi, f_lo, f_hi):
            if hi - lo <= hour:
                return [hi]
            pts = [lo + (hi - lo) * k / 24 for k in range(25)]
            pf = [f_lo] + self._retro_flags(planet, pts[1:-1]) + [f_hi]
            found = []
            for k in range(24):
                if pf[k + 1] != pf[k]:
                    found += refine(pts[k], pts[k + 1], pf[k], pf[k + 1])
            return found

        out = []
        for k in range(len(grid) - 1):
            if flags[k + 1] != flags[k]:
                turns = "vakri" if flags[k + 1] else "margi"
                for w in refine(grid[k], grid[k + 1], flags[k], flags[k + 1]):
                    out.append(dict(planet=planet, when=w, turns=turns))
        return out

    def tara_bala(self, when: datetime, planets=None) -> dict[Planet, dict]:
        """Tārā of each transit's nakṣatra counted from the janma nakṣatra."""
        janma = nakshatra_of(self.chart.longitudes[Planet.MOON]).index
        planets = planets or VEDIC_GRAHAS
        pos = self.positions(when, planets)
        return {p: gochara.tara(janma, nakshatra_of(pos[p]).index)
                for p in planets}

    def vedha(self, when: datetime) -> dict[Planet, dict]:
        """Vedha (Phaladeepika) for every graha's transit, from the natal Moon."""
        hm = self.houses_from(when, self.natal_moon_sign)
        return {p: gochara.vedha(p, hm[p], hm) for p in VEDIC_GRAHAS}

    def saturn_status(self, when: datetime) -> dict:
        """Saturn from the natal Moon: Sāḍhe Sātī phase and Ḍhaiyā."""
        h = (self.transit_sign(when, Planet.SATURN) - self.natal_moon_sign) % 12 + 1
        return gochara.saturn_from_moon(h)

    def snapshot(self, when: datetime) -> dict:
        """Every gochara datum for *when*, per graha — DATA only, no verdict.

        Position (sign, degree, nakṣatra, pada, nakṣatra lord), motion, houses
        from each reference sign, SAV of the transited sign, Kakṣyā (not for
        the nodes), tārā, graha-dṛṣṭi from Lagna and Moon, and Vedha; plus the
        Saturn-from-Moon status.
        """
        refs = self.reference_signs()
        pos = self.positions(when, VEDIC_GRAHAS)
        tb = self.tara_bala(when)
        vd = self.vedha(when)
        asp_l = self.transit_aspects(when, "lagna", VEDIC_GRAHAS)
        asp_m = self.transit_aspects(when, "moon", VEDIC_GRAHAS)
        planets = {}
        for p in VEDIC_GRAHAS:
            lon = pos[p]
            sign = int(lon // 30) % 12
            nk = nakshatra_of(lon)
            try:
                kak = self.kakshya_active(when, p)
            except KeyError:
                kak = None   # no Bhinnāṣṭakavarga for the nodes
            planets[p] = dict(
                longitude=lon, sign=sign, degree=lon % 30,
                nakshatra=nk.index, nakshatra_name=nk.name, pada=nk.pada,
                nakshatra_lord=nk.lord, **self.motion(when, p),
                houses={k: (sign - r) % 12 + 1 for k, r in refs.items()},
                sav=self._sav[sign], kakshya_active=kak, tara=tb[p],
                aspects_from_lagna=asp_l[p], aspects_from_moon=asp_m[p],
                vedha=vd[p])
        return dict(when=when, references=refs, planets=planets,
                    saturn=self.saturn_status(when))

    def sarvatobhadra(self, when: datetime) -> dict:
        """Sarvatobhadra Chakra vedha for every transiting graha — DATA only.

        For each graha: its 28-scheme nakṣatra, motion class (vakri / śīghra /
        madhya), and where each of its three vedha lines (front and the two
        diagonals) lands on the nakṣatra ring. ``hits`` lists the natal
        points whose nakṣatra a line lands on: ``janma`` (the natal Moon) and
        each natal graha. Which line a given motion emphasises is left to the
        reader (see :mod:`.sarvatobhadra`).
        """
        natal = {p: sbc.nakshatra_28(lon) for p, lon in self.chart.longitudes.items()
                 if p in VEDIC_GRAHAS}
        pos = self.positions(when, VEDIC_GRAHAS)
        out = {}
        for p in VEDIC_GRAHAS:
            nk = sbc.nakshatra_28(pos[p])
            lines = sbc.vedha_lines(nk)
            hits = {}
            for name, ln in lines.items():
                tgt = ln["lands"]
                pts = [("janma" if q is Planet.MOON else q.value)
                       for q, n in natal.items() if n == tgt]
                if pts:
                    hits[name] = pts
            out[p] = dict(nakshatra=nk,
                          motion=sbc.motion_class(p, self.motion(when, p)["speed"]),
                          lands={k: v["lands"] for k, v in lines.items()},
                          hits=hits)
        return dict(janma_nakshatra=natal[Planet.MOON], natal_nakshatras=natal,
                    planets=out)
