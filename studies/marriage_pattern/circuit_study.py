"""Chart-specific marriage-circuit study (round 2).

Round 1 asked FIXED questions of every chart. This round builds each chart's own
MARRIAGE CIRCUIT and asks whether the wedding day connects to *that* circuit —
the way a jyotiṣi actually reads: "whose daśā could marry THIS person?"

Rule catalogue tested (school → hypothesis), from the classical literature:
  Parāśara   H1  MD/AD/PD lord ∈ core circuit {7L, occupants of 7th, Venus, DK}
             H2  the ANTARDAŚĀ lord specifically ∈ core circuit
             H3  MD/AD lord sits in a NAKSHATRA whose lord ∈ core circuit
                 ("daśā of a planet in the star of the 7th lord")
  Navāṁśa    H4  MD/AD lord ∈ D9 circuit {D9-7L, D9 dispositor of 7L, planets in D9 7th}
  Strī-jātaka/BNN
             H5  gender kāraka in chain (M: Venus · F: Jupiter-husband / Mars-BNN)
             H9  transit Jupiter conj/trine the gender kāraka's natal degree (orb 6°)
  Rāhu lore  H6  Rahu/Ketu in chain while natally on the 1–7 axis or UL
  W./degree  H7  transit Jupiter within 6° of descendant / 7L / Venus degree (or trine)
             H8  transit Saturn within 6° of the same points (Saturn angles)
  Gochara    H10 transit Jupiter (sign+dṛṣṭi) on 7th, UL, or 7th-from-Moon
             H11 transit Saturn (sign+dṛṣṭi) on 7th, UL, or 7th-from-UL
             H12 CLASSIC double-transit: Jupiter AND Saturn both touching
                 {7th sign, 7L's sign, UL} (sign-level graha-dṛṣṭi)

For every native: evaluate all 12 at the wedding AND at 10 random adult dates
(≥400 d from the wedding). Report per-hypothesis lift, per-native drivers, and the
RANK TEST: where does the wedding's composite score sit among its own controls?

Usage: python -m studies.marriage_pattern.circuit_study
"""

from __future__ import annotations

import json
import random
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from advance_astrology import VedicChart
from advance_astrology.angles import norm360
from advance_astrology.constants import RULERSHIPS, SIGNS, Planet

HERE = Path(__file__).resolve().parent
UTC = timezone.utc
random.seed(1729)
N_CONTROL = 10
EPHEM_MAX = datetime(2053, 1, 1, tzinfo=UTC)
ORB = 6.0

JUP_ASPECT_OFF = (4, 6, 8)        # 5th, 7th, 9th sign-aspects (0-based offsets)
SAT_ASPECT_OFF = (2, 6, 9)        # 3rd, 7th, 10th
JUP_ANGLES = (0.0, 120.0, 180.0, 240.0)
SAT_ANGLES = (0.0, 60.0, 180.0, 270.0)

HYPS = ["H1_dasha_core", "H2_AD_core", "H3_dasha_star", "H4_dasha_D9",
        "H5_gender_karaka", "H6_rahu_axis", "H7_jup_degree", "H8_sat_degree",
        "H9_bnn_gender_jup", "H10_jup_gochara", "H11_sat_gochara",
        "H12_double_transit"]


def _lord_of_sign(sign: int) -> Planet:
    return RULERSHIPS[SIGNS[sign % 12]]


def _hit_deg(t_lon: float, n_lon: float, angles, orb: float = ORB) -> bool:
    for a in angles:
        d = abs((t_lon - n_lon - a + 180.0) % 360.0 - 180.0)
        if d <= orb:
            return True
    return False


def _touches_sign(p_sign: int, target: int, offsets) -> bool:
    return p_sign == target or any((p_sign + o) % 12 == target for o in offsets)


