"""Domain-general triangulation evidence builder (Playbook Phases 2-4).

This automates the *mechanical* half of AI_TRIANGULATION_PROMPT.md so that the
recurring causes of timing-misses can never be silently skipped — and it does so
for **any** life-area, not marriage only. The triangulation machinery is computed
identically for every domain; only a small declarative ``DomainProfile`` changes
per question.

It deliberately draws on the WHOLE toolkit the prompt mandates, in two layers:

  • PROMISE & TEMPO (computed once per domain) — Ṣaḍbala / Iṣṭa-Kaṣṭa strength of
    the house-lord and the kāraka, their Avasthā mood, the varga (D9/D10/D30…)
    placement that confirms the TYPE, the Argala vs Virodhārgala on the matter's
    house, functional nature, the Arudha, and the SAV of the house — together
    deciding whether the matter is promised at all and whether its tempo is
    early / on-time / late / denied.

  • PER-WINDOW TIMING (the full-span candidate ledger) — KP fulfil/negate of the
    running MD>AD>PD, the kāraka surfacing at sūkṣma, the Lagna/Lagnesh
    materialization, the Jupiter+Saturn double-transit on the house AND its lord,
    the BNN degree-trigger, the Kakṣyā narrowing, the domain Saham double-transit,
    the chara antardaśā, the Sudarśana wheels and the Varṣaphal Muntha of the
    year — counted into a convergence score and ranked.

A REVERSAL (divorce / job-loss / relapse) is timed as its OWN event from the
negation significators, never inferred away.

Division of labour is preserved: the engine assembles a COMPLETE evidence pack;
the AI still does the multivalent synthesis on top (a node colours the event's
TYPE, a dark Lagna lowers materialization-INTENSITY rather than denying a
Saham/kāraka-lit event, a strong benefic does not veto a converged reversal).

    python -m interpreter.event_evidence --domain marriage \
        --when "YYYY-MM-DD HH:MM" --lat <LAT> --lon <LON> \
        --start <START> --end <END>
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from advance_astrology import VedicChart, Planet
from advance_astrology.constants import SIGNS
from advance_astrology.vedic.ashtakavarga import (
    ASHTAKAVARGA_PLANETS as _ASHTAKAVARGA_PLANETS,
)

UTC = timezone.utc

# Jupiter's special aspects fall on the 5th/7th/9th, Saturn's on the 3rd/7th/10th
# (sign-offsets). Used so a *glance* counts, not only bodily occupation.
_ASPECT_OFFSETS = {Planet.JUPITER: (4, 6, 8), Planet.SATURN: (2, 6, 9)}
_KENDRA_TRIKONA = {1, 4, 5, 7, 9, 10}
_SIGN_RULER = [Planet.MARS, Planet.VENUS, Planet.MERCURY, Planet.MOON, Planet.SUN,
               Planet.MERCURY, Planet.VENUS, Planet.MARS, Planet.JUPITER,
               Planet.SATURN, Planet.SATURN, Planet.JUPITER]
_EXALT_SIGN = {Planet.SUN: 0, Planet.MOON: 1, Planet.MARS: 9, Planet.MERCURY: 5,
               Planet.JUPITER: 3, Planet.VENUS: 11, Planet.SATURN: 6}
_MALEFIC_NODES = {Planet.SATURN, Planet.RAHU, Planet.KETU, Planet.MARS, Planet.SUN}
_NAT_BENEFIC = {Planet.JUPITER, Planet.VENUS, Planet.MERCURY, Planet.MOON}
_NAT_MALEFIC = {Planet.SATURN, Planet.MARS, Planet.SUN, Planet.RAHU, Planet.KETU}


# ---------------------------------------------------------------------------- #
# WITNESS / NODE REGISTRY — an open list of independent testimonies. A verdict
# (manifest vs cancel, upgrade vs loss) is the WEIGHTED CONVERGENCE of every
# witness that fires, never one rule. Each witness votes a signed strength in
# [-1, +1] (pro = +, anti = -); the engine multiplies by its weight and sums.
# Adding a new node = one register_witness(...) call, not a logic rewrite.
# ---------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Witness:
    name: str
    layer: str                 # "standing" (natal, time-independent) | "timing"
    weight: float
    vote: object               # standing: callable(v, profile); timing: callable(window)
    shared: bool = False        # timing node shared across domains (e.g. Lagna)


WITNESSES: list[Witness] = []


def register_witness(name, layer, weight, vote, shared=False) -> Witness:
    w = Witness(name, layer, weight, vote, shared)
    WITNESSES.append(w)
    return w


# ---------------------------------------------------------------------------- #
# WITNESS FAMILIES — generative nodes. A family is a builder(profile) -> list of
# Witnesses, so one entry instantiates the WHOLE element × technique cross-product
# for whatever the question points at (e.g. one "significator running" node per
# daśā system in the catalogue). This is how the panel covers any domain WITHOUT
# hand-registering a node each time: add a system/technique as DATA, and every
# domain gets it for free. build_panel(profile) = the static WITNESSES plus all
# family-generated witnesses for that domain.
# ---------------------------------------------------------------------------- #
FAMILIES: list = []


def register_family(name, builder) -> None:
    """builder(profile) -> list[Witness]; called once per domain to materialise
    the family's concrete nodes for that matter."""
    FAMILIES.append((name, builder))


_PANEL_CACHE: dict = {}


def build_panel(profile) -> list:
    """All witnesses judging this matter = static nodes + every family's nodes."""
    if profile.name not in _PANEL_CACHE:
        panel = list(WITNESSES)
        for _name, builder in FAMILIES:
            panel.extend(builder(profile))
        _PANEL_CACHE[profile.name] = panel
    return _PANEL_CACHE[profile.name]


def _house_signs(v, profile):
    return [(v.ascendant_sign + h - 1) % 12 for h in profile.houses]


def _aspectors(v, signs):
    out = {}
    for a in v.graha_aspects():
        if a.to_sign in signs and a.planet in (_NAT_BENEFIC | _NAT_MALEFIC):
            out.setdefault(a.planet, a)
    return out


# --- seed STANDING (natal) witnesses — the multi-nodal pattern on the matter --
def _w_benefic_drishti(v, p):
    asp = _aspectors(v, set(_house_signs(v, p)))
    return min(1.0, 0.5 * sum(1 for x in asp if x in _NAT_BENEFIC))


def _w_malefic_drishti(v, p):
    asp = _aspectors(v, set(_house_signs(v, p)))
    return -min(1.0, 0.5 * sum(1 for x in asp if x in _NAT_MALEFIC))


def _w_lord_dignity(v, p):
    score = 0.0
    sb = v.shadbala()
    for h in p.houses:
        lord = v.house_lord(h)
        dig = str(v.dignity(lord))
        if any(k in dig for k in ("Exalt", "Own", "Moolatrikona")):
            score += 1
        elif "Debil" in dig:
            score -= 1
        s = sb.get(lord)
        score += 0.5 if (s and s.is_strong) else -0.5
    return max(-1.0, min(1.0, score / (len(p.houses) or 1)))


def _w_occupant_nature(v, p):
    score = 0.0
    for h in p.houses:
        for x in v.planets_in_house(h):
            score += 0.5 if x in _NAT_BENEFIC else (-0.5 if x in _NAT_MALEFIC else 0)
    return max(-1.0, min(1.0, score))


def _w_rajayoga_lord(v, p):
    """Raja/Mahāpuruṣa-like: the house-lord dignified in a kendra/trikoṇa."""
    for h in p.houses:
        lord = v.house_lord(h)
        if (v.house_of(lord) in _KENDRA_TRIKONA
                and any(k in str(v.dignity(lord)) for k in ("Exalt", "Own", "Moolatrikona"))):
            return 1.0
    return 0.0


def _w_argala(v, p):
    return max(-1.0, min(1.0, _argala_net_on_house(v, p.houses[0]) / 2))


def _w_sav(v, p):
    sav = v.sarvashtakavarga()
    avg = sum(sav[(v.ascendant_sign + h - 1) % 12] for h in p.houses) / len(p.houses)
    if avg >= 30:
        return min(1.0, (avg - 28) / 8)
    if avg <= 25:
        return -min(1.0, (28 - avg) / 8)
    return 0.0


register_witness("benefic-dṛṣṭi-on-house", "standing", 1.0, _w_benefic_drishti)
register_witness("malefic-dṛṣṭi-on-house", "standing", 0.8, _w_malefic_drishti)
register_witness("house-lord-dignity/strength", "standing", 1.2, _w_lord_dignity)
register_witness("occupant-nature", "standing", 0.8, _w_occupant_nature)
register_witness("rāja-yoga (lord dignified in kendra/trikoṇa)", "standing", 1.2, _w_rajayoga_lord)
register_witness("argala-net", "standing", 0.8, _w_argala)
register_witness("SAV-of-house", "standing", 0.8, _w_sav)


# --- standing witnesses for previously-COMPUTED-BUT-UNWIRED quantities -------
# (avasthā moods, Vaiśeṣikāṃśa multi-varga grade, maraka) — each reads the
# matter's lords/kārakas, domain-general, never a native.
_VAISESHIKAMSA_RANK = {"Adhama": 1, "Parijata": 2, "Uttama": 3, "Gopura": 4,
                       "Simhasana": 5, "Paravata": 6, "Devaloka": 7,
                       "Brahmaloka": 8, "Airavata": 9, "Sridhama": 10}


def _matter_planets(v, p):
    """The matter's significating grahas: house-lords + kārakas."""
    return {v.house_lord(h) for h in p.houses} | _karaka_planets(v, p)


def _w_avastha_affliction(v, p):
    """Track-B: occupants/lords/kārakas in a dead/troubled avasthā (BPHS)."""
    bad_bala, bad_deepta = {"Mrita", "Vriddha"}, {"Khala", "Vikala", "Dukhita"}
    nine = _NAT_BENEFIC | _NAT_MALEFIC                 # the 9 grahas (no outer planets)
    planets = set(_matter_planets(v, p))
    for h in p.houses:
        planets |= set(v.planets_in_house(h))
    hit = sum(1 for pl in (planets & nine)
              if v.avasthas(pl).get("baladi") in bad_bala
              or v.avasthas(pl).get("deeptadi") in bad_deepta
              or v.avasthas(pl).get("combust") == "Yes")
    return -min(1.0, 0.5 * hit)


def _w_vaiseshikamsa(v, p):
    """Promise: multi-varga (Vaiśeṣikāṃśa) grade of the matter's lords/kārakas."""
    ranks = [_VAISESHIKAMSA_RANK.get(v.vaiseshikamsa(pl), 1)
             for pl in _matter_planets(v, p)]
    if not ranks:
        return 0.0
    return max(-1.0, min(1.0, (sum(ranks) / len(ranks) - 5) / 4))


def _w_maraka(v, p):
    """Maraka affliction — only for adverse-longevity matters (primary 6/8)."""
    if not ({6, 8} & set(p.houses)):
        return 0.0
    return -1.0 if (set(v.marakas()) & _matter_planets(v, p)) else 0.0


register_witness("avasthā affliction (Mṛta/Khala/combust)", "standing", 0.8, _w_avastha_affliction)
register_witness("Vaiśeṣikāṃśa grade (multi-varga strength)", "standing", 1.0, _w_vaiseshikamsa)
register_witness("maraka afflicts the matter", "standing", 0.8, _w_maraka)


# --- BNN QUALITY standing witnesses (user-approved 2026-07-06; distilled in
# docs/knowledge/bnn/02_marriage.md). Domain-general — each reads the matter's
# kāraka / descriptor, never a native. These shade the NATURE of the outcome
# (quality/promise), never time it; soft weights, and #2/#3 are dormant where a
# matter has no distinct descriptor / clean kāraka. -------------------------- #
def _w_jiva_12th_from_karaka(v, p):
    """BNN: the Jīva (Jupiter, the enjoyer of results) in the 12th (loss) sign
    FROM the matter's kāraka drains the enjoyment of that matter (R.G. Rao —
    Jupiter 12th-to-Venus = unhappy marriage). Dormant when the kāraka IS Jupiter
    (it cannot be 12th from itself)."""
    k = p.natural_karaka
    if k is None or k == Planet.JUPITER:
        return 0.0
    return -0.6 if (v.signs[Planet.JUPITER] - v.signs[k]) % 12 == 11 else 0.0


def _w_karaka_12th_from_descriptor(v, p):
    """BNN: the event-kāraka in the 12th FROM the matter's descriptor graha
    delays the matter (R.G. Rao — Venus 12th-to-Mars = delayed marriage). Uses
    the Nāḍī event-kāraka vs the gender/nature descriptor; dormant when the two
    coincide (no distinct descriptor for the matter)."""
    event, desc = nadi_timing_karaka(v, p), nadi_karaka(v, p)
    if event == desc:
        return 0.0
    return -0.5 if (v.signs[event] - v.signs[desc]) % 12 == 11 else 0.0


def _w_karaka_conjunct_separator(v, p):
    """BNN: the union/event-kāraka in the COMPANY of a separator node (Rāhu/Ketu)
    afflicts the matter — estrangement / progeny-trouble flavour (R.G. Rao —
    Venus+Ketu, Venus+Rahu). Sign-based company (the Nāḍī 'saṅga')."""
    ks = v.signs[nadi_timing_karaka(v, p)]
    return -0.6 if ks in (v.signs[Planet.RAHU], v.signs[Planet.KETU]) else 0.0


register_witness("BNN: jīva 12th-from-kāraka (quality-drag)", "standing", 0.7,
                 _w_jiva_12th_from_karaka)
register_witness("BNN: kāraka 12th-from-descriptor (delay)", "standing", 0.6,
                 _w_karaka_12th_from_descriptor)
register_witness("BNN: kāraka conjunct separator (afflicted union)", "standing", 0.7,
                 _w_karaka_conjunct_separator)


# --- OUTCOME-precision witnesses (user-approved 2026-07-02; see RULE_CHANGELOG).
# Domain-general: each reads the matter's Arudha / lords / kārakas, never a native.
def _w_arudha_sustenance(v, p):
    """2nd-from-Arudha sustenance (Jaimini Sūtras 1.4; Rath, Crux of Vedic
    Astrology): benefics in/aspecting the 2nd from the matter's Arudha SUSTAIN it
    (for UL: the marriage); malefics there make it break-prone."""
    if not p.arudhas:
        return 0.0
    ar = v.arudhas()
    score = 0.0
    for key in p.arudhas:
        s = ar.get(key)
        if s is None:
            continue
        second = (s + 1) % 12
        occ = {pl for pl, sg in v.signs.items()
               if sg == second and pl in (_NAT_BENEFIC | _NAT_MALEFIC)}
        asp = set(_aspectors(v, {second}))
        for pl in occ | asp:
            score += 0.4 if pl in _NAT_BENEFIC else -0.4
    return max(-1.0, min(1.0, score))


