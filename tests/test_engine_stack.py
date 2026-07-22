"""Contract tests for the Jaimini + Tājika engines, the router, and Samanvaya.

Doctrine/contract only — no native event dates. Verifies each engine emits the
right DATA shape (no score/verdict), the router maps intents correctly, and the
Samanvaya bundle runs the routed engines and returns their raw reports.
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from advance_astrology import VedicChart
from advance_astrology.constants import SIGNS
from interpreter.engines import (
    ENGINES, JaiminiEngine, TajikaEngine, classify, route, samanvaya,
)
from interpreter.engines.tajika import DOMAIN_SAHAM
from interpreter.significators import resolve

UTC = timezone.utc


def _chart():
    return VedicChart.create(
        when=datetime(1991, 4, 4, 6, 23, tzinfo=ZoneInfo("Asia/Kolkata")),
        latitude=23.63, longitude=85.52, ayanamsa="lahiri")


# --- Jaimini ---------------------------------------------------------------- #
def test_jaimini_surfaces_upapada_for_marriage_only():
    v = _chart()
    span = (datetime(2015, 1, 1, tzinfo=UTC), datetime(2025, 1, 1, tzinfo=UTC))
    mar = JaiminiEngine().evaluate(v, resolve("marriage"), *span)
    car = JaiminiEngine().evaluate(v, resolve("career"), *span)
    assert mar.upapada_sign in SIGNS               # marriage carries the UL axis
    assert car.upapada_sign is None                # career does not
    assert "Darakaraka" in mar.chara_karakas
    assert "A7" in mar.domain_arudha


def test_jaimini_is_data_only():
    v = _chart()
    rep = JaiminiEngine().evaluate(v, resolve("marriage"),
                                   datetime(2015, 1, 1, tzinfo=UTC),
                                   datetime(2025, 1, 1, tzinfo=UTC))
    for banned in ("score", "salience", "verdict", "confidence"):
        assert not hasattr(rep, banned)


# --- Tājika ----------------------------------------------------------------- #
def test_tajika_uses_the_matter_saham_and_years_span():
    v = _chart()
    rep = TajikaEngine().evaluate(v, resolve("marriage"),
                                  datetime(2020, 1, 1, tzinfo=UTC),
                                  datetime(2023, 1, 1, tzinfo=UTC))
    assert rep.saham_name == DOMAIN_SAHAM["marriage"] == "Vivaha"
    assert [y.year for y in rep.years] == [2020, 2021, 2022, 2023]
    for y in rep.years:
        assert 1 <= y.muntha_house <= 12
        assert isinstance(y.muntha_in_fulfil, bool)


# --- Router ----------------------------------------------------------------- #
def test_router_classifies_intent():
    assert classify("when will he get married") == "timing"
    assert classify("will she get a job") == "yes_no"
    assert classify("will the marriage last, is it a happy one") == "quality"
    assert classify("") == "timing"                 # default


def test_router_maps_timing_to_dasha_first_and_yesno_to_kp_first():
    assert route("timing")[0] == "dasha_timing"
    assert route("yes_no")[0] == "kp"
    assert route("quality")[0] == "kp"


# --- Samanvaya -------------------------------------------------------------- #
def test_samanvaya_runs_routed_engines_and_bundles_reports():
    v = _chart()
    b = samanvaya(v, resolve("marriage"),
                  datetime(2018, 1, 1, tzinfo=UTC), datetime(2024, 1, 1, tzinfo=UTC),
                  question="when will he get married")
    assert b.intent == "timing"
    assert b.engines_run[0] == "dasha_timing"
    assert set(b.engines_run).issubset(set(ENGINES))
    for name in b.engines_run:
        assert b.get(name) is not None             # each routed engine produced data


def test_samanvaya_yesno_leads_with_kp():
    v = _chart()
    b = samanvaya(v, resolve("marriage"),
                  datetime(2018, 1, 1, tzinfo=UTC), datetime(2024, 1, 1, tzinfo=UTC),
                  question="will he ever get married")
    assert b.intent == "yes_no"
    assert b.engines_run[0] == "kp"
