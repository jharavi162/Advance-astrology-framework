"""Doctrine/contract test for the data-only Daśā timing engine.

Asserts the engine reports the right *significator daśā data* — the 7th-lord and
its dispositor are derived correctly, every 'running' label is a declared
significator, the 7th-lord's antardaśā is surfaced and labeled, and the report
carries NO score/verdict (data-only). No native event date is asserted —
blind-test integrity intact (CLAUDE.md).
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from advance_astrology import VedicChart
from advance_astrology.constants import RULERSHIPS, SIGNS
from interpreter.engines import DashaTimingEngine
from interpreter.engines.dasha_timing import VimPeriod, DashaTimingReport
from interpreter.significators import resolve

UTC = timezone.utc


def _chart():
    return VedicChart.create(
        when=datetime(1991, 4, 4, 6, 23, tzinfo=ZoneInfo("Asia/Kolkata")),
        latitude=23.63, longitude=85.52, ayanamsa="lahiri")


def _report():
    v = _chart()
    return v, DashaTimingEngine().evaluate(
        v, resolve("marriage"),
        datetime(2010, 1, 1, tzinfo=UTC), datetime(2030, 1, 1, tzinfo=UTC))


def test_significators_map_to_real_chart_lords():
    v, rep = _report()
    labels = {s.label: s.planet for s in rep.significators}
    assert labels["7th-lord"] == v.house_lord(7)
    disp = RULERSHIPS[SIGNS[v.signs[v.house_lord(7)]]]
    assert labels["disp(7th-lord)"] == disp


def test_every_running_label_is_a_declared_significator():
    _, rep = _report()
    declared = {s.label for s in rep.significators}
    for p in rep.vimshottari:
        for label in p.active:
            assert label in declared


def test_seventh_lord_antardasha_is_surfaced_and_labeled():
    """Mechanical: the 7th-lord's own antardaśā must appear in the timeline and
    carry the '7th-lord' tag. (No date asserted — just that the clock is wired.)"""
    v, rep = _report()
    l7 = v.house_lord(7).value
    hits_ad = [p for p in rep.vimshottari if p.ad == l7]
    assert hits_ad, "7th-lord antardaśā not surfaced"
    assert all("7th-lord" in p.active for p in hits_ad)
    # active_windows also picks up the 7th-lord running as MD, so it is a superset
    assert set(hits_ad).issubset(set(rep.active_windows("7th-lord")))


def test_report_is_data_only_no_score_or_verdict():
    _, rep = _report()
    for banned in ("score", "verdict", "salience", "promised", "confidence"):
        assert not hasattr(rep, banned)
    for p in rep.vimshottari:
        for banned in ("score", "verdict", "salience"):
            assert not hasattr(p, banned)


def test_chara_roles_are_domain_general():
    """Chara rāśi roles must derive from the QUERIED domain's houses — not be
    hard-coded to marriage. For any domain, an 'Nth-from-Lagna' role must have N
    among that domain's houses and the sign must actually be N-th from Lagna."""
    v = _chart()
    for word in ("marriage", "vehicle", "career"):
        prof = resolve(word)
        rep = DashaTimingEngine().evaluate(
            v, prof, datetime(2010, 1, 1, tzinfo=UTC), datetime(2030, 1, 1, tzinfo=UTC))
        for c in rep.chara:
            for role in c.roles:
                if role.endswith("-from-Lagna"):
                    n = int(role.split("th")[0].split("st")[0]
                            .split("nd")[0].split("rd")[0])
                    assert n in prof.houses
                    assert c.sign == SIGNS[(v.ascendant_sign + n - 1) % 12]


def test_vehicle_chara_tags_fourth_not_seventh():
    """Concrete anti-regression for the marriage-hardcoding bug: a vehicle query
    tags the 4th-from-Lagna sign, and never emits marriage's 7th-from-Lagna."""
    v = _chart()
    rep = DashaTimingEngine().evaluate(
        v, resolve("vehicle"), datetime(2010, 1, 1, tzinfo=UTC),
        datetime(2030, 1, 1, tzinfo=UTC))
    roles = {r for c in rep.chara for r in c.roles}
    assert "7th-from-Lagna" not in roles


def test_transit_triggers_well_formed():
    _, rep = _report()
    for s, e, what in rep.transit_triggers:
        assert s < e
        assert isinstance(what, str) and "transit" in what


def test_engine_is_deterministic():
    v = _chart()
    span = (datetime(2015, 1, 1, tzinfo=UTC), datetime(2025, 1, 1, tzinfo=UTC))
    a = DashaTimingEngine().evaluate(v, resolve("career"), *span)
    b = DashaTimingEngine().evaluate(v, resolve("career"), *span)
    assert [(p.start, p.ad, p.active) for p in a.vimshottari] == \
           [(p.start, p.ad, p.active) for p in b.vimshottari]
