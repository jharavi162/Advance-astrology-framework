"""Doctrine and contract tests for the gochara (transit) additions.

No native birth or event dates: the tables are checked against the śāstra
rules they encode, and the scanners against their own definitions on a
generic chart.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from advance_astrology import Planet, VedicChart
from advance_astrology.nakshatra import nakshatra_of
from advance_astrology.vedic import gochara

P = Planet
GENERIC = datetime(2000, 1, 1, 12, 0, tzinfo=timezone.utc)
START = datetime(2030, 1, 1, tzinfo=timezone.utc)
END = START + timedelta(days=365)


@pytest.fixture(scope="module")
def tr():
    v = VedicChart.create(when=GENERIC, latitude=28.6, longitude=77.2,
                          ayanamsa="lahiri")
    return v.transits()


# --------------------------------------------------------------------------- #
# Vedha (Phaladeepika, gochara adhyāya)
# --------------------------------------------------------------------------- #

def test_vedha_blocks_a_good_transit():
    # Jupiter is good in the 5th from the Moon; its vedha point is the 4th.
    hm = {P.JUPITER: 5, P.MARS: 4, P.VENUS: 9}
    r = gochara.vedha(P.JUPITER, 5, hm)
    assert r["good"] and r["vedha_house"] == 4
    assert r["obstructed_by"] == [P.MARS]


def test_no_vedha_between_sun_and_saturn_or_moon_and_mercury():
    # Sun good in the 3rd, vedha point the 9th — Saturn there does not obstruct.
    assert gochara.vedha(P.SUN, 3, {P.SUN: 3, P.SATURN: 9})["obstructed_by"] == []
    assert gochara.vedha(P.SATURN, 3, {P.SATURN: 3, P.SUN: 12})["obstructed_by"] == []
    # Moon good in the 1st, vedha point the 5th — Mercury there does not obstruct.
    assert gochara.vedha(P.MOON, 1, {P.MOON: 1, P.MERCURY: 5})["obstructed_by"] == []
    # ...but another graha in the same point does.
    assert gochara.vedha(P.MOON, 1, {P.MOON: 1, P.MARS: 5})["obstructed_by"] == [P.MARS]


def test_vipareeta_vedha_on_a_bad_house():
    # Sun's pair (3 good, 9 vedha): Sun in the 9th is bad, a graha in the 3rd
    # blocks that bad result.
    r = gochara.vedha(P.SUN, 9, {P.SUN: 9, P.MARS: 3})
    assert not r["good"] and r["vedha_house"] == 3
    assert r["vipareeta_by"] == [P.MARS] and r["obstructed_by"] == []


def test_nodes_follow_saturn_and_never_obstruct():
    assert gochara.VEDHA[P.RAHU] == gochara.VEDHA[P.SATURN]
    # A node sitting in Jupiter's vedha point does not obstruct it.
    assert gochara.vedha(P.JUPITER, 5, {P.JUPITER: 5, P.RAHU: 4})["obstructed_by"] == []


def test_vedha_table_shape():
    # Good houses per graha as listed in the gochara adhyāya.
    assert sorted(gochara.VEDHA[P.SUN]) == [3, 6, 10, 11]
    assert sorted(gochara.VEDHA[P.MOON]) == [1, 3, 6, 7, 10, 11]
    assert sorted(gochara.VEDHA[P.MARS]) == [3, 6, 11]
    assert sorted(gochara.VEDHA[P.MERCURY]) == [2, 4, 6, 8, 10, 11]
    assert sorted(gochara.VEDHA[P.JUPITER]) == [2, 5, 7, 9, 11]
    assert sorted(gochara.VEDHA[P.VENUS]) == [1, 2, 3, 4, 5, 8, 9, 11, 12]
    assert sorted(gochara.VEDHA[P.SATURN]) == [3, 6, 11]


# --------------------------------------------------------------------------- #
# Tārā, Murti, Saturn from the Moon
# --------------------------------------------------------------------------- #

def test_tara_count():
    assert gochara.tara(0, 0)["name"] == "Janma"
    assert gochara.tara(0, 0)["quality"] == "mixed"
    assert gochara.tara(0, 2)["name"] == "Vipat"
    assert gochara.tara(0, 2)["quality"] == "bad"
    assert gochara.tara(0, 1)["quality"] == "good"            # Sampat
    assert gochara.tara(0, 9)["name"] == "Janma"              # 10th = 2nd round
    assert gochara.tara(5, 4) == dict(number=9, name="Parama-mitra",
                                      count=27, quality="good")
    bad = {gochara.tara(0, k)["name"] for k in range(27)
           if gochara.tara(0, k)["quality"] == "bad"}
    assert bad == {"Vipat", "Pratyari", "Vadha"}


def test_murti_mapping():
    want = {"Swarna": {1, 6, 11}, "Rajata": {2, 5, 9},
            "Tamra": {3, 7, 10}, "Loha": {4, 8, 12}}
    for name, houses in want.items():
        assert {h for h in range(1, 13) if gochara.murti(h) == name} == houses


def test_saturn_from_moon():
    assert gochara.saturn_from_moon(12)["sade_sati_phase"] == "Rising (12th)"
    assert gochara.saturn_from_moon(1)["sade_sati_phase"] == "Peak (Janma)"
    assert gochara.saturn_from_moon(2)["sade_sati_phase"] == "Setting (2nd)"
    assert gochara.saturn_from_moon(4)["dhaiya"]
    assert gochara.saturn_from_moon(8)["dhaiya_kind"] == "Ashtama (8th)"
    s = gochara.saturn_from_moon(5)
    assert not s["sade_sati"] and not s["dhaiya"]


# --------------------------------------------------------------------------- #
# Scanners and snapshot (contract, generic chart)
# --------------------------------------------------------------------------- #

def test_vectorised_longitudes_match_scalar(tr):
    whens = [START + timedelta(days=d) for d in (0, 40, 200)]
    for p in (P.SUN, P.MOON, P.SATURN, P.RAHU, P.KETU):
        fast = tr._sidereal_lons(p, whens)
        slow = [tr.positions(w, [p])[p] for w in whens]
        assert max(abs(a - b) for a, b in zip(fast, slow)) < 1e-9


def test_sun_sign_ingresses_one_year(tr):
    ing = tr.sign_ingresses(P.SUN, START, END)
    assert len(ing) == 12
    for x in ing:
        assert x["to_sign"] == (x["from_sign"] + 1) % 12      # Sun never retrogrades
        before = tr.transit_sign(x["when"] - timedelta(hours=2), P.SUN)
        after = tr.transit_sign(x["when"] + timedelta(hours=1), P.SUN)
        assert (before, after) == (x["from_sign"], x["to_sign"])
        assert x["murti"] in {"Swarna", "Rajata", "Tamra", "Loha"}
        assert not x["retrograde"]


def test_sun_nakshatra_ingresses_one_year(tr):
    ing = tr.nakshatra_ingresses(P.SUN, START, END)
    assert len(ing) in (27, 28)
    for x in ing:
        assert x["to_nakshatra"] == (x["from_nakshatra"] + 1) % 27
        lon = tr.positions(x["when"] + timedelta(hours=1), [P.SUN])[P.SUN]
        assert nakshatra_of(lon).index == x["to_nakshatra"]


def test_mercury_stations_alternate(tr):
    st = tr.stations(P.MERCURY, START, END)
    assert len(st) >= 5                                         # ~3 retro spells a year
    for a, b in zip(st, st[1:]):
        assert a["turns"] != b["turns"]
    for s in st:
        before = tr.motion(s["when"] - timedelta(days=2), P.MERCURY)["retrograde"]
        after = tr.motion(s["when"] + timedelta(days=2), P.MERCURY)["retrograde"]
        assert after == (s["turns"] == "vakri") and before != after
    assert tr.stations(P.RAHU, START, END) == []


def test_houses_from_and_snapshot_agree(tr):
    snap = tr.snapshot(START)
    refs = snap["references"]
    assert set(refs) == {"lagna", "moon", "sun", "al", "ul", "karakamsha"}
    hm = tr.houses_from(START, refs["moon"])
    for p, d in snap["planets"].items():
        assert d["houses"]["lagna"] == tr.transit_house(START, p, "lagna")
        assert d["houses"]["moon"] == tr.transit_house(START, p, "moon") == hm[p]
        assert d["tara"] == tr.tara_bala(START)[p]
    assert snap["planets"][P.RAHU]["kakshya_active"] is None
    assert snap["saturn"]["house_from_moon"] == hm[P.SATURN]
