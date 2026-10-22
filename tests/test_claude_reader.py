"""Contract tests for the key-question card pipeline (no network, no API key).

A fake client stands in for the Anthropic SDK, so these check what is sent
and how the answer is handled, not what Claude writes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace as NS
from zoneinfo import ZoneInfo

import pytest

from interpreter import claude_reader as cr


class FakeStream:
    def __init__(self, msg):
        self.msg = msg

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def get_final_message(self):
        return self.msg


class FakeClient:
    def __init__(self, text="## Jawab\nStress 12th se.", stop="end_turn"):
        self.kw = None
        usage = NS(input_tokens=10, output_tokens=5, cache_read_input_tokens=0,
                   cache_creation_input_tokens=3)
        self.msg = NS(content=[NS(type="thinking", thinking=""), NS(type="text", text=text)],
                      stop_reason=stop, usage=usage, model=cr.MODEL)
        self.beta = NS(messages=NS(stream=self._stream))

    def _stream(self, **kw):
        self.kw = kw
        return FakeStream(self.msg)


def test_cards_config_has_stress():
    cards = cr.load_cards()
    assert cards["cards"]["stress"]["question"] == "life ka major stress kahan se aata h"
    assert "Mann Pe kya haavi" in cards["default_question"]


def test_fill_prompt_substitutes_question_and_details():
    p = cr.fill_prompt("life ka major stress kahan se aata h", dob="04/04/1991",
                       place="Giddi, Jharkhand", time="6:23 am", gender="M")
    assert "DOB: 04/04/1991" in p and "Place of birth: Giddi, Jharkhand" in p
    assert "Time - 6:23 am" in p and "Gender - male" in p
    assert "Is chart ko analyse krke Batao life ka major stress kahan se aata h" in p
    assert "generic mat Dena" in p and "{" not in p


def test_system_prompt_carries_the_director_docs():
    s = cr.system_prompt()
    assert "AI TRIANGULATION FRAMEWORK" in s and "Event-Timing" in s
    assert "never recompute" in s


def test_read_sends_cached_system_and_bundle_and_returns_text():
    fake = FakeClient()
    out = cr.read("PROMPT", "BUNDLE", "2026-10-22", client=fake)
    assert out["text"] == "## Jawab\nStress 12th se." and not out["truncated"]
    kw = fake.kw
    assert kw["model"] == cr.MODEL and kw["thinking"] == {"type": "adaptive"}
    assert kw["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert kw["fallbacks"] == "default"
    assert "server-side-fallback-2026-07-01" in kw["betas"]
    body = kw["messages"][0]["content"]
    assert body.startswith("PROMPT") and "BUNDLE" in body and "2026-10-22" in body


def test_read_refusal_and_empty_raise_reader_error():
    with pytest.raises(cr.ReaderError):
        cr.read("P", "B", "d", client=FakeClient(stop="refusal"))
    with pytest.raises(cr.ReaderError):
        cr.read("P", "B", "d", client=FakeClient(text="  "))


def test_read_without_key_raises(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(cr.ReaderError):
        cr.read("P", "B", "d")


def test_prompt_version_is_stable():
    assert cr.prompt_version() == cr.prompt_version() and len(cr.prompt_version()) == 16


def test_bundle_has_every_section():
    from interpreter.reading_bundle import build_bundle
    b = build_bundle(datetime(2000, 1, 1, 12, 0, tzinfo=ZoneInfo("Asia/Kolkata")),
                     28.6, 77.2, place="Delhi", gender="F",
                     as_of=datetime(2030, 1, 1, tzinfo=timezone.utc))
    for sec in ("NATIVE MATRIX DATABANK", "AS-OF DATE: 2030-01-01", "Gulika / Mandi",
                "Vimshottari — running chain", "Jaimini rashi dashas", "Varshaphal",
                "Sahams", "Key vargas", "KP — houses", "Gochara on 2030-01-01",
                "Sarvatobhadra janma points", "Ingresses and stations",
                "Degree (BNN) windows", "double transit per house",
                "Samanvaya engine reports", "### marriage"):
        assert sec in b, sec


def test_card_start_guards(monkeypatch, tmp_path):
    from webapp import server
    monkeypatch.setattr(server, "CARD_CACHE_DIR", str(tmp_path))
    base = {"when": ["1991-04-04 06:23"], "tz": ["Asia/Kolkata"],
            "lat": ["23.72"], "lon": ["85.44"]}
    assert server.card_start(dict(base, card=["nope"]))["status"] == "error"
    assert "kundli" in server.card_start({"card": ["stress"]})["error"].lower()
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    r = server.card_start(dict(base, card=["stress"]))
    assert r["status"] == "error" and "ANTHROPIC_API_KEY" in r["error"]
    # A cached answer is served without a key and without starting a job.
    key = server._card_key(dict(base, card=["stress"]), "stress")
    server._card_cache_put(key, dict(status="done", text="cached", card="stress"))
    hit = server.card_start(dict(base, card=["stress"]))
    assert hit["status"] == "done" and hit["cached"] and hit["text"] == "cached"
