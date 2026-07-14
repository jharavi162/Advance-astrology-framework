"""Correctness self-test for the isolated KP engine.

This validates that the engine faithfully implements KP *doctrine* and the
engine *contract* — NOT that it reproduces any native's known event dates.
Blind-test integrity is preserved: no birth-specific event date is asserted
anywhere (CLAUDE.md). Every assertion is a mechanical property of KP itself.
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from advance_astrology import VedicChart, Planet
from advance_astrology.constants import NAKSHATRA_ARC
from advance_astrology.vedic.kp import kp_chain
from interpreter.engines import KPEngine, kp_window_grade
from interpreter.engines.base import EngineResult, TimelinePoint
from interpreter.significators import resolve

UTC = timezone.utc


def _chart():
    # A fixed chart used only as a computational substrate — no event of this
    # native is asserted; we test KP's rules, not its biography.
    return VedicChart.create(
        when=datetime(1991, 4, 4, 6, 23, tzinfo=ZoneInfo("Asia/Kolkata")),
        latitude=23.63, longitude=85.52, ayanamsa="lahiri")


# --------------------------------------------------------------------------- #
# 1. KP CHAIN MATH — sub-lord division doctrine
# --------------------------------------------------------------------------- #
def test_kp_chain_returns_four_valid_lords_everywhere():
    for deg in range(0, 360, 7):
        c = kp_chain(deg + 0.5)
        for lord in (c.sign_lord, c.star_lord, c.sub_lord, c.sub_sub_lord):
            assert isinstance(lord, Planet)


def test_sub_segments_are_vimshottari_proportional_and_partition_the_nakshatra():
    """Within one nakshatra the sub-lord segments must tile the whole 13°20'
    arc contiguously in Vimśottari proportion (KP's defining subdivision)."""
    from advance_astrology.vedic.kp import _subdivide, _RING, _TOTAL
    star_lord = _RING[0][0]                      # Ketu starts the ring
    segs = _subdivide(0.0, NAKSHATRA_ARC, star_lord)
    # contiguous, no gaps/overlaps
    assert segs[0][1] == pytest.approx(0.0)
    for (_, _, e), (_, s, _) in zip(segs, segs[1:]):
        assert s == pytest.approx(e)
    assert segs[-1][2] == pytest.approx(NAKSHATRA_ARC)
    # proportional to the Vimśottari years
    for (lord, s, e), (_, years) in zip(segs, _ring_from(star_lord)):
        assert (e - s) == pytest.approx(NAKSHATRA_ARC * years / _TOTAL)


def _ring_from(lord):
    from advance_astrology.vedic.kp import _RING
    i = [p for p, _ in _RING].index(lord)
    return _RING[i:] + _RING[:i]


def test_star_lord_flips_at_nakshatra_boundary():
    """The star lord is constant within a nakshatra and changes across the
    boundary — a basic KP invariant."""
    just_before = kp_chain(NAKSHATRA_ARC - 0.01).star_lord
    at_start = kp_chain(0.01).star_lord
    just_after = kp_chain(NAKSHATRA_ARC + 0.01).star_lord
    assert at_start == just_before          # same nakshatra (0th)
    assert just_after != at_start           # crossed into the 1st


# --------------------------------------------------------------------------- #
# 2. SIGNIFICATOR DOCTRINE
# --------------------------------------------------------------------------- #
def test_planet_signifies_its_own_occupied_house():
    v = _chart()
    kps = v.kp_significators()
    for p in v.longitudes:
        occupied = kps.planet_house[p]
        assert occupied in kps.planet_signifies(p)


def test_cusp_owner_is_the_sign_lord_on_the_cusp():
    from advance_astrology.angles import to_zodiac
    from advance_astrology.constants import RULERSHIPS, SIGNS
    v = _chart()
    kps = v.kp_significators()
    for h in range(1, 13):
        expected = RULERSHIPS[SIGNS[to_zodiac(kps.cusps[h]).sign_index]]
        assert kps.house_owner[h] == expected


# --------------------------------------------------------------------------- #
# 3. SCORE-GRADE MAPPING — the normalized [0,1] contract, tested as a pure fn
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("fulfil,negate,grade", [
    (0, 0, 0.30),      # chain silent
    (2, 0, 1.00),      # fulfilment dominant
    (2, 2, 1.00),      # fulfil >= negate (tie) still delivers
    (1, 3, 0.60),      # fulfilment present but out-weighed
    (0, 3, 0.15),      # only negation — KP denial signature
])
def test_kp_window_grade_mapping(fulfil, negate, grade):
    assert kp_window_grade(fulfil, negate) == grade


def test_kp_window_grade_always_in_unit_interval():
    for f in range(0, 6):
        for n in range(0, 6):
            assert 0.0 <= kp_window_grade(f, n) <= 1.0


# --------------------------------------------------------------------------- #
# 4. CONTRACT COMPLIANCE + ISOLATION
# --------------------------------------------------------------------------- #
def test_timeline_point_rejects_out_of_range_score():
    with pytest.raises(ValueError):
        TimelinePoint(when=datetime(2020, 1, 1, tzinfo=UTC), score=1.5)


def test_engine_emits_valid_result_for_every_domain():
    from interpreter.event_evidence import DOMAIN_PROFILES
    v = _chart()
    eng = KPEngine()
    start = datetime(2020, 1, 1, tzinfo=UTC)
    end = datetime(2022, 1, 1, tzinfo=UTC)
    for name, profile in DOMAIN_PROFILES.items():
        res = eng.evaluate(v, profile, start, end)
        assert isinstance(res, EngineResult)
        assert res.engine == "kp"
        assert res.domain == name
        assert res.verdict in {"YES", "NO", "UNCERTAIN"}
        assert res.timeline, f"{name}: KP produced no windows"
        for p in res.timeline:
            assert 0.0 <= p.score <= 1.0
        # normalized-array view matches the [date, factor_id, score] contract
        for when, fid, score in res.as_rows():
            assert fid == "kp"
            assert 0.0 <= score <= 1.0


def test_engine_verdict_follows_cusp_sublord_doctrine():
    """Whatever the chart's actual primary-cusp sub-lord signifies, the verdict
    must follow KP's promise/denial rule exactly — a mechanical consistency
    check, not an event assertion."""
    v = _chart()
    prof = resolve("marriage")
    kps = v.kp_significators()
    cusp_sub = kp_chain(kps.cusps[prof.houses[0]]).sub_lord
    sig = set(kps.planet_signifies(cusp_sub))
    res = KPEngine().evaluate(v, prof, datetime(2020, 1, 1, tzinfo=UTC),
                              datetime(2021, 1, 1, tzinfo=UTC))
    if sig & prof.fulfil_houses:
        assert res.verdict == "YES" and res.promised
    elif sig & prof.negate_houses:
        assert res.verdict == "NO" and not res.promised
    else:
        assert res.verdict == "UNCERTAIN"


def test_engine_is_deterministic():
    v = _chart()
    prof = resolve("career")
    span = (datetime(2020, 1, 1, tzinfo=UTC), datetime(2022, 1, 1, tzinfo=UTC))
    a = KPEngine().evaluate(v, prof, *span)
    b = KPEngine().evaluate(v, prof, *span)
    assert a.verdict == b.verdict
    assert [(p.when, p.score) for p in a.timeline] == \
           [(p.when, p.score) for p in b.timeline]
