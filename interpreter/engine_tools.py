"""Engine tools — the engine's sections offered to Claude as tool calls.

Claude plans which calculations a question needs (by the granthas), records
that plan with ``record_plan``, then fetches each calculation from the engine
through these tools. Every number comes from ``interpreter.reading_bundle``;
the tools only choose which part of it to compute and return. Nothing here
scores or judges.
"""

from __future__ import annotations

from datetime import datetime, time, timezone

from advance_astrology.vedic.vargas import VARGA_FUNCS

from interpreter.reading_bundle import Reading

SECTION_HELP = {
    "strengths": ("Shadbala of the seven grahas by component (sthana/dig/kala/cheshta/naisargika/"
                  "drik and their parts: uccha, saptavargaja, oja-yugma, kendradi, drekkana, "
                  "nathonnatha, paksha, tribhaga, varsha-masa, ayana), Ishta/Kashta phala, and "
                  "Bhava Bala of all twelve houses (lord's shadbala + bhava digbala + bhava "
                  "drishti bala)."),
    "gulika": "Gulika and Mandi (start/middle of Saturn's segment) and the other upagrahas, with natal house.",
    "vimshottari": "Vimshottari running chain MD→AD→PD→Sukshma→Prana now, the ADs/PDs around it, next MDs, next AD's PDs.",
    "rashi_dashas": "Chara, Narayana, Sudasa (Jaimini rashi dashas) with ADs; Yogini; Ashtottari; Mudda; Sudarshana chakra year/month signs.",
    "varshaphal": "Running Tajika annual chart: Varsha lagna, Muntha and its lord, year lord, annual positions.",
    "sahams": "All Tajika sahams with sign/degree and natal house.",
    "vargas": "D9, D7, D10, D30, D60 placements (use the varga tool for any other division).",
    "avasthas": ("Every graha's avasthas: Baladi (incl. Mrita), Jagradadi, Deeptadi (incl. Duhkhita, "
                 "Vikala), combustion, Lajjitadi (Lajjita/Garvita/Kshudhita/Trishita/Mudita/Kshobhita, "
                 "each with the condition that met it; seven grahas) and Shayanadi (twelve activities)."),
    "kp": "KP: houses each graha signifies.",
    "gochara_now": "Today's gochara: houses from Lagna/Moon/Sun/AL/UL/Karakamsha, nakshatra, tara, vedha, SAV, kakshya, aspects, Saturn from Moon (sade-sati/dhaiya), Sarvatobhadra hits.",
    "ingresses": "Next 18 months: rashi and nakshatra ingresses and retro/direct stations of Saturn, Jupiter, Rahu, Ketu, Mars.",
    "bnn_windows": "Degree windows (±2°) of Saturn/Jupiter/Rahu/Ketu over each natal graha and Lagna, past and next 18 months.",
    "double_transit": "Jupiter+Saturn double-transit windows on each house from Lagna, next 4 years.",
}

TOOLS = [
    {
        "name": "record_plan",
        "description": (
            "Call this FIRST, before any other tool. From the granthas (BPHS, Phaladeepika, "
            "Saravali, Jaimini Sutras, Tajika Neelakanthi, KP, Uttara Kalamrita …) list every "
            "calculation this question needs and why. Then list in `gaps` any calculation the "
            "granthas call for that none of the other tools provides; it will be reported to "
            "the engine maintainers, and you must not compute it yourself."),
        "input_schema": {
            "type": "object",
            "properties": {
                "items": {"type": "array", "items": {
                    "type": "object",
                    "properties": {
                        "calculation": {"type": "string", "description": "e.g. 'Deeptadi avastha of the 6th lord'"},
                        "source": {"type": "string", "description": "Grantha and chapter/verse if known"},
                        "why": {"type": "string", "description": "What it tells about this question"},
                        "tool": {"type": "string", "description": "Tool that provides it"},
                    },
                    "required": ["calculation", "source", "why", "tool"]}},
                "gaps": {"type": "array", "items": {
                    "type": "object",
                    "properties": {"calculation": {"type": "string"},
                                   "source": {"type": "string"}},
                    "required": ["calculation", "source"]}},
            },
            "required": ["items", "gaps"],
        },
    },
    {
        "name": "engine_section",
        "description": "Fetch one computed section of the chart. Sections: " + " | ".join(
            f"{k}: {v}" for k, v in SECTION_HELP.items()),
        "input_schema": {"type": "object",
                         "properties": {"section": {"type": "string", "enum": list(SECTION_HELP)}},
                         "required": ["section"]},
    },
    {
        "name": "samanvaya",
        "description": (
            "All five Samanvaya school engines (KP, dasha_timing, jaimini, tajika, nadi) for one "
            "life-area: its houses, karaka, promise/denial data, running-period links and "
            "transit triggers. `domain` is a life-area word (English or Hinglish), e.g. "
            "marriage, career, children, wealth, mother, father, illness, education, "
            "relocation, debt, litigation, mental peace, siblings."),
        "input_schema": {"type": "object",
                         "properties": {"domain": {"type": "string"}},
                         "required": ["domain"]},
    },
    {
        "name": "dasha_at",
        "description": "Vimshottari chain and the Jaimini/Yogini/Ashtottari/Mudda/Sudarshana periods running on a given date (YYYY-MM-DD).",
        "input_schema": {"type": "object",
                         "properties": {"date": {"type": "string"}},
                         "required": ["date"]},
    },
    {
        "name": "gochara_on",
        "description": "The full gochara snapshot (as in engine_section gochara_now) on a given date (YYYY-MM-DD).",
        "input_schema": {"type": "object",
                         "properties": {"date": {"type": "string"}},
                         "required": ["date"]},
    },
    {
        "name": "varga",
        "description": "Placements in any divisional chart. Divisions: " + ", ".join(
            f"D{d}" for d in sorted(VARGA_FUNCS)),
        "input_schema": {"type": "object",
                         "properties": {"division": {"type": "integer"}},
                         "required": ["division"]},
    },
    {
        "name": "varshaphal_year",
        "description": "The Tajika annual chart for a given year (the year of the solar return).",
        "input_schema": {"type": "object",
                         "properties": {"year": {"type": "integer"}},
                         "required": ["year"]},
    },
]


def _date(s: str, tz) -> datetime:
    return datetime.combine(datetime.strptime(s[:10], "%Y-%m-%d").date(), time(12),
                            tzinfo=tz).astimezone(timezone.utc)


def run_tool(r: Reading, name: str, args: dict) -> str:
    """Run one tool call; returns the text result (raises on bad input)."""
    L: list = []
    if name == "engine_section":
        return r.section(args["section"])
    if name == "samanvaya":
        return r.samanvaya(str(args["domain"]).strip().lower())
    if name == "dasha_at":
        at = _date(args["date"], r.tz)
        r._vimshottari(L, at)
        r._rashi_dashas(L, at)
    elif name == "gochara_on":
        r._gochara_now(L, _date(args["date"], r.tz))
    elif name == "varga":
        dv = int(args["division"])
        if dv not in VARGA_FUNCS:
            raise ValueError(f"D{dv} is not computed; available: {sorted(VARGA_FUNCS)}")
        r._vargas(L, (dv,))
    elif name == "varshaphal_year":
        r._varshaphal(L, int(args["year"]))
    else:
        raise ValueError(f"unknown tool {name}")
    return "\n".join(L).strip("\n")
