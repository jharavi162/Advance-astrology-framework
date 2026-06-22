"""Domain-general triangulation evidence builder (Playbook Phases 2-4).

This is the *automation* of the mechanical half of AI_TRIANGULATION_PROMPT.md.
It is **not** marriage-specific: the triangulation machinery (Lagna/Lagnesh
materialization, daśā sūkṣma drill, double-transit on the matter's house AND its
lord, Saham + Sudarśana corroboration, candidate-map-then-converge, and the
independent timing of a reversal/cancellation) is computed *identically for every
life-area*. Only a small declarative ``DomainProfile`` changes per question — the
houses, the KP fulfilment/negation houses, the chara-kāraka, the Arudha, the
Saham and the varga that the matter is read through.

Division of labour is preserved: the engine gathers a *complete* evidence pack so
nothing is ever silently skipped (the recurring cause of timing misses), while
the AI still does the multivalent *synthesis* on top of it (e.g. reading a node
as the event's TYPE, or the Lagna as materialization-intensity, not as a yes/no).

    python -m interpreter.event_evidence --domain marriage \
        --when "1991-04-04 06:23" --tz Asia/Kolkata --lat 23.63 --lon 85.52 \
        --start 2023-01-01 --end 2027-12-31

    # open question — rank which domain is hottest in a window:
    python -m interpreter.event_evidence --domain scan \
        --when "1991-04-04 06:23" --lat 23.63 --lon 85.52 \
        --start 2024-01-01 --end 2025-12-31
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from advance_astrology import VedicChart, Planet
from advance_astrology.constants import SIGNS

UTC = timezone.utc

# Jupiter's special aspects fall on the 5th/7th/9th, Saturn's on the 3rd/7th/10th
# (counted inclusively as sign-offsets). Used for the materialization + double
# transit checks so a glance counts, not only bodily occupation.
_ASPECT_OFFSETS = {Planet.JUPITER: (4, 6, 8), Planet.SATURN: (2, 6, 9)}


@dataclass(frozen=True)
class DomainProfile:
    """Declarative spec for ONE life-area. Adding a domain = adding a row."""

    name: str
    houses: tuple[int, ...]               # primary bhāvas of the matter
    fulfil_houses: frozenset              # KP houses that MAKE the matter happen
    negate_houses: frozenset              # KP houses that BREAK/deny the matter
    karakas: tuple[str, ...]              # Jaimini chara-kārakas (by name)
    natural_karaka: Planet | None         # the natural significator graha
    arudhas: tuple[str, ...]              # Arudha keys (A1..A12, UL)
    saham: str | None                     # Tājika Saham that times the matter
    reversal_saham: str | None            # Saham timing the matter's *reversal*
    varga: int                            # divisional chart confirming the TYPE


# ---------------------------------------------------------------------------- #
# THE DOMAIN REGISTRY — pure data. The engine code below is domain-agnostic.
# ---------------------------------------------------------------------------- #
DOMAIN_PROFILES: dict[str, DomainProfile] = {
    "marriage": DomainProfile(
        "marriage", (7,), frozenset({2, 7, 11}), frozenset({1, 6, 10}),
        ("Darakaraka",), Planet.VENUS, ("A7", "UL"), "Vivaha", "Punarvivaha", 9),
    "career": DomainProfile(
        "career", (10,), frozenset({2, 6, 10, 11}), frozenset({5, 8, 9, 12}),
        ("Amatyakaraka",), Planet.SATURN, ("A10",), "Karma", None, 10),
    "children": DomainProfile(
        "children", (5,), frozenset({2, 5, 11}), frozenset({1, 4, 10, 12}),
        ("Putrakaraka",), Planet.JUPITER, ("A5",), "Putra", None, 7),
    "wealth": DomainProfile(
        "wealth", (2, 11), frozenset({2, 5, 9, 11}), frozenset({6, 8, 12}),
        (), Planet.JUPITER, ("A2",), "Artha", None, 2),
    "mother": DomainProfile(
        "mother", (4,), frozenset({2, 4, 11}), frozenset({3, 8, 12}),
        ("Matrikaraka",), Planet.MOON, ("A4",), None, None, 4),
    "father": DomainProfile(
        "father", (9,), frozenset({2, 9, 11}), frozenset({3, 8, 12}),
        ("Pitrikaraka",), Planet.SUN, ("A9",), None, None, 9),
    "illness": DomainProfile(
        "illness", (6, 8), frozenset({6, 8, 12}), frozenset({1, 5, 11}),
        ("Gnatikaraka", "Atmakaraka"), Planet.SATURN, ("A6",), "Roga", None, 30),
    "education": DomainProfile(
        "education", (4, 5, 9), frozenset({4, 5, 9, 11}), frozenset({6, 8, 12}),
        (), Planet.MERCURY, ("A5",), "Vidya", None, 24),
}


@dataclass
class WindowEvidence:
    """One candidate window's triangulated testimony (pre-synthesis)."""

    start: datetime
    chain: list                            # MD>AD>PD lord abbreviations
    kp_fulfil: int
    kp_negate: int
    karaka_in_chain: bool
    karaka_sukshma: bool                   # the micro-trigger (sūkṣma/prāṇa)
    lagnesh_in_chain: bool
    lagna_activators: list                 # slow movers on the Lagna (intensity)
    house_double_transit: bool
    lord_double_transit: bool
    saham_double_transit: bool
    chara_ad: str
    sudarshana_hit: bool

    @property
    def convergence(self) -> int:
        """Independent networks endorsing this window — ranks windows WITHIN a
        domain (includes the Lagna materialization vote)."""
        return self.domain_score + (1 if self.lagna_activators else 0)

    @property
    def domain_score(self) -> int:
        """Convergence EXCLUDING the shared Lagna-activation vote — use this to
        rank different domains against each other, since the Lagna is the same
        for every life-area and would otherwise inflate them all equally."""
        votes = 0
        votes += 1 if self.kp_fulfil > 0 and self.kp_fulfil >= self.kp_negate else 0
        votes += 1 if self.karaka_in_chain or self.karaka_sukshma else 0
        votes += 1 if self.lagnesh_in_chain else 0
        votes += 1 if self.house_double_transit or self.lord_double_transit else 0
        votes += 1 if self.saham_double_transit else 0
        votes += 1 if self.sudarshana_hit else 0
        return votes


