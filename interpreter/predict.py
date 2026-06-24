"""Blind prediction runner — the convergence engine as a one-command tool.

Casts the chart, then prints the deterministic triangulation **timeline**
(theme peaks with precise gochara triggers) and a **single-window dossier**.
This is the harness for the no-calibration blind test: run it, read the engine's
committed calls, and compare against real life events yourself.

    python -m interpreter.predict \
        --when "YYYY-MM-DD HH:MM" --tz Asia/Kolkata \
        --lat <LAT> --lon <LON> --place "<City>" --name Native \
        --years 6
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from advance_astrology import VedicChart


NARRATOR_PROMPT = """\
You are a careful NARRATOR for a Vedic-astrology prediction engine. A
deterministic engine has ALREADY done every calculation and triangulation and
committed the prediction below. Your ONLY job is to translate that fixed output
into clear, readable prose. This is a blind test of the engine.

HARD RULES (read twice):
1. Do NOT recompute, re-derive, or "double-check" any position, score, date, or
   verdict. Treat every number and date below as ground truth.
2. Do NOT add any astrological factor, planet, house, yoga, dasha or transit
   that is not already present in the engine output.
3. Do NOT guess, infer, or invent what real-life event happened. You describe
   only what the engine's themes/texture/timing SAY; you have no knowledge of
   the native's actual life and must not pretend to.
4. If the engine did not flag something, it is silent — do not fill the gap.
5. Keep each theme's committed dates, salience and texture exactly as given.

Your output, per active theme, should read like a directive analytical summary:
the theme, its candidate window/peak date(s), the texture (clean manifestation /
friction / fixed-then-cancelled / blocked), and the precise gochara/BNN/Kakṣyā
triggers the engine attached — phrased so a human can compare it against memory.

Finally, format using this template (from the playbook's Section 6):
● The Activated Macro-Patterns — which themes the engine isolated and ranked.
● Structural Micro-Dissection — texture (success vs cancellation) per theme,
  strictly from the engine's support/obstruction reasons.
● Cross-Paddhati Verification & Timing — the committed peak dates and the
  precise trigger windows.
● The Core Synthesis Summary — a short blockquote per top theme: "<theme>,
  <texture>, around <date(s)>" — nothing more.

================= ENGINE OUTPUT (GROUND TRUTH — DO NOT ALTER) =================
{engine_output}
==============================================================================
Now narrate the above under the four headings. Add no astrology of your own.
"""


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
    ap.add_argument("--prompt", action="store_true",
                    help="Wrap the engine output as a paste-ready AI narrator prompt")
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
    engine_output = (header + "\n" + tl.text()
                     + "\n\n" + "=" * 66 + "\n"
                     + "AGGREGATE DOSSIER (whole window — committed call)\n"
                     + "=" * 66 + "\n" + dossier.text())

    if args.prompt:
        text = NARRATOR_PROMPT.format(engine_output=engine_output)
    else:
        text = engine_output

    if args.out:
        with open(args.out, "w") as fh:
            fh.write(text)
        print(f"Wrote prediction to {args.out} ({len(text)} chars)")
    else:
        print(text)


if __name__ == "__main__":
    main()
