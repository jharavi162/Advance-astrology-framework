"""Claude reader — turns the engine bundle + a prompt template into a reading.

The engine computes (``interpreter.reading_bundle``); Claude interprets. The
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
MAX_TOKENS = 32000

SYSTEM_HEADER = """You are the interpretation layer of HoraSutra, a Vedic astrology app.

A deterministic engine has already computed everything about this chart. Its
output is in the ENGINE DATA block of the user message. Treat every position,
degree, lord, daśā date, transit date, bala, bindu and window in it as ground
truth: never recompute, correct or invent a number, and if something you need
is not in the data, say it is not available rather than guess.

Interpret by the director below (the AI Triangulation Framework and the Event
Timing Guide): triangulate across systems, never let one system judge alone,
and never treat a score as the verdict.

Answer only the question asked in the user message, in the user's register
(Hinglish), as a finished reading written for the seeker in Markdown. Be
specific and tie each point to the chart data that shows it; no generic
statements. State the as-of date the reading is for.

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
    for p in (os.path.join(PROMPTS, "reading_default.md"),
              os.path.join(PROMPTS, "cards.json"),
              os.path.join(DOCS, "AI_TRIANGULATION_PROMPT.md"),
              os.path.join(DOCS, "AI_EVENT_TIMING_GUIDE.md")):
        h.update(_read(p).encode())
    h.update(f"{MODEL}|{EFFORT}|{SYSTEM_HEADER}".encode())
    return h.hexdigest()[:16]


class ReaderError(RuntimeError):
    """A reading could not be produced; the message is safe to show."""


def read(user_prompt: str, bundle: str, as_of: str, client=None) -> dict:
    """One Claude call: prompt + engine bundle → Markdown reading.

    Returns ``dict(text=..., model=..., usage=...)``. *client* may be injected
    (tests); otherwise an ``anthropic.Anthropic()`` client is built from the
    environment (``ANTHROPIC_API_KEY``).
    """
    import anthropic

    if client is None:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise ReaderError("ANTHROPIC_API_KEY server par set nahi hai.")
        client = anthropic.Anthropic()
    content = (f"{user_prompt}\n\n---\nENGINE DATA (as of {as_of}) — ground truth:\n\n"
               f"{bundle}")
    try:
        # Long input and long output: stream, then take the final message.
        # Server-side refusal fallback is enabled so a declined request is
        # retried on a fallback model inside the same call.
        with client.beta.messages.stream(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=[{"type": "text", "text": system_prompt(),
                     "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": content}],
            thinking={"type": "adaptive"},
            output_config={"effort": EFFORT},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        ) as stream:
            msg = stream.get_final_message()
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
    if not text:
        raise ReaderError("Claude ne khaali jawab diya.")
    u = msg.usage
    usage = {k: getattr(u, k, None) for k in ("input_tokens", "output_tokens",
                                             "cache_read_input_tokens",
                                             "cache_creation_input_tokens")}
    return dict(text=text, model=getattr(msg, "model", MODEL), usage=usage,
                truncated=msg.stop_reason == "max_tokens")
