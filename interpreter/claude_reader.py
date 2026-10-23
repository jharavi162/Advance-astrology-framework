"""Claude reader — turns the engine bundle + a prompt template into a reading.

The engine computes (``interpreter.reading_bundle``); Claude interprets. It
first records a grantha-based plan of the calculations the question needs,
then fetches them through ``interpreter.engine_tools``, then writes. The
prompt the user wrote lives in ``prompts/reading_default.md`` with a
``{question}`` slot, and the key-question cards in ``prompts/cards.json`` fill
that slot. The interpretive director (``docs/AI_TRIANGULATION_PROMPT.md`` and
``docs/AI_EVENT_TIMING_GUIDE.md``) is sent as the system prompt, unchanged and
cached, so every card reads the chart the same way.
"""

from __future__ import annotations

import hashlib
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPTS = os.path.join(ROOT, "prompts")
DOCS = os.path.join(ROOT, "docs")

MODEL = os.environ.get("HORASUTRA_MODEL", "claude-opus-5-5")
EFFORT = os.environ.get("HORASUTRA_EFFORT", "high")
MAX_TOKENS = 64000      # the multi-topic PDF report is long; thinking counts too

SYSTEM_HEADER = """You are the interpretation layer of HoraSutra, a Vedic astrology app.

A deterministic engine computes everything about this chart. The natal matrix
is in the ENGINE DATA block of the user message, and every other calculation
comes from the engine tools. Treat every position, degree, lord, daśā date,
transit date, bala, bindu and window they return as ground truth: never
recompute, correct or invent a number, and if something you need is not
available from the tools, say so rather than guess.

Work in this order:
1. Before anything else, call `record_plan`. From the granthas (BPHS,
   Phaladeepika, Saravali, Jaimini Sūtras, Tājika Nīlakaṇṭhī, KP, Uttara
   Kālāmṛta and the rest), list every calculation this particular question
   needs: which bhāvas and their lords, kārakas, avasthās (Bālādi such as
   Mṛta, Dīptādi such as Dukhita/Khala, and so on), daśās, vargas, sāhams,
   upagrahas, Ashtakavarga, gochara and timing data, each with its source and
   why it matters here. Put in `gaps` any calculation the granthas call for
   that no tool provides.
2. Fetch every planned calculation with the engine tools. Call several tools
   in one turn when they are independent. Add to the plan only by fetching
   more, never by assuming.
3. Write the reading.

Interpret by the director below (the AI Triangulation Framework and the Event
Timing Guide): triangulate across systems, never let one system judge alone,
and never treat a score as the verdict.

Answer only the question asked in the user message, in the user's register
(Hinglish), as a finished reading written for the seeker in Markdown. Be
specific and tie each point to the chart data that shows it; no generic
statements. State the as-of date the reading is for. The plan is shown to the
seeker separately, so do not repeat it in the reading.

Care rules: do not predict death or lifespan; do not diagnose illness (say it
is the chart's indication, not a diagnosis); do not frighten. Do not offer
extra services or ask follow-up questions at the end.
"""


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def load_cards() -> dict:
    return json.loads(_read(os.path.join(PROMPTS, "cards.json")))


def system_prompt() -> str:
    return (SYSTEM_HEADER
            + "\n\n=== DIRECTOR: AI_TRIANGULATION_PROMPT.md ===\n\n"
            + _read(os.path.join(DOCS, "AI_TRIANGULATION_PROMPT.md"))
            + "\n\n=== DIRECTOR: AI_EVENT_TIMING_GUIDE.md ===\n\n"
            + _read(os.path.join(DOCS, "AI_EVENT_TIMING_GUIDE.md")))


def fill_prompt(question: str, *, dob: str, place: str, time: str,
                gender: str = "", marital: str = "") -> str:
    """The user's prompt template with the seeker's details and *question*."""
    g = {"male": "male", "m": "male", "female": "female", "f": "female"}.get(
        (gender or "").lower(), gender or "")
    gl = " ".join(x for x in (g, marital) if x)
    t = _read(os.path.join(PROMPTS, "reading_default.md"))
    return (t.replace("{dob}", dob).replace("{place}", place or "—")
             .replace("{time}", time).replace("{question}", question)
             .replace("{gender_line}", f"Gender - {gl}" if gl else "").strip())


def prompt_version() -> str:
    """Hash of everything that shapes an answer, for cache keys."""
    h = hashlib.sha256()
    # cards.json is not here: each card's own spec goes into its cache key,
    # so editing one card does not regenerate the others.
    for p in (os.path.join(PROMPTS, "reading_default.md"),
              os.path.join(DOCS, "AI_TRIANGULATION_PROMPT.md"),
              os.path.join(DOCS, "AI_EVENT_TIMING_GUIDE.md")):
        h.update(_read(p).encode())
    for p in (os.path.join(ROOT, "interpreter", "engine_tools.py"),):
        h.update(_read(p).encode())
    h.update(f"{MODEL}|{EFFORT}|{SYSTEM_HEADER}".encode())
    return h.hexdigest()[:16]


class ReaderError(RuntimeError):
    """A reading could not be produced; the message is safe to show."""


MAX_ROUNDS = int(os.environ.get("HORASUTRA_MAX_ROUNDS", "14"))


