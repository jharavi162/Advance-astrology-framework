"""Tests for the Vedic (Jyotish) suite."""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from advance_astrology import Planet, VedicChart
from advance_astrology.constants import SIGNS
from advance_astrology.vedic import (
    arudha,
    ashtakavarga,
    compatibility,
    dashas,
    dignities,
    jaimini,
)
from advance_astrology.vedic.aspects import graha_aspect_houses, rashi_aspects
from advance_astrology.vedic.vargas import (
    SHODASHAVARGA,
    VARGA_FUNCS,
    divisional_sign,
)

WHEN = datetime(1990, 5, 15, 14, 30, tzinfo=ZoneInfo("America/New_York"))
LAT, LON = 40.7128, -74.0060


@pytest.fixture(scope="module")
def vchart():
    return VedicChart.create(when=WHEN, latitude=LAT, longitude=LON)


# --------------------------------------------------------------------------- #
# Vargas
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("lon,expected", [
    (0.0, "Aries"),        # Aries (movable) 1st navamsha
    (30.0, "Capricorn"),   # Taurus (fixed) 1st navamsha
    (60.0, "Libra"),       # Gemini (dual) 1st navamsha
])
def test_navamsha_known(lon, expected):
    assert SIGNS[divisional_sign(lon, 9)] == expected


@pytest.mark.parametrize("varga", SHODASHAVARGA)
def test_all_vargas_valid_signs(varga):
    for lon in (5.0, 47.3, 123.9, 271.1, 359.5):
        s = divisional_sign(lon, varga)
        assert 0 <= s <= 11


def test_sixteen_vargas_present():
    assert len(VARGA_FUNCS) == 16


def test_d30_uses_planet_signs():
    # Odd sign 0-5° -> Mars -> Aries.
    assert SIGNS[divisional_sign(3.0, 30)] == "Aries"
    # Even sign 0-5° -> Venus -> Taurus.
    assert SIGNS[divisional_sign(33.0, 30)] == "Taurus"


# --------------------------------------------------------------------------- #
# Dashas
# --------------------------------------------------------------------------- #

def test_vimshottari_total():
    periods = dashas.vimshottari(200.0, WHEN, levels=1)
    assert sum(p.years for p in periods) == pytest.approx(120, abs=0.05)


def test_ashtottari_total():
    periods = dashas.ashtottari(200.0, WHEN, levels=1)
    assert sum(p.years for p in periods) == pytest.approx(108, abs=0.05)


def test_yogini_total():
    periods = dashas.yogini(200.0, WHEN, levels=1)
    assert sum(p.years for p in periods) == pytest.approx(36, abs=0.05)


def test_dasha_registry():
    for name in ("vimshottari", "ashtottari", "yogini", "kalachakra"):
        out = dashas.compute_dasha(name, 200.0, WHEN)
        assert out


def test_antardasha_sums_to_mahadasha():
    periods = dashas.vimshottari(200.0, WHEN, levels=2)
    maha = periods[0]
    sub_total = sum(s.years for s in maha.sub_periods)
    assert sub_total == pytest.approx(maha.years, rel=1e-6)


# --------------------------------------------------------------------------- #
# Dignities
# --------------------------------------------------------------------------- #

def test_exaltation():
    assert dignities.dignity(Planet.SUN, 10.0).is_exalted          # Aries 10
    assert dignities.dignity(Planet.SATURN, 190.0).is_exalted      # Libra 10


def test_debilitation():
    assert dignities.dignity(Planet.SUN, 190.0).is_debilitated     # Libra


def test_compound_relationship_symmetry_inputs():
    rel = dignities.compound_relationship(Planet.SUN, 0, Planet.MOON, 1)
    assert rel in (dignities.GREAT_FRIEND, dignities.FRIEND,
                   dignities.NEUTRAL, dignities.ENEMY, dignities.GREAT_ENEMY)


# --------------------------------------------------------------------------- #
# Jaimini
# --------------------------------------------------------------------------- #

