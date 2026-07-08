"""Round 4 — NAKSHATRA-LORD transit study (star-level timing).

User hypothesis: the sign-level window is coarse; the fine trigger should show at
the NAKSHATRA level — transits THROUGH stars whose lords belong to the chart's
marriage circuit (KP: "the event fructifies when the daśā lords / slow planets /
the luminaries transit the stars of the significators"), and transits OVER the
natal stars of the circuit planets.

Star-level hypotheses evaluated at each of the 50 weddings vs 10 random adult
dates per native (seed-matched to circuit_study):

  slow (month-scale):
    N1  transit Jupiter in a star whose lord ∈ core circuit
    N2  transit Saturn  in a star whose lord ∈ core circuit
    N3  transit Jupiter in the SAME star as a natal circuit planet
    N4  transit Saturn  in the SAME star as a natal circuit planet
  daśā-linked (KP transit rule):
    N5  MD lord's own transit position sits in a star whose lord ∈ core circuit
    N6  AD lord's own transit position sits in a star whose lord ∈ core circuit
  fast (month/day pickers):
    N7  transit Sun   in a star whose lord ∈ core circuit  (KP month marker)
    N8  transit Moon  in a star whose lord ∈ core circuit  (KP day marker)
    N9  transit Venus in a star whose lord ∈ core circuit
    N10 transit Moon in the SAME star as a natal circuit planet (day, over natal)
  conjunctions (window × day-trigger):
    C1  H12 double-transit AND N8 (sign-window open AND Moon day-key)
    C2  (N1 or N2) AND N8         (star-window open AND Moon day-key)

core circuit = {7th lord, occupants of 7th, Venus, Dārā-kāraka} (as Round 2).

Usage: python -m studies.marriage_pattern.nakshatra_study
"""

from __future__ import annotations

import json
import random
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

from advance_astrology.constants import Planet
from studies.marriage_pattern.circuit_study import Native

HERE = Path(__file__).resolve().parent
UTC = timezone.utc
random.seed(1729)                      # same protocol as circuit_study
N_CONTROL = 10
EPHEM_MAX = datetime(2053, 1, 1, tzinfo=UTC)

SPAN = 360.0 / 27.0                    # one nakshatra
VIM_LORDS = (Planet.KETU, Planet.VENUS, Planet.SUN, Planet.MOON, Planet.MARS,
             Planet.RAHU, Planet.JUPITER, Planet.SATURN, Planet.MERCURY)

NHYPS = ["N1_jup_star", "N2_sat_star", "N3_jup_natal_star", "N4_sat_natal_star",
         "N5_md_star", "N6_ad_star", "N7_sun_star", "N8_moon_star",
         "N9_venus_star", "N10_moon_natal_star", "C1_dt_and_moon",
         "C2_slowstar_and_moon"]


def star_idx(lon: float) -> int:
    return int((lon % 360.0) / SPAN)


def star_lord(lon: float) -> Planet:
    return VIM_LORDS[star_idx(lon) % 9]


def evaluate_stars(nat: Native, d: datetime) -> dict:
    v = nat.v
    core = nat.core
    natal_stars = {star_idx(float(v.longitudes[p])) for p in core
                   if p in v.longitudes}

    chain = [p.lord for p in v.current_dasha("vimshottari", d, levels=2)]
    md, ad = chain[0], (chain[1] if len(chain) > 1 else chain[0])

    lon = {p: nat.transit_lon(d, p)
           for p in (Planet.SUN, Planet.MOON, Planet.VENUS, Planet.JUPITER,
                     Planet.SATURN, md, ad)}

    res = {
        "N1_jup_star": star_lord(lon[Planet.JUPITER]) in core,
        "N2_sat_star": star_lord(lon[Planet.SATURN]) in core,
        "N3_jup_natal_star": star_idx(lon[Planet.JUPITER]) in natal_stars,
        "N4_sat_natal_star": star_idx(lon[Planet.SATURN]) in natal_stars,
        "N5_md_star": star_lord(lon[md]) in core,
        "N6_ad_star": star_lord(lon[ad]) in core,
        "N7_sun_star": star_lord(lon[Planet.SUN]) in core,
        "N8_moon_star": star_lord(lon[Planet.MOON]) in core,
        "N9_venus_star": star_lord(lon[Planet.VENUS]) in core,
        "N10_moon_natal_star": star_idx(lon[Planet.MOON]) in natal_stars,
    }
    h12 = nat.evaluate(d)["H12_double_transit"]
    res["C1_dt_and_moon"] = h12 and res["N8_moon_star"]
    res["C2_slowstar_and_moon"] = (res["N1_jup_star"] or res["N2_sat_star"]) \
        and res["N8_moon_star"]
    res["_core_size"] = len({star_lord(float(v.longitudes[p]))
                             for p in core})  # informational
    return res


def main() -> None:
    people = json.loads((HERE / "dataset.json").read_text())["people"]
    wed_freq, ctl_freq = Counter(), Counter()
    n_ctl = 0
    natives_out = []

    for i, person in enumerate(people, 1):
        nat = Native(person)
        marr = datetime.strptime(person["marriage"], "%Y-%m-%d").replace(
            hour=12, tzinfo=UTC)
        wed = evaluate_stars(nat, marr)
        for h in NHYPS:
            wed_freq[h] += bool(wed[h])

        lo = nat.birth_utc + timedelta(days=int(18 * 365.25))
        hi = min(nat.birth_utc + timedelta(days=int(62 * 365.25)), EPHEM_MAX)
        ctl_vecs = []
        got, tries = 0, 0
        while got < N_CONTROL and tries < 80:
            tries += 1
            d = lo + (hi - lo) * random.random()
            if abs((d - marr).days) < 400:
                continue
            c = evaluate_stars(nat, d)
            ctl_vecs.append({h: bool(c[h]) for h in NHYPS})
            for h in NHYPS:
                ctl_freq[h] += bool(c[h])
            got += 1
        n_ctl += got
        natives_out.append({"name": person["name"],
                            "wedding": {h: bool(wed[h]) for h in NHYPS},
                            "controls": ctl_vecs})
        fired = [h for h in NHYPS if wed[h]]
        print(f"[{i:2}/50] {person['name']:<22} fired={len(fired):2}  "
              f"{','.join(h.split('_')[0] for h in fired)}")

    nW = len(natives_out)
    print(f"\n=== STAR-LEVEL LIFT ({nW} weddings vs {n_ctl} controls) ===")
    print(f"{'hypothesis':<26} {'wed%':>6} {'ctl%':>6} {'lift':>7}")
    lift = []
    for h in NHYPS:
        w = 100 * wed_freq[h] / nW
        c = 100 * ctl_freq[h] / n_ctl
        lift.append({"hyp": h, "wedding_pct": round(w, 1),
                     "control_pct": round(c, 1), "lift": round(w - c, 1)})
        print(f"{h:<26} {w:6.0f} {c:6.0f} {w - c:+7.1f}")

    (HERE / "nakshatra_results.json").write_text(json.dumps(
        {"lift": lift, "natives": natives_out}, indent=2))


if __name__ == "__main__":
    main()
