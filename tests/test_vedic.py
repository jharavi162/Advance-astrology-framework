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


def test_narayana_dasha_twelve_signs(vchart):
    nd = vchart.narayana_dasha()
    assert len(nd) == 12
    assert len({d.note for d in nd}) == 12
    # Each span is a whole number of years in 1..12.
    for d in nd:
        assert 1 <= round(d.years) <= 12


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


def test_argala_houses_and_counters():
    # Argala/virodhargala pairs are symmetric about the lagna axis:
    # primary 2/4/11 (counter 12/10/3) and secondary 5/8 (counter 9/6).
    assert jaimini.ARGALA_HOUSES == {2: 12, 4: 10, 11: 3, 5: 9, 8: 6}


def test_secondary_argala_from_eighth(vchart):
    # A planet in the 8th from a reference sign casts secondary argala on it,
    # countered only by a planet in the 6th.
    ref = vchart.ascendant_sign
    eighth_sign = (ref + 7) % 12
    signs = {Planet.SUN: eighth_sign}        # lone causer, no counter in 6th
    args = {a.house: a for a in jaimini.argala_on_sign(ref, signs)}
    assert 8 in args
    assert args[8].counter_house == 6
    assert args[8].causers == [Planet.SUN]
    assert args[8].effective


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


# --------------------------------------------------------------------------- #
# Shadbala & strengths
# --------------------------------------------------------------------------- #

def test_shadbala_seven_planets(vchart):
    sb = vchart.shadbala()
    assert set(sb) == {Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
                       Planet.JUPITER, Planet.VENUS, Planet.SATURN}


def test_shadbala_components_nonnegative(vchart):
    for r in vchart.shadbala().values():
        assert r.sthana >= 0 and r.dig >= 0 and r.kala >= 0
        assert r.naisargika > 0
        assert r.total_rupa > 0
        assert r.total_rupa == pytest.approx(r.total_virupa / 60.0)


def test_uccha_bala_extremes():
    from advance_astrology.vedic.shadbala import uccha_bala
    from advance_astrology.vedic.dignities import EXALTATION
    from advance_astrology.constants import SIGNS
    sign, deg = EXALTATION[Planet.SUN]
    exalt_lon = SIGNS.index(sign) * 30 + deg
    assert uccha_bala(Planet.SUN, exalt_lon) == pytest.approx(60, abs=1e-6)
    assert uccha_bala(Planet.SUN, (exalt_lon + 180) % 360) == pytest.approx(0, abs=1e-6)


def test_naisargika_order():
    from advance_astrology.vedic.shadbala import NAISARGIKA
    assert NAISARGIKA[Planet.SUN] > NAISARGIKA[Planet.MOON] > NAISARGIKA[Planet.SATURN]


def test_ishta_kashta_bounds(vchart):
    for ik in vchart.ishta_kashta().values():
        assert 0 <= ik.ishta <= 60
        assert 0 <= ik.kashta <= 60


def test_functional_nature_has_yogakaraka():
    # Taurus lagna: Saturn rules 9th & 10th -> classic Yogakaraka.
    from advance_astrology.vedic.nature import functional_nature
    nat = functional_nature(1)   # Taurus ascendant
    assert nat[Planet.SATURN] == "Yogakaraka"


def test_marakas_are_2nd_7th_lords():
    from advance_astrology.vedic.nature import marakas
    # Aries lagna: 2nd=Taurus(Venus), 7th=Libra(Venus) -> Venus is maraka.
    assert Planet.VENUS in marakas(0)


def test_vaiseshikamsa_returns_tier(vchart):
    tier = vchart.vaiseshikamsa(Planet.VENUS)
    assert isinstance(tier, str) and tier


def test_combustion_detection():
    from advance_astrology.vedic.avastha import is_combust
    assert is_combust(Planet.MERCURY, 100.0, 105.0)      # 5° from Sun
    assert not is_combust(Planet.MERCURY, 100.0, 150.0)  # far from Sun


def test_bhrigu_bindu_is_rahu_moon_midpoint(vchart):
    from advance_astrology.angles import angular_separation
    bb = vchart.bhrigu_bindu()
    rahu = vchart.longitudes[Planet.RAHU]
    moon = vchart.longitudes[Planet.MOON]
    # Equidistant from Rahu and Moon along the short arc.
    assert angular_separation(bb, rahu) == pytest.approx(
        angular_separation(bb, moon), abs=1e-6)


# --------------------------------------------------------------------------- #
# Bhava-Chalit, KP, Kakshya, Transits
# --------------------------------------------------------------------------- #

def test_bhava_chalit_houses_valid(vchart):
    chalit = vchart.bhava_chalit()
    for c in chalit.values():
        assert 1 <= c.rashi_house <= 12
        assert 1 <= c.chalit_house <= 12


def test_kp_chain_four_lords(vchart):
    chain = vchart.kp_chain(Planet.MOON)
    assert chain.sign_lord and chain.star_lord and chain.sub_lord
    assert chain.sub_sub_lord


def test_kp_sublord_partitions_sum_to_nakshatra():
    # The nine subs of a nakshatra must tile its 13°20' span exactly.
    from advance_astrology.vedic.kp import _subdivide
    from advance_astrology.constants import NAKSHATRA_ARC, Planet
    segs = _subdivide(0.0, NAKSHATRA_ARC, Planet.KETU)
    assert len(segs) == 9
    assert segs[-1][2] == pytest.approx(NAKSHATRA_ARC)


def test_kp_significators_present(vchart):
    kps = vchart.kp_significators()
    assert kps.planet_signifies(Planet.SUN)
    assert kps.house_significators(7)


def test_kakshya_lords_order():
    from advance_astrology.vedic.kakshya import KAKSHYA_LORDS, kakshya_index
    assert len(KAKSHYA_LORDS) == 8
    assert KAKSHYA_LORDS[0] == Planet.SATURN
    assert kakshya_index(0.0) == 0
    assert kakshya_index(29.9) == 7


def test_contributor_bindu_consistency(vchart):
    # Summing each contributor's bindu over all signs reproduces the BAV total.
    from advance_astrology.vedic.ashtakavarga import (
        _CONTRIBUTORS, contributor_gives_bindu)
    total = 0
    for sign in range(12):
        for c in _CONTRIBUTORS:
            if contributor_gives_bindu(Planet.SUN, c, sign,
                                       vchart.signs, vchart.ascendant_sign):
                total += 1
    assert total == sum(vchart.bhinnashtakavarga(Planet.SUN)) == 48


def test_transits_positions_and_sade_sati(vchart):
    tr = vchart.transits()
    when = datetime(2026, 6, 18, tzinfo=timezone.utc)
    pos = tr.positions(when)
    assert all(0 <= v < 360 for v in pos.values())
    ss = tr.sade_sati(when)
    assert set(ss) == {"active", "phase", "saturn_sign"}
    assert 1 <= tr.transit_house(when, Planet.JUPITER) <= 12
