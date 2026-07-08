"""Marriage-window PREDICTOR — applies the validated trigger composite forward.

Given birth details + a search span, samples the span every ~10 days, scores each
date with the trigger set validated on the 50-chart study (transit-driven; daśā
link kept as an annotation/gate, not the ranker), groups high scores into windows
and prints the top-ranked marriage windows.

Honest contract (see FINDINGS.md): this concentrates probability ~2× around true
wedding windows (permutation p=0.007 on the validation set); it emits WINDOWS,
never a specific day. Whether the person marries at all is the natal-promise
question — run the engine's marriage pack for that.

Blind-test mode: pass --actual YYYY-MM-DD[,YYYY-MM-DD…] AFTER the ranking is
computed purely from birth data; the script then reports where each real wedding
landed (score percentile + top-window membership).

Usage:
  python -m studies.marriage_pattern.predict_marriage \
      --date 1955-03-19 --time 18:32 --tz Europe/Berlin \
      --lat 49.7128 --lon 7.3134 --sex M \
      --start 1985-01-01 --end 2012-01-01 \
      [--actual 1987-11-21,2009-03-21] [--top 5]
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone

from studies.marriage_pattern.circuit_study import HYPS, Native

UTC = timezone.utc
STEP_DAYS = 10

# Trigger weights validated on the 50-chart study (circuit_results/FINDINGS.md).
TRIGGER_WEIGHTS = {
    "H12_double_transit": 2.0,     # Jup+Sat both on 7th/7L/UL   (+16 lift)
    "H7_jup_degree": 1.0,          # Jupiter ≤6° of desc/7L/Venus (+10)
    "H11_sat_gochara": 1.0,        # Saturn on 7th/UL/7th-from-UL (+9)
    "H9_bnn_gender_jup": 1.0,      # BNN: Jup on Venus(M)/Mars(F)  (+5)
    "H10_jup_gochara": 0.5,        # Jupiter on 7th/UL/Moon-7th    (+4)
    "H3_dasha_star": 0.5,          # daśā lord in star of circuit  (+3)
}
DASHA_LINK = ("H1_dasha_core", "H3_dasha_star", "H4_dasha_D9", "H5_gender_karaka")


def trigger_score(res: dict) -> float:
    return sum(w for h, w in TRIGGER_WEIGHTS.items() if res[h])


def scan(nat: Native, start: datetime, end: datetime) -> list[dict]:
    out = []
    d = start
    while d <= end:
        res = nat.evaluate(d)
        out.append({
            "date": d,
            "score": trigger_score(res),
            "dasha_link": any(res[h] for h in DASHA_LINK),
            "drivers": [h for h in TRIGGER_WEIGHTS if res[h]],
        })
        d += timedelta(days=STEP_DAYS)
    return out

def group_windows(samples: list[dict], threshold: float) -> list[dict]:
    """Contiguous runs of samples ≥ threshold (gap ≤ 3 steps) → windows."""
    windows, cur = [], None
    for s in samples:
        if s["score"] >= threshold:
            if cur and (s["date"] - cur["end"]).days <= 3 * STEP_DAYS:
                cur["end"] = s["date"]
                if s["score"] > cur["peak"]:
                    cur.update(peak=s["score"], peak_date=s["date"],
                               drivers=s["drivers"], dasha_link=s["dasha_link"])
            else:
                if cur:
                    windows.append(cur)
                cur = dict(start=s["date"], end=s["date"], peak=s["score"],
                           peak_date=s["date"], drivers=s["drivers"],
                           dasha_link=s["dasha_link"])
        # gaps handled by the distance check above
    if cur:
        windows.append(cur)
    return sorted(windows, key=lambda w: (-w["peak"],
                                          -(w["end"] - w["start"]).days))


def main() -> None:
    ap = argparse.ArgumentParser(description="Marriage-window predictor (validated trigger composite).")
    ap.add_argument("--date", required=True)
    ap.add_argument("--time", required=True)
    ap.add_argument("--tz", required=True)
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--sex", choices=["M", "F"], required=True)
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--actual", default="",
                    help="comma-separated real wedding dates for blind evaluation")
    ap.add_argument("--top", type=int, default=5)
    args = ap.parse_args()

    person = dict(name="query", date=args.date, time=args.time, tz=args.tz,
                  lat=args.lat, lon=args.lon, sex=args.sex)
    nat = Native(person)
    start = datetime.strptime(args.start, "%Y-%m-%d").replace(hour=12, tzinfo=UTC)
    end = datetime.strptime(args.end, "%Y-%m-%d").replace(hour=12, tzinfo=UTC)

    samples = scan(nat, start, end)
    scores = sorted(s["score"] for s in samples)
    threshold = scores[int(0.85 * len(scores))]          # top ~15% of the span
    windows = group_windows(samples, threshold)[:args.top]

    print(f"# Marriage-window forecast — {args.date} {args.time} {args.tz} "
          f"({args.sex}), span {args.start} → {args.end}")
    print(f"  samples={len(samples)} step={STEP_DAYS}d "
          f"score threshold (top ~15%)={threshold:.1f}\n")
    print(f"  TOP {len(windows)} WINDOWS (peak-scored; drivers at peak):")
    for i, w in enumerate(windows, 1):
        print(f"  {i}. {w['start']:%Y-%m-%d} → {w['end']:%Y-%m-%d}   "
              f"peak={w['peak']:.1f} @ {w['peak_date']:%Y-%m}  "
              f"daśā-link={'Y' if w['dasha_link'] else 'n'}")
        print(f"     drivers: {', '.join(w['drivers'])}")

    if args.actual:
        print("\n  BLIND EVALUATION against actual wedding date(s):")
        n = len(samples)
        for ds in args.actual.split(","):
            d = datetime.strptime(ds.strip(), "%Y-%m-%d").replace(hour=12, tzinfo=UTC)
            res = nat.evaluate(d)
            sc = trigger_score(res)
            pct = 100.0 * (sum(1 for s in samples if s["score"] < sc)
                           + 0.5 * sum(1 for s in samples if s["score"] == sc)) / n
            pad = timedelta(days=STEP_DAYS)
            hit = next((i for i, w in enumerate(windows, 1)
                        if w["start"] - pad <= d <= w["end"] + pad), None)
            print(f"    {ds}: score={sc:.1f} → percentile {pct:.0f} of the span"
                  + (f"  ✔ inside top-window #{hit}" if hit
                     else "  ✘ not inside a top window"))


if __name__ == "__main__":
    main()