# ---------------------------------------------------------------------------- #
# Domain-INDEPENDENT machinery
# ---------------------------------------------------------------------------- #
def _slow_on_sign(v, tr, sign: int, when: datetime,
                  planets=(Planet.JUPITER, Planet.SATURN)) -> list:
    """Which slow movers occupy OR aspect a natal sign (the activation test)."""
    out = []
    for p in planets:
        ps = tr.transit_sign(when, p)
        if ps == sign or any((ps + a) % 12 == sign for a in _ASPECT_OFFSETS[p]):
            out.append(p.value + ("(in)" if ps == sign else "(asp)"))
    return out


def _kp_score(kps, planet, profile: DomainProfile) -> tuple[int, int]:
    houses = set(kps.planet_signifies(planet))
    return (len(houses & profile.fulfil_houses),
            len(houses & profile.negate_houses))


def _double_transit_windows(tr, house: int, start, end):
    return [(w.start, w.end) for w in tr.double_transit_windows(house, start, end)]


def _in_windows(when, windows) -> bool:
    return any(a <= when <= b for a, b in windows)


def _chain_lords(v, when, levels=3):
    return [c.lord for c in v.current_dasha("vimshottari", when, levels=levels)]


def _karaka_planets(v, profile: DomainProfile) -> set:
    ks = {p for nm, p in v.chara_karakas().items() if nm in profile.karakas}
    if profile.natural_karaka:
        ks.add(profile.natural_karaka)
    return ks