def _w_retro_significator(v, p):
    """Vakri significator (Phaladeepika; KP Readers): the matter's lord/kāraka
    retrograde → reversal / repeat / comes-back texture on the outcome. The nodes
    are excluded (Rāhu/Ketu are always vakri — no information)."""
    seven = (_NAT_BENEFIC | _NAT_MALEFIC) - {Planet.RAHU, Planet.KETU}
    hits = 0
    for pl in _matter_planets(v, p) & seven:
        try:
            if v.natal.placements[pl].retrograde:
                hits += 1
        except Exception:
            pass
    return -min(1.0, 0.4 * hits)


register_witness("2nd-from-Arudha sustenance (Jaimini)", "standing", 0.8,
                 _w_arudha_sustenance)
register_witness("vakri (retrograde) significator", "standing", 0.6,
                 _w_retro_significator)


# --- Task-4 standing nodes (user-approved 2026-07-05, with classical sources) - #
def _house_from(sign, asc):
    return (sign - asc) % 12 + 1


_MANGLIK_HOUSES = {1, 2, 4, 7, 8, 12}


def _w_manglik(v, p):
    """Kuja / Maṅgala dosha (BPHS; Saravali): Mars in 1/2/4/7/8/12 reckoned from
    the lagna, the Moon AND Venus → friction/delay in marriage. Marriage-class
    matters only (does not touch career, wealth, …)."""
    if 7 not in p.houses and (getattr(p, "base_domain", None) or "") != "marriage":
        return 0.0
    mars = v.signs[Planet.MARS]
    hits = sum(1 for ref in (v.ascendant_sign, v.signs[Planet.MOON],
                             v.signs[Planet.VENUS])
               if _house_from(mars, ref) in _MANGLIK_HOUSES)
    return -1.0 if hits >= 2 else (-0.5 if hits == 1 else 0.0)


def _w_female_husband_karaka(v, p):
    """Strī-jātaka (BPHS): in a woman's chart the husband is read from JUPITER
    (besides the 7th lord). Reads Jupiter's benefic/malefic company for a
    marriage-class female chart — the marriage EVENT still times on Venus/7th."""
    if (getattr(v, "gender", "") or "").lower()[:1] != "f":
        return 0.0
    if 7 not in p.houses and (getattr(p, "base_domain", None) or "") != "marriage":
        return 0.0
    co = set(v.planets_in_house(_house_from(v.signs[Planet.JUPITER],
                                            v.ascendant_sign))) - {Planet.JUPITER}
    b, m = len(co & _NAT_BENEFIC), len(co & _NAT_MALEFIC)
    return 0.4 * (1 if b > m else -1 if m > b else 0)


def _w_karakamsha_spouse(v, p):
    """Jaimini Karakāṃśa: the 7th-from-Karakāṃśa (the Ātmakāraka's D9 sign) shows
    the spouse — benefics occupying it = good, malefics = troubled. Marriage-class
    matters only."""
    if 7 not in p.houses and (getattr(p, "base_domain", None) or "") != "marriage":
        return 0.0
    try:
        seventh = (v.karakamsha() + 6) % 12
        d9 = v.navamsha.signs
    except Exception:
        return 0.0
    occ = [pl for pl, s in d9.items()
           if s == seventh and pl in (_NAT_BENEFIC | _NAT_MALEFIC)]
    b = sum(1 for pl in occ if pl in _NAT_BENEFIC)
    m = sum(1 for pl in occ if pl in _NAT_MALEFIC)
    return 0.5 * (1 if b > m else -1 if m > b else 0)


def _w_indu_lagna(v, p):
    """Indu Lagna (BPHS special lagna) — the wealth ascendant. Benefic company
    strengthens dhana. Wealth-class matters (2nd/11th houses) only."""
    if not ({2, 11} & set(p.houses)):
        return 0.0
    try:
        co = set(v.planets_in_house(_house_from(v.indu_lagna(), v.ascendant_sign)))
    except Exception:
        return 0.0
    b, m = len(co & _NAT_BENEFIC), len(co & _NAT_MALEFIC)
    return 0.4 * (1 if b > m else -1 if m > b else 0)


def _w_bhava_chalit_shift(v, p):
    """Bhāva-Chalit (KP/BPHS): when the matter's house-lord's physical (Placidus
    Chalit) house differs from its rāśi house, its rāśi-based result is weakened /
    shifted — a small caution on the promise."""
    try:
        chalit = v.bhava_chalit()
    except Exception:
        return 0.0
    shifted = sum(1 for h in p.houses
                  if getattr(chalit.get(v.house_lord(h)), "shifted", False))
    return -min(0.6, 0.3 * shifted)


register_witness("Maṅgala/Kuja dosha (Mars 1/2/4/7/8/12)", "standing", 0.8,
                 _w_manglik)
register_witness("Strī-jātaka husband kāraka (Jupiter, ♀ chart)", "standing",
                 0.8, _w_female_husband_karaka)
register_witness("Karakāṃśa 7th-spouse (Jaimini D9)", "standing", 0.8,
                 _w_karakamsha_spouse)
register_witness("Indu Lagna wealth-ascendant (special lagna)", "standing", 0.6,
                 _w_indu_lagna)
register_witness("Bhāva-Chalit result-shift of house-lord", "standing", 0.6,
                 _w_bhava_chalit_shift)


def standing_balance(v, profile):
    """Net natal pro/anti pattern on the matter + the list of firing nodes."""
    total = 0.0
    fired = []
    for w in build_panel(profile):
        if w.layer != "standing":
            continue
        c = w.vote(v, profile) * w.weight
        if abs(c) > 1e-9:
            fired.append((w.name, round(c, 2)))
        total += c
    return round(total, 2), fired


# ---------------------------------------------------------------------------- #
# DYNAMIC DOMAIN REGISTRY — a plain dict. Add a life-area = add one entry, by
# editing DOMAIN_PROFILES or calling register_domain(...) at runtime. The engine
# code below never names a domain; it reads only the profile's fields.
# ---------------------------------------------------------------------------- #
@dataclass(frozen=True)
class DomainProfile:
    name: str
    houses: tuple[int, ...]               # primary bhāvas of the matter
    fulfil_houses: frozenset              # KP houses that MAKE the matter happen
    negate_houses: frozenset              # KP houses that BREAK/deny it (reversal)
    karakas: tuple[str, ...]              # Jaimini chara-kārakas (by name)
    natural_karaka: Planet | None         # natural significator graha
    arudhas: tuple[str, ...]              # Arudha keys (A1..A12, UL)
    saham: str | None                     # Tājika Saham timing the matter
    reversal_saham: str | None            # Saham timing the matter's reversal
    varga: int                            # divisional chart confirming the TYPE
    rupture_matter: bool = False          # the matter IS a rupture (divorce/…):
                                          # time it with the reversal timer
    base_domain: str | None = None        # the underlying matter whose reversal
                                          # this rupture is (divorce → marriage)

    @classmethod
    def from_dict(cls, name: str, spec: dict) -> "DomainProfile":
        """Build a profile from a loose dict so domains can be data-driven."""
        return cls(
            name=name,
            houses=tuple(spec["houses"]),
            fulfil_houses=frozenset(spec["fulfil_houses"]),
            negate_houses=frozenset(spec.get("negate_houses", ())),
            karakas=tuple(spec.get("karakas", ())),
            natural_karaka=spec.get("natural_karaka"),
            arudhas=tuple(spec.get("arudhas", ())),
            saham=spec.get("saham"),
            reversal_saham=spec.get("reversal_saham"),
            varga=spec.get("varga", 9),
            rupture_matter=bool(spec.get("rupture_matter", False)),
            base_domain=spec.get("base_domain"),
        )


DOMAIN_PROFILES: dict[str, DomainProfile] = {}


def register_domain(name: str, **spec) -> DomainProfile:
    """Register (or override) a life-area at runtime — keeps domains open-ended."""
    prof = DomainProfile.from_dict(name, spec)
    DOMAIN_PROFILES[name] = prof
    return prof


# The shipped set — illustrative, NOT a closed list. Extend freely.
_SEED = {
    "marriage":  dict(houses=[7], fulfil_houses=[2, 7, 11], negate_houses=[1, 6, 10],
                      karakas=["Darakaraka"], natural_karaka=Planet.VENUS,
                      arudhas=["A7", "UL"], saham="Vivaha",
                      reversal_saham="Punarvivaha", varga=9),
    "career":    dict(houses=[10], fulfil_houses=[2, 6, 10, 11], negate_houses=[5, 8, 9, 12],
                      karakas=["Amatyakaraka"], natural_karaka=Planet.SATURN,
                      arudhas=["A10"], saham="Karma", varga=10),
    "children":  dict(houses=[5], fulfil_houses=[2, 5, 11], negate_houses=[1, 4, 10, 12],
                      karakas=["Putrakaraka"], natural_karaka=Planet.JUPITER,
                      arudhas=["A5"], saham="Putra", varga=7),
    "wealth":    dict(houses=[2, 11], fulfil_houses=[2, 5, 9, 11], negate_houses=[6, 8, 12],
                      natural_karaka=Planet.JUPITER, arudhas=["A2"], saham="Artha", varga=2),
    "mother":    dict(houses=[4], fulfil_houses=[2, 4, 11], negate_houses=[3, 8, 12],
                      karakas=["Matrikaraka"], natural_karaka=Planet.MOON,
                      arudhas=["A4"], varga=4),
    "father":    dict(houses=[9], fulfil_houses=[2, 9, 11], negate_houses=[3, 8, 12],
                      karakas=["Pitrikaraka"], natural_karaka=Planet.SUN,
                      arudhas=["A9"], varga=9),
    "illness":   dict(houses=[6, 8], fulfil_houses=[6, 8, 12], negate_houses=[1, 5, 11],
                      karakas=["Gnatikaraka", "Atmakaraka"], natural_karaka=Planet.SATURN,
                      arudhas=["A6"], saham="Roga", varga=30),
    "education": dict(houses=[4, 5, 9], fulfil_houses=[4, 5, 9, 11], negate_houses=[6, 8, 12],
                      natural_karaka=Planet.MERCURY, arudhas=["A5"], saham="Vidya", varga=24),
    "relocation": dict(houses=[4], fulfil_houses=[3, 4, 11, 12], negate_houses=[1, 6, 8],
                       karakas=["Matrikaraka"], natural_karaka=Planet.MOON,
                       arudhas=["A4"], varga=4),
}
for _n, _s in _SEED.items():
    register_domain(_n, **_s)


# ---------------------------------------------------------------------------- #
# Promise & Tempo (computed once per domain)
# ---------------------------------------------------------------------------- #
@dataclass
class PromiseTempo:
    promised: bool
    cusp_sublord: str
    cusp_signifies: list
    lord_strength: dict                   # house -> (is_strong, ishta, kashta)
    karaka_strength: dict                 # planet -> (is_strong, avastha, ishta)
    varga_ok: dict                        # planet -> well-placed in varga?
    argala_net: int                       # +support / -obstruction on the house
    house_sav: dict                       # house -> SAV bindus
    tempo: str                            # early | on-time | late/difficult | denied
    notes: list


def _well_placed_in_varga(vc, planet) -> bool:
    s = vc.signs[planet]
    return (_SIGN_RULER[s] == planet or _EXALT_SIGN.get(planet) == s
            or vc.house_of(planet) in _KENDRA_TRIKONA)


def _argala_net_on_house(v, house: int) -> int:
    """+1 per effective support argala, -1 per dominant Virodhārgala on the house."""
    net = 0
    for a in v.argala(house):
        cz, cx = len(a.causers), len(a.counterers)
        if cz and cz > cx:
            net += 1
        elif cx and cx > cz:
            net -= 1
    return net


_KP_VIEW_CACHE: dict = {}


def _kp_view(v):
    """KP must be judged on the **Krishnamurti (KP) ayanāṃśa** with **Placidus**
    cusps — not the main (Lahiri/whole-sign) chart. Build that KP sub-chart once
    per native and cache it; returns (kp_chart, KPSignificators)."""
    key = id(v)
    if key not in _KP_VIEW_CACHE:
        vkp = VedicChart.create(when=v.when_utc, latitude=v.natal.latitude,
                                longitude=v.natal.longitude, ayanamsa="kp")
        _KP_VIEW_CACHE[key] = (vkp, vkp.kp_significators())
    return _KP_VIEW_CACHE[key]


def promise_and_tempo(v, profile: DomainProfile) -> PromiseTempo:
    _, kps = _kp_view(v)                       # KP significators on the KP-ayanāṃśa chart
    tr = v.transits()
    sav = v.sarvashtakavarga()
    sb = v.shadbala()
    ik = v.ishta_kashta()
    primary = profile.houses[0]
    from advance_astrology.vedic.kp import kp_chain
    cusp_sub = kp_chain(kps.cusps[primary]).sub_lord   # TRUE Placidus cusp (not equal-house)
    cusp_sig = kps.planet_signifies(cusp_sub)
    promised = bool(set(cusp_sig) & profile.fulfil_houses)

    lord_strength, karaka_strength, varga_ok, house_sav = {}, {}, {}, {}
    vc = v.varga(profile.varga)
    notes = []
    saturn_node_pressure = False
    for h in profile.houses:
        lord = v.house_lord(h)
        s = sb.get(lord)
        k = ik.get(lord)
        lord_strength[h] = (bool(s.is_strong) if s else None,
                            round(k.ishta) if k else None,
                            round(k.kashta) if k else None)
        varga_ok[lord] = _well_placed_in_varga(vc, lord)
        house_sav[h] = sav[(v.ascendant_sign + h - 1) % 12]
        # Saturn / node natal pressure on the house = classic delay signature
        hsign = (v.ascendant_sign + h - 1) % 12
        for mal in (Planet.SATURN, Planet.RAHU, Planet.KETU):
            ms = v.signs[mal]
            if ms == hsign or any((ms + a) % 12 == hsign
                                  for a in _ASPECT_OFFSETS.get(mal, (6,))):
                saturn_node_pressure = True

    karakas = _karaka_planets(v, profile)
    weak_karaka = False
    for p in karakas:
        s = sb.get(p)
        k = ik.get(p)
        av = v.avasthas(p)
        karaka_strength[p] = (bool(s.is_strong) if s else None, av["baladi"],
                              round(k.ishta) if k else None)
        varga_ok[p] = _well_placed_in_varga(vc, p)
        if (s and not s.is_strong) or av["baladi"] in ("Mrita", "Vriddha"):
            weak_karaka = True

    argala_net = _argala_net_on_house(v, primary)

    # tempo heuristic (engine-suggested; the AI refines it)
    lords_strong = all((t[0] for t in lord_strength.values() if t[0] is not None))
    if not promised:
        tempo = "denied / not promised by cusp sub-lord"
    elif saturn_node_pressure or weak_karaka or argala_net < 0:
        tempo = "late / with-friction (Saturn-node pressure or weak kāraka)"
    elif lords_strong and argala_net > 0 and not weak_karaka:
        tempo = "early / smooth"
    else:
        tempo = "on-time"
    if saturn_node_pressure:
        notes.append("Saturn/node touches the matter's house (delay signature)")
    if weak_karaka:
        notes.append("kāraka weak or in Mṛta/Vṛddha avasthā (Track-B friction)")
    if any(not ok for ok in varga_ok.values()):
        notes.append(f"some significator ill-placed in D{profile.varga} "
                     f"(internal weakness — delay/qualify)")
    return PromiseTempo(promised, cusp_sub.value, cusp_sig, lord_strength,
                        karaka_strength, varga_ok, argala_net, house_sav,
                        tempo, notes)


