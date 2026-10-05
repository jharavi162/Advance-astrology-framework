"""Doctrine tests for the time-based upagrahas Gulika and Mandi (BPHS,
Upagraha-adhyāya): the day/night is cut into eight parts, Saturn's part rules
Gulika (its start) and Mandi (its middle); the vāra runs sunrise-to-sunrise."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from advance_astrology import VedicChart
from advance_astrology.vedic import upagrahas

UTC = timezone.utc
# A synthetic Thursday: 12 h day, 12 h night → each eighth-part is 1.5 h.
RISE = datetime(2024, 1, 4, 6, 0, tzinfo=UTC)            # Thursday
SET = RISE + timedelta(hours=12)
NEXT_RISE = SET + timedelta(hours=12)
SEG = timedelta(hours=1.5)


def test_day_gulika_is_start_of_saturns_part():
    # Thursday day parts: Ju, Ve, Sa … → Saturn is the 3rd part (index 2).
    birth = RISE + timedelta(hours=1)
    assert upagrahas.gulika_time(birth, RISE, SET, NEXT_RISE,
                                 weekday="Thursday") == RISE + 2 * SEG


def test_night_gulika_starts_from_fifth_lord():
    # Thursday night starts from the 5th lord (Moon): Mo, Ma, Me, Ju, Ve, Sa.
    birth = SET + timedelta(hours=3)
    assert upagrahas.gulika_time(birth, RISE, SET, NEXT_RISE,
                                 weekday="Thursday") == SET + 5 * SEG


def test_mandi_is_middle_of_saturns_part():
    for birth in (RISE + timedelta(hours=1), SET + timedelta(hours=3)):
        g = upagrahas.gulika_time(birth, RISE, SET, NEXT_RISE, weekday="Thursday")
        m = upagrahas.mandi_time(birth, RISE, SET, NEXT_RISE, weekday="Thursday")
        assert m - g == SEG / 2


def test_vedic_weekday_follows_local_sunrise():
    # A sunrise at 21:30 UTC Wednesday at 135°E is Thursday morning locally.
    rise = datetime(2024, 1, 3, 21, 30, tzinfo=UTC)
    assert upagrahas.vedic_weekday(rise, 135.0) == "Thursday"
    assert upagrahas.vedic_weekday(RISE, 0.0) == "Thursday"


def test_pre_sunrise_birth_uses_previous_vara():
    # 03:00 local (before sunrise) belongs to the previous day's night.
    lat, lon = 26.0, 85.0
    when = datetime(2024, 1, 5, 3, 0, tzinfo=timezone(timedelta(hours=5.5)))
    v = VedicChart.create(when=when, latitude=lat, longitude=lon)
    eph = v.natal._ephemeris
    rise, setting, nxt, is_day = eph.day_portions(v.when_utc, lat, lon)
    assert not is_day
    assert upagrahas.vedic_weekday(rise, lon) == "Thursday"   # civil date is Friday


def test_chart_gulika_mandi_are_ascendants_at_their_instants():
    lat, lon = 26.0, 85.0
    when = datetime(2024, 1, 4, 14, 0, tzinfo=timezone(timedelta(hours=5.5)))
    v = VedicChart.create(when=when, latitude=lat, longitude=lon)
    pts = v.time_upagrahas()
    assert set(pts) == {"Gulika", "Mandi"}
    eph = v.natal._ephemeris
    rise, setting, nxt, is_day = eph.day_portions(v.when_utc, lat, lon)
    vara = upagrahas.vedic_weekday(rise, lon)
    gt = upagrahas.gulika_time(v.when_utc, rise, setting, nxt,
                               use_night=not is_day, weekday=vara)
    ref = VedicChart.create(when=gt, latitude=lat, longitude=lon)
    assert abs((pts["Gulika"] - ref.ascendant + 180) % 360 - 180) < 1e-6
    assert pts["Gulika"] != pts["Mandi"]
