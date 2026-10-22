"""Doctrine tests for Bhāva Bala — B.V. Raman, *Graha and Bhava Balas*,
ch. IX, Example 59 (the book's Standard Horoscope). Only the book's own
longitudes and Ṣaḍbala figures are used; no native event dates."""

from __future__ import annotations

import pytest

from advance_astrology.constants import Planet as P
from advance_astrology.vedic import bhava_bala as bb

dm = lambda d, m: d + m / 60
LON = {P.SUN: dm(180, 54), P.MOON: dm(311, 17), P.MARS: dm(229, 31),
       P.MERCURY: dm(181, 32), P.JUPITER: dm(84, 1), P.VENUS: dm(171, 10),
       P.SATURN: dm(124, 23)}
MADHYA = dict(zip(range(1, 13), [dm(298, 27), dm(331, 10), dm(3, 53), dm(36, 36),
                                 dm(63, 53), dm(91, 10), dm(118, 27), dm(151, 10),
                                 dm(183, 51), dm(216, 36), dm(243, 53), dm(271, 10)]))
SHADBALA = {P.SATURN: 389.21, P.JUPITER: 433.77, P.MARS: 298.14, P.VENUS: 376.25,
            P.MERCURY: 537.02, P.MOON: 389.80, P.SUN: 0.0}
# Book: digbala per bhāva, net drishti, total (virūpas).
DIG = [30, 40, 10, 0, 20, 40, 30, 10, 20, 30, 40, 40]
DRISHTI = [54.18, 36.44, 58.99, 28.10, 11.57, 2.92, 5.70, 32.51, 44.80, 44.51, 33.12, 97.55]
TOTAL = [473.39, 510.21, 367.33, 404.15, 568.59, 432.72, 425.50, 579.53, 440.95,
         372.65, 506.89]


@pytest.fixture(scope="module")
def result():
    return bb.bhava_bala(MADHYA, LON, SHADBALA, moon_waxing=True)


def test_digbala_matches_the_book(result):
    assert [result[h].dig for h in range(1, 13)] == DIG


def test_drishti_bala_matches_the_book(result):
    for h, want in zip(range(1, 13), DRISHTI):
        assert result[h].drishti == pytest.approx(want, abs=0.3), h


def test_first_bhava_benefic_and_malefic_totals(result):
    assert result[1].subha_drishti == pytest.approx(79.99, abs=0.05)
    assert result[1].papa_drishti == pytest.approx(25.81, abs=0.05)


def test_totals_match_the_book(result):
    for h, want in zip(range(1, 12), TOTAL):
        assert result[h].total_virupa == pytest.approx(want, abs=0.3), h
    assert result[1].lord is P.SATURN and result[5].lord is P.MERCURY


def test_sign_kinds_split_dhanus_and_makara():
    assert bb.sign_kind(8 * 30 + 3) == "nara" and bb.sign_kind(8 * 30 + 20) == "chatushpada"
    assert bb.sign_kind(9 * 30 + 3) == "chatushpada" and bb.sign_kind(9 * 30 + 20) == "jalachara"
    assert bb.sign_kind(7 * 30 + 1) == "keeta"


def test_sripati_drishti_curve():
    assert bb.drishti_value(20) == 0 and bb.drishti_value(310) == 0
    assert bb.drishti_value(60) == 15 and bb.drishti_value(90) == 45
    assert bb.drishti_value(120) == 30 and bb.drishti_value(150) == 0
    assert bb.drishti_value(180) == 60 and bb.drishti_value(240) == 30
    assert bb.drishti_value(75, P.SATURN) == bb.drishti_value(75) + 45
    assert bb.drishti_value(130, P.JUPITER) == bb.drishti_value(130) + 30
    assert bb.drishti_value(100, P.MARS) == bb.drishti_value(100) + 15


def test_chart_method_runs():
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from advance_astrology import VedicChart
    v = VedicChart.create(when=datetime(2000, 1, 1, 12, tzinfo=ZoneInfo("Asia/Kolkata")),
                          latitude=28.6, longitude=77.2)
    r = v.bhava_bala()
    assert sorted(r) == list(range(1, 13)) and r[1].madhya == pytest.approx(v.ascendant)