# ---------------------------------------------------------------------------- #
# Per-window timing machinery (all domain-independent)
# ---------------------------------------------------------------------------- #
@dataclass
class WindowEvidence:
    start: datetime
    chain: list
    kp_fulfil: int
    kp_negate: int
    karaka_in_chain: bool
    karaka_sukshma: bool
    lagnesh_in_chain: bool
    lagna_activators: list
    house_double_transit: bool
    lord_double_transit: bool
    saham_double_transit: bool
    bnn: bool
    kakshya: bool
    varshaphal_muntha: bool
    chara_ad: str
    sudarshana_hit: bool
    gochara_from_moon: bool = False        # Jup+Sat double-transit reckoned from the Moon
    fulfil_house_dt: bool = False          # double-transit on the OTHER fulfilment houses + lords
    kp_star_transit: bool = False          # slow planet transiting a fulfilment-significator's star
    tajika_sig: bool = False               # Varṣeśa / Muntha-lord signifies the matter (annual)
    arudha_axis: bool = False              # slow benefic/kāraka activating the Arudha axis (UL/2nd-from-UL …)
    bb_active: bool = False                # Bhṛgu Bindu activated by a slow mover (Nāḍī timing)
    func_valence: float = 0.0              # signed: chain lords functional benefic(+) vs malefic/māraka(−)
    nadi_jeeva: bool = False               # transit Jupiter conj/trine the Nāḍī kāraka (BNN year-marker)
    nadi_karma: bool = False               # transit Saturn sanction (conj/trine kāraka OR in fulfil-houses)
    sade_sati: bool = False                # transit Saturn in 12/1/2 from natal Moon (Sade-Sati/Kaṇṭaka)
    karaka_kakshya: float = 0.0            # fraction of the matter's OWN significators (kārakas + slow timers) in a bindu-bearing kakṣyā of their Bhinnāṣṭakavarga (BPHS Aṣṭakavarga delivery)
    signals: dict = field(default_factory=dict)   # generic bag for FAMILY-generated nodes
    panel: object = None                          # the domain's full witness panel (families incl.)
    systems_firing: int = 0                       # # of INDEPENDENT paddhatis firing (set by _score_rows)
    salience: float = 0.0                         # convergence-gated, information-weighted rank score

    def firing_nodes(self, shared=None) -> list:
        """The timing witnesses that fire for this window, with their votes.
        Every timekeeper — the daśā included — is just one node here. Iterates the
        domain's full panel (static nodes + family-generated nodes) when attached."""
        out = []
        for w in (self.panel or WITNESSES):
            if w.layer != "timing":
                continue
            if shared is not None and w.shared != shared:
                continue
            c = w.weight * w.vote(self)
            if abs(c) > 1e-9:
                out.append((w.name, round(c, 2)))
        return out

    @property
    def domain_score(self):
        """Convergence of the per-window timing NODES, EXCLUDING the shared Lagna
        node (the Lagna is the same for every domain). The daśā is simply two of
        these nodes — never the privileged judge."""
        return round(sum(c for _, c in self.firing_nodes(shared=False)), 2)

    @property
    def convergence(self):
        """Within-domain window ranking (adds the shared Lagna node)."""
        return round(self.domain_score
                     + sum(c for _, c in self.firing_nodes(shared=True)), 2)


# --- seed TIMING witnesses — every timekeeper is one node; the daśā is NOT
# privileged, it is simply two of these among many. -------------------------- #
register_witness("daśā: kāraka in MD>AD>PD", "timing", 1.0,
                 lambda w: 1.0 if w.karaka_in_chain else 0.0)
register_witness("daśā: kāraka at sūkṣma (micro-trigger)", "timing", 1.0,
                 lambda w: 1.0 if w.karaka_sukshma else 0.0)
register_witness("KP fulfilment ≥ negation", "timing", 1.0,
                 lambda w: 1.0 if (w.kp_fulfil > 0 and w.kp_fulfil >= w.kp_negate) else 0.0)
register_witness("Lagneśa in daśā", "timing", 1.0,
                 lambda w: 1.0 if w.lagnesh_in_chain else 0.0)
register_witness("double-transit (house/lord)", "timing", 1.0,
                 lambda w: 1.0 if (w.house_double_transit or w.lord_double_transit) else 0.0)
register_witness("domain Saham double-transit", "timing", 1.0,
                 lambda w: 1.0 if w.saham_double_transit else 0.0)
register_witness("BNN degree-trigger", "timing", 1.0,
                 lambda w: 1.0 if w.bnn else 0.0)
register_witness("Kakṣyā window", "timing", 1.0,
                 lambda w: 1.0 if w.kakshya else 0.0)
# Bhinnāṣṭakavarga DELIVERY — a transit fructifies in proportion to the bindus
# the TRANSITING SIGNIFICATOR holds (BPHS Aṣṭakavarga gochara; K.N. Rao,
# transits-with-Ashtakavarga). Distinct from the generic Jupiter/Saturn Kakṣyā
# window above: this reads the MATTER'S OWN kārakas' own BAV, so it is
# domain-scoped. Soft (0.6), graded, purely additive — it up-weights a window
# whose delivering planets sit in fruitful kakṣyās; it can never veto one.
register_witness("Bhinnāṣṭakavarga delivery (kāraka in bindu-bearing Kakṣyā)",
                 "timing", 0.6, lambda w: w.karaka_kakshya)
register_witness("Varṣaphal Muntha", "timing", 1.0,
                 lambda w: 1.0 if w.varshaphal_muntha else 0.0)
register_witness("Sudarśana wheel", "timing", 1.0,
                 lambda w: 1.0 if w.sudarshana_hit else 0.0)
register_witness("Sade-Sati / Kaṇṭaka (Saturn-from-Moon)", "timing", 0.5,
                 lambda w: 1.0 if w.sade_sati else 0.0)
register_witness("Lagna materialization", "timing", 1.0,
                 lambda w: 1.0 if w.lagna_activators else 0.0, shared=True)

# --- nodes added 2026-06-23 (user-approved): classical residence-change /
# timing witnesses the panel was missing. Domain-general — each reads the
# domain's houses/fulfil set, never a native. (RULE_CHANGELOG documents sources
# and weights.) ------------------------------------------------------------- #
register_witness("gochara from Moon (Chandra-lagna double-transit)", "timing", 1.0,
                 lambda w: 1.0 if w.gochara_from_moon else 0.0)
register_witness("fulfilment-houses double-transit (+lords)", "timing", 0.7,
                 lambda w: 1.0 if w.fulfil_house_dt else 0.0)
register_witness("KP transit: slow planet in significator's star", "timing", 0.7,
                 lambda w: 1.0 if w.kp_star_transit else 0.0)
register_witness("Tājika Varṣeśa/Muntha signifies the matter", "timing", 0.6,
                 lambda w: 1.0 if w.tajika_sig else 0.0)
# Outcome valence (user-approved 2026-07-02): the window's daśā lords' FUNCTIONAL
# nature for this lagna signs the outcome (Laghu Pārāśarī: functional benefic
# daśā favours, functional malefic / māraka daśā adverses). Signed vote — the
# sign shows the direction in the ledger; salience uses |vote| so it cannot
# inflate rank, and the "daśā" name keeps it inside the dasha paddhati group.
register_witness("daśā-lord functional valence (Laghu Pārāśarī)", "timing", 0.8,
                 lambda w: w.func_valence)
# NĀḌĪ timing pair (user-approved 2026-07-04; sources at the NĀḌĪ family block):
# Guru-jeeva marks the YEAR (slow), Śani sanctions the karma — both firing is
# the classical Nāḍī fructification signature. Grouped under the independent
# "nadi" paddhati for the convergence gate.
register_witness("nadi: Guru-jeeva activates kāraka (BNN)", "timing", 1.0,
                 lambda w: 1.0 if w.nadi_jeeva else 0.0)
register_witness("nadi: Śani karma-sanction (BNN)", "timing", 0.7,
                 lambda w: 1.0 if w.nadi_karma else 0.0)
# Jaimini Arudha-axis gochara (user-approved 2026-06-23). Domain-general: the
# matter's Arudha (for marriage UL) and the 2nd-from-it (sustenance) lit by a slow
# benefic (Jupiter/Saturn occupation OR dṛṣṭi) or the domain kāraka (conjunction).
# Source: Jaimini Sūtras / BPHS Upapada doctrine; Common-Timing-Miss #3. This was a
# computed-but-UNWIRED quantity (arudhas existed in the profile, no node read them).
register_witness("Jaimini Arudha-axis activation (UL / 2nd-from-Arudha)", "timing", 0.8,
                 lambda w: 1.0 if w.arudha_axis else 0.0)
# Bhṛgu Bindu (Moon–Rāhu midpoint) — a Nāḍī sensitive point; slow-transit activation
# marks event-timing. Computed by the engine but previously unwired. Own paddhati.
register_witness("Bhṛgu Bindu activation (Nāḍī)", "timing", 0.5,
                 lambda w: 1.0 if w.bb_active else 0.0)


# ---------------------------------------------------------------------------- #
# DAŚĀ-SYSTEM CATALOGUE (systems-as-data) + its generative FAMILY.
# Each entry is an adapter: build(v, profile, start, end) -> active(when)->set[Planet]
# (the significators a system has running at a moment). The family turns the whole
# catalogue into one "significator running" timing node PER system — so adding a
# daśā system is a single dict entry, never a code change. Vimśottari keeps its own
# detailed kāraka/sūkṣma nodes above, so it is excluded here to avoid double count.
# ---------------------------------------------------------------------------- #
def _ring_system(system: str, cycles: int = 3):
    def build(v, profile, start, end):
        from advance_astrology.dasha import current_dasha as _cd
        periods = v.dasha(system, levels=3, cycles=cycles)
        return lambda when: {c.lord for c in _cd(periods, when)}
    return build


def _mudda_system():
    def build(v, profile, start, end):
        from advance_astrology.dasha import current_dasha as _cd
        from advance_astrology.vedic.varshaphal import solar_return_time
        md_cache, sr_cache = {}, {}

        def _sr(y):
            if y not in sr_cache:
                sr_cache[y] = solar_return_time(v, y)
            return sr_cache[y]

        def active(when):
            y = when.year
            if when < _sr(y):
                y -= 1
            if y not in md_cache:
                md_cache[y] = v.mudda_dasha(y, levels=3)
            return {c.lord for c in _cd(md_cache[y], when)}
        return active
    return build


def _chara_system():
    def build(v, profile, start, end):
        def active(when):
            out = set()
            for c in v.current_chara_dasha(when, levels=2):
                if c.note in SIGNS:
                    out.add(_SIGN_RULER[SIGNS.index(c.note)])
            return out
        return active
    return build


def _rashi_dasha_system(method: str):
    """Generic adapter for a Jaimini rāśi daśā (Nārāyaṇa, Sudasā…): precompute the
    sign-periods once, then map the active sign(s) → their rulers as significators."""
    def build(v, profile, start, end):
        from advance_astrology.dasha import current_dasha as _cd
        periods = getattr(v, method)(levels=2)

        def active(when):
            out = set()
            for c in _cd(periods, when):
                if c.note in SIGNS:
                    out.add(_SIGN_RULER[SIGNS.index(c.note)])
            return out
        return active
    return build


# Open dict — add a system = one entry; every domain gets the node automatically.
DASHA_SYSTEMS: dict = {
    "yogini": _ring_system("yogini"),
    "ashtottari": _ring_system("ashtottari"),
    "muddā": _mudda_system(),
    "chara": _chara_system(),
    "nārāyaṇa": _rashi_dasha_system("narayana_dasha"),
    "sudasā": _rashi_dasha_system("sudasa_dasha"),
}


def _dasha_family(profile) -> list:
    """One 'significator running' timing node per catalogue daśā system."""
    out = []
    for name in DASHA_SYSTEMS:
        key = f"dasha::{name}"
        out.append(Witness(
            f"daśā[{name}]: significator running", "timing", 0.6,
            (lambda k: (lambda w: 1.0 if w.signals.get(k) else 0.0))(key)))
    return out


register_family("daśā-system catalogue", _dasha_family)


# Vimśottari nakṣatra-lord cycle (KP star-lord), from Aśvinī = Ketu.
_NAK_LORDS = [Planet.KETU, Planet.VENUS, Planet.SUN, Planet.MOON, Planet.MARS,
              Planet.RAHU, Planet.JUPITER, Planet.SATURN, Planet.MERCURY]


def _nakshatra_lord(lon: float) -> Planet:
    return _NAK_LORDS[int((lon % 360) / (360 / 27)) % 9]


def _slow_on_sign(tr, sign, when, planets=(Planet.JUPITER, Planet.SATURN)):
    out = []
    for p in planets:
        ps = tr.transit_sign(when, p)
        if ps == sign or any((ps + a) % 12 == sign for a in _ASPECT_OFFSETS[p]):
            out.append(p.value + ("(in)" if ps == sign else "(asp)"))
    return out


def _kp_score(kps, planet, profile):
    h = set(kps.planet_signifies(planet))
    return len(h & profile.fulfil_houses), len(h & profile.negate_houses)


def _dt_windows(tr, house, start, end):
    return [(w.start, w.end) for w in tr.double_transit_windows(house, start, end)]


def _conj_windows(tr, transit, natal_lon, start, end):
    return [(w.start, w.end) for w in
            tr.conjunction_windows(transit, natal_lon, start, end, orb=4.0)]


