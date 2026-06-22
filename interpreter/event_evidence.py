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
        --when "1991-04-04 06:23" --lat 23.63 --lon 85.52 \
        --start 2023-01-01 --end 2027-12-31
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from advance_astrology import VedicChart, Planet
from advance_astrology.constants import SIGNS

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


def promise_and_tempo(v, profile: DomainProfile) -> PromiseTempo:
    kps = v.kp_significators()
    tr = v.transits()
    sav = v.sarvashtakavarga()
    sb = v.shadbala()
    ik = v.ishta_kashta()
    primary = profile.houses[0]
    cusp_sign = (v.ascendant_sign + primary - 1) % 12
    cusp_lon = (cusp_sign * 30) + ((v.ascendant % 30))
    from advance_astrology.vedic.kp import kp_chain
    cusp_sub = kp_chain(cusp_lon).sub_lord
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

    def _domain_votes(self) -> int:
        v = 0
        v += 1 if self.kp_fulfil > 0 and self.kp_fulfil >= self.kp_negate else 0
        v += 1 if self.karaka_in_chain or self.karaka_sukshma else 0
        v += 1 if self.lagnesh_in_chain else 0
        v += 1 if self.house_double_transit or self.lord_double_transit else 0
        v += 1 if self.saham_double_transit else 0
        v += 1 if self.bnn else 0
        v += 1 if self.kakshya else 0
        v += 1 if self.varshaphal_muntha else 0
        v += 1 if self.sudarshana_hit else 0
        return v

    @property
    def domain_score(self) -> int:
        """Convergence EXCLUDING the shared Lagna-activation vote — used to rank
        different domains against each other (the Lagna is the same for all)."""
        return self._domain_votes()

    @property
    def convergence(self) -> int:
        """Within-domain window ranking (adds the Lagna materialization vote)."""
        return self._domain_votes() + (1 if self.lagna_activators else 0)


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


@dataclass
class ReversalRow:
    start: datetime
    chain: list
    kp_rupture: int
    separators_running: bool
    break_house_dt: bool
    reversal_saham_dt: bool
    lagna_dark_with_malefic: bool

    @property
    def rupture_score(self) -> int:
        return (int(self.kp_rupture >= 2) + int(self.separators_running)
                + int(self.break_house_dt) + int(self.reversal_saham_dt)
                + int(self.lagna_dark_with_malefic))


def reversal_map(v, profile, start, end, step_days=7) -> list[ReversalRow]:
    """Time the matter's REVERSAL as its own event, from DIFFERENT significators:
    the 6/8/12-from-the-matter houses, the separators (Saturn + nodes + the
    6th-from-house lord), the reversal Saham, the double-transit on the breaking
    house, and a DARK Lagna under a malefic/node daśā (de-materialization)."""
    tr = v.transits()
    kps = v.kp_significators()
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
    rows, d, last = [], start, None
    while d < end:
        chain = _chain_lords(v, d, levels=3)
        if tuple(chain) != last:
            last = tuple(chain)
            kp = sum(len(set(kps.planet_signifies(l)) & rupture_houses) for l in chain)
            dark = not _slow_on_sign(tr, lagna, d)
            rows.append(ReversalRow(
                start=d, chain=[c.value[:2] for c in chain], kp_rupture=kp,
                separators_running=any(l in separators for l in chain),
                break_house_dt=_in(d, bh_dt), reversal_saham_dt=_in(d, saham_dt),
                lagna_dark_with_malefic=dark and any(l in nodes_sat for l in chain)))
        d += timedelta(days=step_days)
    return rows


