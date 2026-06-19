"""Blind prediction runner — the convergence engine as a one-command tool.

Casts the chart, then prints the deterministic triangulation **timeline**
(theme peaks with precise gochara triggers) and a **single-window dossier**.
This is the harness for the no-calibration blind test: run it, read the engine's
committed calls, and compare against real life events yourself.

    python -m interpreter.predict \
        --when "1991-04-04 06:23" --tz Asia/Kolkata \
        --lat 23.62 --lon 85.48 --place "Ramgarh" --name Native \
        --years 6
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from advance_astrology import VedicChart


def main() -> None:
    ap = argparse.ArgumentParser(description="Blind triangulation prediction.")
    ap.add_argument("--when", required=True, help='Birth datetime "YYYY-MM-DD HH:MM"')
    ap.add_argument("--tz", default="Asia/Kolkata")
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--place", default="")
    ap.add_argument("--name", default="")
    ap.add_argument("--ayanamsa", default="lahiri")
    ap.add_argument("--start", default="", help='Window start "YYYY-MM-DD" (UTC)')
    ap.add_argument("--end", default="", help='Window end "YYYY-MM-DD" (UTC)')
    ap.add_argument("--years", type=int, default=6,
                    help="If --start/--end omitted: last N years up to --asof")
    ap.add_argument("--asof", default="", help='Reference date "YYYY-MM-DD" (default today)')
    ap.add_argument("--width", type=int, default=183, help="Timeline window width (days)")
    ap.add_argument("--step", type=int, default=30, help="Timeline step (days)")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    when_local = datetime.strptime(args.when, "%Y-%m-%d %H:%M").replace(
        tzinfo=ZoneInfo(args.tz))
    v = VedicChart.create(when=when_local, latitude=args.lat, longitude=args.lon,
                          name=args.name, ayanamsa=args.ayanamsa)

    asof = (datetime.strptime(args.asof, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if args.asof else datetime.now(timezone.utc))
    if args.start and args.end:
        start = datetime.strptime(args.start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end = datetime.strptime(args.end, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        end = asof
        start = end - timedelta(days=int(365.25 * args.years))

    header = (f"NATIVE: {args.name or '(unnamed)'}  @ {args.place}\n"
              f"BIRTH : {when_local:%Y-%m-%d %H:%M %Z}  "
              f"({args.lat}, {args.lon})  ayanamsa={args.ayanamsa}\n")
    tl = v.triangulate_timeline(start, end, width_days=args.width,
                                step_days=args.step)
    dossier = v.triangulate(start, end)
    text = (header + "\n" + tl.text()
            + "\n\n" + "=" * 66 + "\n"
            + "AGGREGATE DOSSIER (whole window — committed call)\n"
            + "=" * 66 + "\n" + dossier.text())

    if args.out:
        with open(args.out, "w") as fh:
            fh.write(text)
        print(f"Wrote prediction to {args.out} ({len(text)} chars)")
    else:
        print(text)


if __name__ == "__main__":
    main()
