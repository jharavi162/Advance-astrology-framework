"""Doctrine tests for the Lajjitādi and Śayanādi avasthās (BPHS, avasthā
adhyāya). Synthetic placements and published arithmetic only — no native
event dates."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from advance_astrology.constants import Planet as P
from advance_astrology.vedic import avastha as av

# Aries lagna. Leo (5th) holds Sun 25°, Saturn and Mercury; Moon exalted in
# Taurus; Venus in watery Cancer aspected only by Mars from Capricorn.
SIGNS = {P.SUN: 4, P.SATURN: 4, P.MERCURY: 4, P.MOON: 1, P.VENUS: 3,
         P.MARS: 9, P.JUPITER: 8, P.RAHU: 2, P.KETU: 8}
LONS = {P.SUN: 145.0, P.SATURN: 130.0, P.MERCURY: 135.0, P.MOON: 33.0,
        P.VENUS: 100.0, P.MARS: 280.0, P.JUPITER: 250.0, P.RAHU: 70.0, P.KETU: 250.0}


def states(p):
    return {x["state"] for x in av.lajjitadi_avastha(p, SIGNS, LONS, 0)}


def test_lajjita_in_fifth_with_sun_saturn_mars_or_nodes():
    assert "Lajjita" in states(P.MERCURY) and "Lajjita" in states(P.SUN)
    assert "Lajjita" not in states(P.MOON)


def test_garvita_exalted_or_mulatrikona():
    assert "Garvita" in states(P.MOON)
    assert "Garvita" not in states(P.SUN)          # Leo 25° is own, not mūlatrikoṇa


def test_kshudhita_joined_by_saturn():
    assert "Kshudhita" in states(P.SUN)


def test_trishita_watery_malefic_aspect_no_benefic():
    assert "Trishita" in states(P.VENUS)
    signs = dict(SIGNS, **{P.JUPITER: 11})           # Jupiter in Pisces aspects Cancer (5th)
    assert "Trishita" not in {x["state"] for x in
                              av.lajjitadi_avastha(P.VENUS, signs, LONS, 0)}


def test_kshobhita_with_sun_and_a_malefic():
    r = {x["state"]: x["reason"] for x in av.lajjitadi_avastha(P.MERCURY, SIGNS, LONS, 0)}
    assert "Kshobhita" in r and "Saturn" in r["Kshobhita"]


def test_mudita_aspected_by_benefic():
    assert "Mudita" in states(P.SUN)                 # Jupiter's 9th aspect on Leo


def test_nodes_have_no_lajjitadi():
    assert av.lajjitadi_avastha(P.RAHU, SIGNS, LONS, 0) == []


def test_shayanadi_arithmetic_published_example():
    # Yenbeeyes, "Avasthas of Planets" (2009), after BPHS: Sun in Hasta (13),
    # navāṁśa 6, Moon in Pūrvabhādrapadā (25), 20th ghaṭī, Capricorn lagna (10)
    # → 133 mod 12 = 1 → Śayana; Rāhu (27, A 8) and Ketu (14, A 8) → Sabhā.
    assert av.shayanadi_index(13, 1, 6, 25, 20, 10) == 1
    assert av.shayanadi_index(27, av.SHAYANADI_NUMBER[P.RAHU], 8, 25, 20, 10) == 7
    assert av.shayanadi_index(14, av.SHAYANADI_NUMBER[P.KETU], 8, 25, 20, 10) == 7
    assert av.SHAYANADI_STATES[0] == "Shayana" and av.SHAYANADI_STATES[6] == "Sabha"


def test_shayanadi_zero_remainder_is_nidra():
    assert av.shayanadi_index(1, 1, 1, 1, 8, 2) == 12
    assert av.SHAYANADI_STATES[11] == "Nidra"


def test_running_ghati_counts_the_current_one():
    rise = datetime(2000, 1, 1, tzinfo=timezone.utc)
    assert av.running_ghati(rise + timedelta(minutes=463), rise) == 20
    assert av.running_ghati(rise + timedelta(minutes=24), rise) == 2
    assert av.running_ghati(rise, rise) == 1


def test_shayanadi_navamsa_is_counted_within_the_sign():
    # 18°36′ Virgo is the 6th navāṁśa of Virgo (not the 60th of the zodiac).
    a = av.shayanadi_avastha(P.SUN, 150 + 18.6, 330 + 0.5, 9, 20)
    assert a == av.SHAYANADI_STATES[av.shayanadi_index(13, 1, 6, 25, 20, 10) - 1]
