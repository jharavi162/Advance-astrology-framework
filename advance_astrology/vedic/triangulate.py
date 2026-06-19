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
from datetime import datetime, timezone

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
STATIC_FAMILIES = {"lord", "occupant", "argala", "karaka", "varga", "sav"}
DYNAMIC_FAMILIES = {"vimshottari", "rashi_dasha", "gochara", "kp"}


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
        self.scores = {d.key: DomainScore(d) for d in DOMAINS}

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
        try:
            kps = self.c.kp_significators()
        except Exception:
            return
        md = self.c.current_dasha("vimshottari", self.mid)[0].lord
        for d in DOMAINS:
            sig_fulfil = any(md in kps.house_significators(h) for h in d.houses)
            sig_negate = any(md in kps.house_significators(h) for h in d.negation)
            if sig_fulfil and not sig_negate:
                self.scores[d.key].add("kp", +1, W_KP,
                    f"KP: period lord {md.value} signifies fulfilment houses")
            elif sig_negate and not sig_fulfil:
                self.scores[d.key].add("kp", -1, W_KP,
                    f"KP: period lord {md.value} signifies negation houses")

    # -- timing ---------------------------------------------------------- #
    def _windows_for(self, d: Domain) -> list:
        out = []
        movers = (Planet.SATURN, Planet.JUPITER, Planet.RAHU, Planet.KETU)
        for p in movers:
            for h in d.houses[:2]:
                out += self.tr.house_windows(p, h, self.start, self.end,
                                             step_days=15)
        out.sort(key=lambda w: w.start)
        return out[:8]

    # -- orchestration --------------------------------------------------- #
    def run(self) -> Triangulation:
        for w in (self.w_natal_lords, self.w_occupants, self.w_argala,
                  self.w_karakas, self.w_varga, self.w_sav, self.w_vimshottari,
                  self.w_rashi_dasha, self.w_gochara, self.w_kp):
            w()
        all_scores = list(self.scores.values())
        # Field-relative salience: min-max normalise raw_score across converged
        # domains so the ranking SEPARATES rather than saturating near 1. This
        # answers "which domain stands out in this window", not an absolute
        # probability (we make no calibrated-probability claim).
        conv = [s for s in all_scores if s.converged]
        if conv:
            hi = max(s.raw_score for s in conv)
            lo = min(s.raw_score for s in conv)
            span = hi - lo or 1.0
            for s in conv:
                s.confidence = round(0.30 + 0.70 * (s.raw_score - lo) / span, 3)
        ranked = sorted(all_scores,
                        key=lambda s: (s.converged, s.raw_score), reverse=True)
        # Timing windows only for the top calls (the only ones rendered).
        top = [s for s in ranked if s.converged][:3]
        windows = {s.domain.key: self._windows_for(s.domain) for s in top}
        return Triangulation(self.start, self.end, ranked, windows)


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