def candidate_map(v, profile, start, end, step_days=7) -> list[WindowEvidence]:
    """Full-span candidate ledger for the matter's MANIFESTATION."""
    tr = v.transits()
    kps = v.kp_significators()
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
    muntha = {y: v.varshaphal(y).muntha_house for y in range(start.year, end.year + 1)}

    rows, d, last = [], start, None
    while d < end:
        chain = _chain_lords(v, d, levels=3)
        if tuple(chain) != last:
            last = tuple(chain)
            f = n = 0
            for lord in chain:
                a, b = _kp_score(kps, lord, profile)
                f += a
                n += b
            deep = v.current_dasha("vimshottari", d, levels=5)
            su = v.sudarshana(d)
            chara = v.current_chara_dasha(d, levels=2)
            rows.append(WindowEvidence(
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
                varshaphal_muntha=muntha.get(d.year) in profile.houses,
                chara_ad=" > ".join(c.note for c in chara),
                sudarshana_hit=any(s in dom_signs for s in
                                   (su.lagna_month_sign, su.moon_month_sign,
                                    su.lagna_year_sign, su.moon_year_sign)),
            ))
        d += timedelta(days=step_days)
    return rows


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
            f"{'Y' if r.sudarshana_hit else '-'}  {r.convergence}")


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
    L += _fmt_tempo(pt)
    L += ["", "  CANDIDATE LEDGER (cols: KPf/n · kār+sūkṣ · lgnś · Lagna-activation · "
          "Hdt+Ldt · Sdt · BNN · Kakṣ · Muntha · Sud · conv):"]
    for r in sorted(rows, key=lambda x: x.start):
        L.append(_row_line(r))
    top = sorted(rows, key=lambda x: (-x.convergence, x.start))[:5]
    L += ["", "  TOP-RANKED WINDOWS (independent-system convergence):"]
    for r in top:
        L.append(f"    {r.start:%Y-%m-%d} {'>'.join(r.chain):<9} conv={r.convergence}"
                 f"  KP {r.kp_fulfil}/{r.kp_negate}  Lagna[{','.join(r.lagna_activators) or '—'}]"
                 f"  chara {r.chara_ad}")

    # Reversal as its OWN event (separators + dark Lagna + reversal saham)
    primary = profile.houses[0]
    break_house = (primary - 1 + 6 - 1) % 12 + 1
    rev = reversal_map(v, profile, start, end)
    rtop = sorted(rev, key=lambda x: (-x.rupture_score, x.start))[:3]
    L += ["", f"  REVERSAL / CANCELLATION timed as its OWN event "
          f"(6/8/12-from-H{primary}; separators Saturn+nodes+H{break_house}-lord"
          + (f"; saham {profile.reversal_saham}" if profile.reversal_saham else "")
          + ") — top windows:"]
    for r in rtop:
        flags = []
        if r.separators_running:
            flags.append("separator-daśā")
        if r.lagna_dark_with_malefic:
            flags.append("dark-Lagna+malefic")
        if r.break_house_dt:
            flags.append("break-house dbl-transit")
        if r.reversal_saham_dt:
            flags.append("reversal-saham")
        L.append(f"    {r.start:%Y-%m-%d} {'>'.join(r.chain):<9} "
                 f"rupture-score={r.rupture_score}  KP-rupture={r.kp_rupture}  "
                 f"[{', '.join(flags) or '—'}]")

    L += ["", "  NB: EVIDENCE, not verdict. Read it MULTIVALENTLY — a node colours "
          "the TYPE (sudden/court/unconventional), a dark Lagna lowers "
          "materialization-INTENSITY (low-key) but does not deny a Saham/kāraka-lit "
          "event, and the reversal block is timed independently — a strong benefic "
          "elsewhere does NOT veto a converged reversal."]
    return "\n".join(L)


def scan_domains(v, start, end) -> str:
    """Open question: which life-area STANDS OUT most across [start, end]?

    Ranked by stand-out = peak domain-score minus that domain's own mean score
    over the window, so a broad-significator area cannot win merely by running a
    high background — it must genuinely spike."""
    L = ["# DOMAIN MACRO-SCAN (open question) — life-areas by stand-out spike"]
    ranked = []
    for name, profile in DOMAIN_PROFILES.items():
        rows = candidate_map(v, profile, start, end)
        if not rows:
            continue
        scores = [r.domain_score for r in rows]
        peak_row = max(rows, key=lambda x: x.domain_score)
        standout = peak_row.domain_score - (sum(scores) / len(scores))
        ranked.append((round(standout, 2), peak_row.domain_score, name, peak_row))
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
        raise SystemExit(f"unknown domain {args.domain!r}; registered: "
                         f"{list(DOMAIN_PROFILES)} (or 'scan')")


if __name__ == "__main__":
    main()
