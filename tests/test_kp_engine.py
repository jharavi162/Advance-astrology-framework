"""Doctrine/contract test for the data-only KP engine.

Validates KP *doctrine* and the *data contract* — the sub-lord arc math, the
significator rules, and that the engine emits DATA (sub-lord significations +
per-window fulfil/negate counts) with NO score and NO verdict. No native event
date is asserted (blind-test integrity, CLAUDE.md).
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from advance_astrology import VedicChart, Planet
from advance_astrology.constants import NAKSHATRA_ARC
from advance_astrology.vedic.kp import kp_chain
from interpreter.engines import KPEngine
from interpreter.engines.kp_engine import KPReport, KPWindow
from interpreter.significators import resolve

UTC = timezone.utc


def _chart():
    return VedicChart.create(
        when=datetime(1991, 4, 4, 6, 23, tzinfo=ZoneInfo("Asia/Kolkata")),
        latitude=23.63, longitude=85.52, ayanamsa="lahiri")


def _ring_from(lord):
    from advance_astrology.vedic.kp import _RING
    i = [p for p, _ in _RING].index(lord)
    return _RING[i:] + _RING[:i]


# --- 1. KP CHAIN MATH ------------------------------------------------------- #
def test_kp_chain_returns_four_valid_lords_everywhere():
    for deg in range(0, 360, 7):
        c = kp_chain(deg + 0.5)
        for lord in (c.sign_lord, c.star_lord, c.sub_lord, c.sub_sub_lord):
            assert isinstance(lord, Planet)


def test_sub_segments_partition_the_nakshatra_proportionally():
    from advance_astrology.vedic.kp import _subdivide, _RING, _TOTAL
    star_lord = _RING[0][0]
    segs = _subdivide(0.0, NAKSHATRA_ARC, star_lord)
    assert segs[0][1] == pytest.approx(0.0)
    for (_, _, e), (_, s, _) in zip(segs, segs[1:]):
        assert s == pytest.approx(e)
    assert segs[-1][2] == pytest.approx(NAKSHATRA_ARC)
    for (lord, s, e), (_, years) in zip(segs, _ring_from(star_lord)):
        assert (e - s) == pytest.approx(NAKSHATRA_ARC * years / _TOTAL)


def test_star_lord_flips_at_nakshatra_boundary():
    assert kp_chain(0.01).star_lord == kp_chain(NAKSHATRA_ARC - 0.01).star_lord
    assert kp_chain(NAKSHATRA_ARC + 0.01).star_lord != kp_chain(0.01).star_lord


# --- 2. SIGNIFICATOR DOCTRINE ----------------------------------------------- #
def test_planet_signifies_its_own_occupied_house():
    v = _chart()
    kps = v.kp_significators()
    for p in v.longitudes:
        assert kps.planet_house[p] in kps.planet_signifies(p)


# --- 3. DATA CONTRACT (no score, no verdict) -------------------------------- #
def test_report_is_data_only():
    v = _chart()
    rep = KPEngine().evaluate(v, resolve("marriage"),
                              datetime(2018, 1, 1, tzinfo=UTC),
                              datetime(2022, 1, 1, tzinfo=UTC))
    assert isinstance(rep, KPReport)
    for banned in ("verdict", "promised", "score", "salience", "confidence"):
        assert not hasattr(rep, banned)
    for w in rep.windows:
        assert not hasattr(w, "score")


def test_hits_are_the_sublords_significations_intersected_with_house_sets():
    """The reported fulfil/negate hits must be exactly the cusp sub-lord's
    significations intersected with the domain's house sets — a mechanical
    consistency check, not an event assertion."""
    v = _chart()
    prof = resolve("marriage")
    rep = KPEngine().evaluate(v, prof, datetime(2020, 1, 1, tzinfo=UTC),
                              datetime(2021, 1, 1, tzinfo=UTC))
    kps = v.kp_significators()
    cusp_sub = kp_chain(kps.cusps[prof.houses[0]]).sub_lord
    assert rep.cusp_sublord == cusp_sub.value
    sig = set(kps.planet_signifies(cusp_sub))
    assert set(rep.hits_fulfil) == sig & prof.fulfil_houses
    assert set(rep.hits_negate) == sig & prof.negate_houses


def test_windows_carry_fulfil_negate_counts_for_every_domain():
    from interpreter.engines import ENGINES
    v = _chart()
    for name in ("marriage", "career", "children", "wealth"):
        rep = KPEngine().evaluate(v, resolve(name),
                                  datetime(2020, 1, 1, tzinfo=UTC),
                                  datetime(2022, 1, 1, tzinfo=UTC))
        assert rep.windows, f"{name}: no KP windows"
        for w in rep.windows:
            assert isinstance(w, KPWindow)
            assert w.fulfil >= 0 and w.negate >= 0
    assert ENGINES["kp"].name == "kp"


def test_engine_is_deterministic():
    v = _chart()
    span = (datetime(2020, 1, 1, tzinfo=UTC), datetime(2022, 1, 1, tzinfo=UTC))
    a = KPEngine().evaluate(v, resolve("career"), *span)
    b = KPEngine().evaluate(v, resolve("career"), *span)
    assert a.cusp_sublord == b.cusp_sublord
    assert [(w.when, w.fulfil, w.negate) for w in a.windows] == \
           [(w.when, w.fulfil, w.negate) for w in b.windows]
