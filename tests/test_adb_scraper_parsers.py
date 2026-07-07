"""Offline unit tests for the ADB scraper's pure parsers (src/adb_scraper.py).

All sample data here is FABRICATED (no real natives) — these tests verify
parsing mechanics only, keeping blind-test integrity intact.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from adb_scraper import (  # noqa: E402
    AdbEntry, entry_ok, parse_birth_datetime, parse_coord, parse_event_date,
    parse_person_page, parse_place, parse_rodden, parse_timezone,
)


def test_parse_coord():
    assert parse_coord("37n52") == round(37 + 52 / 60, 6)
    assert parse_coord("122w16") == -round(122 + 16 / 60, 6)
    assert parse_coord("2e20") == round(2 + 20 / 60, 6)
    assert parse_coord("48n51.5") == round(48 + 51.5 / 60, 6)
    assert parse_coord("13s10") == -round(13 + 10 / 60, 6)
    assert parse_coord("Paris") is None


def test_parse_place():
    place, lat, lon = parse_place("Testville, Somewhere, 28n36, 77e12")
    assert place == "Testville, Somewhere"
    assert lat == round(28 + 36 / 60, 6)
    assert lon == round(77 + 12 / 60, 6)


def test_parse_timezone():
    assert parse_timezone("PDT h7w (is daylight saving time)")[0] == -7.0
    assert parse_timezone("IST h5:30e (is standard time)")[0] == 5.5
    assert parse_timezone("CET h1e")[0] == 1.0
    # Local mean time from longitude: 77°03'W → -(77.05/15) h
    off, _ = parse_timezone("LMT m77w03 (is local mean time)")
    assert abs(off - (-(77 + 3 / 60) / 15)) < 1e-3
    assert parse_timezone("garbage")[0] is None


def test_parse_birth_datetime():
    assert parse_birth_datetime("15 August 1972 at 02:53 (= 02:53 AM)") == \
        ("1972-08-15", "02:53")
    assert parse_birth_datetime("3 January 1950 at 23:10 (= 11:10 PM)") == \
        ("1950-01-03", "23:10")
    assert parse_birth_datetime("7 May 1960 (no time known)") == ("1960-05-07", "")
    assert parse_birth_datetime("nonsense") == ("", "")


def test_parse_rodden():
    assert parse_rodden("Quoted BC/BR, Rodden Rating AA") == "AA"
    assert parse_rodden("From memory, Rodden Rating A") == "A"
    assert parse_rodden("Rectified, Rodden Rating C") == "C"
    assert parse_rodden("no rating here") == ""


def test_parse_event_date():
    assert parse_event_date(
        "Relationship : Marriage 29 June 2005 (Some Spouse)") == "2005-06-29"
    assert parse_event_date("Relationship : Marriage 1975") == ""      # year-only
    assert parse_event_date("Relationship : Marriage 31 February 1980") == ""


SAMPLE_HTML = """
<html><body>
<h1 id="firstHeading">Doe, Jane</h1>
<table>
<tr><td>Name</td><td>Doe, Jane</td></tr>
<tr><td>Gender</td><td>F</td></tr>
<tr><td>born on</td><td>12 March 1955 at 06:45 (= 06:45 AM)</td></tr>
<tr><td>Place</td><td>Faketown, Nowhere, 40n45, 73w59</td></tr>
<tr><td>Timezone</td><td>EST h5w (is standard time)</td></tr>
<tr><td>Data source</td><td>Quoted BC/BR, Rodden Rating AA</td></tr>
</table>
<h2>Events</h2>
<ul>
<li>Relationship : Marriage 20 June 1980 (John Smith)</li>
<li>Relationship : Marriage end 1990</li>
<li>Relationship : Marriage 5 October 1995</li>
<li>Work : New job 1978</li>
</ul>
</body></html>
"""


def test_parse_person_page_full():
    e = parse_person_page(SAMPLE_HTML, "Doe,_Jane")
    assert e.name == "Doe, Jane"
    assert e.gender == "F"
    assert e.birth_date == "1955-03-12"
    assert e.birth_time == "06:45"
    assert e.place == "Faketown, Nowhere"
    assert e.lat == round(40 + 45 / 60, 6)
    assert e.lon == -round(73 + 59 / 60, 6)
    assert e.tz_offset_hours == -5.0
    assert e.rodden == "AA"
    assert e.marriage_dates == ["1980-06-20", "1995-10-05"]
    # 'Marriage end' must NOT be captured as a marriage
    assert not any("end" in d for d in e.marriage_dates)
    ok, why = entry_ok(e)
    assert ok, why


def test_entry_ok_filters():
    good = parse_person_page(SAMPLE_HTML, "Doe,_Jane")
    bad = AdbEntry(adb_id="x", rodden="C")
    assert entry_ok(good)[0]
    assert not entry_ok(bad)[0]
    no_time = parse_person_page(SAMPLE_HTML.replace(
        "12 March 1955 at 06:45 (= 06:45 AM)", "12 March 1955"), "y")
    assert not entry_ok(no_time)[0]