def _domain_signs(v, profile: DomainProfile) -> set:
    """Rāśis occupied by the matter's houses (for Sudarśana wheel hits)."""
    return {(v.ascendant_sign + h - 1) % 12 for h in profile.houses}


def candidate_map(v, profile: DomainProfile, start: datetime, end: datetime,
                  step_days: int = 7) -> list[WindowEvidence]:
    """Build the FULL candidate ledger across [start, end], THEN it is ranked.

    Every domain-independent discriminator is attached to each PD segment:
    KP fulfil/negate, kāraka (running + sūkṣma), Lagnesh + Lagna materialization,
    double-transit on the matter's house AND its lord, Saham double-transit,
    chara antardaśā and Sudarśana corroboration.
    """
    tr = v.transits()
    kps = v.kp_significators()
    lagnesh = v.house_lord(1)
    lagna_sign = v.ascendant_sign
    lagnesh_sign = v.signs[lagnesh]
    karakas = _karaka_planets(v, profile)
    dom_signs = _domain_signs(v, profile)

    # Pre-compute the slow full-span double-transit bands ONCE (no early cut-off).
    house_dt, lord_dt = [], []
    for h in profile.houses:
        house_dt += _double_transit_windows(tr, h, start, end)
        lord_sign = v.signs[v.house_lord(h)]
        lord_house = (lord_sign - lagna_sign) % 12 + 1
        lord_dt += _double_transit_windows(tr, lord_house, start, end)
    saham_dt = []
    if profile.saham:
        sah = v.sahams().get(profile.saham)
        if sah:
            sh = (sah.sign_index - lagna_sign) % 12 + 1
            saham_dt = _double_transit_windows(tr, sh, start, end)

    rows: list[WindowEvidence] = []
    d = start
    last_key = None
    while d < end:
        chain = _chain_lords(v, d, levels=3)
        key = tuple(chain)
        if key != last_key:
            last_key = key
            mid = d
            fulfil = negate = 0
            for lord in chain:
                f, n = _kp_score(kps, lord, profile)
                fulfil += f
                negate += n
            # sūkṣma micro-trigger: kāraka surfacing at level 4/5 inside segment
            deep = v.current_dasha("vimshottari", mid, levels=5)
            karaka_sukshma = any(c.lord in karakas for c in deep[3:])
            su = v.sudarshana(mid)
            sud_hit = any(s in dom_signs for s in
                          (su.lagna_month_sign, su.moon_month_sign,
                           su.lagna_year_sign, su.moon_year_sign))
            chara = v.current_chara_dasha(mid, levels=2)
            rows.append(WindowEvidence(
                start=mid,
                chain=[c.value[:2] for c in chain],
                kp_fulfil=fulfil, kp_negate=negate,
                karaka_in_chain=any(l in karakas for l in chain),
                karaka_sukshma=karaka_sukshma,
                lagnesh_in_chain=lagnesh in chain,
                lagna_activators=_slow_on_sign(v, tr, lagna_sign, mid),
                house_double_transit=_in_windows(mid, house_dt),
                lord_double_transit=_in_windows(mid, lord_dt),
                saham_double_transit=_in_windows(mid, saham_dt),
                chara_ad=" > ".join(c.note for c in chara),
                sudarshana_hit=sud_hit,
            ))
        d += timedelta(days=step_days)
    return rows


