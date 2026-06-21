"""Test suite for the Advance Astrology Framework."""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from advance_astrology import (
    NatalChart,
    Planet,
    ayanamsa,
    find_aspects,
    nakshatra_of,
    to_zodiac,
    vimshottari_dasha,
)
from advance_astrology.angles import angular_separation, norm180, norm360
from advance_astrology.constants import NAKSHATRA_ARC
from advance_astrology.houses import compute_cusps


# Reference instant used across tests: 1990-05-15 14:30 EDT, New York City.
WHEN = datetime(1990, 5, 15, 14, 30, tzinfo=ZoneInfo("America/New_York"))
LAT, LON = 40.7128, -74.0060


@pytest.fixture(scope="module")
def chart():
    return NatalChart.create(when=WHEN, latitude=LAT, longitude=LON)


# --------------------------------------------------------------------------- #
# Angle utilities
# --------------------------------------------------------------------------- #

def test_norm360():
    assert norm360(370) == 10
    assert norm360(-10) == 350
    assert norm360(0) == 0


def test_norm180():
    assert norm180(190) == -170
    assert norm180(-190) == 170
    assert norm180(180) == 180


def test_angular_separation():
    assert angular_separation(10, 350) == pytest.approx(20)
    assert angular_separation(0, 180) == pytest.approx(180)
    assert angular_separation(90, 90) == pytest.approx(0)


def test_to_zodiac():
    pos = to_zodiac(35.5)
    assert pos.sign == "Taurus"
    assert pos.degree == 5
    assert pos.minute == 30


# --------------------------------------------------------------------------- #
# Ephemeris / positions
# --------------------------------------------------------------------------- #

def test_sun_position_reasonable(chart):
    # Mid-May → Sun in late Taurus.
    sun = chart.get(Planet.SUN)
    assert sun.sign == "Taurus"
    assert 20 < sun.position.degree_in_sign < 30


def test_known_sun_longitude():
    # Independent almanac check: Sun ~54.6° (24-25° Taurus) on this instant.
    c = NatalChart.create(when=WHEN, latitude=LAT, longitude=LON)
    assert c.get(Planet.SUN).tropical_longitude == pytest.approx(54.66, abs=0.1)


def test_retrograde_detection(chart):
    # Mercury and the outer planets are retrograde at this instant.
    assert chart.get(Planet.MERCURY).retrograde
    assert chart.get(Planet.PLUTO).retrograde


def test_nodes_opposite(chart):
    rahu = chart.get(Planet.RAHU).longitude
    ketu = chart.get(Planet.KETU).longitude
    assert angular_separation(rahu, ketu) == pytest.approx(180, abs=1e-6)


def test_node_retrograde(chart):
    # The mean lunar node always regresses.
    assert chart.get(Planet.RAHU).speed < 0


# --------------------------------------------------------------------------- #
# Houses & angles
# --------------------------------------------------------------------------- #

def test_cusp1_is_ascendant(chart):
    assert chart.cusps[1] == pytest.approx(chart.angles.ascendant)


def test_cusp10_is_midheaven(chart):
    assert chart.cusps[10] == pytest.approx(chart.angles.midheaven)


def test_opposite_cusps_180_apart(chart):
    for h in range(1, 7):
        sep = angular_separation(chart.cusps[h], chart.cusps[h + 6])
        assert sep == pytest.approx(180, abs=1e-6)


@pytest.mark.parametrize("system", ["placidus", "whole_sign", "equal", "porphyry"])
def test_house_systems_monotonic(system):
    cusps, _ = compute_cusps(system, ramc=120.0, obliquity=23.44, latitude=40.0)
    # Walking the cusps forward should advance monotonically around the circle.
    total = sum(
        norm360(cusps[h % 12 + 1] - cusps[h]) for h in range(1, 13)
    )
    assert total == pytest.approx(360, abs=1e-6)


def test_placidus_polar_fallback():
    # Beyond the polar circle Placidus is undefined; should not raise.
    cusps, _ = compute_cusps("placidus", ramc=90.0, obliquity=23.44, latitude=70.0)
    assert len(cusps) == 12


def test_every_placement_has_house(chart):
    for placement in chart.placements.values():
        assert 1 <= placement.house <= 12