# ---------------------------------------------------------------------------- #
# NĀḌĪ (Bhrigu-Nandi) family — planets AS kārakas, houses secondary.
# Sources: R.G. Rao (Bhrigu Nandi Nadi); Satyanarayana Naik (Revelation from
# Naadi Jyotisha). Doctrine wired here (user-provided rule-set, 2026-07-04):
#   • gender-aware kalatra kāraka — male: Venus, female: Mars;
#   • Jeeva = Jupiter: the event fructifies when TRANSIT Jupiter conjuncts or
#     trines (1-5-9) the matter's natal kāraka — the Nāḍī year-marker;
#   • Śani's sanction: karma begins only when transit Saturn also touches the
#     kāraka (conj/trine) or the matter's fulfilment houses;
#   • kāraka-saṅga colours the NATURE: Rahu = sudden/unconventional,
#     Ketu = delay / talks-break / vairāgya (trine counts as "with" in Nāḍī).
# ---------------------------------------------------------------------------- #
NADI_KARAKAS = {
    "marriage": "kalatra",          # gender-aware: Venus (male) / Mars (female)
    "divorce": "kalatra",
    "career": Planet.SATURN, "children": Planet.JUPITER,
    "education": Planet.MERCURY, "wealth": Planet.VENUS,
    "mother": Planet.MOON, "father": Planet.SUN,
    "illness": Planet.SATURN, "relocation": Planet.RAHU,
    "foreign": Planet.RAHU, "property": Planet.MARS,
}


def nadi_karaka(v, profile) -> Planet:
    """The matter's Nāḍī kāraka. Gender-aware for kalatra matters; unknown
    domains fall back to the profile's natural kāraka (data-driven)."""
    spec = NADI_KARAKAS.get(profile.name)
    if spec is None:      # derived (e.g. 'second-marriage') → follow base matter
        spec = NADI_KARAKAS.get(getattr(profile, "base_domain", None) or "")
    if spec == "kalatra":
        g = (getattr(v, "gender", "") or "").lower()
        return Planet.MARS if g.startswith("f") else Planet.VENUS
    if spec is None:
        return profile.natural_karaka or Planet.JUPITER
    return spec


def nadi_timing_karaka(v, profile) -> Planet:
    """The kāraka that TIMES the event (distinct from the spouse-descriptor kāraka).
    For marriage-class matters it is ALWAYS **Venus** — R.G. Rao's universal
    "Venus for marriages" event-kāraka — regardless of gender. The gender kāraka
    (Mars for a female) describes the SPOUSE/husband and is used by nadi_chain /
    nadi_nature, NOT the marriage date. (Source: docs/knowledge/bnn/, book — a
    female's marriage & marital-happiness are read from Venus; Mars only reads the
    husband.) All other domains time on their own kāraka."""
    spec = (NADI_KARAKAS.get(profile.name)
            or NADI_KARAKAS.get(getattr(profile, "base_domain", None) or ""))
    if spec == "kalatra":
        return Planet.VENUS
    return nadi_karaka(v, profile)


def role_significators(v, profile) -> list:
    """Rank the grahas by the DENSITY of the matter's ROLES each one carries — so
    the timer is found by ROLE, never by a hard-coded planet. The highest-density
    graha is the matter's principal significator (its MAHĀDAŚĀ frames the event);
    the spouse/gender kāraka and the Lagna-lord are the usual sub-period
    ACTIVATORS (antara/pratyantara). Domain-general: every role is read from the
    profile's houses / kāraka / primary-cusp sub-lord + KP significations +
    Jaimini Darakaraka + occupancy/aspect — never a native. Returns
    ``[{planet, score, roles}]``, highest score first.

    Rationale (docs/AI_TRIANGULATION_PROMPT §4C-bis, reverse-engineered from two
    independent verified charts): both married in the mahādaśā of the graha most
    loaded with marriage-roles (7th-lord + primary-cusp-sub-lord + kalatra-kāraka
    + Darakaraka + in/aspecting-7th + 2nd/11th-lord + in-Lagna), which happened to
    be Venus in both — but the RULE is ROLE-DENSITY, so a chart whose top-role
    graha is Jupiter/Sun/… times the matter in THAT graha's daśā, not Venus's."""
    from advance_astrology.vedic.kp import kp_chain
    _, kps = _kp_view(v)
    asc = v.ascendant_sign
    prim = profile.houses[0]                       # the matter's primary house
    prim_sign = (asc + prim - 1) % 12
    l1 = v.house_lord(1)
    sub = kp_chain(kps.cusps[prim]).sub_lord if prim in kps.cusps else None
    dk = {nm: p for nm, p in v.chara_karakas().items()}.get("Darakaraka")
    kalatra = nadi_timing_karaka(v, profile)       # matter's event-kāraka (Venus for marriage)
    spouse = nadi_karaka(v, profile)               # spouse/gender kāraka (Mars ♀)
    house_lords = {h: v.house_lord(h) for h in profile.houses}
    fulfil_lords = {v.house_lord(h) for h in profile.fulfil_houses}
    starlords = {_nakshatra_lord(float(v.longitudes[p]))
                 for p in {house_lords[prim], kalatra, spouse}}

    def house_of(pl):
        return (v.signs[pl] - asc) % 12 + 1

    def aspects_prim(pl):
        return any((prim_sign - v.signs[pl]) % 12 == off
                   for off in _ASPECT_OFFSETS.get(pl, [6]))

    # role WEIGHTS: the promise-giving roles (owns/is-kāraka-of/sub-lord-of the
    # matter) outweigh the incidental ones (a stray aspect, sitting in Lagna,
    # being a star-lord) — otherwise a graha with many soft roles falsely ties the
    # true significator (magnifying-lens robustness).
    out = []
    for p in (_NAT_BENEFIC | _NAT_MALEFIC):        # the nine grahas
        roles = []                                  # (label, weight)
        if p == l1:
            roles.append(("Lagna-lord", 1))
        for h, lord in house_lords.items():
            if p == lord:
                roles.append((f"{h}H-lord" + ("(primary)" if h == prim else ""),
                              3 if h == prim else 2))
        if p == sub:
            roles.append(("primary-cusp-sub-lord", 3))     # KP promise-giver
        if p == kalatra:
            roles.append(("event-kāraka", 3))
        if p == spouse and spouse != kalatra:
            roles.append(("spouse/gender-kāraka", 2))
        if dk is not None and p == dk:
            roles.append(("Darakaraka", 3))
        if p in fulfil_lords and p not in house_lords.values():
            roles.append(("fulfil-house-lord", 2))
        h_ = house_of(p)
        if h_ in profile.houses:
            # a graha PLACED IN the matter's house gives that house's results in
            # its daśā (BPHS) — as strong a timer as the house-lord itself.
            roles.append((f"in-{h_}H(matter)", 3))
        elif h_ == 1:
            roles.append(("in-Lagna", 1))
        if aspects_prim(p):
            roles.append(("aspects-primary-house", 1))
        if p in starlords:
            roles.append(("star-lord-of-core-sig", 1))
        sig = sorted(set(kps.planet_signifies(p)) & set(profile.fulfil_houses))
        if sig:
            roles.append((f"KP-signifies-{sig}", 2 if prim in sig else 1))
        if roles:
            out.append(dict(planet=p, score=sum(w for _, w in roles),
                            roles=[r for r, _ in roles]))
    out.sort(key=lambda x: (-x["score"], x["planet"].value))
    return out


def nadi_nature(v, profile) -> str:
    """Kāraka-saṅga (same sign or trine = 'with' in Nāḍī): the EVENT's flavour."""
    nk = nadi_karaka(v, profile)
    s = v.signs[nk]
    trines = {s, (s + 4) % 12, (s + 8) % 12}
    notes = []
    if v.signs[Planet.RAHU] in trines:
        notes.append("Rahu-saṅga → sudden/unconventional (love/inter-community rang)")
    if v.signs[Planet.KETU] in trines:
        notes.append("Ketu-saṅga → delay / baat-toot-na / vairāgya rang")
    try:
        if v.natal.placements[nk].retrograde:
            notes.append("vakri kāraka → repeat/revisit pattern")
    except Exception:
        pass
    return "; ".join(notes)


_NADI_REL = {0, 4, 8}     # 1 / 5 / 9 (conjunction + trine) — golden relations.
# Professional BNN standard (R.G. Rao class + user 2026-07-04): the "with /
# holding-hands" relation is conjunction + the 1/5/9 trine ONLY — the 7th
# (opposition) is NOT a Nāḍī golden relation. (The kāraka's own chart validation
# never relied on the 7th — every lock there was a conjunction or 5/9 trine.)


def _nrel(s_from, s_to) -> bool:
    return (s_to - s_from) % 12 in _NADI_REL


def _deg_close(l1, l2, orb=3.0) -> bool:
    """Nāḍī degree-to-degree: same degree-number in the respective signs."""
    return abs((l1 % 30.0) - (l2 % 30.0)) <= orb


