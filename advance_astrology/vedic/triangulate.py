"""Convergence engine — multi-paddhati triangulation over a time window.

Deterministic, parameter-free synthesis layer. It turns the engine's raw
witnesses (Vimśottari + rashi daśās, slow gochara, Shadbala/Iṣṭa-Kaṣṭa, Argala,
Aṣṭakavarga, vargas, KP) into a *ranked* set of activated life-event DOMAINS,
each with a support-vs-obstruction texture, a strength-weighted confidence, and
candidate timing windows.

Design contract (see docs/RULE_CHANGELOG.md):
  * One mechanical assembly, identical every run — no hindsight nudging.
  * No constant is fit to any chart's history. Every weight is a documented
    methodological choice grounded in the Architectural Playbook (§3-4) and
    classical śāstra.
  * A domain is declared *active* only when independent paddhati FAMILIES
    converge (≥ MIN_FAMILIES) — single-factor signals are suppressed.
  * Varga confirmation disambiguates the event TYPE; the scanner dates it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from ..constants import RULERSHIPS, SIGNS, Planet
from .nature import natural_benefic

# --------------------------------------------------------------------------- #
# Domain definitions (śāstra-grounded house / kāraka / varga maps)
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Domain:
    key: str
    label: str
    houses: tuple[int, ...]        # houses whose activation manifests the event
    negation: tuple[int, ...]      # KP / house signatures of cancellation
    karakas: tuple[Planet, ...]    # natural significators
    chara_karaka: str | None       # Jaimini role, e.g. "Darakaraka"
    varga: int                     # confirming divisional chart
    malefic_event: bool = False    # True = the event itself is adverse


DOMAINS: tuple[Domain, ...] = (
    Domain("career", "Career / profession", (10, 6, 7, 11), (5, 8, 12),
           (Planet.SUN, Planet.SATURN, Planet.MERCURY), "Amatyakaraka", 10),
    Domain("marriage", "Marriage / partnership", (7, 2, 11), (1, 6, 10),
           (Planet.VENUS,), "Darakaraka", 9),
    Domain("wealth", "Wealth / gains", (2, 11, 5, 9), (12, 6, 8),
           (Planet.JUPITER, Planet.VENUS), None, 2),
    Domain("education", "Education / learning", (4, 5, 9, 2), (8, 12),
           (Planet.MERCURY, Planet.JUPITER), None, 24),
    Domain("property", "Property / vehicles", (4, 2, 11), (3, 8, 12),
           (Planet.MARS, Planet.VENUS), "Matrikaraka", 4),
    Domain("children", "Children / progeny", (5, 9, 2), (1, 4, 8),
           (Planet.JUPITER,), "Putrakaraka", 7),
    Domain("relocation", "Relocation / foreign", (3, 9, 12), (4,),
           (Planet.RAHU, Planet.MOON), None, 4),
    Domain("health", "Health crisis / surgery", (6, 8, 1), (1,),
           (Planet.MARS, Planet.SATURN, Planet.SUN), None, 30,
           malefic_event=True),
    Domain("litigation", "Litigation / loss", (6, 8, 12), (11, 5),
           (Planet.SATURN, Planet.MARS), "Gnatikaraka", 30, malefic_event=True),
    Domain("spirituality", "Spirituality / dharma", (9, 12, 5), (),
           (Planet.JUPITER, Planet.KETU), None, 20),
)

# --------------------------------------------------------------------------- #
# Methodological weights (documented constants; NOT fit to data)
# --------------------------------------------------------------------------- #
W_DASHA = {1: 1.0, 2: 0.7, 3: 0.5}   # Mahā / Antar / Pratyantar activation
W_RASHI_DASHA = 0.6
W_GOCHARA = 0.6
W_LORD = 1.0
W_OCCUPANT = 0.5
W_ARGALA = 0.5
W_KARAKA = 0.6
W_VARGA = 0.8
W_SAV = 0.5
W_KP = 0.7
W_AVASTHA = 0.6
W_ASPECT = 0.5
W_CHALIT = 0.4
W_YOGA = 0.8
W_ARUDHA = 0.6
W_CHARAKARAKA = 0.6
W_VIMSOPAKA = 0.6
W_MARAKA = 0.5
W_VARSHAPHAL = 0.7

# Vaiśeṣikāṃśa grades (varga-strength); Gopura+ = strong, Adhama = weak.
HIGH_VAISESHIKA = {"Gopura", "Simhasana", "Paravata", "Devaloka",
                   "Brahmaloka", "Airavata", "Sridhama"}
LOW_VAISESHIKA = {"Adhama"}

# Named yogas → (domain, polarity). Falls back to kind (Raja→career, Dhana→wealth).
YOGA_MAP = {
    "Raja": (("career", +1), ("wealth", +1)),
    "Dhana": (("wealth", +1),),
    "Gajakesari": (("education", +1), ("career", +1), ("spirituality", +1)),
    "Budha-Aditya": (("education", +1), ("career", +1)),
    "Chandra-Mangala": (("wealth", +1), ("property", +1)),
    "Kemadruma": (("wealth", -1),),
    "Kala Sarpa": (("career", -1), ("wealth", -1), ("marriage", -1)),
}

# Temperamental moods (Dīptādi) — the playbook's §3 Step-2 "mood blockade".
GOOD_MOODS = {"Dipta", "Svastha", "Pramudita"}
BAD_MOODS = {"Khala", "Vikala", "Dukhita"}     # corrupt the house promise

SAV_HIGH, SAV_LOW = 30, 22           # playbook §3 Step-1 density thresholds
STRONG_RATIO = 1.0                   # Shadbala ratio ≥1 meets required rūpa
MIN_FAMILIES = 3                     # ≥3 independent paddhatis ⇒ "active" theme
MIN_DYNAMIC = 2                      # ≥2 time-varying paddhatis must light it NOW
KENDRA = (1, 4, 7, 10)
TRIKONA = (5, 9)                     # (1 already in kendra)
DUSTHANA = (6, 8, 12)

# Families split by independence type. STATIC = lifelong natal promise (same in
# every window); DYNAMIC = what is actually lit during THIS window. A domain is
# only "hot" when DYNAMIC witnesses fire — the natal promise merely gates whether
# the activated theme can manifest. This separation is what discriminates one
# window's event from the lifelong background. (Playbook: Step-1 macro-scan =
# activation; Step-2 filtration = promise/strength.)
STATIC_FAMILIES = {"lord", "occupant", "argala", "karaka", "varga", "sav",
                   "avastha", "aspect", "chalit", "yoga", "arudha",
                   "charakaraka", "vimsopaka", "maraka"}
DYNAMIC_FAMILIES = {"vimshottari", "rashi_dasha", "gochara", "kp", "varshaphal"}


# --------------------------------------------------------------------------- #
# Vote + per-domain accumulator
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Vote:
    family: str        # witness family — the unit of independence
    polarity: int      # +1 manifestation (Track A), -1 obstruction (Track B)
    weight: float
    reason: str


@dataclass
class DomainScore:
    domain: Domain
    votes: list[Vote] = field(default_factory=list)
    confidence: float = 0.0          # field-relative salience, set by run()

    def add(self, family: str, polarity: int, weight: float, reason: str) -> None:
        if weight > 0:
            self.votes.append(Vote(family, polarity, weight, reason))

    def _net(self, families: set[str]) -> float:
        return sum(v.weight * v.polarity
                   for v in self.votes if v.family in families)

    @property
    def support(self) -> float:
        return sum(v.weight for v in self.votes if v.polarity > 0)

    @property
    def obstruction(self) -> float:
        return sum(v.weight for v in self.votes if v.polarity < 0)

    @property
    def net(self) -> float:
        return self.support - self.obstruction

    @property
    def promise(self) -> float:
        """Lifelong natal potential (static families)."""
        return self._net(STATIC_FAMILIES)

    @property
    def activation(self) -> float:
        """How strongly THIS window lights the domain (dynamic families)."""
        return self._net(DYNAMIC_FAMILIES)

    @property
    def support_families(self) -> set[str]:
        return {v.family for v in self.votes if v.polarity > 0}

    @property
    def dynamic_families(self) -> set[str]:
        return {v.family for v in self.votes
                if v.polarity > 0 and v.family in DYNAMIC_FAMILIES}

    @property
    def converged(self) -> bool:
        """Active only if the chart promises it AND ≥2 dynamic paddhatis fire."""
        return (self.promise > 0
                and len(self.dynamic_families) >= MIN_DYNAMIC
                and len(self.support_families) >= MIN_FAMILIES)

    @property
    def raw_score(self) -> float:
        """Discriminating score: window-activation gated by natal promise.

        Activation is the discriminator (what differs window to window); a
        positive promise opens the gate and adds a small confirming term.
        """
        if self.promise <= 0:
            return 0.0
        gate = 1.0 - math.exp(-self.promise / 4.0)   # 0..1 promise gate
        return self.activation * gate + 0.25 * self.promise

    @property
    def band(self) -> str:
        c = self.confidence
        return "high" if c >= 0.66 else "moderate" if c >= 0.40 else "low"

    @property
    def texture(self) -> str:
        sup, obs = self.support, self.obstruction
        if sup <= 0 and obs <= 0:
            return "dormant"
        if not self.converged:
            return "latent (below convergence threshold)"
        ratio = obs / sup if sup else 99.0
        if ratio < 0.35:
            return "clean manifestation"
        if ratio < 0.80:
            return "manifestation with friction"
        if ratio <= 1.30:
            return "fixed-then-cancelled (explosive near-miss)"
        return "blocked / does not manifest"


@dataclass
class Triangulation:
    start: datetime
    end: datetime
    scores: list[DomainScore]                       # ranked, all domains
    windows: dict[str, list]                         # per active domain key

    @property
    def active(self) -> list[DomainScore]:
        return [s for s in self.scores if s.converged]

    def text(self) -> str:
        return _render(self)


@dataclass
class Sample:
    mid: datetime
    scores: dict[str, float]      # domain key -> raw_score
    lead: str | None              # leading converged domain key
    lead_conf: float
    lead_texture: str


@dataclass
class TimelineEvent:
    domain: Domain
    peak: datetime                # date of strongest activation
    window_start: datetime        # span over which this theme led
    window_end: datetime
    score: float
    texture: str
    timing: list = field(default_factory=list)   # precise gochara windows


@dataclass
class TimelineResult:
    start: datetime
    end: datetime
    width_days: int
    step_days: int
    samples: list[Sample]
    events: list[TimelineEvent]
    _engine: "Triangulator" = None

    def with_timing(self, top_n: int = 6) -> "TimelineResult":
        """Attach precise BNN/Kakṣyā trigger windows to the strongest events
        (capped at *top_n* by salience to bound runtime)."""
        ranked = sorted(self.events, key=lambda e: e.score, reverse=True)[:top_n]
        chosen = set(id(e) for e in ranked)
        for e in self.events:
            if id(e) not in chosen:
                continue
            eng = self._engine
            saved = (eng.start, eng.end)
            eng.start, eng.end = e.window_start, e.window_end
            e.timing = eng._windows_for(e.domain)
            eng.start, eng.end = saved
        return self

    def text(self) -> str:
        return _render_timeline(self)


# --------------------------------------------------------------------------- #
# Engine
# --------------------------------------------------------------------------- #
def _utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


class Triangulator:
    """Builds a :class:`Triangulation` for a chart over [start, end]."""

    def __init__(self, chart, start: datetime, end: datetime):
        self.c = chart
        self.start = _utc(start)
        self.end = _utc(end)
        self.mid = self.start + (self.end - self.start) / 2
        self.asc = chart.ascendant_sign
        self.signs = chart.signs
        self.shad = chart.shadbala()
        self.ik = chart.ishta_kashta()
        self.sav = chart.sarvashtakavarga()
        self.nature = chart.functional_nature()
        self.tr = chart.transits()
        self.moods = {p: chart.avasthas(p)["deeptadi"] for p in self.shad}
        self.aspects = [a for a in chart.graha_aspects()
                        if a.planet in self.shad]
        self.chalit = chart.bhava_chalit()
        self._annual_cache: dict[int, object] = {}
        self.scores = {d.key: DomainScore(d) for d in DOMAINS}

    def _annual(self, year: int):
        if year not in self._annual_cache:
            from .varshaphal import annual_chart
            self._annual_cache[year] = annual_chart(self.c, year)
        return self._annual_cache[year]

    # -- small helpers --------------------------------------------------- #
    def house_lord(self, house: int) -> Planet:
        return RULERSHIPS[SIGNS[(self.asc + house - 1) % 12]]

    def house_sign(self, house: int) -> int:
        return (self.asc + house - 1) % 12

    def rules_house(self, planet: Planet, houses: tuple[int, ...]) -> bool:
        return any(self.house_lord(h) == planet for h in houses)

    def occupies_house(self, planet: Planet, houses: tuple[int, ...]) -> bool:
        hp = self.c.house_of(planet)
        return hp in houses

    def strength(self, planet: Planet) -> tuple[float, float]:
        """(Shadbala ratio, Iṣṭa−Kaṣṭa valence in −1..+1)."""
        sb = self.shad.get(planet)
        ratio = sb.ratio if sb else 0.5
        ik = self.ik.get(planet)
        val = (ik.ishta - ik.kashta) / 60.0 if ik else 0.0
        return ratio, val

    def is_benefic(self, planet: Planet) -> bool:
        n = self.nature.get(planet)
        if n is not None:
            return n in ("Benefic", "Yogakaraka")
        return natural_benefic(planet)

    # -- witnesses ------------------------------------------------------- #
    def w_natal_lords(self) -> None:
        for d in DOMAINS:
            for h in d.houses:
                lord = self.house_lord(h)
                ratio, val = self.strength(lord)
                w = W_LORD * min(1.5, ratio) * (0.6 + 0.4 * (h == d.houses[0]))
                if ratio >= STRONG_RATIO and val >= 0:
                    self.scores[d.key].add("lord", +1, w,
                        f"H{h} lord {lord.value} strong (ratio {ratio:.2f})")
                elif ratio < STRONG_RATIO * 0.7 or val < -0.15:
                    self.scores[d.key].add("lord", -1, w * 0.8,
                        f"H{h} lord {lord.value} weak/afflicted (ratio {ratio:.2f})")

    def w_occupants(self) -> None:
        for d in DOMAINS:
            for h in d.houses:
                for p in self.c.planets_in_house(h):
                    if p not in self.shad and p not in (Planet.RAHU, Planet.KETU):
                        continue
                    benefic = self.is_benefic(p)
                    # manifestation semantics: a malefic in an adverse-event
                    # house manifests the event; a benefic there averts it.
                    manifests = benefic if not d.malefic_event else (not benefic)
                    pol = +1 if manifests else -1
                    self.scores[d.key].add("occupant", pol, W_OCCUPANT,
                        f"{p.value} occupies H{h}")

    def w_argala(self) -> None:
        from .jaimini import argala_on_sign
        vedic = {p: self.signs[p] for p in self.shad}
        vedic[Planet.RAHU] = self.signs[Planet.RAHU]
        vedic[Planet.KETU] = self.signs[Planet.KETU]
        for d in DOMAINS:
            ref = self.house_sign(d.houses[0])
            for a in argala_on_sign(ref, vedic):
                if a.effective and a.causers:
                    self.scores[d.key].add("argala", +1, W_ARGALA,
                        f"Argala on H{d.houses[0]} from {a.house}H")
                elif a.counterers and len(a.counterers) > len(a.causers):
                    self.scores[d.key].add("argala", -1, W_ARGALA * 0.8,
                        f"Virodhārgala obstructs H{d.houses[0]} from {a.counter_house}H")

    def w_karakas(self) -> None:
        for d in DOMAINS:
            for k in d.karakas:
                ratio, val = self.strength(k)
                if k in (Planet.RAHU, Planet.KETU):
                    self.scores[d.key].add("karaka", +1, W_KARAKA * 0.6,
                        f"node kāraka {k.value} present")
                    continue
                if ratio >= STRONG_RATIO and val >= 0:
                    self.scores[d.key].add("karaka", +1, W_KARAKA,
                        f"kāraka {k.value} strong")
                elif val < -0.15:
                    self.scores[d.key].add("karaka", -1, W_KARAKA * 0.8,
                        f"kāraka {k.value} afflicted (Kaṣṭa)")

    def w_varga(self) -> None:
        for d in DOMAINS:
            try:
                vc = self.c.varga(d.varga)
            except Exception:
                continue
            lord = self.house_lord(d.houses[0])
            if lord not in vc.signs:
                continue
            hv = (vc.signs[lord] - vc.ascendant_sign) % 12 + 1
            if hv in KENDRA or hv in TRIKONA:
                self.scores[d.key].add("varga", +1, W_VARGA,
                    f"D{d.varga}: H{d.houses[0]} lord in kendra/trikoṇa (H{hv})")
            elif hv in DUSTHANA:
                self.scores[d.key].add("varga", -1, W_VARGA,
                    f"D{d.varga}: H{d.houses[0]} lord in dusthāna (H{hv})")

    def w_avastha(self) -> None:
        """Mood (Dīptādi) blockade — §3 Step-2. A Khala/Vikala/Dukhita lord or
        kāraka corrupts the house promise (a Track-B cancellation signature)."""
        for d in DOMAINS:
            actors = {self.house_lord(d.houses[0])} | set(d.karakas)
            for p in actors:
                mood = self.moods.get(p)
                if mood in GOOD_MOODS:
                    self.scores[d.key].add("avastha", +1, W_AVASTHA,
                        f"{p.value} in {mood} (radiant)")
                elif mood in BAD_MOODS:
                    self.scores[d.key].add("avastha", -1, W_AVASTHA,
                        f"{p.value} in {mood} (mood blockade)")

    def w_aspect(self) -> None:
        """Graha Dṛṣṭi onto the domain houses — §3 Step-2 aspectual geometry."""
        for a in self.aspects:
            house = (a.to_sign - self.asc) % 12 + 1
            benefic = self.is_benefic(a.planet)
            for d in DOMAINS:
                if house in d.houses:
                    manifests = benefic if not d.malefic_event else (not benefic)
                    self.scores[d.key].add("aspect", +1 if manifests else -1,
                        W_ASPECT, f"{a.planet.value} aspects H{house}")

    def w_chalit(self) -> None:
        """Bhāva-Chalit (Placidus) shift — §2.5/§3 Step-2. A planet whose
        physical result-house moves out of the domain weakens it; into it
        strengthens it."""
        for p, pl in self.chalit.items():
            if not pl.shifted or (p not in self.shad
                                  and p not in (Planet.RAHU, Planet.KETU)):
                continue
            r, cc = pl.rashi_house, pl.chalit_house
            for d in DOMAINS:
                if r in d.houses and cc not in d.houses:
                    self.scores[d.key].add("chalit", -1, W_CHALIT,
                        f"{p.value} result shifts H{r}→H{cc} (out of domain)")
                elif cc in d.houses and r not in d.houses:
                    self.scores[d.key].add("chalit", +1, W_CHALIT,
                        f"{p.value} result shifts H{r}→H{cc} (into domain)")

    def w_sav(self) -> None:
        for d in DOMAINS:
            for h in d.houses:
                bindus = self.sav[self.house_sign(h)]
                if bindus >= SAV_HIGH:
                    self.scores[d.key].add("sav", +1, W_SAV,
                        f"SAV H{h}={bindus} (high)")
                elif bindus <= SAV_LOW:
                    self.scores[d.key].add("sav", -1, W_SAV,
                        f"SAV H{h}={bindus} (depleted)")

    def w_yoga(self) -> None:
        """Natal yogas → domain promise (Rāja/Dhana/Mahāpuruṣa, etc.)."""
        for y in self.c.yogas():
            hit = False
            for key, maps in YOGA_MAP.items():
                if key in y.name:
                    for dk, pol in maps:
                        self.scores[dk].add("yoga", pol, W_YOGA, y.name)
                    hit = True
                    break
            if hit:
                continue
            if y.kind == "Raja":
                self.scores["career"].add("yoga", +1, W_YOGA, y.name)
            elif y.kind == "Dhana":
                self.scores["wealth"].add("yoga", +1, W_YOGA, y.name)
            elif y.kind == "Mahapurusha":
                self.scores["career"].add("yoga", +1, W_YOGA, y.name)

    def w_arudha(self) -> None:
        """Arudha pada of the domain's primary house — its worldly manifestation.
        Benefic occupants project the theme, malefics distort it (§2.6)."""
        occ_by_sign: dict[int, list[Planet]] = {}
        for p in list(self.shad) + [Planet.RAHU, Planet.KETU]:
            occ_by_sign.setdefault(self.signs[p], []).append(p)
        ar = self.c.arudhas()
        for d in DOMAINS:
            pada = ar.get(f"A{d.houses[0]}")
            if pada is None:
                continue
            for p in occ_by_sign.get(pada, []):
                benefic = self.is_benefic(p)
                manifests = benefic if not d.malefic_event else (not benefic)
                self.scores[d.key].add("arudha", +1 if manifests else -1,
                    W_ARUDHA, f"{p.value} in Arudha A{d.houses[0]}")

    def w_charakaraka(self) -> None:
        """Jaimini chara-kāraka placement (e.g. DK for marriage, AmK career)."""
        ck = self.c.chara_karakas()
        for d in DOMAINS:
            if not d.chara_karaka:
                continue
            p = ck.get(d.chara_karaka)
            if p is None:
                continue
            if self.occupies_house(p, d.houses) or self.rules_house(p, d.houses):
                self.scores[d.key].add("charakaraka", +1, W_CHARAKARAKA,
                    f"{d.chara_karaka} {p.value} on a domain house")
            if p in (Planet.RAHU, Planet.KETU):
                continue
            ratio, val = self.strength(p)
            if ratio >= STRONG_RATIO and val >= 0:
                self.scores[d.key].add("charakaraka", +1, W_CHARAKARAKA * 0.7,
                    f"{d.chara_karaka} {p.value} strong")
            elif val < -0.15:
                self.scores[d.key].add("charakaraka", -1, W_CHARAKARAKA * 0.7,
                    f"{d.chara_karaka} {p.value} afflicted")

    def w_vimsopaka(self) -> None:
        """Vaiśeṣikāṃśa (multi-varga) strength of the domain lord and kārakas."""
        for d in DOMAINS:
            actors = {self.house_lord(d.houses[0])} | set(d.karakas)
            for p in actors:
                if p in (Planet.RAHU, Planet.KETU):
                    continue
                grade = self.c.vaiseshikamsa(p)
                if grade in HIGH_VAISESHIKA:
                    self.scores[d.key].add("vimsopaka", +1, W_VIMSOPAKA,
                        f"{p.value} {grade} (varga-strong)")
                elif grade in LOW_VAISESHIKA:
                    self.scores[d.key].add("vimsopaka", -1, W_VIMSOPAKA,
                        f"{p.value} {grade} (varga-weak)")

    def w_vimshottari(self) -> None:
        chain = self.c.current_dasha("vimshottari", self.mid)
        for period in chain[:3]:
            lvl = period.level
            lord = period.lord
            w = W_DASHA.get(lvl, 0.4)
            for d in DOMAINS:
                if (self.rules_house(lord, d.houses)
                        or self.occupies_house(lord, d.houses)
                        or lord in d.karakas):
                    self.scores[d.key].add("vimshottari", +1, w,
                        f"L{lvl} lord {lord.value} activates domain")
                elif (self.rules_house(lord, d.negation)
                        or self.occupies_house(lord, d.negation)):
                    self.scores[d.key].add("vimshottari", -1, w * 0.6,
                        f"L{lvl} lord {lord.value} ties to negation house")

    def w_rashi_dasha(self) -> None:
        for name, func in (("Nārāyaṇa", self.c.narayana_dasha),
                           ("Chara", self.c.chara_dasha),
                           ("Sudasā", self.c.sudasa_dasha)):
            try:
                periods = func(cycles=3)
            except TypeError:
                periods = func()
            active = next((p for p in periods
                           if p.start <= self.mid < p.end), None)
            if active is None:
                continue
            try:
                sign = SIGNS.index(active.note)
            except (ValueError, AttributeError):
                continue
            rel_house = (sign - self.asc) % 12 + 1
            lord = active.lord
            for d in DOMAINS:
                if (rel_house in d.houses or self.rules_house(lord, d.houses)
                        or lord in d.karakas):
                    self.scores[d.key].add("rashi_dasha", +1, W_RASHI_DASHA,
                        f"{name} {active.note} (H{rel_house}) activates domain")

    def w_gochara(self) -> None:
        movers = self.tr.slow_movers(self.mid)
        for p, info in movers.items():
            h = info["house_from_lagna"]
            benefic = self.is_benefic(p)
            for d in DOMAINS:
                if h in d.houses:
                    self.scores[d.key].add("gochara", +1, W_GOCHARA,
                        f"transit {p.value} in H{h} (SAV {info['sav']})")
                    # malefic pressure on a benefic domain's anchor = friction
                    if not benefic and not d.malefic_event and h == d.houses[0]:
                        self.scores[d.key].add("gochara", -1, W_GOCHARA * 0.5,
                            f"malefic {p.value} pressures H{h}")

    def w_kp(self) -> None:
        """KP sub-lord verdict (§3 Step-3.2, the ultimate negation tool).

        For the active Mahā/Antar lords, take the *sub-lord* of their natal
        longitude and read what it signifies: fulfilment houses ⇒ manifestation,
        negation houses ⇒ obstruction, BOTH ⇒ the 'fixed-then-cancelled' texture.
        """
        from .kp import kp_chain
        try:
            kps = self.c.kp_significators()
        except Exception:
            return
        for period in self.c.current_dasha("vimshottari", self.mid)[:2]:
            lord = period.lord
            sub = kp_chain(self.c.longitudes[lord]).sub_lord
            for d in DOMAINS:
                fulfil = kps.signifies_any(sub, d.houses)
                negate = kps.signifies_any(sub, d.negation)
                if fulfil and negate:
                    self.scores[d.key].add("kp", -1, W_KP * 0.6,
                        f"L{period.level} {lord.value}→sub {sub.value} signifies "
                        f"both fulfil & negation (cancellation signature)")
                elif fulfil:
                    self.scores[d.key].add("kp", +1, W_KP,
                        f"L{period.level} {lord.value}→sub {sub.value} signifies fulfilment")
                elif negate:
                    self.scores[d.key].add("kp", -1, W_KP,
                        f"L{period.level} {lord.value}→sub {sub.value} signifies negation")

    def w_varshaphal(self) -> None:
        """Varṣaphal (Tājika annual) witness — the Muntha's house is the year's
        live theme; the Muntha/Varṣa-lagna lords tie it to natal domains."""
        try:
            ann = self._annual(self.mid.year)
        except Exception:
            return
        for d in DOMAINS:
            if ann.muntha_house in d.houses:
                self.scores[d.key].add("varshaphal", +1, W_VARSHAPHAL,
                    f"Muntha in H{ann.muntha_house} this Varṣa")
            if (self.rules_house(ann.muntha_lord, d.houses)
                    or self.rules_house(ann.lagna_lord, d.houses)):
                self.scores[d.key].add("varshaphal", +1, W_VARSHAPHAL * 0.6,
                    f"Varṣeśa ({ann.muntha_lord.value}/{ann.lagna_lord.value}) "
                    f"rules a domain house")

    def w_maraka(self) -> None:
        """Maraka planets reinforce the adverse-event (health/litigation)
        domains when they sit on a domain house (§2.2 maraka doctrine)."""
        marakas = set(self.c.marakas())
        for d in DOMAINS:
            if not d.malefic_event:
                continue
            for p in marakas:
                if self.occupies_house(p, d.houses):
                    self.scores[d.key].add("maraka", +1, W_MARAKA,
                        f"maraka {p.value} on a domain house")

    # -- timing ---------------------------------------------------------- #
    def _windows_for(self, d: Domain) -> list:
        """Timing for a domain over [start, end]: coarse slow-gochara house
        windows always; on short (event-scale) spans also the BNN degree-to-
        degree conjunctions to the domain's natal kārakas/lord and the Kakṣyā
        4–5-day narrowing — the §3 Step-3.3/3.4 precision triggers."""
        out = []
        movers = (Planet.SATURN, Planet.JUPITER, Planet.RAHU, Planet.KETU)
        for p in movers:
            for h in d.houses[:2]:
                out += self.tr.house_windows(p, h, self.start, self.end,
                                             step_days=15)
        span_days = (self.end - self.start).days
        if span_days <= 400:                       # event-scale: add precision
            targets = {k: self.c.longitudes[k] for k in d.karakas
                       if k in self.c.longitudes}
            lord = self.house_lord(d.houses[0])
            if lord in self.c.longitudes:
                targets[lord] = self.c.longitudes[lord]
            for p in (Planet.SATURN, Planet.JUPITER):
                for name, tgt in targets.items():
                    out += self.tr.conjunction_windows(
                        p, tgt, self.start, self.end, orb=2.0, step_days=6)
            out += self.tr.kakshya_windows(Planet.SATURN, self.start,
                                           self.end, step_days=4)
        out.sort(key=lambda w: w.start)
        return out[:10]

    # -- orchestration --------------------------------------------------- #
    _STATIC = ("w_natal_lords", "w_occupants", "w_argala", "w_karakas",
               "w_varga", "w_sav", "w_avastha", "w_aspect", "w_chalit",
               "w_yoga", "w_arudha", "w_charakaraka", "w_vimsopaka", "w_maraka")
    _DYNAMIC = ("w_vimshottari", "w_rashi_dasha", "w_gochara", "w_kp",
                "w_varshaphal")

    def _prepare_static(self) -> None:
        """Compute the lifelong (window-independent) votes exactly once."""
        for name in self._STATIC:
            getattr(self, name)()
        self._static_votes = {k: list(s.votes) for k, s in self.scores.items()}

    @staticmethod
    def _normalise(scores: list[DomainScore]) -> None:
        """Field-relative salience: min-max raw_score across converged domains
        so the ranking SEPARATES rather than saturating near 1. This answers
        'which domain stands out', not an absolute probability."""
        conv = [s for s in scores if s.converged]
        if not conv:
            return
        hi = max(s.raw_score for s in conv)
        lo = min(s.raw_score for s in conv)
        span = hi - lo or 1.0
        for s in conv:
            s.confidence = round(0.30 + 0.70 * (s.raw_score - lo) / span, 3)

    def _score_at(self, mid: datetime) -> list[DomainScore]:
        """Snapshot the ranked domains at a given mid-date (reuses static votes)."""
        if not hasattr(self, "_static_votes"):
            self._prepare_static()
        self.mid = mid
        self.scores = {d.key: DomainScore(d, votes=list(self._static_votes[d.key]))
                       for d in DOMAINS}
        for name in self._DYNAMIC:
            getattr(self, name)()
        scores = list(self.scores.values())
        self._normalise(scores)
        return sorted(scores, key=lambda s: (s.converged, s.raw_score),
                      reverse=True)

    def run(self) -> Triangulation:
        ranked = self._score_at(self.mid)
        top = [s for s in ranked if s.converged][:3]
        windows = {s.domain.key: self._windows_for(s.domain) for s in top}
        return Triangulation(self.start, self.end, ranked, windows)

    def timeline(self, width_days: int = 183, step_days: int = 30) -> "TimelineResult":
        """Slide a short window across [start, end] and detect when each theme
        peaks — turning a multi-year sweep into discrete, dated events."""
        self._prepare_static()
        half = timedelta(days=width_days / 2)
        step = timedelta(days=step_days)
        samples: list[Sample] = []
        cursor = self.start + half
        last = self.end - half
        if last < cursor:
            last = cursor
        while cursor <= last:
            ranked = self._score_at(cursor)
            lead = next((s for s in ranked if s.converged), None)
            samples.append(Sample(
                mid=cursor,
                scores={s.domain.key: (s.raw_score if s.converged else 0.0)
                        for s in ranked},
                lead=lead.domain.key if lead else None,
                lead_conf=lead.confidence if lead else 0.0,
                lead_texture=lead.texture if lead else "",
            ))
            cursor += step

        # Per-domain peak detection: for each promised domain, find the local
        # maxima of ITS OWN activation series (against its own baseline). This
        # localizes each theme's event(s) independently, instead of letting the
        # two highest-promise domains monopolise a cross-domain "lead".
        import statistics
        events: list[TimelineEvent] = []
        for d in DOMAINS:
            vals = [s.scores.get(d.key, 0.0) for s in samples]
            pos = [v for v in vals if v > 0]
            if len(pos) < 1:
                continue                       # never converged in the span
            mean = statistics.mean(pos)
            spread = statistics.pstdev(pos) if len(pos) > 1 else 0.0
            thr = mean + 0.4 * spread          # prominence floor
            # Contiguous above-threshold runs = distinct events (separated by
            # genuine valleys); plateaus collapse to their single peak.
            peaks = []
            i, n = 0, len(vals)
            while i < n:
                if vals[i] > 0 and vals[i] >= thr:
                    j = i
                    while j + 1 < n and vals[j + 1] > 0 and vals[j + 1] >= thr:
                        j += 1
                    v, mid = max((vals[k], samples[k].mid) for k in range(i, j + 1))
                    peaks.append((v, mid))
                    i = j + 1
                else:
                    i += 1
            for v, mid in sorted(peaks, reverse=True)[:3]:   # ≤3 events/theme
                ranked = self._score_at(mid)
                ds = next(s for s in ranked if s.domain.key == d.key)
                events.append(TimelineEvent(
                    domain=d, peak=mid,
                    window_start=mid - half, window_end=mid + half,
                    score=v, texture=ds.texture))
        events.sort(key=lambda e: e.peak)
        return TimelineResult(self.start, self.end, width_days, step_days,
                              samples, events, self)




# --------------------------------------------------------------------------- #
# Dossier rendering
# --------------------------------------------------------------------------- #
def _render(t: Triangulation) -> str:
    L: list[str] = []
    L.append("# BLIND TRIANGULATION DOSSIER")
    L.append(f"Window: {t.start:%Y-%m-%d} → {t.end:%Y-%m-%d}")
    active = t.active
    if not active:
        L.append("\nNo domain reached the convergence threshold "
                 f"(≥{MIN_FAMILIES} independent paddhatis). No blind call made.")
        return "\n".join(L)

    top = active[0]
    L.append("")
    L.append("## Committed call (most-likely event)")
    L.append(f"- **Domain:** {top.domain.label}")
    L.append(f"- **Texture:** {top.texture}")
    L.append(f"- **Confidence:** {top.confidence:.2f} ({top.band})  "
             f"[support {top.support:.1f} vs obstruction {top.obstruction:.1f}, "
             f"{len(top.support_families)} paddhatis]")
    wins = t.windows.get(top.domain.key, [])
    if wins:
        L.append("- **Candidate timing windows (slow gochara over domain houses):**")
        for w in wins[:5]:
            L.append(f"    {w}")

    # tied forms: other converged domains within a small confidence delta
    ties = [s for s in active[1:] if top.confidence - s.confidence <= 0.12]
    if ties:
        L.append("- **Tied / overlapping categories:** "
                 + ", ".join(f"{s.domain.label} ({s.confidence:.2f})" for s in ties))

    L.append("")
    L.append("## All converged domains (ranked)")
    L.append(f"  {'Domain':<26}{'Conf':<7}{'Band':<10}{'Net':<7}{'Paddhatis':<10}Texture")
    L.append("  " + "-" * 88)
    for s in active:
        L.append(f"  {s.domain.label:<26}{s.confidence:<7.2f}{s.band:<10}"
                 f"{s.net:<7.1f}{len(s.support_families):<10}{s.texture}")

    L.append("")
    L.append("## Witness ledger (why — top domain)")
    for v in sorted(top.votes, key=lambda v: (-v.polarity, -v.weight)):
        sign = "＋" if v.polarity > 0 else "－"
        L.append(f"  {sign} [{v.family:<12}] {v.weight:.2f}  {v.reason}")
    return "\n".join(L)


def _render_timeline(t: TimelineResult) -> str:
    L: list[str] = []
    L.append("# TRIANGULATION TIMELINE (theme peaks across the span)")
    L.append(f"Window: {t.start:%Y-%m-%d} → {t.end:%Y-%m-%d}  "
             f"(sliding {t.width_days}d / step {t.step_days}d)")
    if not t.events:
        L.append("\nNo domain led any sub-window (nothing converged).")
        return "\n".join(L)
    # Group by domain, strongest theme first, peaks chronological within.
    by_domain: dict[str, list[TimelineEvent]] = {}
    for e in t.events:
        by_domain.setdefault(e.domain.key, []).append(e)
    order = sorted(by_domain.values(),
                   key=lambda evs: max(e.score for e in evs), reverse=True)
    L.append("")
    L.append("## Theme peaks (narrow to a theme → its candidate event dates)")
    for evs in order:
        evs.sort(key=lambda e: e.peak)
        dom = evs[0].domain
        L.append(f"\n● {dom.label}")
        for e in evs:
            L.append(f"    Peak {e.peak:%Y-%m-%d}  "
                     f"[{e.window_start:%Y-%m-%d}→{e.window_end:%Y-%m-%d}]  "
                     f"salience {e.score:.2f} · {e.texture}")
            for w in e.timing[:3]:
                L.append(f"        ⟶ {w}")
    return "\n".join(L)