# --------------------------------------------------------------------------- #
# Aspects
# --------------------------------------------------------------------------- #

def test_aspects_found(chart):
    aspects = chart.aspects()
    assert len(aspects) > 0
    # Rahu/Ketu are exactly opposite by construction.
    node_opp = [
        a for a in aspects
        if {a.body1, a.body2} == {Planet.RAHU, Planet.KETU}
    ]
    assert node_opp and node_opp[0].name == "Opposition"
    assert node_opp[0].orb == pytest.approx(0, abs=1e-6)


def test_orb_factor_widens_results(chart):
    tight = find_aspects(chart.placements, orb_factor=0.5)
    loose = find_aspects(chart.placements, orb_factor=2.0)
    assert len(loose) >= len(tight)


# --------------------------------------------------------------------------- #
# Sidereal / Vedic
# --------------------------------------------------------------------------- #

def test_ayanamsa_monotonic_increase():
    early = ayanamsa(2415020.0, "lahiri")   # ~1900
    late = ayanamsa(2451545.0, "lahiri")    # 2000
    assert late > early
    assert 22 < early < 24
    assert 23 < late < 25


def test_sidereal_shift_matches_ayanamsa():
    c_trop = NatalChart.create(when=WHEN, latitude=LAT, longitude=LON,
                               zodiac="tropical")
    c_sid = NatalChart.create(when=WHEN, latitude=LAT, longitude=LON,
                              zodiac="sidereal", ayanamsa="lahiri")
    diff = norm360(
        c_trop.get(Planet.SUN).longitude - c_sid.get(Planet.SUN).longitude
    )
    assert diff == pytest.approx(c_sid.ayanamsa_value, abs=1e-6)


def test_nakshatra_resolution():
    # 0° sidereal Aries → start of Ashwini, pada 1.
    nak = nakshatra_of(0.0)
    assert nak.name == "Ashwini"
    assert nak.pada == 1
    # Just inside the next nakshatra.
    nak2 = nakshatra_of(NAKSHATRA_ARC + 0.1)
    assert nak2.name == "Bharani"


def test_naamakshara_syllables():
    from advance_astrology.constants import PADA_SYLLABLES
    # Table is the full 108-syllable correspondence (27 nakshatras x 4 padas).
    assert len(PADA_SYLLABLES) == 27
    assert all(len(p) == 4 for p in PADA_SYLLABLES)
    # 0° Aries → Ashwini pada 1 → "Chu"; pada 4 (last 3°20') → "La".
    assert nakshatra_of(0.0).syllable == "Chu"
    assert nakshatra_of(NAKSHATRA_ARC - 0.1).syllable == "La"
    # Krittika pada 1 begins at 2 * 13°20' = 26°40' → "A".
    assert nakshatra_of(2 * NAKSHATRA_ARC + 0.1).syllable == "A"


def test_dasha_total_is_120_years():
    periods = vimshottari_dasha(45.0, WHEN, levels=1)
    total = sum(p.years for p in periods)
    assert total == pytest.approx(120, abs=0.05)


def test_dasha_first_lord_matches_moon_nakshatra():
    moon_lon = 200.0
    nak = nakshatra_of(moon_lon)
    periods = vimshottari_dasha(moon_lon, WHEN, levels=1)
    assert periods[0].lord == nak.lord


def test_current_dasha_chain_nested(chart):
    chain = chart.current_dasha(datetime(2026, 6, 18, tzinfo=timezone.utc))
    assert len(chain) == 3
    assert [d.level for d in chain] == [1, 2, 3]
    # Each sub-period must fall within its parent.
    assert chain[0].start <= chain[1].start
    assert chain[1].end <= chain[0].end


# --------------------------------------------------------------------------- #
# Chart API guards
# --------------------------------------------------------------------------- #

def test_naive_datetime_rejected():
    with pytest.raises(ValueError):
        NatalChart.create(when=datetime(1990, 5, 15, 14, 30),
                          latitude=LAT, longitude=LON)


def test_invalid_zodiac_rejected():
    with pytest.raises(ValueError):
        NatalChart.create(when=WHEN, latitude=LAT, longitude=LON, zodiac="x")


def test_element_balance_sums_to_planet_count(chart):
    balance = chart.element_balance()
    assert sum(balance.values()) == len(chart.placements)
