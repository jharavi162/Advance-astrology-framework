"""Doctrine/contract test for the data-only Gochara (transit) engine.

Mechanical properties only — house arithmetic from Lagna/Moon, contact symmetry,
double-transit definition, data-only shape. No native event date is asserted
(blind-test integrity, CLAUDE.md).
"""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from advance_astrology import VedicChart, Planet
from advance_astrology.constants import SIGNS
from interpreter.engines import GocharaEngine
from interpreter.engines.gochara import GocharaReport

UTC = timezone.utc
AS_OF = datetime(2024, 6, 1, tzinfo=UTC)      # a fixed instant, not an event date


def _chart():
    v = VedicChart.create(
        when=datetime(1991, 4, 4, 6, 23, tzinfo=ZoneInfo("Asia/Kolkata")),
        latitude=23.63, longitude=85.52, ayanamsa="lahiri")
    try:
        v.gender = "male"
    except Exception:
        pass
    return v


def _report(v=None):
    v = v or _chart()
    return v, GocharaEngine().evaluate(v, None, AS_OF, AS_OF + timedelta(days=200))


def test_report_is_data_only():
    _, r = _report()
    assert isinstance(r, GocharaReport)
    for banned in ("score", "verdict", "salience", "confidence", "promised"):
        assert not hasattr(r, banned)


def test_every_graha_has_a_position_with_valid_houses():
    _, r = _report()
    assert len(r.positions) == 9
    for p in r.positions:
        assert p.sign in SIGNS
        assert 0.0 <= p.degree < 30.0
        assert 1 <= p.house_from_lagna <= 12
        assert 1 <= p.house_from_moon <= 12


def test_house_from_lagna_and_moon_match_the_chart_arithmetic():
    """The reported bhāva must equal the sign-offset from Lagna / natal Moon."""
    v, r = _report()
    asc, moon = v.ascendant_sign, v.signs[Planet.MOON]
    for p in r.positions:
        s = SIGNS.index(p.sign)
        assert p.house_from_lagna == (s - asc) % 12 + 1
        assert p.house_from_moon == (s - moon) % 12 + 1


def test_conjunction_contacts_are_degree_locked_only_within_three_degrees():
    _, r = _report()
    for c in r.natal_contacts:
        if c.relation == "conjunction":
            assert c.degree_lock == (c.orb <= 3.0)
        else:
            assert c.relation.startswith("aspect")
            assert c.degree_lock is False


def test_double_transit_houses_are_lit_by_both_jupiter_and_saturn():
    """A house counts as double-transited only when BOTH slow movers activate it
    (occupation OR graha-dṛṣṭi) — the classical definition."""
    v, r = _report()
    tr = v.transits()
    for h in r.double_transit_houses:
        assert {Planet.JUPITER, Planet.SATURN} <= set(tr.slow_activators(AS_OF, h))


def test_house_activation_covers_both_references():
    _, r = _report()
    refs = {a.reference for a in r.house_activation}
    assert refs == {"lagna", "moon"}
    for a in r.house_activation:
        assert a.occupied_by or a.aspected_by      # only active houses are listed


def test_luminaries_and_nodes_are_never_reported_retrograde():
    _, r = _report()
    never = {"Sun", "Moon", "Rahu", "Ketu"}
    assert not (set(r.retrogrades) & never)


def test_ingresses_are_ordered_and_inside_the_horizon():
    _, r = _report()
    ons = [i.on for i in r.upcoming_ingresses]
    assert ons == sorted(ons)
    for i in r.upcoming_ingresses:
        assert AS_OF <= i.on <= AS_OF + timedelta(days=205)
        assert i.from_sign != i.to_sign


def test_engine_registered_and_routed_for_gochara_intent():
    from interpreter.engines import ENGINES, classify, route
    assert ENGINES["gochara"].name == "gochara"
    assert classify("abhi mere upar kya gochar chal raha hai") == "gochara"
    assert classify("sade sati kab tak hai") == "gochara"
    assert route("gochara")[0] == "gochara"
    # a plain WHEN question must still route to the daśā clock, not gochara
    assert classify("shaadi kab hogi") == "timing"


def test_engine_is_deterministic():
    v = _chart()
    a = GocharaEngine().evaluate(v, None, AS_OF, AS_OF + timedelta(days=100))
    b = GocharaEngine().evaluate(v, None, AS_OF, AS_OF + timedelta(days=100))
    assert [(p.planet, p.sign, p.degree) for p in a.positions] == \
           [(p.planet, p.sign, p.degree) for p in b.positions]
    assert a.double_transit_houses == b.double_transit_houses
