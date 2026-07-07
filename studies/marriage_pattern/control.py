"""Control / baseline for the marriage-trigger study.

A node that fires at 98% of wedding dates only means something if it does NOT also
fire at 98% of *random* dates. This evaluates every native at several random
non-marriage dates (adulthood window, kept clear of their actual wedding) and
reports each timing node's LIFT = P(fires | wedding) − P(fires | random date).

High positive lift ⇒ a genuine trigger. ~0 lift ⇒ ambient (fires all the time).
"""

from __future__ import annotations

import json
import random
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from advance_astrology import VedicChart
from interpreter.event_evidence import DOMAIN_PROFILES, candidate_map

HERE = Path(__file__).resolve().parent
UTC = timezone.utc
PROFILE = DOMAIN_PROFILES["marriage"]
random.seed(1729)
N_CONTROL = 4                      # random dates per native
EPHEM_MAX = datetime(2053, 1, 1, tzinfo=UTC)


def firing_at(v, when):
    lo, hi = when - timedelta(hours=12), when + timedelta(hours=12)
    rows = candidate_map(v, PROFILE, lo, hi)
    if not rows:
        return None
    row = min(rows, key=lambda r: abs((r.start - when).total_seconds()))
    return [n for n, _ in row.firing_nodes()]


def main() -> None:
    people = json.loads((HERE / "dataset.json").read_text())["people"]
    marr_res = json.loads((HERE / "results.json").read_text())["results"]
    marr_freq = Counter()
    for r in marr_res:
        marr_freq.update(r["firing_nodes"])
    nM = len(marr_res)

    base_freq = Counter()
    n_ctrl = 0
    for person in people:
        when = datetime.strptime(f"{person['date']} {person['time']}",
                                 "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo(person["tz"]))
        v = VedicChart.create(when=when, latitude=person["lat"], longitude=person["lon"])
        birth_utc = when.astimezone(UTC)
        marr = datetime.strptime(person["marriage"], "%Y-%m-%d").replace(
            hour=12, tzinfo=UTC)
        lo = birth_utc + timedelta(days=int(18 * 365.25))
        hi = min(birth_utc + timedelta(days=int(62 * 365.25)), EPHEM_MAX)
        got = 0
        tries = 0
        while got < N_CONTROL and tries < 40:
            tries += 1
            frac = random.random()
            d = lo + (hi - lo) * frac
            if abs((d - marr).days) < 400:          # keep clear of the real wedding
                continue
            nodes = firing_at(v, d)
            if nodes is None:
                continue
            base_freq.update(nodes)
            got += 1
            n_ctrl += 1
        print(f"  {person['name']:<22} control dates used: {got}")

    all_nodes = set(marr_freq) | set(base_freq)
    rows = []
    for node in all_nodes:
        m = 100 * marr_freq[node] / nM
        b = 100 * base_freq[node] / (n_ctrl or 1)
        rows.append((node, m, b, m - b))
    rows.sort(key=lambda x: -x[3])

    print(f"\n=== LIFT: marriage% − baseline% ({nM} weddings vs {n_ctrl} random dates) ===")
    print(f"{'node':<55} {'wed%':>6} {'base%':>6} {'lift':>7}")
    for node, m, b, lift in rows:
        print(f"{node:<55} {m:6.0f} {b:6.0f} {lift:+7.0f}")

    (HERE / "control.json").write_text(json.dumps(
        {"n_weddings": nM, "n_control": n_ctrl,
         "lift": [{"node": n, "wedding_pct": round(m, 1),
                   "baseline_pct": round(b, 1), "lift": round(l, 1)}
                  for n, m, b, l in rows]}, indent=2))


if __name__ == "__main__":
    main()