def _nadi_sign(lon, retrograde=False) -> int:
    """BNN reckoning sign of a longitude — a RETROGRADE (vakri) planet is taken
    ONE sign BACK (it walks backwards), then its conjunction/trine is judged from
    there. Nodes are excluded by the caller (treated at their actual sign)."""
    s = int(lon // 30)
    return (s - 1) % 12 if retrograde else s


# Generic planetary significations (relationship/marriage flavour, per the BNN
# class) — reference DATA the chain carries so the read is legible; the AI still
# does the interpretation (charter). Not native-specific.
_NADI_SIGNIF = {
    Planet.SUN: "authority/govt/father; influential, ego-driven spouse",
    Planet.MOON: "emotions/instability; caring but changeable, mood-swings",
    Planet.MARS: "husband(♀)/passion/drive; the cutter & executor",
    Planet.MERCURY: "communication/business; witty, playful, younger-seeming",
    Planet.JUPITER: "jeeva/blessing/expansion; mature, fortunate, abundant",
    Planet.VENUS: "spouse(♂)/love/quality-of-marriage; comfort, romance",
    Planet.SATURN: "delay/karma/cold; older/serious spouse, karmic bond",
    Planet.RAHU: "foreign/inter-caste/unconventional; sharp, affair-prone",
    Planet.KETU: "cut/break/detachment; separation, disinterest",
}
_CHAIN_BODIES = (Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
                 Planet.JUPITER, Planet.VENUS, Planet.SATURN,
                 Planet.RAHU, Planet.KETU)


def nadi_chain(v, profile) -> list:
    """The BNN natal CHAIN — the heart of a Bhrigu-Nandi reading. Take the hero
    (`nadi_karaka`), collect every planet in a golden relation (conjunction or
    1/5/9 trine) to the hero's BNN sign, and order them by DEGREE. The degree
    order IS the chronology: a member with a LOWER degree than the hero acted
    'before / already' (pre-existing); a HIGHER degree comes 'after' (post-
    event). A retrograde member is reckoned one sign back (`_nadi_sign`) before
    the relation is tested — its degree number is kept; the nodes are always
    taken at their actual sign. The ENGINE returns the deterministic ordered
    chain; the AI narrates the significations/story (charter division)."""
    hero = nadi_karaka(v, profile)

    def _retro(p):
        try:
            return (bool(v.natal.placements[p].retrograde)
                    and p not in (Planet.RAHU, Planet.KETU))
        except Exception:
            return False

    hero_lon = float(v.longitudes[hero])
    hero_sign = _nadi_sign(hero_lon, _retro(hero))
    hero_deg = hero_lon % 30.0
    rows = []
    for p in _CHAIN_BODIES:
        lon = float(v.longitudes[p])
        retro = _retro(p)
        off = (_nadi_sign(lon, retro) - hero_sign) % 12
        if off not in _NADI_REL:
            continue
        deg = lon % 30.0
        rel = ("conjunction" if off == 0
               else "trine-5th" if off == 4 else "trine-9th")
        when = ("HERO (kāraka — the pivot)" if p == hero
                else "before / already (pre-existing)" if deg < hero_deg
                else "after (post-event / follows)")
        rows.append(dict(planet=p.value, degree=round(deg, 1), relation=rel,
                         retrograde=retro, when=when,
                         signifies=_NADI_SIGNIF.get(p, "")))
    rows.sort(key=lambda r: r["degree"])
    return rows


def nadi_pinpoint(v, profile, start, end, top=6, min_gap_days=7) -> list:
    """Nāḍī (BNN) event-timing FUNNEL — CANONICAL per R.G. Rao (see
    docs/knowledge/bnn/01_timing_method.md). Two tiers per day:

    PRIMARY APPROVAL (the slow gate — decides the PERIOD):
      • Guru (jeeva) contacts the kāraka or the 7th-from-kāraka (+3): transit
        Jupiter in a golden relation (1/5/9 or conjunction) to the natal kāraka
        OR to the 7th-from-kāraka (the partner seat) — Rao: "Jupiter gives the
        results of the sign he transits"; marriage = Jupiter contacts Venus.
        A tight degree-lock adds +1.
      • Śani karma-approval (+2): transit Saturn in a golden relation to the
        kāraka/7th — Saturn is the karma planet; timely marriage runs on Jupiter
        activation, LATE marriage on Saturn. Jupiter + Saturn together = the
        classical DOUBLE-APPROVAL (strongest).
    A day with NEITHER slow-planet approval is not an event-time (skipped).

    FAST REFINEMENT (picks the exact DAY inside an approved period, +1 each):
      • Śukra≈Guru degree-lock (NATAL-ANCHORED — counts only when the transit
        pair sits on this chart's kāraka / natal-Jupiter / spouse-kāraka degree;
        a bare transit-to-transit contact is the same sky for every chart and
        carries no personal information), Śukra→kāraka golden relation, Maṅgal
        degree-lock onto the kāraka/natal-Jupiter (the universal executor).
        These no longer drive the call — they only sharpen the day.
    TIE-BREAK: within an equal score, the TIGHTEST combined degree-lock orb wins
    (Nāḍī exactness = strength). Returns top clusters (≥ min_gap_days apart)."""
    tr = v.transits()
    nk = nadi_timing_karaka(v, profile)     # marriage → Venus (event-kāraka)
    sk = nadi_karaka(v, profile)            # spouse/gender kāraka (Mars ♀ / Venus ♂)
    nk_lon = float(v.longitudes[nk])
    nk_sign = int(nk_lon // 30)
    sev_lon = (nk_lon + 180.0) % 360.0          # 7th-from-kāraka (partner seat)
    sev_sign = int(sev_lon // 30)
    nj_lon = float(v.longitudes[Planet.JUPITER])
    nj_sign = int(nj_lon // 30)
    # SLOW-GATE anchor set: the event-kāraka + its 7th, PLUS the spouse/gender
    # kāraka + its 7th when distinct (BNN: for a female the husband is read from
    # Mars — so the husband-kāraka's activation ALSO opens the marriage period).
    sk_lon = float(v.longitudes[sk]); sk_sign = int(sk_lon // 30)
    sk7_lon = (sk_lon + 180.0) % 360.0; sk7_sign = int(sk7_lon // 30)
    anchors_ks = [(nk_lon, nk_sign), (sev_lon, sev_sign)]
    if sk != nk:
        anchors_ks += [(sk_lon, sk_sign), (sk7_lon, sk7_sign)]
    movers = [Planet.VENUS, Planet.MARS, Planet.JUPITER, Planet.SATURN]
    days = []

    def _dd(l1, l2):
        return abs((l1 % 30.0) - (l2 % 30.0))
    # sample at day granularity (00:00) so the labelled day/orb is independent of
    # the anchor window's intraday timestamp — the pin is a DATE.
    d = datetime(start.year, start.month, start.day, tzinfo=start.tzinfo)
    while d <= end:
        pos = tr.positions(d, movers)
        ven, mar, jup, sat = (float(pos[p]) for p in movers)
        js, vs, ms, ss = (int(jup // 30), int(ven // 30),
                          int(mar // 30), int(sat // 30))
        jup_targets = [lon for lon, sg in anchors_ks if _nrel(sg, js)]
        sat_gate = any(_nrel(sg, ss) for _, sg in anchors_ks)
        jup_gate = bool(jup_targets)
        if not (jup_gate or sat_gate):          # no slow-planet approval → skip
            d += timedelta(days=1); continue
        score, hits, orb, locked = 0, [], 0.0, False
        if jup_gate:
            score += 3; hits.append("Guru(jeeva) contacts kāraka/7th [primary]")
            dl = [_dd(jup, t) for t in jup_targets if _deg_close(jup, t)]
            if dl:
                score += 1; orb += min(dl); locked = True
                hits.append("Guru≈kāraka degree-lock")
        if sat_gate:
            score += 2
            hits.append("Śani karma-approval (double-approval)" if jup_gate
                        else "Śani karma-approval (late)")
        # Śukra≈Guru refine — NATAL-ANCHORED: a transit-Venus≈transit-Jupiter
        # contact is the same sky for EVERY chart on that day, so by itself it
        # carries no personal information. It counts only when the pair sits ON
        # the natal degree of one of its OWN participants — THIS chart's natal
        # Venus or natal Jupiter (degree-to-degree, BNN). Verified failure-mode:
        # two different charts "locking" the same calendar day purely on this
        # stamp, presented as mutual corroboration.
        if _nrel(js, vs) and _deg_close(ven, jup):
            nv_lon = float(v.longitudes[Planet.VENUS])
            if _deg_close(jup, nv_lon) or _deg_close(jup, nj_lon):
                score += 1; orb += _dd(ven, jup); locked = True
                hits.append("Śukra≈Guru degree-lock on natal degree (refine)")
        if _nrel(nk_sign, vs):
            score += 1; hits.append("Śukra→kāraka golden (refine)")
        m_orbs = [_dd(mar, a) for a, ok in
                  ((nk_lon, _nrel(nk_sign, ms)), (nj_lon, _nrel(nj_sign, ms)))
                  if ok and _deg_close(mar, a)]
        if m_orbs:
            score += 1; orb += min(m_orbs); locked = True
            hits.append("Maṅgal degree-lock (refine)")
        # spouse-kāraka DEGREE-RETURN (BNN "own degree" = give much importance):
        # transit spouse-kāraka back on its natal degree — e.g. ♀ husband-kāraka
        # Mars returning to its natal degree stamps the day (only when distinct).
        if sk != nk and _deg_close(float(pos[sk]), sk_lon):
            score += 1; orb += _dd(float(pos[sk]), sk_lon); locked = True
            hits.append("spouse-kāraka degree-return (refine)")
        days.append((d, score, hits, orb if locked else 99.0))
        d += timedelta(days=1)
    days.sort(key=lambda x: (-x[1], x[3], x[0]))
    picked = []
    for d, sc, h, ob in days:
        if all(abs((d - p[0]).days) >= min_gap_days for p in picked):
            picked.append((d, sc, h, ob))
        if len(picked) >= top:
            break
    picked.sort(key=lambda x: x[0])
    return [dict(date=f"{x[0]:%Y-%m-%d}", score=x[1], hits=x[2],
                 orb=round(x[3], 2)) for x in picked]


def nadi_pinpoint_multi(v, profile, anchors, start, end, radius_days=45,
                        top=5, min_gap_days=7, funnel=None) -> list:
    """Run the day-funnel around SEVERAL candidate-window anchor dates and merge
    into one ranked list. The salience engine's #1 window is not always the
    matter's only real window (e.g. a wedding ceremony vs its legal date can be
    two different high windows); anchoring the pinpoint on just the top window
    would then miss the other. So we funnel around each of the top elapsed
    windows (±radius_days), merge, and rank tightest-lock-first — the strongest,
    most-exact day surfaces regardless of which anchor window it fell in.
    Deterministic; gap-separated across the merged set. ``funnel`` selects the
    per-day scorer: `nadi_pinpoint` (auspicious union) by default, or
    `nadi_rupture_pinpoint` for break-class matters."""
    funnel = funnel or nadi_pinpoint
    seen, merged = set(), []
    for a in anchors:
        s0 = max(a - timedelta(days=radius_days), start)
        e0 = min(a + timedelta(days=radius_days), end)
        if e0 <= s0:
            continue
        for p in funnel(v, profile, s0, e0, min_gap_days=min_gap_days):
            if p["date"] not in seen:
                seen.add(p["date"]); merged.append(p)
    merged.sort(key=lambda p: (-p["score"], p["orb"], p["date"]))
    out = []
    for p in merged:
        pd = datetime.strptime(p["date"], "%Y-%m-%d")
        if all(abs((pd - datetime.strptime(q["date"], "%Y-%m-%d")).days)
               >= min_gap_days for q in out):
            out.append(p)
        if len(out) >= top:
            break
    return out


def nadi_rupture_pinpoint(v, profile, start, end, top=6, min_gap_days=7) -> list:
    """RUPTURE-mode Nāḍī funnel — the canonical MIRROR of `nadi_pinpoint`. A union
    runs on the benefics (Guru primary + Śukra); a BREAK runs on the SEPARATORS,
    same two-tier shape (see docs/knowledge/bnn/01_timing_method.md):

    PRIMARY APPROVAL (the slow karmic gate — decides the PERIOD):
      • Śani contacts the kāraka or 7th-from-kāraka (+3; tight degree-lock +1) —
        Saturn is the viyoga/karma planet, the break's equivalent of Guru-jeeva.
      • Rāhu/Ketu severance (+2): a transit node in a golden relation to the
        kāraka/7th — Śani + node together = the DOUBLE-separator approval
        (strongest break; nodes = the sudden/karmic cut).
    A day with NEITHER separator approval is not a break-time (skipped).

    FAST REFINEMENT (+1): Maṅgal (the universal cheda/executor) degree-locked onto
    the kāraka or natal Śani — only inside an approved period; Mars alone also
    recurs at a MARRIAGE, so it never signals a break by itself.
    Tightest combined orb wins ties. Sources: BPHS māraka/viyoga (Śani); Jaimini/
    KP separative significators (Śani/Rāhu/Ketu); Maṅgal the universal executor.
    Kāraka is domain-driven — no native hard-coding."""
    tr = v.transits()
    nk = nadi_timing_karaka(v, profile)     # marriage-class → Venus (event-kāraka)
    nk_lon = float(v.longitudes[nk])
    nk_sign = int(nk_lon // 30)
    sev_lon = (nk_lon + 180.0) % 360.0      # 7th-from-kāraka (partner seat)
    sev_sign = int(sev_lon // 30)
    sat_nat = float(v.longitudes[Planet.SATURN])
    sat_nat_sign = int(sat_nat // 30)
    movers = [Planet.SATURN, Planet.RAHU, Planet.KETU, Planet.MARS]
    days = []

    def _dd(l1, l2):
        return abs((l1 % 30.0) - (l2 % 30.0))
    d = datetime(start.year, start.month, start.day, tzinfo=start.tzinfo)
    while d <= end:
        pos = tr.positions(d, movers)
        sat, rah, ket, mar = (float(pos[p]) for p in movers)
        ss, rs, ks, ms = (int(sat // 30), int(rah // 30),
                          int(ket // 30), int(mar // 30))
        sat_k, sat_7 = _nrel(nk_sign, ss), _nrel(sev_sign, ss)
        sat_gate = sat_k or sat_7
        node_gate = (_nrel(nk_sign, rs) or _nrel(nk_sign, ks)
                     or _nrel(sev_sign, rs) or _nrel(sev_sign, ks))
        if not (sat_gate or node_gate):     # no separator approval → skip
            d += timedelta(days=1); continue
        score, hits, orb, locked = 0, [], 0.0, False
        if sat_gate:
            score += 3
            hits.append("Śani (karma) contacts kāraka/7th [primary]")
            dl = [_dd(sat, t) for t, ok in ((nk_lon, sat_k), (sev_lon, sat_7))
                  if ok and _deg_close(sat, t)]
            if dl:
                score += 1; orb += min(dl); locked = True
                hits.append("Śani degree-lock")
        if node_gate:
            score += 2
            hits.append("Rāhu/Ketu severance (double-approval)" if sat_gate
                        else "Rāhu/Ketu severance")
        m_orbs = [_dd(mar, a) for a, ok in
                  ((nk_lon, _nrel(nk_sign, ms)), (sat_nat, _nrel(sat_nat_sign, ms)))
                  if ok and _deg_close(mar, a)]
        if m_orbs:
            score += 1; orb += min(m_orbs); locked = True
            hits.append("Maṅgal degree-lock (refine)")
        days.append((d, score, hits, orb if locked else 99.0))
        d += timedelta(days=1)
    days.sort(key=lambda x: (-x[1], x[3], x[0]))
    picked = []
    for d, sc, h, ob in days:
        if all(abs((d - p[0]).days) >= min_gap_days for p in picked):
            picked.append((d, sc, h, ob))
        if len(picked) >= top:
            break
    picked.sort(key=lambda x: x[0])
    return [dict(date=f"{x[0]:%Y-%m-%d}", score=x[1], hits=x[2],
                 orb=round(x[3], 2)) for x in picked]


def _w_nadi_ketu_sanga(v, p):
    """Standing: Ketu with/trine the Nāḍī kāraka = classical delay/break-prone."""
    nk = nadi_karaka(v, p)
    s = v.signs[nk]
    return -0.5 if v.signs[Planet.KETU] in {s, (s + 4) % 12, (s + 8) % 12} else 0.0


register_witness("nadi: Ketu-saṅga on kāraka (delay/break-prone)", "standing",
                 0.6, _w_nadi_ketu_sanga)


# ---------------------------------------------------------------------------- #
# MULTI-METHOD DAY CONVERGENCE (user-approved 2026-07-05) — the "wholesome
# reading" made scalable. A fixed library of PURE, independent day-detectors
# (each one classical technique, kept pure — never cross-contaminated), computed
# for ANY chart/domain; a day's CONVERGENCE = how many independent methods light
# it; a separate DIRECTION pass (benefics-on-the-axis vs separators) says whether
# the energised day reads as UNION/fulfil or BREAK/separation. Adding coverage =
# registering one more pure detector ONCE (serves every chart) — never a per-case
# tweak, never a date-fit. The engine reports the energised days; it does NOT
# assume any particular date is "the" event.
# ---------------------------------------------------------------------------- #
_BENEFICS = (Planet.JUPITER, Planet.VENUS, Planet.MOON)
_SEPARATORS = (Planet.SATURN, Planet.RAHU, Planet.KETU)
_DRISHTI = {Planet.JUPITER: (4, 6, 8), Planet.SATURN: (2, 6, 9),
            Planet.MARS: (3, 6, 10)}          # special aspects (+ universal 7th)


def _aspects_sign(planet, from_sign, target_sign):
    return any((from_sign + a) % 12 == target_sign
               for a in _DRISHTI.get(planet, (6,)))


def _window_direction(dt, windows, rwindows, radius_days=45):
    """Direction of the day from the engine's tested window signals. Only a
    rupture-timer LOSS/BREAK (rupture-score ≥3) is a real 'break'; a KP
    negation-lean is 'troubled' (afflicted quality, NOT a break — Affliction ≠
    Denial), a KP fulfil-lean is 'union'. Returns (label, signed_score) or None."""
    if rwindows:
        rn = min((r for r in rwindows if abs((r.start - dt).days) <= radius_days),
                 key=lambda r: abs((r.start - dt).days), default=None)
        if rn is not None and rn.kind == "LOSS/BREAK" and rn.rupture_score >= 3:
            return "break", -int(rn.rupture_score)
    if windows:
        wn = min((w for w in windows if abs((w.start - dt).days) <= radius_days),
                 key=lambda w: abs((w.start - dt).days), default=None)
        if wn is not None and (wn.kp_fulfil or wn.kp_negate):
            net = int(wn.kp_fulfil) - int(wn.kp_negate)
            if net > 0:
                return "union", net
            if net < 0:
                return "troubled", net       # afflicted axis, not a break
    return None


def day_convergence(v, profile, start, end, top=8, min_gap_days=10,
                    min_methods=3, windows=None, rwindows=None) -> list:
    """Scan each day and report where the most INDEPENDENT pure methods converge,
    with a fulfil-vs-break DIRECTION. Domain-general; deterministic. Methods:
      • BNN-golden  — transit Venus/Mars/Jupiter golden (1/5/9/conj) + degree-lock
        to the natal event-kāraka;
      • deg-return  — a marital planet transiting its OWN natal degree
        (conj/trine/opposition ±orb) — the BNN 'give much importance' rule;
      • drishti     — transit Jupiter/Saturn casting a graha-dṛṣṭi on the domain
        house OR the kāraka (Parāśari);
      • Moon-hand   — transit Moon in the domain house or golden to the kāraka
        (the fast day-hand);
      • kāraka-return — the gender/descriptor kāraka (e.g. Mars=husband for a ♀
        chart) golden + degree onto its own natal place.
    DIRECTION per day is taken FIRST from the engine's canonical, already-tested
    window signals when `windows` (candidate rows) / `rwindows` (reversal rows)
    are supplied — an elapsed LOSS/BREAK rupture window ⇒ 'break', a KP
    fulfil>negate window ⇒ 'union' — because those (not a fresh day-heuristic)
    are what reliably separate a union from a rupture (both energise the SAME
    axis). Only when no window covers the day does it fall back to the day-level
    benefic-vs-separator lean. 'union' / 'break' / 'mixed'."""
    tr = v.transits()
    ek = nadi_timing_karaka(v, profile)           # event kāraka (marriage→Venus)
    gk = nadi_karaka(v, profile)                  # descriptor kāraka (♀→Mars)
    ek_lon = float(v.longitudes[ek]); ek_sign = int(ek_lon // 30)
    gk_lon = float(v.longitudes[gk]); gk_sign = int(gk_lon // 30)
    house_sign = (v.ascendant_sign + profile.houses[0] - 1) % 12
    # DIRECTION axes (classical): union happens on the SUSTENANCE group
    # (fulfil houses, e.g. 2/7/11 for marriage); a break on the matter's own
    # DUSTHANA axis (6/8/12 counted FROM its primary house).
    fulfil_signs = {(v.ascendant_sign + h - 1) % 12 for h in profile.fulfil_houses}
    rupture_signs = {(house_sign + off) % 12 for off in (5, 7, 11)}
    nat = {p: float(v.longitudes[p]) for p in
           (Planet.VENUS, Planet.MARS, Planet.JUPITER, Planet.SATURN)}
    movers = [Planet.MOON, Planet.VENUS, Planet.MARS, Planet.JUPITER,
              Planet.SATURN, Planet.RAHU, Planet.KETU]

    def _rel(a, b):
        return (int(b // 30) - int(a // 30)) % 12

    out = []
    d = datetime(start.year, start.month, start.day, tzinfo=start.tzinfo)
    while d <= end:
        pos = {p: float(x) for p, x in tr.positions(d, movers).items()}
        active = []
        if any(_rel(ek_lon, pos[p]) in _NADI_REL and _deg_close(pos[p], ek_lon)
               for p in (Planet.VENUS, Planet.MARS, Planet.JUPITER)):
            active.append("BNN-golden")
        if any(_rel(nat[p], pos[p]) in (0, 4, 6, 8) and _deg_close(pos[p], nat[p])
               for p in nat):
            active.append("deg-return")
        if any(_aspects_sign(p, int(pos[p] // 30), house_sign)
               or _aspects_sign(p, int(pos[p] // 30), ek_sign)
               for p in (Planet.JUPITER, Planet.SATURN)):
            active.append("drishti")
        if int(pos[Planet.MOON] // 30) == house_sign \
                or _rel(ek_lon, pos[Planet.MOON]) in _NADI_REL:
            active.append("Moon-hand")
        if (_rel(gk_lon, pos[Planet.MARS]) in _NADI_REL
                and _deg_close(pos[Planet.MARS], gk_lon)):
            active.append("kāraka-return")
        if len(active) < min_methods:
            d += timedelta(days=1); continue
        # DIRECTION — signed. Two classical axes combined:
        #   (i) WHO contacts the kāraka — benefic (Guru/Śukra) = union, separator
        #       (Śani/Rāhu/Ketu) = break; tight golden/degree contact weighs 2,
        #       a looser golden/drishti 1; Ketu/Śani conj-or-oppo the kāraka +1.
        #   (ii) WHICH axis a separator/benefic sits on — a benefic on the
        #       SUSTENANCE (fulfil) signs = +1 union; a separator on the matter's
        #       DUSTHANA (rupture) signs = +1 break.
        def _contact(p):
            if _rel(ek_lon, pos[p]) in _NADI_REL:
                return 2 if _deg_close(pos[p], ek_lon) else 1
            if _aspects_sign(p, int(pos[p] // 30), ek_sign) \
                    or _aspects_sign(p, int(pos[p] // 30), house_sign):
                return 1
            return 0
        ben = sum(_contact(p) for p in (Planet.JUPITER, Planet.VENUS))
        sep = sum(_contact(p) for p in _SEPARATORS)
        ben += sum(1 for p in (Planet.JUPITER, Planet.VENUS)
                   if int(pos[p] // 30) in fulfil_signs)          # benefic on union axis
        sep += sum(1 for p in _SEPARATORS
                   if int(pos[p] // 30) in rupture_signs)          # separator on break axis
        if _rel(ek_lon, pos[Planet.KETU]) in (0, 6):    # Ketu cut on the kāraka
            sep += 1
        score = ben - sep
        # PRIMARY direction = the engine's tested window signal covering this day;
        # the day-lean above is only the fallback.
        wdir = _window_direction(d, windows, rwindows)
        if wdir is not None:
            direction, score = wdir
        else:
            direction = ("union" if score > 0
                         else "troubled" if score < 0 else "mixed")
        out.append((d, len(active), active, direction, score))
        d += timedelta(days=1)
    # rank by method-count, then by |direction| (clearer signal first)
    out.sort(key=lambda x: (-x[1], -abs(x[4]), x[0]))
    picked = []
    for row in out:
        if all(abs((row[0] - p[0]).days) >= min_gap_days for p in picked):
            picked.append(row)
        if len(picked) >= top:
            break
    picked.sort(key=lambda x: x[0])
    return [dict(date=f"{x[0]:%Y-%m-%d}", methods=x[1], active=x[2],
                 direction=x[3], score=x[4]) for x in picked]


def _trine_windows(tr, transit, natal_lon, start, end, orb=9.0):
    """Windows where a transit holds a Nāḍī golden relation (conjunction or the
    1/5/9 trine — NOT the 7th; professional BNN standard) to a natal point —
    Nāḍī reads these as 'with'. Slow movers only (Jupiter/Saturn)."""
    out = []
    for ang in (0.0, 120.0, 240.0):
        out += [(w.start, w.end) for w in
                tr.conjunction_windows(transit, (natal_lon + ang) % 360.0,
                                       start, end, orb=orb, step_days=10.0)]
    return out


def _kakshya_windows(tr, start, end):
    out = []
    for p in (Planet.JUPITER, Planet.SATURN):
        out += [(w.start, w.end) for w in tr.kakshya_windows(p, start, end)]
    return out


def _in(when, windows):
    return any(a <= when <= b for a, b in windows)


def _chain_lords(v, when, levels=3):
    return [c.lord for c in v.current_dasha("vimshottari", when, levels=levels)]


def _karaka_planets(v, profile):
    ks = {p for nm, p in v.chara_karakas().items() if nm in profile.karakas}
    if profile.natural_karaka:
        ks.add(profile.natural_karaka)
    return ks


def _domain_signs(v, profile):
    return {(v.ascendant_sign + h - 1) % 12 for h in profile.houses}


def _pratyantar_midpoints(v, start, end) -> list:
    """Deterministic evaluation dates: the MIDPOINT of every Vimśottari
    pratyantar intersecting [start, end] (clipped). Replaces the old start+k·step
    grid, whose landing spot inside each pratyantar was an accident of the scan
    parameters — the same chart could rank windows differently at step 45 vs 60."""
    out = []
    for m in v.dasha("vimshottari", levels=3):
        if m.end <= start or m.start >= end:
            continue
        for a in (m.sub_periods or []):
            if a.end <= start or a.start >= end:
                continue
            for p in (a.sub_periods or []):
                if p.end <= start or p.start >= end:
                    continue
                s2, e2 = max(p.start, start), min(p.end, end)
                out.append(s2 + (e2 - s2) / 2)
    return sorted(out)


@dataclass
class ReversalRow:
    start: datetime
    chain: list
    kp_rupture: int
    separators_running: bool
    break_house_dt: bool
    reversal_saham_dt: bool
    lagna_dark_with_malefic: bool
    kp_fulfil: int = 0                     # manifestation lit in the SAME window?
    standing: float = 0.0                  # natal witness-balance on the matter

    @property
    def rupture_score(self) -> int:
        return (int(self.kp_rupture >= 2) + int(self.separators_running)
                + int(self.break_house_dt) + int(self.reversal_saham_dt)
                + int(self.lagna_dark_with_malefic))

    @property
    def kind(self) -> str:
        """Disambiguate a dusthāna-from-the-house activation as a MULTI-NODAL
        pattern, not a single rule. The 6/8/12-from-H houses light up BOTH for
        leaving the matter (loss) AND for upgrading it. The verdict is the balance
        of PRO testimony — the timing fulfilment (AD/PD) PLUS the STANDING natal
        pattern on the matter (benefic dṛṣṭi, a dignified/strong lord, a rāja-yoga,
        good argala/SAV) — against the rupture. A chart whose matter-house is
        natally blessed rarely breaks; it upgrades. A true LOSS/BREAK needs the
        rupture lit, the fulfilment absent, a dark Lagna under malefics, AND a
        non-positive standing pattern."""
        pro = self.kp_fulfil >= 2 or self.standing >= 1.0
        if self.rupture_score >= 2 and pro:
            return "CHANGE/UPGRADE"
        if (self.rupture_score >= 3 and self.kp_fulfil < 2
                and self.lagna_dark_with_malefic and self.standing < 1.0):
            return "LOSS/BREAK"
        return "transition-watch"


def reversal_map(v, profile, start, end, step_days=7) -> list[ReversalRow]:
    """Time the matter's REVERSAL as its own event, from DIFFERENT significators:
    the 6/8/12-from-the-matter houses, the separators (Saturn + nodes + the
    6th-from-house lord), the reversal Saham, the double-transit on the breaking
    house, and a DARK Lagna under a malefic/node daśā (de-materialization)."""
    tr = v.transits()
    _, kps = _kp_view(v)                       # KP on the KP-ayanāṃśa / Placidus chart
    lagna = v.ascendant_sign
    primary = profile.houses[0]
    rupture_houses = {(primary - 1 + off - 1) % 12 + 1 for off in (6, 8, 12)}
    break_house = (primary - 1 + 6 - 1) % 12 + 1          # 6th-from-the-matter
    sep_lord = v.house_lord(break_house)
    separators = {Planet.SATURN, Planet.RAHU, Planet.KETU, sep_lord}
    nodes_sat = {Planet.SATURN, Planet.RAHU, Planet.KETU}
    bh_dt = _dt_windows(tr, break_house, start, end)
    saham_dt = []
    if profile.reversal_saham:
        sah = v.sahams().get(profile.reversal_saham)
        if sah:
            saham_dt = _dt_windows(tr, (sah.sign_index - lagna) % 12 + 1, start, end)
    standing, _ = standing_balance(v, profile)   # natal multi-nodal pattern (once)
    rows = []
    for d in _pratyantar_midpoints(v, start, end):   # deterministic (no grid jitter)
        chain = _chain_lords(v, d, levels=3)
        kp = sum(len(set(kps.planet_signifies(l)) & rupture_houses) for l in chain)
        # judge fulfilment co-occurrence from the TIMING lords (AD+PD), not the
        # mahādaśā — else a domain-lord MD (e.g. the 7th-lord running for 20y)
        # permanently inflates fulfilment and masks a real loss.
        fulfil = sum(len(set(kps.planet_signifies(l)) & profile.fulfil_houses)
                     for l in chain[1:])
        dark = not _slow_on_sign(tr, lagna, d)
        rows.append(ReversalRow(
            start=d, chain=[c.value[:2] for c in chain], kp_rupture=kp,
            separators_running=any(l in separators for l in chain),
            break_house_dt=_in(d, bh_dt), reversal_saham_dt=_in(d, saham_dt),
            lagna_dark_with_malefic=dark and any(l in nodes_sat for l in chain),
            kp_fulfil=fulfil, standing=standing))
    return rows


def candidate_map(v, profile, start, end, step_days=7) -> list[WindowEvidence]:
    """Full-span candidate ledger for the matter's MANIFESTATION."""
    tr = v.transits()
    _, kps = _kp_view(v)                       # KP on the KP-ayanāṃśa / Placidus chart
    lagnesh = v.house_lord(1)
    lagna_sign = v.ascendant_sign
    karakas = _karaka_planets(v, profile)
    dom_signs = _domain_signs(v, profile)

    house_dt, lord_dt, bnn_w = [], [], []
    for h in profile.houses:
        house_dt += _dt_windows(tr, h, start, end)
        lord = v.house_lord(h)
        lord_dt += _dt_windows(tr, (v.signs[lord] - lagna_sign) % 12 + 1, start, end)
        bnn_w += _conj_windows(tr, Planet.JUPITER, v.longitudes[lord], start, end)
    for p in karakas:
        bnn_w += _conj_windows(tr, Planet.JUPITER, v.longitudes[p], start, end)
    saham_dt = []
    if profile.saham:
        sah = v.sahams().get(profile.saham)
        if sah:
            saham_dt = _dt_windows(tr, (sah.sign_index - lagna_sign) % 12 + 1,
                                   start, end)
    kak_w = _kakshya_windows(tr, start, end)
    # --- node: Bhinnāṣṭakavarga DELIVERY — the matter's OWN significators (its
    # kārakas + the slow universal timers) deliver a transit only in proportion
    # to the bindus they hold in their own BAV (BPHS Aṣṭakavarga gochara). Graded
    # fraction, domain-general (reads the profile's kārakas, never a native). ----
    # Ashtakavarga is defined only for the seven grahas Sun..Saturn — nodes
    # (Rāhu/Ketu) have no BAV, so a nodal kāraka simply doesn't contribute here.
    bav_planets = [p for p in dict.fromkeys([Planet.JUPITER, Planet.SATURN, *karakas])
                   if p in _ASHTAKAVARGA_PLANETS]
    bav_windows = {p: [(w.start, w.end) for w in tr.kakshya_windows(p, start, end)]
                   for p in bav_planets}

    def _bav_delivery(when) -> float:
        if not bav_planets:
            return 0.0
        return sum(1 for p in bav_planets if _in(when, bav_windows[p])) / len(bav_planets)

    muntha = {y: v.varshaphal(y).muntha_house for y in range(start.year, end.year + 1)}

    # --- node: gochara reckoned FROM THE MOON (classical Janma-rāśi gochara) ---
    moon_sign = v.signs[Planet.MOON]
    moon_dt = []
    for h in profile.houses:
        sgn = (moon_sign + h - 1) % 12
        moon_dt += _dt_windows(tr, (sgn - lagna_sign) % 12 + 1, start, end)

    # --- node: double-transit on the OTHER fulfilment houses + their lords -----
    # (the primary house + its lord are already covered by the Lagna-based node)
    fulfil_dt = []
    for h in sorted(profile.fulfil_houses):
        if h in profile.houses:
            continue
        fulfil_dt += _dt_windows(tr, h, start, end)
        flord = v.house_lord(h)
        fulfil_dt += _dt_windows(tr, (v.signs[flord] - lagna_sign) % 12 + 1, start, end)

    # --- node: Tājika Varṣeśa / Muntha-lord signifies the matter (per year) ----
    tajika = {}
    for y in range(start.year, end.year + 1):
        vp = v.varshaphal(y)
        hit = vp.muntha_house in profile.fulfil_houses
        for lord in (vp.lagna_lord, vp.muntha_lord):
            if lord and set(kps.planet_signifies(lord)) & profile.fulfil_houses:
                hit = True
        tajika[y] = hit

    def _kp_star_hit(when) -> bool:
        """KP: a slow planet transiting the star of a fulfilment-significator."""
        pos = tr.positions(when, [Planet.JUPITER, Planet.SATURN])
        for p in (Planet.JUPITER, Planet.SATURN):
            nl = _nakshatra_lord(pos[p])
            if set(kps.planet_signifies(nl)) & profile.fulfil_houses:
                return True
        return False

    # --- node: Jaimini Arudha-axis gochara (the matter's Arudha + 2nd-from-it) ---
    ar = v.arudhas()
    axis_signs = set()
    for k in profile.arudhas:
        s = ar.get(k)
        if s is not None:
            axis_signs.add(s)
            axis_signs.add((s + 1) % 12)            # 2nd-from-the-Arudha (sustenance)

    def _arudha_axis_hit(when) -> bool:
        for p in (Planet.JUPITER, Planet.SATURN):   # slow benefic: occupation OR dṛṣṭi
            ps = tr.transit_sign(when, p)
            if ps in axis_signs or any((ps + a) % 12 in axis_signs
                                       for a in _ASPECT_OFFSETS[p]):
                return True
        for p in karakas:                            # domain kāraka (e.g. DK): conjunction
            if tr.transit_sign(when, p) in axis_signs:
                return True
        return False

    # --- NĀḌĪ: Guru-jeeva × kāraka + Śani karma-sanction ----------------------
    nk = nadi_timing_karaka(v, profile)     # marriage-class → Venus (event-kāraka)
    nk_lon = float(v.longitudes[nk])
    nadi_jeeva_w = _trine_windows(tr, Planet.JUPITER, nk_lon, start, end)
    nadi_sat_w = (_trine_windows(tr, Planet.SATURN, nk_lon, start, end)
                  + _trine_windows(tr, Planet.SATURN,
                                   float(v.longitudes[Planet.JUPITER]),
                                   start, end))
    fulfil_signs = {(lagna_sign + h - 1) % 12 for h in profile.fulfil_houses}

    def _nadi_sanction(when) -> bool:
        return (_in(when, nadi_sat_w)
                or tr.transit_sign(when, Planet.SATURN) in fulfil_signs)

    # --- node: Bhṛgu Bindu (Moon–Rāhu midpoint) activated by a slow mover -----
    bb_sign = int(v.bhrigu_bindu() // 30)

    def _bb_hit(when) -> bool:
        for p in (Planet.JUPITER, Planet.SATURN):
            ps = tr.transit_sign(when, p)
            if ps == bb_sign or any((ps + a) % 12 == bb_sign for a in _ASPECT_OFFSETS[p]):
                return True
        return False

    # --- DAŚĀ-SYSTEM CATALOGUE: instantiate each system's active-significator
    # lookup ONCE (per-system caching lives inside the adapter), then per window
    # set a generic signal the family-generated node reads. Adding a system =
    # one DASHA_SYSTEMS entry; no change here.
    panel = build_panel(profile)

    def _signifies_matter(lord) -> bool:
        return bool(set(kps.planet_signifies(lord)) & profile.fulfil_houses) \
            or lord in karakas

    dasha_lookups = {name: build(v, profile, start, end)
                     for name, build in DASHA_SYSTEMS.items()}

    # Outcome valence of the daśā lords (functional nature for THIS lagna).
    fnature = v.functional_nature()
    fmarakas = set(v.marakas())

    def _chain_valence(lords) -> float:
        sc = 0.0
        for l in lords:
            nat = fnature.get(l, "")
            sc += 1.0 if nat == "Benefic" else (-1.0 if nat == "Malefic" else 0.0)
            if l in fmarakas:
                sc -= 0.5
        return max(-1.0, min(1.0, sc / max(1, len(lords))))

    rows = []
    for d in _pratyantar_midpoints(v, start, end):   # deterministic (no grid jitter)
        chain = _chain_lords(v, d, levels=3)
        f = n = 0
        for lord in chain:
            a, b = _kp_score(kps, lord, profile)
            f += a
            n += b
        deep = v.current_dasha("vimshottari", d, levels=5)
        su = v.sudarshana(d)
        chara = v.current_chara_dasha(d, levels=2)
        sig = {f"dasha::{name}":
               (1.0 if any(_signifies_matter(p) for p in look(d)) else 0.0)
               for name, look in dasha_lookups.items()}
        we = WindowEvidence(
            start=d, chain=[c.value[:2] for c in chain],
            kp_fulfil=f, kp_negate=n,
            karaka_in_chain=any(l in karakas for l in chain),
            karaka_sukshma=any(c.lord in karakas for c in deep[3:]),
            lagnesh_in_chain=lagnesh in chain,
            lagna_activators=_slow_on_sign(tr, lagna_sign, d),
            house_double_transit=_in(d, house_dt),
            lord_double_transit=_in(d, lord_dt),
            saham_double_transit=_in(d, saham_dt),
            bnn=_in(d, bnn_w),
            kakshya=_in(d, kak_w),
            karaka_kakshya=_bav_delivery(d),
            varshaphal_muntha=muntha.get(d.year) in profile.houses,
            chara_ad=" > ".join(c.note for c in chara),
            sudarshana_hit=any(s in dom_signs for s in
                               (su.lagna_month_sign, su.moon_month_sign,
                                su.lagna_year_sign, su.moon_year_sign)),
            gochara_from_moon=_in(d, moon_dt),
            fulfil_house_dt=_in(d, fulfil_dt),
            kp_star_transit=_kp_star_hit(d),
            tajika_sig=tajika.get(d.year, False),
            arudha_axis=_arudha_axis_hit(d),
            bb_active=_bb_hit(d),
            func_valence=_chain_valence(chain),
            nadi_jeeva=_in(d, nadi_jeeva_w),
            nadi_karma=_nadi_sanction(d),
            sade_sati=tr.sade_sati(d).get("active", False),
            signals=sig,
        )
        we.panel = panel
        rows.append(we)
    _score_rows(rows)
    return rows


# ---------------------------------------------------------------------------- #
# The DECISION RULE — convergence-gating + information-weighting (slices 3+4)
#
# Why not just sum the votes: with a wide node-set, a flat sum lets many trivial
# nodes drown the few high-information ones, and "everything lights up". Two
# principled fixes (NEITHER is calibration to a native's history):
#   • INFORMATION-WEIGHTING — weight a firing node by its specificity 1−p, where p
#     is how often it fires across the span. A node that fires on every window
#     carries no discriminating information (weight→0); a rare one carries a lot.
#   • CONVERGENCE-GATING — group nodes into INDEPENDENT paddhatis (daśā, KP,
#     gochara, Saham, Sudarśana, Varṣaphal, Aṣṭakavarga, …) and require ≥2 distinct
#     systems to agree; a lone-system window is discounted. (The project's Cardinal
#     Rule, made mechanical.)
# The result is `salience` — the ranking metric. `domain_score`/`convergence` stay
# the raw transparent sums.
# ---------------------------------------------------------------------------- #
_PADDHATI_RULES = [
    ("nadi:", "nadi"),
    ("daśā", "dasha"), ("Lagneśa", "dasha"),
    ("Arudha", "jaimini"), ("Upapada", "jaimini"),
    ("Bhṛgu Bindu", "nadi"),
    ("KP", "kp"),
    ("double-transit", "gochara"), ("gochara", "gochara"),
    ("Lagna materialization", "gochara"), ("BNN", "gochara"),
    ("Saham", "saham"),
    ("Sudarśana", "sudarshana"),
    ("Muntha", "varshaphal"), ("Varṣeśa", "varshaphal"), ("Tājika", "varshaphal"),
    ("Kakṣyā", "ashtakavarga"),
]


# ---------------------------------------------------------------------------- #
# VERDICT layer (user-approved 2026-07-02) — the committed yes/no decision rule
# a KP professional follows, made deterministic. Sources: KP Readers III & VI
# (promise vs denial by the cusp sub-lord's house-groups; event stands DELIVERED
# once its significators' daśā has run), BPHS daśā-phala (the daśā delivers what
# the natal chart promises). No calibration: confidence = convergence count only.
# ---------------------------------------------------------------------------- #
@dataclass
class Verdict:
    answer: str          # "YES" | "NO (denied)" | "NOT-YET" | "UNCERTAIN"
    confidence: str      # "HIGH" | "MEDIUM" | "LOW"
    best_window: str     # "YYYY-MM-DD" of the committed window ("" if none)
    chain: str           # daśā chain at that window
    systems: int         # independent systems converging there
    quality: str         # affliction/outcome texture — QUALITY, never existence
    reasons: list
    next_window: str = ""    # strongest UPCOMING window after asof ("" if none)
    next_chain: str = ""


def domain_verdict(v, profile, rows, asof, rrows=None,
                   min_elapsed_days=30) -> Verdict:
    """Committed retrodiction for "has this matter's event happened in the scanned
    window?" — decides from (1) KP promise-vs-denial, (2) elapsed high-convergence
    windows, (3) convergence count as confidence. Affliction NEVER vetoes
    existence; it only sets the quality (KP: affliction = troubled event, denial =
    no event).

    RUPTURE matters (``profile.rupture_matter``, e.g. divorce): the fulfilment
    scan times the AXIS (which also spikes for the marriage itself), so elapsed
    evidence comes from the REVERSAL timer instead — pass its rows as ``rrows``;
    an elapsed LOSS/BREAK window is the delivered event, its rupture-score the
    confidence.

    A window only counts as ELAPSED once it has matured ``min_elapsed_days``
    before ``asof`` — otherwise a forward scan's very first row (which starts AT
    the scan boundary, i.e. today) masquerades as delivered evidence.

    Kept SIMPLE by design (user rollback, 2026-07-04): the completion-grade
    machinery (panel votes, ATTEMPTED/CONTESTED, attempt-arcs, candidate
    clusters) was removed — the verdict commits YES / NO / NOT-YET / UNCERTAIN
    only; whether an elapsed axis-window was the completed matter vs an attempt
    is left to the user's own account and the AI's multivalent reading."""
    pt = promise_and_tempo(v, profile)
    sig = set(pt.cusp_signifies)
    denied = ((not pt.promised) and bool(sig & profile.negate_houses))
    bal, _ = standing_balance(v, profile)
    quality = ("blessed/clean" if bal >= 1.0
               else "afflicted/troubled" if bal < 0 else "mixed")
    reasons = [f"KP: {primary_label(profile)} sub-lord {pt.cusp_sublord} "
               f"signifies {sorted(sig)} (fulfil={sorted(profile.fulfil_houses)}, "
               f"negate={sorted(profile.negate_houses)})",
               f"standing balance {bal:+.2f} → quality: {quality} "
               "(quality ≠ existence)"]
    nn = nadi_nature(v, profile)
    if nn:
        reasons.append(f"nāḍī kāraka-saṅga ({nadi_karaka(v, profile).value}): {nn}")

    def _matured(r):
        return (asof - r.start).days >= min_elapsed_days

    # strongest UPCOMING window (committed "agla window" for the narration)
    upcoming = [r for r in rows if r.start > asof]
    nxt = max(upcoming, key=lambda r: r.salience) if upcoming else None
    nw = f"{nxt.start:%Y-%m-%d}" if nxt else ""
    nc = ">".join(nxt.chain) if nxt else ""

    if denied:
        conf = "HIGH" if not (sig & profile.fulfil_houses) else "MEDIUM"
        reasons.append("sub-lord signifies ONLY the negation group → denial")
        return Verdict("NO (denied)", conf, "", "", 0, quality, reasons, nw, nc)
    if not pt.promised:
        reasons.append("sub-lord signifies neither group decisively")
        return Verdict("UNCERTAIN", "LOW", "", "", 0, quality, reasons, nw, nc)
    if profile.rupture_matter and rrows is not None:
        hits = [r for r in rrows
                if r.kind == "LOSS/BREAK" and _matured(r)]
        if hits:
            best = max(hits, key=lambda r: (r.rupture_score, r.start))
            conf = ("HIGH" if best.rupture_score >= 4
                    else "MEDIUM" if best.rupture_score >= 3 else "LOW")
            reasons.append(f"rupture promised + elapsed LOSS/BREAK window "
                           f"{best.start:%Y-%m-%d} (rupture-score "
                           f"{best.rupture_score}/5) → the break stands delivered")
            return Verdict("YES", conf, f"{best.start:%Y-%m-%d}",
                           ">".join(best.chain), best.rupture_score, quality,
                           reasons, nw, nc)
        reasons.append("rupture promised, but no LOSS/BREAK window has elapsed "
                       "in the scanned span → not yet (or outside this span)")
        return Verdict("NOT-YET", "MEDIUM", "", "", 0, quality, reasons, nw, nc)
    elapsed = [r for r in rows if _matured(r) and r.systems_firing >= 2]
    if elapsed:
        best = max(elapsed, key=lambda r: r.salience)
        # confidence = # of INDEPENDENT schools converging (max 5)
        conf = ("HIGH" if best.systems_firing >= 4
                else "MEDIUM" if best.systems_firing == 3 else "LOW")
        reasons.append(
            f"promised + elapsed window {best.start:%Y-%m-%d} "
            f"({best.systems_firing} systems) → the event stands delivered; "
            "afflicted standing (if any) is the matter's QUALITY, not denial")
        return Verdict("YES", conf, f"{best.start:%Y-%m-%d}",
                       ">".join(best.chain), best.systems_firing, quality,
                       reasons, nw, nc)
    reasons.append("promised, but no ≥2-system window has elapsed in the scanned "
                   "span → not yet (or the event lies outside this span)")
    return Verdict("NOT-YET", "MEDIUM", "", "", 0, quality, reasons, nw, nc)


def primary_label(profile) -> str:
    return f"H{profile.houses[0]}-cusp"


def _paddhati(name: str) -> str:
    """Map a node name to its fine-grained technique group (kept for the ledger
    and tests). The convergence GATE uses `_school` (the independent parent), not
    this — see `_school`."""
    for needle, group in _PADDHATI_RULES:
        if needle in name:
            return group
    return "misc"


# The FIVE genuinely-independent schools. Sudarśana, Aṣṭakavarga, Vimśottari and
# gochara are SUB-TOOLS of Parāśari (BPHS) — NOT independent schools — so they
# collapse into "parashari"; counting them as separate convergence inflated
# confidence (a window lit by dasha+gochara+Sudarśana is ONE school agreeing with
# itself, not three). Verified against the classical taxonomy (2026-07-05).
_SCHOOLS = ("parashari", "jaimini", "kp", "tajika", "nadi")
_SCHOOL_RULES = [
    ("nadi:", "nadi"), ("BNN", "nadi"), ("Bhṛgu Bindu", "nadi"),
    ("KP", "kp"),
    ("Arudha", "jaimini"), ("Upapada", "jaimini"), ("argala", "jaimini"),
    ("daśā[chara]", "jaimini"), ("daśā[nārāyaṇa]", "jaimini"),
    ("daśā[sudasā]", "jaimini"),
    ("Muntha", "tajika"), ("Varṣeśa", "tajika"), ("Tājika", "tajika"),
    ("Saham", "tajika"),
    # everything else = Parāśari corpus (Vimśottari, gochara, yogas, Ṣaḍbala,
    # Aṣṭakavarga, Sudarśana, Lagna materialization, māraka, avasthā …)
]


def _school(name: str) -> str:
    """Collapse a witness to its INDEPENDENT parent school (one of `_SCHOOLS`).
    Parāśari is the default corpus."""
    for needle, sch in _SCHOOL_RULES:
        if needle in name:
            return sch
    return "parashari"


def _score_rows(rows: list) -> None:
    """Set `salience` and `systems_firing` on each row: info-weighted votes,
    grouped by INDEPENDENT SCHOOL (not fine sub-technique), gated on ≥2 schools
    converging. `systems_firing` is therefore the count of independent schools
    (max 5) lighting the window — the true convergence signal."""
    if not rows:
        return
    total = len(rows)
    fire: dict = {}
    for r in rows:
        for n, _ in r.firing_nodes():
            fire[n] = fire.get(n, 0) + 1
    for r in rows:
        groups: dict = {}
        for n, c in r.firing_nodes():
            info = 1.0 - fire[n] / total            # specificity (rare ⇒ ~1)
            grp = _school(n)                         # independent-school gate
            groups[grp] = groups.get(grp, 0.0) + abs(c) * info
        n_systems = len(groups)
        gate = 1.0 if n_systems >= 2 else 0.4       # ≥2 INDEPENDENT schools
        # KP PRIMARY TIMING RULE (KP Readers; the #1 discriminator): the running
        # daśā-chain (MD>AD>PD) lords must SIGNIFY the matter's fulfil-houses for
        # the period to deliver — otherwise transit convergence alone cannot make
        # an event happen. `kp_fulfil`/`kp_negate` already hold the chain-lords'
        # fulfil/negate significations; here they act as a graded DISCRIMINATOR
        # (not a diluted single vote): a window whose daśā-lords do not signify
        # the matter is strongly damped, however many transits pile on. Graded
        # (never a hard 0) so it discriminates without being sole judge.
        kf, kn = getattr(r, "kp_fulfil", 0), getattr(r, "kp_negate", 0)
        sig = (1.0 if kf >= max(1, kn) else 0.6 if kf >= 1 else 0.3)
        r.systems_firing = n_systems
        r.salience = round(sum(groups.values()) * gate * sig, 3)


def school_report(v, profile, rows) -> list:
    """LAYER-1 per-school timing breakdown (the two-layer view). For each of the 5
    independent schools, find WHERE it independently points — the window carrying
    the most of that school's info-weighted vote — or mark it 'abstains' when the
    school never fires (thin/absent coverage, so it casts no vote rather than a
    false one). Layer-2 convergence is then simply how many schools cluster on the
    committed window (systems_firing). Existence stays with domain_verdict; this
    surfaces agreement/disagreement so a wrong school is visible, not blended
    away."""
    if not rows:
        return []
    total = len(rows)
    fire: dict = {}
    for r in rows:
        for n, _ in r.firing_nodes():
            fire[n] = fire.get(n, 0) + 1
    out = []
    for sch in _SCHOOLS:
        best, best_str = None, 0.0
        for r in rows:
            s = sum(abs(c) * (1.0 - fire[n] / total)
                    for n, c in r.firing_nodes() if _school(n) == sch)
            if s > best_str:
                best_str, best = s, r
        if best is None:
            out.append(dict(school=sch, fires=False, window="",
                            chain="", strength=0.0))
        else:
            out.append(dict(school=sch, fires=True,
                            window=f"{best.start:%Y-%m-%d}",
                            chain=">".join(best.chain),
                            strength=round(best_str, 2)))
    return out


# ---------------------------------------------------------------------------- #
# Rendering
# ---------------------------------------------------------------------------- #
def _fmt_tempo(pt: PromiseTempo) -> list:
    L = ["  PROMISE & TEMPO (Ṣaḍbala · Iṣṭa/Kaṣṭa · Avasthā · Varga · Argala · SAV):"]
    L.append(f"    promised={pt.promised} (7th-cusp-style sub-lord {pt.cusp_sublord} "
             f"signifies {pt.cusp_signifies})")
    for h, (strong, ish, kash) in pt.lord_strength.items():
        L.append(f"    H{h} lord: strong={strong} Iṣṭa={ish} Kaṣṭa={kash} "
                 f"SAV={pt.house_sav[h]}")
    for p, (strong, av, ish) in pt.karaka_strength.items():
        L.append(f"    kāraka {p.value}: strong={strong} avasthā={av} Iṣṭa={ish} "
                 f"varga-ok={pt.varga_ok.get(p)}")
    L.append(f"    Argala net on house = {pt.argala_net:+d}   "
             f"→ TEMPO: {pt.tempo}")
    for nb in pt.notes:
        L.append(f"      · {nb}")
    return L


def _row_line(r: WindowEvidence) -> str:
    return (f"  {r.start:%Y-%m-%d} {'>'.join(r.chain):<9} "
            f"{r.kp_fulfil}/{r.kp_negate:<3} "
            f"{'Y' if r.karaka_in_chain else '-'}{'Y' if r.karaka_sukshma else '-'} "
            f"{'Y' if r.lagnesh_in_chain else '-'} "
            f"{(','.join(r.lagna_activators) or '—'):<22} "
            f"{'Y' if r.house_double_transit else '-'}{'Y' if r.lord_double_transit else '-'} "
            f"{'Y' if r.saham_double_transit else '-'} "
            f"{'Y' if r.bnn else '-'} {'Y' if r.kakshya else '-'} "
            f"{'Y' if r.varshaphal_muntha else '-'}  "
            f"{'Y' if r.sudarshana_hit else '-'} "
            f"{'Y' if r.gochara_from_moon else '-'}{'Y' if r.fulfil_house_dt else '-'}"
            f"{'Y' if r.kp_star_transit else '-'}{'Y' if r.tajika_sig else '-'}"
            f"{'Y' if r.arudha_axis else '-'}{'Y' if r.bb_active else '-'}  "
            f"D:{sum(1 for x in r.signals.values() if x)}/{len(r.signals)}  "
            f"{r.convergence}")


def render_domain(v, profile, start, end) -> str:
    pt = promise_and_tempo(v, profile)
    rows = candidate_map(v, profile, start, end)
    lagnesh = v.house_lord(1)
    L = [f"# EVENT-EVIDENCE PACK — domain: {profile.name.upper()}",
         f"  Lagna={SIGNS[v.ascendant_sign]} | Lagnesh={lagnesh.value} in "
         f"{SIGNS[v.signs[lagnesh]]} | Moon(mind)={SIGNS[v.signs[Planet.MOON]]}",
         f"  Houses={profile.houses} KP fulfil={sorted(profile.fulfil_houses)} "
         f"negate={sorted(profile.negate_houses)} kāraka={profile.karakas}"
         f"+{profile.natural_karaka.value if profile.natural_karaka else '-'} "
         f"Saham={profile.saham} Varga=D{profile.varga}", ""]
    # completeness gate — every pack declares its own coverage + the known RED gaps
    from interpreter.coverage import coverage_summary
    L += [coverage_summary(), ""]
    L += _fmt_tempo(pt)
    # STANDING WITNESS PATTERN — the natal multi-nodal weight on the matter
    bal, fired = standing_balance(v, profile)
    L += ["", f"  STANDING WITNESS PATTERN (natal nodes on the matter) — "
          f"net balance = {bal:+.2f} "
          f"({'PRO/blessed ⇒ tends to upgrade not break' if bal >= 1.0 else ('afflicted ⇒ loss possible' if bal < 0 else 'mixed')}):"]
    for nm, c in sorted(fired, key=lambda x: -abs(x[1])):
        L.append(f"    {'＋' if c > 0 else '－'} {nm}: {c:+.2f}")
    L += ["", "  CANDIDATE LEDGER (cols: KPf/n · kār+sūkṣ · lgnś · Lagna-activation · "
          "Hdt+Ldt · Sdt · BNN · Kakṣ · Muntha · Sud · "
          "[Moon-gochara·Fulfil-dt·KPstar·Tājika·Arudha-axis·BhṛguBindu] · D:daśā-catalogue/n · conv):"]
    for r in sorted(rows, key=lambda x: x.start):
        L.append(_row_line(r))
    top = sorted(rows, key=lambda x: (-x.salience, x.start))[:5]
    L += ["", "  TOP-RANKED WINDOWS (by SALIENCE = info-weighted votes, gated on ≥2 "
          "independent systems agreeing — the daśā is only one of them):"]
    for r in top:
        L.append(f"    {r.start:%Y-%m-%d} {'>'.join(r.chain):<9} "
                 f"salience={r.salience} ({r.systems_firing} systems) conv={r.convergence}"
                 f"  KP {r.kp_fulfil}/{r.kp_negate}  Lagna[{','.join(r.lagna_activators) or '—'}]"
                 f"  chara {r.chara_ad}")
    if top:
        L.append(f"    nodes firing at {top[0].start:%Y-%m-%d}: "
                 + ", ".join(n for n, _ in top[0].firing_nodes()))

    # Reversal as its OWN event (separators + dark Lagna + reversal saham)
    primary = profile.houses[0]
    break_house = (primary - 1 + 6 - 1) % 12 + 1
    rev = reversal_map(v, profile, start, end)
    losses = sorted([r for r in rev if r.kind == "LOSS/BREAK"],
                    key=lambda x: (-x.rupture_score, x.start))
    changes = sorted([r for r in rev if r.kind == "CHANGE/UPGRADE"],
                     key=lambda x: (-x.rupture_score, x.start))
    L += ["", f"  TRANSITION / REVERSAL of the matter (6/8/12-from-H{primary}; "
          f"separators Saturn+nodes+H{break_house}-lord"
          + (f"; saham {profile.reversal_saham}" if profile.reversal_saham else "")
          + "):"]
    L.append("    A dusthāna-from-the-house activation is a LOSS only if the "
             "fulfilment signature is ABSENT; if fulfilment co-occurs it is a "
             "positive CHANGE/UPGRADE (old ended, better gained).")
    if losses:
        L.append("    ▸ true LOSS/BREAK windows (rupture, fulfilment absent, dark Lagna):")
        for r in losses[:3]:
            L.append(f"        {r.start:%Y-%m-%d} {'>'.join(r.chain):<9} "
                     f"rupture={r.rupture_score} fulfil={r.kp_fulfil}")
    else:
        L.append("    ▸ NO pure LOSS/BREAK window — the dusthāna activations all "
                 "co-occur with fulfilment ⇒ CHANGE/UPGRADE, not loss.")
    if changes:
        L.append("    ▸ CHANGE/UPGRADE windows (leaving old + gaining better):")
        for r in changes[:3]:
            L.append(f"        {r.start:%Y-%m-%d} {'>'.join(r.chain):<9} "
                     f"rupture={r.rupture_score} fulfil={r.kp_fulfil}")

    L += ["", "  NB: EVIDENCE, not verdict. Read it MULTIVALENTLY — a node colours "
          "the TYPE (sudden/court/unconventional), a dark Lagna lowers "
          "materialization-INTENSITY (low-key) but does not deny a Saham/kāraka-lit "
          "event, and the reversal block is timed independently — a strong benefic "
          "elsewhere does NOT veto a converged reversal."]
    return "\n".join(L)


def scan_domains(v, start, end) -> str:
    """Open question: which life-area STANDS OUT most across [start, end]?

    Ranked by stand-out = peak SALIENCE minus that domain's own mean salience
    over the window, so a broad-significator area cannot win merely by running a
    high background — it must genuinely spike (and on ≥2 converging systems)."""
    L = ["# DOMAIN MACRO-SCAN (open question) — life-areas by stand-out spike"]
    ranked = []
    for name, profile in DOMAIN_PROFILES.items():
        rows = candidate_map(v, profile, start, end)
        if not rows:
            continue
        scores = [r.salience for r in rows]
        peak_row = max(rows, key=lambda x: x.salience)
        standout = peak_row.salience - (sum(scores) / len(scores))
        ranked.append((round(standout, 2), peak_row.salience, name, peak_row))
    for standout, peak, name, row in sorted(ranked, reverse=True):
        L.append(f"  {name:<10} stand-out=+{standout:<4} (peak {peak} around "
                 f"{row.start:%Y-%m}, M>A>P {'>'.join(row.chain)})")
    L.append("")
    L.append("  → Take the top 2-3 here as a SHORTLIST, then run the full per-domain "
             "pack on each and let the AI judge. The per-domain pack is authoritative.")
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description="Domain-general event-evidence pack.")
    ap.add_argument("--domain", required=True,
                    help="any registered domain name, or 'scan' for open questions")
    ap.add_argument("--when", required=True)
    ap.add_argument("--tz", default="Asia/Kolkata")
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--ayanamsa", default="lahiri")
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    args = ap.parse_args()

    when = datetime.strptime(args.when, "%Y-%m-%d %H:%M").replace(
        tzinfo=ZoneInfo(args.tz))
    start = datetime.strptime(args.start, "%Y-%m-%d").replace(tzinfo=UTC)
    end = datetime.strptime(args.end, "%Y-%m-%d").replace(tzinfo=UTC)
    v = VedicChart.create(when=when, latitude=args.lat, longitude=args.lon,
                          ayanamsa=args.ayanamsa)
    if args.domain == "scan":
        print(scan_domains(v, start, end))
    elif args.domain in DOMAIN_PROFILES:
        print(render_domain(v, DOMAIN_PROFILES[args.domain], start, end))
    else:
        # not a registered domain — resolve the word via the significator dictionary
        from interpreter.significators import resolve
        try:
            profile = resolve(args.domain)
        except ValueError as e:
            raise SystemExit(str(e))
        print(render_domain(v, profile, start, end))


if __name__ == "__main__":
    main()
