"""Marriage-trigger pattern study.

For each of the 50 Rodden-rated natives, build the Vedic chart and evaluate the
engine's ``marriage`` event-evidence panel AT the wedding date, then record which
timing WITNESSES (nodes) fired and the concrete DRIVERS behind them (which daśā
lords, which transit). Aggregate to expose the common pattern vs. the varying
drivers.

The at-date snapshot uses a tight ±12h window: ``_pratyantar_midpoints`` clips the
containing pratyantar to that window so the single evaluation lands on the wedding
date, and ``scan_windows`` samples both endpoints so slow-transit booleans reflect
the instantaneous state.

Usage:
    python -m studies.marriage_pattern.run_marriage_study            # all 50
    python -m studies.marriage_pattern.run_marriage_study "Barack Obama"  # one
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from advance_astrology import VedicChart
from advance_astrology.constants import SIGNS, Planet
from interpreter.event_evidence import (
    DOMAIN_PROFILES,
    candidate_map,
    standing_balance,
)

HERE = Path(__file__).resolve().parent
DATASET = HERE / "dataset.json"
UTC = timezone.utc
PROFILE = DOMAIN_PROFILES["marriage"]           # houses=[7], fulfil=[2,7,11], kāraka Venus


def _sign(idx: int) -> str:
    return SIGNS[idx % 12]


def _lord_roles(v: VedicChart, lord: Planet, dk: Planet) -> list[str]:
    """Why this daśā lord is (or isn't) a marriage significator."""
    ruled = [h for h in range(1, 13) if v.house_lord(h) == lord]
    roles = [f"{h}L" for h in ruled]
    if lord == Planet.VENUS:
        roles.append("Venus/kalatra-kāraka")
    if lord == Planet.JUPITER:
        roles.append("Jupiter/jīva")
    if lord == dk:
        roles.append("DK/dārā-kāraka")
    return roles


def _signifies_marriage(roles: list[str]) -> bool:
    fulfil = {"2L", "7L", "11L"}
    return bool(fulfil.intersection(roles)) or "Venus/kalatra-kāraka" in roles \
        or "DK/dārā-kāraka" in roles


def analyse(person: dict) -> dict:
    when = datetime.strptime(f"{person['date']} {person['time']}", "%Y-%m-%d %H:%M") \
        .replace(tzinfo=ZoneInfo(person["tz"]))
    v = VedicChart.create(when=when, latitude=person["lat"], longitude=person["lon"])

    marr = datetime.strptime(person["marriage"], "%Y-%m-%d") \
        .replace(hour=12, tzinfo=UTC)
    lo, hi = marr - timedelta(hours=12), marr + timedelta(hours=12)

    rows = candidate_map(v, PROFILE, lo, hi)
    if not rows:
        raise RuntimeError("no evaluation row produced at marriage date")
    row = min(rows, key=lambda r: abs((r.start - marr).total_seconds()))

    # --- authoritative daśā chain at the wedding date ------------------------
    chain = [p.lord for p in v.current_dasha("vimshottari", marr, levels=3)]
    md_ad_pd = [p.value for p in chain]
    dk = v.chara_karakas().get("Darakaraka")
    chain_roles = {p.value: _lord_roles(v, p, dk) for p in chain}
    chain_signifies = any(_signifies_marriage(r) for r in chain_roles.values())

    # --- transit drivers at the wedding date ---------------------------------
    tr = v.transits()
    asc = v.ascendant_sign
    seventh_sign = (asc + 6) % 12
    jup_s = tr.transit_sign(marr, Planet.JUPITER)
    sat_s = tr.transit_sign(marr, Planet.SATURN)
    ul_sign = None
    try:
        ul_sign = v.arudhas().get("UL")
    except Exception:
        pass

    firing = [n for n, _ in row.firing_nodes()]
    bal, _ = standing_balance(v, PROFILE)

    return {
        "name": person["name"],
        "rating": person["rating"],
        "marriage": person["marriage"],
        "lagna": _sign(asc),
        "lagnesh": v.house_lord(1).value,
        "seventh_lord": v.house_lord(7).value,
        "darakaraka": dk.value if dk else None,
        "dasha_MD_AD_PD": md_ad_pd,
        "dasha_roles": chain_roles,
        "dasha_signifies_marriage": chain_signifies,
        "kp_fulfil": row.kp_fulfil,
        "kp_negate": row.kp_negate,
        "transit_jupiter_sign": _sign(jup_s),
        "transit_saturn_sign": _sign(sat_s),
        "seventh_sign": _sign(seventh_sign),
        "upapada_sign": _sign(ul_sign) if ul_sign is not None else None,
        "standing_balance": round(bal, 2),
        "firing_nodes": firing,
        "n_firing": len(firing),
        "fields": {
            "house_double_transit": row.house_double_transit,
            "lord_double_transit": row.lord_double_transit,
            "saham_double_transit": row.saham_double_transit,
            "fulfil_house_dt": row.fulfil_house_dt,
            "gochara_from_moon": row.gochara_from_moon,
            "arudha_axis": row.arudha_axis,
            "nadi_jeeva": row.nadi_jeeva,
            "nadi_karma": row.nadi_karma,
            "bnn": row.bnn,
            "kakshya": row.kakshya,
            "sudarshana_hit": row.sudarshana_hit,
            "varshaphal_muntha": row.varshaphal_muntha,
            "bb_active": row.bb_active,
            "sade_sati": row.sade_sati,
            "kp_star_transit": row.kp_star_transit,
            "karaka_in_chain": row.karaka_in_chain,
            "karaka_sukshma": row.karaka_sukshma,
            "lagnesh_in_chain": row.lagnesh_in_chain,
            "lagna_activators": row.lagna_activators,
        },
    }


def main() -> None:
    data = json.loads(DATASET.read_text())
    people = data["people"]
    if len(sys.argv) > 1:
        want = sys.argv[1].lower()
        people = [p for p in people if want in p["name"].lower()]

    results, failures = [], []
    for i, person in enumerate(people, 1):
        try:
            r = analyse(person)
            results.append(r)
            print(f"[{i:2}/{len(people)}] {r['name']:<22} "
                  f"nodes={r['n_firing']:2}  KP {r['kp_fulfil']}/{r['kp_negate']}  "
                  f"dasha-signifies={'Y' if r['dasha_signifies_marriage'] else 'n'}  "
                  f"MD>AD>PD={'>'.join(r['dasha_MD_AD_PD'])}")
        except Exception as e:  # keep the batch alive
            failures.append({"name": person["name"], "error": repr(e)})
            print(f"[{i:2}/{len(people)}] {person['name']:<22} FAILED: {e!r}")

    # ---- aggregate ---------------------------------------------------------
    node_freq = Counter()
    field_freq = Counter()
    for r in results:
        node_freq.update(r["firing_nodes"])
        field_freq.update(k for k, val in r["fields"].items()
                          if isinstance(val, bool) and val)
    n = len(results) or 1
    aggregate = {
        "n_people": len(results),
        "node_frequency": [
            {"node": k, "count": c, "pct": round(100 * c / n, 1)}
            for k, c in node_freq.most_common()
        ],
        "field_frequency": [
            {"field": k, "count": c, "pct": round(100 * c / n, 1)}
            for k, c in field_freq.most_common()
        ],
        "dasha_signifies_marriage_pct": round(
            100 * sum(r["dasha_signifies_marriage"] for r in results) / n, 1),
        "kp_fulfil_ge_negate_pct": round(
            100 * sum(r["kp_fulfil"] >= max(1, r["kp_negate"]) for r in results) / n, 1),
    }

    out = {"aggregate": aggregate, "results": results, "failures": failures}
    (HERE / "results.json").write_text(json.dumps(out, indent=2, default=str))

    print("\n===== AGGREGATE across", len(results), "charts "
          f"({len(failures)} failed) =====")
    print(f"daśā chain signifies marriage (2/7/11 lord, Venus, or DK): "
          f"{aggregate['dasha_signifies_marriage_pct']}%")
    print(f"KP fulfil >= negate in running chain: "
          f"{aggregate['kp_fulfil_ge_negate_pct']}%")
    print("\nTiming NODE frequency (the shared pattern):")
    for e in aggregate["node_frequency"]:
        print(f"  {e['pct']:5.1f}%  ({e['count']:2}/{n})  {e['node']}")
    if failures:
        print("\nFailures:")
        for f in failures:
            print(" ", f["name"], f["error"])


if __name__ == "__main__":
    main()