class Native:
    """One chart + its personal marriage circuit, precomputed once."""

    def __init__(self, person: dict):
        self.person = person
        self.sex = person["sex"]
        when = datetime.strptime(f"{person['date']} {person['time']}",
                                 "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo(person["tz"]))
        self.v = v = VedicChart.create(when=when, latitude=person["lat"],
                                       longitude=person["lon"])
        self.eph = v.natal._ephemeris
        self.birth_utc = when.astimezone(UTC)

        asc = v.ascendant_sign
        self.seventh_sign = (asc + 6) % 12
        self.sevenL = v.house_lord(7)
        occupants7 = [p for p in v.planets_in_house(7)
                      if p in v.longitudes and p.value in
                      ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
                       "Saturn", "Rahu", "Ketu")]
        self.dk = v.chara_karakas().get("Darakaraka")

        # core circuit — Parāśara
        self.core = {self.sevenL, Planet.VENUS} | set(occupants7)
        if self.dk:
            self.core.add(self.dk)

        # D9 circuit
        d9 = v.navamsha
        d9_7L = _lord_of_sign(d9.ascendant_sign + 6)
        d9_disp_7L = _lord_of_sign(d9.signs[self.sevenL])
        d9_7_occupants = {p for p, s in d9.signs.items()
                          if s == (d9.ascendant_sign + 6) % 12 and p in v.longitudes}
        self.d9_circuit = {d9_7L, d9_disp_7L} | d9_7_occupants

        # Jaimini
        self.ul_sign = v.arudhas()["UL"]
        self.ul7_sign = (self.ul_sign + 6) % 12

        # gender kārakas (Strī-jātaka: Jupiter = husband; BNN: Mars causative for F)
        self.gender_karakas = ({Planet.JUPITER, Planet.MARS} if self.sex == "F"
                               else {Planet.VENUS})
        self.bnn_karaka = Planet.MARS if self.sex == "F" else Planet.VENUS

        # nodes on the 1-7 axis or UL (for the Rāhu rule)
        self.node_marriage_axis = {
            n for n in (Planet.RAHU, Planet.KETU)
            if v.signs[n] in (asc, self.seventh_sign, self.ul_sign)}

        # degree anchors
        self.desc_deg = norm360(v.ascendant + 180.0)
        self.sevenL_deg = float(v.longitudes[self.sevenL])
        self.venus_deg = float(v.longitudes[Planet.VENUS])
        self.bnn_deg = float(v.longitudes[self.bnn_karaka])
        self.moon7_sign = (v.signs[Planet.MOON] + 6) % 12

        # star-lord helper (engine KP chain)
        self._star = {p: v.kp_chain(p).star_lord for p in v.longitudes
                      if isinstance(v.longitudes[p], float)}

    # ------------------------------------------------------------------ #
    def transit_lon(self, when: datetime, planet: Planet) -> float:
        t = self.eph.time(when)
        return norm360(self.eph.position(planet, t).longitude - self.v.ayanamsa)

    def evaluate(self, d: datetime) -> dict:
        v = self.v
        chain = [p.lord for p in v.current_dasha("vimshottari", d, levels=3)]
        md_ad = chain[:2]
        ad = chain[1] if len(chain) > 1 else chain[0]

        jup = self.transit_lon(d, Planet.JUPITER)
        sat = self.transit_lon(d, Planet.SATURN)
        jup_s, sat_s = int(jup // 30), int(sat // 30)

        jup_targets = {self.seventh_sign, self.ul_sign, self.moon7_sign}
        sat_targets = {self.seventh_sign, self.ul_sign, self.ul7_sign}
        dt_targets = {self.seventh_sign, v.signs[self.sevenL], self.ul_sign}

        jup_deg_hit = any(_hit_deg(jup, x, JUP_ANGLES)
                          for x in (self.desc_deg, self.sevenL_deg, self.venus_deg))
        sat_deg_hit = any(_hit_deg(sat, x, SAT_ANGLES)
                          for x in (self.desc_deg, self.sevenL_deg, self.venus_deg))

        res = {
            "H1_dasha_core": any(l in self.core for l in chain),
            "H2_AD_core": ad in self.core,
            "H3_dasha_star": any(self._star.get(l) in self.core for l in md_ad),
            "H4_dasha_D9": any(l in self.d9_circuit for l in md_ad),
            "H5_gender_karaka": any(l in self.gender_karakas for l in chain),
            "H6_rahu_axis": any(l in self.node_marriage_axis for l in chain),
            "H7_jup_degree": jup_deg_hit,
            "H8_sat_degree": sat_deg_hit,
            "H9_bnn_gender_jup": _hit_deg(jup, self.bnn_deg, JUP_ANGLES),
            "H10_jup_gochara": any(_touches_sign(jup_s, t, JUP_ASPECT_OFF)
                                   for t in jup_targets),
            "H11_sat_gochara": any(_touches_sign(sat_s, t, SAT_ASPECT_OFF)
                                   for t in sat_targets),
            "H12_double_transit": (
                any(_touches_sign(jup_s, t, JUP_ASPECT_OFF) for t in dt_targets)
                and any(_touches_sign(sat_s, t, SAT_ASPECT_OFF) for t in dt_targets)),
        }
        res["_chain"] = [p.value for p in chain]
        res["_score"] = sum(bool(res[h]) for h in HYPS)
        return res


def main() -> None:
    people = json.loads((HERE / "dataset.json").read_text())["people"]
    wed_freq, ctl_freq = Counter(), Counter()
    n_ctrl_total = 0
    out_rows = []

    for i, person in enumerate(people, 1):
        nat = Native(person)
        marr = datetime.strptime(person["marriage"], "%Y-%m-%d").replace(
            hour=12, tzinfo=UTC)
        wed = nat.evaluate(marr)
        for h in HYPS:
            wed_freq[h] += bool(wed[h])

        lo = nat.birth_utc + timedelta(days=int(18 * 365.25))
        hi = min(nat.birth_utc + timedelta(days=int(62 * 365.25)), EPHEM_MAX)
        ctl_scores, ctl_vectors = [], []
        got, tries = 0, 0
        while got < N_CONTROL and tries < 80:
            tries += 1
            d = lo + (hi - lo) * random.random()
            if abs((d - marr).days) < 400:
                continue
            c = nat.evaluate(d)
            ctl_scores.append(c["_score"])
            ctl_vectors.append({h: bool(c[h]) for h in HYPS})
            for h in HYPS:
                ctl_freq[h] += bool(c[h])
            got += 1
        n_ctrl_total += got

        below = sum(1 for s in ctl_scores if s < wed["_score"])
        ties = sum(1 for s in ctl_scores if s == wed["_score"])
        pct = 100.0 * (below + 0.5 * ties) / len(ctl_scores)
        drivers = [h for h in HYPS if wed[h]]
        out_rows.append({
            "name": person["name"], "sex": person["sex"],
            "marriage": person["marriage"],
            "wedding_score": wed["_score"],
            "control_scores": ctl_scores,
            "percentile": round(pct, 1),
            "chain": wed["_chain"],
            "drivers": drivers,
            "wedding_vector": {h: bool(wed[h]) for h in HYPS},
            "control_vectors": ctl_vectors,
        })
        print(f"[{i:2}/50] {person['name']:<22} score={wed['_score']:2}/12 "
              f"pct={pct:5.1f}  drivers={len(drivers)}  "
              f"chain={'>'.join(wed['_chain'])}")

    nW = len(out_rows)
    print(f"\n=== PER-HYPOTHESIS LIFT ({nW} weddings vs {n_ctrl_total} controls) ===")
    print(f"{'hypothesis':<22} {'wed%':>6} {'ctl%':>6} {'lift':>7}")
    lift_tbl = []
    for h in HYPS:
        w = 100 * wed_freq[h] / nW
        c = 100 * ctl_freq[h] / n_ctrl_total
        lift_tbl.append({"hyp": h, "wedding_pct": round(w, 1),
                         "control_pct": round(c, 1), "lift": round(w - c, 1)})
        print(f"{h:<22} {w:6.0f} {c:6.0f} {w - c:+7.1f}")

    pcts = [r["percentile"] for r in out_rows]
    mean_pct = sum(pcts) / nW
    top_quarter = sum(1 for p in pcts if p >= 75)
    above_median = sum(1 for p in pcts if p > 50)
    w_scores = [r["wedding_score"] for r in out_rows]
    all_ctl = [s for r in out_rows for s in r["control_scores"]]
    print(f"\n=== RANK TEST (wedding vs its own {N_CONTROL} random dates) ===")
    print(f"  mean wedding percentile : {mean_pct:.1f} (50 = chance)")
    print(f"  weddings above median   : {above_median}/{nW}")
    print(f"  weddings in top quartile: {top_quarter}/{nW}")
    print(f"  mean score  wedding={sum(w_scores)/nW:.2f}  control={sum(all_ctl)/len(all_ctl):.2f}")

    (HERE / "circuit_results.json").write_text(json.dumps({
        "hypotheses": HYPS, "lift": lift_tbl,
        "rank_test": {"mean_percentile": round(mean_pct, 1),
                      "above_median": above_median,
                      "top_quartile": top_quarter, "n": nW},
        "natives": out_rows}, indent=2))


if __name__ == "__main__":
    main()
