"""Regression tests for the domain-general event-evidence builder."""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from advance_astrology import VedicChart
from interpreter.event_evidence import (
    DOMAIN_PROFILES, candidate_map, render_domain, reversal_map, scan_domains,
)

UTC = timezone.utc


def _chart():
    return VedicChart.create(
        when=datetime(1991, 4, 4, 6, 23, tzinfo=ZoneInfo("Asia/Kolkata")),
        latitude=23.63, longitude=85.52, ayanamsa="lahiri")


def test_every_domain_builds_without_error():
    v = _chart()
    start = datetime(2024, 1, 1, tzinfo=UTC)
    end = datetime(2025, 1, 1, tzinfo=UTC)
    for name, profile in DOMAIN_PROFILES.items():
        rows = candidate_map(v, profile, start, end)
        assert rows, f"{name} produced no candidate windows"
        for r in rows:
            assert 0 <= r.domain_score <= 6
            assert r.domain_score <= r.convergence  # Lagna vote only adds


def test_marriage_band_is_lit_around_known_wedding():
    """Jan-2024 wedding must fall inside a Lagna-materialised, lord-double-transit
    band — the engine should bound the right ~12-month window."""
    v = _chart()
    rows = candidate_map(v, DOMAIN_PROFILES["marriage"],
                         datetime(2023, 6, 1, tzinfo=UTC),
                         datetime(2024, 5, 1, tzinfo=UTC))
    around = [r for r in rows if datetime(2023, 8, 1, tzinfo=UTC) <= r.start
              <= datetime(2024, 3, 1, tzinfo=UTC)]
    assert around, "no rows around the wedding band"
    # Lagna double-activated and the 7th-lord under double transit through the band
    assert all(r.lagna_activators for r in around)
    assert any(r.lord_double_transit for r in around)


def test_remarriage_caught_despite_dark_lagna():
    """The Jan-2027 court remarriage has a dark Lagna (low-key) but must still
    surface via the Venus stack / Saham / Sudarśana — domain_score >= 3."""
    v = _chart()
    rows = candidate_map(v, DOMAIN_PROFILES["marriage"],
                         datetime(2027, 1, 1, tzinfo=UTC),
                         datetime(2027, 3, 1, tzinfo=UTC))
    # the wedding PD is the Venus stack (Ve>Ra>Ve) opening late January
    venus_pd = [r for r in rows if r.chain[2] == "Ve"]
    assert venus_pd, "Venus pratyantar (the remarriage trigger) not found"
    best = max(venus_pd, key=lambda r: r.domain_score)
    assert best.domain_score >= 3
    assert best.karaka_sukshma  # Venus also surfacing at sūkṣma


def test_career_dusthana_is_change_not_loss():
    """This native NEVER had a job loss/break — only changes upward. A
    6/8/12-from-10th activation must classify as CHANGE/UPGRADE (fulfilment
    co-occurs), never a pure LOSS/BREAK."""
    v = _chart()
    rev = reversal_map(v, DOMAIN_PROFILES["career"],
                       datetime(2019, 1, 1, tzinfo=UTC),
                       datetime(2024, 12, 31, tzinfo=UTC))
    assert not [r for r in rev if r.kind == "LOSS/BREAK"], \
        "career wrongly flagged a loss — there was none"
    assert [r for r in rev if r.kind == "CHANGE/UPGRADE"], \
        "the 2021-22 upward job-change should register as CHANGE/UPGRADE"


def test_marriage_divorce_is_loss_remarriage_is_change():
    """The Feb-2026 divorce is a genuine LOSS/BREAK; the Jan-2027 remarriage is a
    CHANGE/UPGRADE — judged from the timing (AD/PD) lords, not the standing MD."""
    v = _chart()
    rev = reversal_map(v, DOMAIN_PROFILES["marriage"],
                       datetime(2025, 1, 1, tzinfo=UTC),
                       datetime(2027, 3, 1, tzinfo=UTC))
    losses = [r for r in rev if r.kind == "LOSS/BREAK"]
    assert any(r.start.year == 2026 or (r.start.year == 2025 and r.start.month >= 8)
               for r in losses), "the divorce window must surface as LOSS/BREAK"
    jan27 = [r for r in rev if r.start.year == 2027 and r.start.month == 1]
    assert jan27 and any(r.kind == "CHANGE/UPGRADE" for r in jan27), \
        "the remarriage must surface as CHANGE/UPGRADE, not loss"


def test_render_and_scan_are_strings():
    v = _chart()
    s = datetime(2024, 1, 1, tzinfo=UTC)
    e = datetime(2024, 6, 1, tzinfo=UTC)
    assert "EVENT-EVIDENCE PACK" in render_domain(v, DOMAIN_PROFILES["career"], s, e)
    assert "MACRO-SCAN" in scan_domains(v, s, e)
