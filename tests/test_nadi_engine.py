"""Doctrine/contract test for the data-only Nāḍī engine.

Asserts Nāḍī doctrine (gender-aware kāraka, golden-relation chain, degree
chronology) and the data contract (no score/verdict). No native event date.
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from advance_astrology import VedicChart, Planet
from advance_astrology.constants import SIGNS
from interpreter.engines import NadiEngine
from interpreter.engines.nadi import NadiReport, _descriptor_karaka, _timing_karakas
from interpreter.significators import resolve

UTC = timezone.utc


def _chart(gender="m"):
    v = VedicChart.create(
        when=datetime(1991, 4, 4, 6, 23, tzinfo=ZoneInfo("Asia/Kolkata")),
        latitude=23.63, longitude=85.52, ayanamsa="lahiri")
    try:
        v.gender = gender
    except Exception:
        pass
    return v


def test_kalatra_karaka_is_gender_aware():
    male, female = _chart("m"), _chart("f")
    mar = resolve("marriage")
    assert _descriptor_karaka(male, mar) == Planet.VENUS      # ♂ → Venus (spouse)
    assert _descriptor_karaka(female, mar) == Planet.MARS     # ♀ → Mars (husband)


def test_timing_karaka_is_venus_universal_plus_mars_for_female():
    mar = resolve("marriage")
    assert _timing_karakas(_chart("m"), mar) == [Planet.VENUS]
    assert _timing_karakas(_chart("f"), mar) == [Planet.VENUS, Planet.MARS]


def test_chain_is_degree_ordered_and_contains_the_hero():
    v = _chart("m")
    rep = NadiEngine().evaluate(v, resolve("marriage"),
                                datetime(2020, 1, 1, tzinfo=UTC),
                                datetime(2025, 1, 1, tzinfo=UTC))
    degs = [m.degree for m in rep.chain]
    assert degs == sorted(degs)                               # degree = chronology
    assert any("HERO" in m.when for m in rep.chain)           # the kāraka is in its own chain
    for m in rep.chain:
        assert m.relation in ("conjunction", "trine-5th", "trine-9th")


def test_report_is_data_only():
    v = _chart("m")
    rep = NadiEngine().evaluate(v, resolve("marriage"),
                                datetime(2020, 1, 1, tzinfo=UTC),
                                datetime(2024, 1, 1, tzinfo=UTC))
    assert isinstance(rep, NadiReport)
    for banned in ("score", "verdict", "salience", "confidence"):
        assert not hasattr(rep, banned)
    assert rep.bhrigu_bindu_sign in SIGNS
    for s, e, what in rep.jeeva_windows + rep.sanction_windows + rep.bb_windows:
        assert s < e and isinstance(what, str)


def test_nadi_is_registered_and_routed_for_timing_and_quality():
    from interpreter.engines import ENGINES, route
    assert ENGINES["nadi"].name == "nadi"
    assert "nadi" in route("timing")
    assert "nadi" in route("quality")