def test_chara_karakas_unique(vchart):
    karakas = vchart.chara_karakas()
    assert len(set(karakas.values())) == len(karakas) == 8


def test_atmakaraka_is_highest_degree(vchart):
    from advance_astrology.angles import to_zodiac
    ak = vchart.atmakaraka()
    degs = {}
    for p in [Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
              Planet.JUPITER, Planet.VENUS, Planet.SATURN]:
        degs[p] = to_zodiac(vchart.longitudes[p]).degree_in_sign
    # AK has the highest degree among the seven (Rahu handled separately).
    assert degs[ak] == max(degs.values()) or ak == Planet.RAHU


def test_chara_dasha_twelve_signs(vchart):
    cd = vchart.chara_dasha()
    assert len(cd) == 12
    assert len({d.note for d in cd}) == 12


# --------------------------------------------------------------------------- #
# Arudha
# --------------------------------------------------------------------------- #

def test_arudha_exception_not_in_house_or_seventh():
    # Lord in the 1st: arudha must shift to the 10th (cannot be the house).
    a = arudha.arudha_of_sign(0, 0)
    assert a not in (0, 6)


def test_all_arudhas_complete(vchart):
    ar = vchart.arudhas()
    assert set(ar) >= {f"A{i}" for i in range(1, 13)} | {"AL", "UL"}


# --------------------------------------------------------------------------- #
# Ashtakavarga
# --------------------------------------------------------------------------- #

def test_sarvashtakavarga_total(vchart):
    sav = vchart.sarvashtakavarga()
    assert sum(sav) == 337


def test_bhinnashtakavarga_totals(vchart):
    expected = {Planet.SUN: 48, Planet.MOON: 49, Planet.MARS: 39,
               Planet.MERCURY: 54, Planet.JUPITER: 56, Planet.VENUS: 52,
               Planet.SATURN: 39}
    for planet, total in expected.items():
        assert sum(vchart.bhinnashtakavarga(planet)) == total


# --------------------------------------------------------------------------- #
# Aspects
# --------------------------------------------------------------------------- #

def test_special_graha_aspects():
    assert graha_aspect_houses(Planet.MARS) == [4, 7, 8]
    assert graha_aspect_houses(Planet.JUPITER) == [5, 7, 9]
    assert graha_aspect_houses(Planet.SATURN) == [3, 7, 10]
    assert graha_aspect_houses(Planet.VENUS) == [7]


def test_rashi_drishti_mutual():
    # Rashi drishti is mutual: if A aspects B then B aspects A.
    for a in range(12):
        for b in rashi_aspects(a):
            assert a in rashi_aspects(b)


# --------------------------------------------------------------------------- #
# Panchanga & compatibility
# --------------------------------------------------------------------------- #

def test_panchanga_fields(vchart):
    p = vchart.panchanga()
    assert p.tithi.number in range(1, 31)
    assert 1 <= p.yoga_number <= 27
    assert p.karana


def test_guna_milan_bounds():
    g = compatibility.guna_milan(200.0, 45.0)
    assert 0 <= g.total <= 36
    assert sum(g.scores.values()) == g.total


def test_nadi_dosha_same_nadi():
    # Identical Moon longitudes share a nakshatra => same nadi => 0 points.
    g = compatibility.guna_milan(123.4, 123.4)
    assert g.scores["Nadi"] == 0


# --------------------------------------------------------------------------- #
# Integrated chart
# --------------------------------------------------------------------------- #

def test_vedic_requires_sidereal():
    from advance_astrology import NatalChart
    trop = NatalChart.create(when=WHEN, latitude=LAT, longitude=LON)
    with pytest.raises(ValueError):
        VedicChart(trop)


def test_house_calculation(vchart):
    for p in vchart.signs:
        assert 1 <= vchart.house_of(p) <= 12


def test_navamsha_cached(vchart):
    assert vchart.navamsha is vchart.navamsha


def test_current_dasha_chain(vchart):
    chain = vchart.current_dasha("vimshottari",
                                 datetime(2026, 6, 18, tzinfo=timezone.utc))
    assert chain and chain[0].level == 1
