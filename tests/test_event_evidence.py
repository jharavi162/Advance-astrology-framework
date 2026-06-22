"""Regression tests for the domain-general event-evidence builder."""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from advance_astrology import VedicChart
from interpreter.event_evidence import (
    DOMAIN_PROFILES, candidate_map, render_domain, scan_domains,
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


def test_render_and_scan_are_strings():
    v = _chart()
    s = datetime(2024, 1, 1, tzinfo=UTC)
    e = datetime(2024, 6, 1, tzinfo=UTC)
    assert "EVENT-EVIDENCE PACK" in render_domain(v, DOMAIN_PROFILES["career"], s, e)
    assert "MACRO-SCAN" in scan_domains(v, s, e)
