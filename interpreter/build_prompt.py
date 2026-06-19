"""Assemble a ready-to-paste interpretation prompt.

Combines the playbook (the triangulation rules / system instructions) with
the engine's Phase-I matrix for a given birth, producing one self-contained
prompt. Paste the result into any chat LLM (claude.ai, Gemini, ChatGPT —
all have free tiers) for a zero-API-cost reading, or feed it to a provider
adapter later.

    python -m interpreter.build_prompt \
        --playbook playbook.txt \
        --when "1991-04-04 06:23" --tz Asia/Kolkata \
        --lat 23.63 --lon 85.52 --place "Ramgarh, Jharkhand" --sex male \
        --query "Analyse the last 5 years of major life events" \
        --out dryrun_prompt.txt
"""

from __future__ import annotations

import argparse
from datetime import datetime
from zoneinfo import ZoneInfo

from interpreter.build_matrix import build_matrix

PROMPT_TEMPLATE = """\
{playbook}

==================================================================
END OF PLAYBOOK. The native's computed matrix follows. Treat every
number below as ground truth produced by a verified astronomical
engine — do NOT recompute positions. Execute the playbook's
Macro-to-Micro Rule-Out workflow (Sections 3-6) on this data.
==================================================================

{matrix}

==================================================================
NATIVE'S QUERY
==================================================================
{query}

Follow the Section 6 output template exactly:
- The Activated Macro-Pattern
- Structural Micro-Dissection (with Success vs. Cancellation filters)
- Cross-Paddhati Verification & Timing
- The Core Synthesis Summary (blockquote)
"""


def build_prompt(playbook_text: str, when_local: datetime, lat: float,
                 lon: float, place: str, sex: str, name: str,
                 ayanamsa: str, query: str, transit_years: int = 6) -> str:
    matrix = build_matrix(when_local, lat, lon, place, sex, name, ayanamsa,
                          transit_years)
    return PROMPT_TEMPLATE.format(playbook=playbook_text.strip(),
                                  matrix=matrix, query=query.strip())


def main() -> None:
    ap = argparse.ArgumentParser(description="Build a paste-ready interpretation prompt.")
    ap.add_argument("--playbook", required=True, help="Path to playbook text file")
    ap.add_argument("--when", required=True)
    ap.add_argument("--tz", default="Asia/Kolkata")
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--place", default="")
    ap.add_argument("--sex", default="")
    ap.add_argument("--name", default="")
    ap.add_argument("--ayanamsa", default="lahiri")
    ap.add_argument("--transit-years", type=int, default=6,
                    help="Years of slow-gochara timeline to emit (default 6)")
    ap.add_argument("--query", required=True, help="The native's question for the engine")
    ap.add_argument("--out", default="", help="Output file (default: stdout)")
    args = ap.parse_args()

    with open(args.playbook) as fh:
        playbook_text = fh.read()
    when_local = datetime.strptime(args.when, "%Y-%m-%d %H:%M").replace(
        tzinfo=ZoneInfo(args.tz))
    prompt = build_prompt(playbook_text, when_local, args.lat, args.lon,
                          args.place, args.sex, args.name, args.ayanamsa,
                          args.query, args.transit_years)
    if args.out:
        with open(args.out, "w") as fh:
            fh.write(prompt)
        print(f"Wrote prompt to {args.out} ({len(prompt)} chars)")
    else:
        print(prompt)


if __name__ == "__main__":
    main()