def render_domain(v, profile: DomainProfile, start, end) -> str:
    rows = candidate_map(v, profile, start, end)
    L: list[str] = []
    lagnesh = v.house_lord(1)
    L.append(f"# EVENT-EVIDENCE PACK — domain: {profile.name.upper()}")
    L.append(f"  Lagna={SIGNS[v.ascendant_sign]} | Lagnesh={lagnesh.value} "
             f"in {SIGNS[v.signs[lagnesh]]} | Moon(mind)={SIGNS[v.signs[Planet.MOON]]}")
    L.append(f"  Houses={profile.houses}  KP fulfil={sorted(profile.fulfil_houses)}"
             f" negate={sorted(profile.negate_houses)}  kāraka={profile.karakas}"
             f"+{profile.natural_karaka.value if profile.natural_karaka else '-'}"
             f"  Saham={profile.saham}  Varga=D{profile.varga}")
    L.append("")
    L.append("  date        M>A>P     KP(f/n) kār kS lgnś Lagna-activation       "
             "Hdt Ldt Sdt Sud  conv")
    L.append("  " + "-" * 96)
    for r in sorted(rows, key=lambda x: x.start):
        L.append(
            f"  {r.start:%Y-%m-%d}  {'>'.join(r.chain):<9} "
            f"{r.kp_fulfil}/{r.kp_negate:<5} "
            f"{'Y' if r.karaka_in_chain else '-'}  "
            f"{'Y' if r.karaka_sukshma else '-'}  "
            f"{'Y' if r.lagnesh_in_chain else '-'}   "
            f"{(','.join(r.lagna_activators) or '—'):<22} "
            f"{'Y' if r.house_double_transit else '-'}   "
            f"{'Y' if r.lord_double_transit else '-'}   "
            f"{'Y' if r.saham_double_transit else '-'}   "
            f"{'Y' if r.sudarshana_hit else '-'}    {r.convergence}")
    L.append("")
    top = sorted(rows, key=lambda x: (-x.convergence, x.start))[:5]
    L.append("  TOP-RANKED WINDOWS (by independent-system convergence):")
    for r in top:
        L.append(f"    {r.start:%Y-%m-%d}  {'>'.join(r.chain):<9} "
                 f"convergence={r.convergence}/6  "
                 f"(KP {r.kp_fulfil}/{r.kp_negate}; "
                 f"Lagna [{','.join(r.lagna_activators) or '—'}]; "
                 f"chara {r.chara_ad})")
    L.append("")
    L.append("  NB: this is the EVIDENCE, not the verdict. The AI must now read it "
             "MULTIVALENTLY — a node colours the TYPE (sudden/court/unconventional),"
             " a dark Lagna lowers materialization-INTENSITY (low-key) but does not "
             "deny a Saham/kāraka-lit event, and a reversal is timed as its OWN event.")
    return "\n".join(L)


def scan_domains(v, start, end) -> str:
    """Open question: which life-area is hottest across [start, end]?"""
    L = ["# DOMAIN MACRO-SCAN (open question) — peak convergence per life-area"]
    ranked = []
    for name, profile in DOMAIN_PROFILES.items():
        rows = candidate_map(v, profile, start, end)
        peak = max(rows, key=lambda x: x.domain_score) if rows else None
        if peak:
            ranked.append((peak.domain_score, name, peak))
    for conv, name, peak in sorted(ranked, reverse=True):
        L.append(f"  {name:<10} peak domain-score={conv}/6 around "
                 f"{peak.start:%Y-%m} (M>A>P {'>'.join(peak.chain)})")
    L.append("")
    L.append("  ⚠️ v1 CAVEAT: this cross-domain ranking is APPROXIMATE — the raw "
             "score is not yet normalised per domain, so broad-significator areas "
             "(education/illness) can over-fire. Treat it as a shortlist of "
             "candidate life-areas, then run the full per-domain pack on each and "
             "let the AI judge. The per-domain pack is the reliable artefact.")
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description="Domain-general event-evidence pack.")
    ap.add_argument("--domain", required=True,
                    help="marriage|career|children|wealth|mother|father|illness|"
                         "education|scan")
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
    else:
        profile = DOMAIN_PROFILES.get(args.domain)
        if not profile:
            raise SystemExit(f"unknown domain {args.domain!r}; "
                             f"choose from {list(DOMAIN_PROFILES)} or 'scan'")
        print(render_domain(v, profile, start, end))


if __name__ == "__main__":
    main()
