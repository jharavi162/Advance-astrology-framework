"""Doctrine and contract tests for the gochara (transit) additions.

No native birth or event dates: the tables are checked against the śāstra
rules they encode, and the scanners against their own definitions on a
generic chart.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from advance_astrology import Planet, VedicChart
from advance_astrology.constants import SIGNS
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


# --------------------------------------------------------------------------- #
# Sarvatobhadra Chakra (grid + vedha lines; worked lines from Rath, Saptarishis)
# --------------------------------------------------------------------------- #

from advance_astrology.vedic import sarvatobhadra as sbc  # noqa: E402


def _names(nak, line):
    return [x["name"] for x in sbc.vedha_lines(nak)[line]["content"]]


def test_sbc_grid_composition():
    kinds = {}
    for row in sbc.GRID:
        assert len(row) == 9
        for cell in row:
            kinds.setdefault(cell["kind"], []).append(cell["name"])
    assert len(kinds["nakshatra"]) == 28 and len(set(kinds["nakshatra"])) == 28
    assert sorted(kinds["rashi"]) == sorted(SIGNS)
    assert len(set(kinds["vowel"])) == 16                    # "a" appears twice
    assert sorted(kinds["tithi"]) == sorted(sbc.TITHI_GROUPS)
    assert sbc.GRID[4][4]["name"] == "Purna" and sbc.GRID[4][4]["weekdays"] == ["Saturday"]
    days = [d for row in sbc.GRID for c in row if c["kind"] == "tithi" for d in c["weekdays"]]
    assert sorted(days) == sorted(sbc.WEEKDAYS)
    sides = {}
    for n, s_ in sbc.SIDE.items():
        sides[s_] = sides.get(s_, 0) + 1
    assert sides == dict(east=7, south=7, west=7, north=7)
    assert sbc.SIDE["Krittika"] == "east" and sbc.SIDE["Magha"] == "south"
    assert sbc.SIDE["Anuradha"] == "west" and sbc.SIDE["Dhanishta"] == "north"


def test_sbc_krittika_worked_lines():
    # Rath: hind Bharaṇī; fore a, Taurus, Nandā, Bhadrā, Libra, ta, Viśākhā;
    # across Śravaṇa.
    assert _names("Krittika", "hind") == ["Bharani"]
    assert _names("Krittika", "fore") == ["a", "Taurus", "Nanda", "Bhadra",
                                         "Libra", "ta", "Vishakha"]
    assert sbc.vedha_lines("Krittika")["across"]["lands"] == "Shravana"


def test_sbc_rohini_and_mrigashira_worked_lines():
    # Rohiṇī: u, Aśvinī, va, Gemini, au, Virgo, ra, Svātī and Abhijit.
    assert _names("Rohini", "hind") == ["u", "Ashwini"]
    assert _names("Rohini", "fore") == ["va", "Gemini", "au", "Virgo", "ra", "Swati"]
    assert sbc.vedha_lines("Rohini")["across"]["lands"] == "Abhijit"
    # Mṛgaśirā: Cancer, ka, Leo, pa, Citrā, Revatī, la, a, Uttarāṣāḍhā.
    assert _names("Mrigashira", "fore") == ["ka", "Cancer", "Leo", "pa", "Chitra"]
    assert _names("Mrigashira", "hind") == ["a", "la", "Revati"]
    assert sbc.vedha_lines("Mrigashira")["across"]["lands"] == "Uttara Ashadha"


def test_sbc_punarvasu_worked_lines():
    # Hind: Pūrva Bhādrapadā, da, ka, Aries…; fore: Uttara Phalgunī, ḍa, ma;
    # across: Mūla, ha, au, aṁ, ya, Cancer, Scorpio, Bhadrā (Mon, Wed).
    hind = _names("Punarvasu", "hind")
    assert hind[-1] == "Purva Bhadrapada" and {"da", "ka", "Aries"} <= set(hind)
    assert _names("Punarvasu", "fore") == ["dda", "ma", "Uttara Phalguni"]
    across = sbc.vedha_lines("Punarvasu")["across"]
    assert [x["name"] for x in across["content"]] == ["ha", "Cancer", "au", "Bhadra",
                                                       "am", "Scorpio", "ya", "Mula"]
    bhadra = [x for x in across["content"] if x["name"] == "Bhadra"][0]
    assert bhadra["weekdays"] == ["Monday", "Wednesday"]


def test_sbc_central_nakshatras_across_syllables():
    # Ārdrā, Hastā, P.Āṣāḍhā, U.Bhādrapadā: across vedha on ka, pa, bha, da,
    # each with its attached triplet.
    first = {n: sbc.vedha_lines(n)["across"]["content"][0]
             for n in ("Ardra", "Hasta", "Purva Ashadha", "Uttara Bhadrapada")}
    assert {n: c["name"] for n, c in first.items()} == {
        "Ardra": "ka", "Hasta": "pa", "Purva Ashadha": "bha", "Uttara Bhadrapada": "da"}
    assert first["Ardra"]["attached"] == ["gha", "nga", "cha"]
    assert sbc.syllables_hit([first["Ardra"]]) >= {"ka", "gha", "nga", "cha"}


def test_sbc_lines_are_reciprocal():
    for n in sbc.CELLS:
        lines = sbc.vedha_lines(n)
        assert sbc.vedha_lines(lines["across"]["lands"])["across"]["lands"] == n
        assert sbc.vedha_lines(lines["fore"]["lands"])["hind"]["lands"] == n


def test_sbc_corner_rule():
    k = sbc.corner_trigger(2 * (360 / 27) + 1.0)          # Kṛttikā pada 1
    assert k["corner"] == "NE" and k["activated"] == ["a", "Purna"]
    assert sbc.corner_trigger(2 * (360 / 27) - 1.0)["corner"] == "NE"   # Bharaṇī p4
    assert sbc.corner_trigger(2 * (360 / 27) + 5.0) is None            # Kṛttikā p2
    assert sbc.corner_trigger(9 * (360 / 27) + 1.0)["corner"] == "SE"  # Maghā p1


def test_sbc_abhijit_span():
    assert sbc.nakshatra_28(277.0) == "Abhijit"
    assert sbc.nakshatra_28(276.5) == "Uttara Ashadha"
    assert sbc.nakshatra_28(281.0) == "Shravana"
    assert sbc.nakshatra_28(0.5) == "Ashwini"
    assert sbc.nakshatra_28(359.9) == "Revati"


def test_sbc_motion_and_predominant_line():
    assert sbc.motion_class(P.RAHU, -0.05) == "vakri"
    assert sbc.motion_class(P.JUPITER, 0.2) == "shighra"
    assert sbc.motion_class(P.SATURN, 0.01) == "madhya"
    assert sbc.predominant_line(P.KETU, "vakri") == "hind"
    assert sbc.predominant_line(P.SUN, "madhya") == "fore"
    assert sbc.predominant_line(P.MARS, "vakri") == "hind"
    assert sbc.predominant_line(P.MARS, "shighra") == "fore"
    assert sbc.predominant_line(P.MARS, "madhya") == "across"
    assert [sbc.tithi_group(n) for n in (1, 5, 6, 15, 16, 30)] == [
        "Nanda", "Purna", "Nanda", "Purna", "Nanda", "Purna"]


def test_transit_sarvatobhadra_contract(tr):
    r = tr.sarvatobhadra(START)
    assert r["janma"]["nakshatra"] == sbc.nakshatra_28(tr.chart.longitudes[P.MOON])
    for p, d in r["planets"].items():
        assert d["nakshatra"] == sbc.nakshatra_28(tr.positions(START, [p])[p])
        assert set(d["lands"]) == {"across", "fore", "hind"}
        assert d["predominant"] == sbc.predominant_line(p, d["motion"])
        for line, labels in d["hits"].items():
            key = "across" if line == "across_boxes" else line
            for lab in labels:
                if lab == "janma_nakshatra":
                    assert r["janma"]["nakshatra"] in d["boxes"][key]
                elif lab.endswith("_nakshatra"):
                    q = P(lab[: -len("_nakshatra")])
                    assert r["natal_nakshatras"][q] in d["boxes"][key]
