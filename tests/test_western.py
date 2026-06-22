"""Tests for the Western extensions."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from advance_astrology import NatalChart, Planet
from advance_astrology.angles import angular_separation
from advance_astrology.houses import compute_cusps
from advance_astrology.western import declination as decl
from advance_astrology.western import dignities as wd
from advance_astrology.western import lots, midpoints

WHEN = datetime(1990, 5, 15, 14, 30, tzinfo=ZoneInfo("America/New_York"))
LAT, LON = 40.7128, -74.0060


@pytest.fixture(scope="module")
def chart():
    return NatalChart.create(when=WHEN, latitude=LAT, longitude=LON)


# --------------------------------------------------------------------------- #
# Houses
# --------------------------------------------------------------------------- #

def test_regiomontanus_reduces_to_angles():
    cusps, angles = compute_cusps("regiomontanus", ramc=123.0,
                                  obliquity=23.44, latitude=41.0)
    assert cusps[1] == pytest.approx(angles.ascendant, abs=1e-6)
    assert cusps[10] == pytest.approx(angles.midheaven, abs=1e-6)


def test_regiomontanus_opposite_cusps():
    cusps, _ = compute_cusps("regiomontanus", ramc=200.0,
                             obliquity=23.44, latitude=51.0)
    for h in range(1, 7):
        assert angular_separation(cusps[h], cusps[h + 6]) == pytest.approx(180, abs=1e-6)


# --------------------------------------------------------------------------- #
# Lots
# --------------------------------------------------------------------------- #

def test_part_of_fortune_sect_reversal():
    pos = {Planet.SUN: 50.0, Planet.MOON: 200.0}
    asc = 100.0
    day = lots.compute_lot("Fortune", pos, asc, is_day=True)
    night = lots.compute_lot("Fortune", pos, asc, is_day=False)
    # Day: Asc+Moon-Sun ; Night: Asc+Sun-Moon — they differ.
    assert day != night
    assert day == pytest.approx((100 + 200 - 50) % 360)
    assert night == pytest.approx((100 + 50 - 200) % 360)


def test_all_lots_present(chart):
    out = chart.lots()
    assert {"Fortune", "Spirit", "Eros", "Marriage"} <= set(out)


# --------------------------------------------------------------------------- #
# Essential dignities
# --------------------------------------------------------------------------- #

def test_domicile_and_almuten():
    # 15° Leo: domicile = Sun.
    ed = wd.essential_dignity(135.0, is_day=True)
    assert ed.domicile == Planet.SUN
    assert ed.almuten() in wd.DOMICILE.values()


def test_term_ruler_within_sign():
    # Aries 0-6 is Jupiter's Egyptian term.
    assert wd.term_ruler(3.0) == Planet.JUPITER
    # Aries 25-30 is Saturn's.
    assert wd.term_ruler(27.0) == Planet.SATURN


def test_face_ruler_chaldean():
    # First face of Aries is Mars.
    assert wd.face_ruler(5.0) == Planet.MARS
    # Second face of Aries (10-20) is the Sun.
    assert wd.face_ruler(15.0) == Planet.SUN


# --------------------------------------------------------------------------- #
# Declination / antiscia / midpoints
# --------------------------------------------------------------------------- #

def test_declination_within_obliquity(chart):
    decls = chart.declinations()
    for d in decls.values():
        assert -27 < d < 27   # bounded by obliquity + max ecliptic latitude


def test_sun_declination_matches_known(chart):
    # Mid-May Sun declination ~ +18.9°.
    assert chart.declinations()[Planet.SUN] == pytest.approx(18.9, abs=0.3)


def test_antiscion_involution():
    # Antiscion is its own inverse.
    assert decl.antiscion(decl.antiscion(73.0)) == pytest.approx(73.0)


def test_midpoint_is_between():
    m = midpoints.midpoint(10.0, 50.0)
    assert m == pytest.approx(30.0)
    # Wrap-around midpoint uses the short arc.
    m2 = midpoints.midpoint(350.0, 10.0)
    assert m2 == pytest.approx(0.0)


def test_harmonic_chart():
    h = midpoints.harmonic_chart({Planet.SUN: 40.0}, 9)
    assert h[Planet.SUN] == pytest.approx(360.0 % 360.0)
