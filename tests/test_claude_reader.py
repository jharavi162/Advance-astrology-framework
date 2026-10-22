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


def _msg(content, stop):
    usage = NS(input_tokens=10, output_tokens=5, cache_read_input_tokens=0,
               cache_creation_input_tokens=3)
    return NS(content=content, stop_reason=stop, usage=usage, model=cr.MODEL)


def _tool(i, name, inp):
    return NS(type="tool_use", id=f"t{i}", name=name, input=inp)


PLAN = {"items": [{"calculation": "Deeptadi avastha of the 6th lord", "source": "BPHS ch.45",
                   "why": "mood of the stress lord", "tool": "engine_section"}],
        "gaps": [{"calculation": "Lajjitadi avastha", "source": "BPHS ch.45"}]}


class FakeClient:
    """Scripted rounds: plan + a section fetch, then the reading."""

    def __init__(self, text="## Jawab\nStress 12th se.", stop="end_turn", rounds=None):
        self.calls = []
        self.rounds = rounds if rounds is not None else [
            _msg([NS(type="thinking", thinking=""), _tool(1, "record_plan", PLAN),
                  _tool(2, "engine_section", {"section": "avasthas"})], "tool_use"),
            _msg([NS(type="thinking", thinking=""), NS(type="text", text=text)], stop),
        ]
        self.beta = NS(messages=NS(stream=self._stream))

    def _stream(self, **kw):
        import copy
        self.calls.append(copy.deepcopy(kw))
        return FakeStream(self.rounds[min(len(self.calls), len(self.rounds)) - 1])


class FakeReading:
    tz = ZoneInfo("Asia/Kolkata")

    def matrix(self):
        return "MATRIX"

    def section(self, name):
        return f"SECTION {name}"


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


def test_read_plans_then_fetches_then_answers():
    fake = FakeClient()
    steps = []
    out = cr.read("PROMPT", FakeReading(), "2026-10-22", client=fake, on_step=steps.append)
    assert out["text"] == "## Jawab\nStress 12th se." and not out["truncated"]
    assert out["plan"] == PLAN["items"] and out["gaps"] == PLAN["gaps"]
    assert out["calls"] == [dict(tool="engine_section", input={"section": "avasthas"}, error=False)]
    first, second = fake.calls
    assert first["model"] == cr.MODEL and first["thinking"] == {"type": "adaptive"}
    assert first["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert first["fallbacks"] == "default"
    assert "server-side-fallback-2026-07-01" in first["betas"]
    assert {t["name"] for t in first["tools"]} >= {"record_plan", "engine_section", "samanvaya"}
    body = first["messages"][0]["content"][0]["text"]
    assert body.startswith("PROMPT") and "MATRIX" in body and "2026-10-22" in body
    # Round two carries the tool results, with the one cache breakpoint on them.
    res = second["messages"][-1]["content"]
    assert [r["content"] for r in res] == ["Plan recorded. Now fetch each calculation.",
                                           "SECTION avasthas"]
    assert "cache_control" in res[-1]
    assert "cache_control" not in second["messages"][0]["content"][0]
    assert out["usage"]["input_tokens"] == 20 and steps == [out["calls"]]


def test_tools_before_plan_are_refused():
    rounds = [_msg([_tool(1, "engine_section", {"section": "kp"})], "tool_use"),
              _msg([NS(type="text", text="ok")], "end_turn")]
    fake = FakeClient(rounds=rounds)
    out = cr.read("P", FakeReading(), "d", client=fake)
    r = fake.calls[1]["messages"][-1]["content"][0]
    assert r["is_error"] and "record_plan" in r["content"] and out["calls"] == []


def test_last_round_forbids_tools(monkeypatch):
    monkeypatch.setattr(cr, "MAX_ROUNDS", 2)
    loop = _msg([_tool(1, "record_plan", PLAN)], "tool_use")
    fake = FakeClient(rounds=[loop, _msg([NS(type="text", text="done")], "end_turn")])
    assert cr.read("P", FakeReading(), "d", client=fake)["text"] == "done"
    assert [c["tool_choice"]["type"] for c in fake.calls] == ["auto", "none"]


def test_read_refusal_and_empty_raise_reader_error():
    with pytest.raises(cr.ReaderError):
        cr.read("P", FakeReading(), "d", client=FakeClient(stop="refusal"))
    with pytest.raises(cr.ReaderError):
        cr.read("P", FakeReading(), "d", client=FakeClient(text="  "))


def test_read_without_key_raises(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(cr.ReaderError):
        cr.read("P", FakeReading(), "d")


def test_prompt_version_is_stable():
    assert cr.prompt_version() == cr.prompt_version() and len(cr.prompt_version()) == 16


def test_bundle_has_every_section():
    from interpreter.reading_bundle import build_bundle
    b = build_bundle(datetime(2000, 1, 1, 12, 0, tzinfo=ZoneInfo("Asia/Kolkata")),
                     28.6, 77.2, place="Delhi", gender="F",
                     as_of=datetime(2030, 1, 1, tzinfo=timezone.utc))
    for sec in ("NATIVE MATRIX DATABANK", "Shadbala by component", "Bhava Bala (Raman", "AS-OF DATE: 2030-01-01", "Gulika / Mandi",
                "Vimshottari — running chain", "Jaimini rashi dashas", "Varshaphal",
                "Sahams", "Vargas (graha", "KP — houses", "Gochara on 2030-01-01",
                "Sarvatobhadra janma points", "Ingresses and stations",
                "Degree (BNN) windows", "double transit per house",
                "Samanvaya engine reports", "### marriage"):
        assert sec in b, sec


def test_engine_tools_run_on_a_real_chart():
    from interpreter.engine_tools import TOOLS, run_tool
    from interpreter.reading_bundle import Reading
    r = Reading(datetime(2000, 1, 1, 12, 0, tzinfo=ZoneInfo("Asia/Kolkata")), 28.6, 77.2,
                as_of=datetime(2030, 1, 1, tzinfo=timezone.utc))
    names = {t["name"] for t in TOOLS}
    assert names == {"record_plan", "engine_section", "samanvaya", "dasha_at",
                     "gochara_on", "varga", "varshaphal_year"}
    assert "Mrita" in TOOLS[1]["description"] or "Deeptadi" in TOOLS[1]["description"]
    assert "deeptadi" in run_tool(r, "engine_section", {"section": "avasthas"})
    assert "H12 madhya" in run_tool(r, "engine_section", {"section": "strengths"})
    assert "resolved to domain 'mind'" in run_tool(r, "samanvaya", {"domain": "stress"})
    assert "MD " in run_tool(r, "dasha_at", {"date": "2031-06-01"})
    assert "Gochara on 2031-06-01" in run_tool(r, "gochara_on", {"date": "2031-06-01"})
    assert "D24 asc" in run_tool(r, "varga", {"division": 24})
    assert "Year 2031" in run_tool(r, "varshaphal_year", {"year": 2031})
    with pytest.raises(ValueError):
        run_tool(r, "varga", {"division": 5})


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