def _stream(client, messages, *, last_round: bool):
    from interpreter.engine_tools import TOOLS
    with client.beta.messages.stream(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        # Tools + system are the same for every reading: cache them for an
        # hour so readings within the hour read them at the cache price.
        system=[{"type": "text", "text": system_prompt(),
                 "cache_control": {"type": "ephemeral", "ttl": "1h"}}],
        tools=TOOLS,
        # The last round may not call tools, so the reading gets written.
        tool_choice={"type": "none"} if last_round else {"type": "auto"},
        messages=messages,
        thinking={"type": "adaptive"},
        output_config={"effort": EFFORT},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    ) as stream:
        return stream.get_final_message()


def _cache_last(messages) -> None:
    """Keep one cache breakpoint, on the newest user turn, so each round
    reads the conversation so far from the cache."""
    for m in messages:
        if m["role"] == "user" and isinstance(m["content"], list):
            for b in m["content"]:
                b.pop("cache_control", None)
    last = messages[-1]["content"]
    if isinstance(last, str):
        messages[-1]["content"] = last = [{"type": "text", "text": last}]
    last[-1]["cache_control"] = {"type": "ephemeral"}


def _preloaded_text(preloaded) -> str:
    if not preloaded:
        return ""
    parts = ["\n\n---\nENGINE DATA ALREADY FETCHED for this chart this month (same as "
             "calling these tools again; fetch only what is not here):"]
    for r in preloaded:
        args = json.dumps(r["input"], ensure_ascii=False, sort_keys=True)
        parts.append(f"\n### {r['tool']} {args}\n{r['result']}")
    return "\n".join(parts)


def read(user_prompt: str, reading, as_of: str, client=None,
         on_step=None, preloaded=None) -> dict:
    """Plan → engine tool calls → reading.

    *reading* is an ``interpreter.reading_bundle.Reading``. Returns
    ``dict(text, plan, gaps, calls, results, model, usage, truncated)``;
    ``results`` holds each successful tool call with its output, and a later
    reading of the same chart can pass them back as *preloaded* so the data
    is in hand from the start instead of costing tool rounds. *client* may
    be injected (tests); otherwise an ``anthropic.Anthropic()`` client is
    built from ``ANTHROPIC_API_KEY``. *on_step(calls, plan)* is told after each
    tool round, for progress display.
    """
    import anthropic

    from interpreter.engine_tools import run_tool

    if client is None:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise ReaderError("ANTHROPIC_API_KEY server par set nahi hai.")
        client = anthropic.Anthropic()
    messages = [{"role": "user", "content": (
        f"{user_prompt}\n\n---\nENGINE DATA (as of {as_of}) — ground truth. The natal "
        f"matrix is below; call record_plan, then fetch every other calculation with the "
        f"engine tools.\n\n{reading.matrix()}{_preloaded_text(preloaded)}")}]
    plan, gaps, calls, results_ = [], [], [], []
    usage: dict = {}
    msg = None
    try:
        for rnd in range(MAX_ROUNDS):
            _cache_last(messages)
            msg = _stream(client, messages, last_round=rnd == MAX_ROUNDS - 1)
            for k in ("input_tokens", "output_tokens", "cache_read_input_tokens",
                      "cache_creation_input_tokens"):
                usage[k] = usage.get(k, 0) + (getattr(msg.usage, k, 0) or 0)
            if msg.stop_reason != "tool_use":
                break
            results = []
            for b in msg.content:
                if getattr(b, "type", "") != "tool_use":
                    continue
                args = dict(b.input or {})
                if b.name == "record_plan":
                    plan, gaps = list(args.get("items") or []), list(args.get("gaps") or [])
                    out, err = "Plan recorded. Now fetch each calculation.", False
                elif not plan and not calls:
                    out, err = "Call record_plan first.", True
                else:
                    try:
                        out, err = run_tool(reading, b.name, args), False
                        results_.append(dict(tool=b.name, input=args, result=out))
                    except Exception as e:
                        out, err = f"{type(e).__name__}: {e}", True
                    calls.append(dict(tool=b.name, input=args, error=err))
                results.append({"type": "tool_result", "tool_use_id": b.id,
                                "content": out, "is_error": err})
            messages.append({"role": "assistant", "content": msg.content})
            messages.append({"role": "user", "content": results})
            if on_step:
                on_step(calls, plan)
    except anthropic.AuthenticationError:
        raise ReaderError("Claude API key galat hai ya band hai.")
    except anthropic.RateLimitError:
        raise ReaderError("Claude abhi busy hai (rate limit). Thodi der baad dobara try karein.")
    except anthropic.APIStatusError as e:
        raise ReaderError(f"Claude API error {e.status_code}.")
    except anthropic.APIConnectionError:
        raise ReaderError("Claude se connect nahi ho paya.")
    if msg.stop_reason == "refusal":
        raise ReaderError("Is sawaal ka jawab abhi nahi ban paya.")
    text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()
    if not text or msg.stop_reason == "tool_use":
        raise ReaderError("Claude ne khaali jawab diya.")
    return dict(text=text, plan=plan, gaps=gaps, calls=calls, results=results_,
                model=getattr(msg, "model", MODEL), usage=usage,
                truncated=msg.stop_reason == "max_tokens")
