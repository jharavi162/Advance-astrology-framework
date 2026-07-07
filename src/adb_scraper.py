#!/usr/bin/env python3
"""Astro-Databank scraper — Phase 1 of the marriage-timing research pipeline.

Collects entries from the Astro-Databank wiki (astro.com/astro-databank)
category "Relationship : Marriage date", keeping only Rodden Rating AA/A
charts with a known birth time, and writes the raw rows to CSV
(data/raw/adb_marriage_raw.csv). Raw page HTML is cached under
data/raw/html/ so nothing scraped is ever lost or re-fetched.

Usage:
    python src/adb_scraper.py --samples 5          # fetch + print 5 samples, no batch
    python src/adb_scraper.py --limit 200          # full pilot batch
    python src/adb_scraper.py --category "Marriage_date" --limit 200

Etiquette: one request every ~2.5 s. On HTTP 403/429 (or a captcha page)
the scraper aborts immediately and tells you — it never hammers the site.

All parsing lives in pure functions (parse_*) that are unit-tested offline
in tests/test_adb_scraper_parsers.py.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import random
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = "https://www.astro.com"
WIKI = f"{BASE}/astro-databank"
API = f"{WIKI}/api.php"
# The on-page category is "Relationship : Marriage date"; MediaWiki page title
# uses underscores. If the exact title differs, pass --category.
DEFAULT_CATEGORY = "Relationship_:_Marriage_date"

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw"
HTML_CACHE = RAW_DIR / "html"
RAW_CSV = RAW_DIR / "adb_marriage_raw.csv"

USER_AGENT = (
    "vedic-marriage-research/0.1 (academic astrology research; "
    "contact: jharavi162@gmail.com; respects robots + rate limits)"
)
RATE_SECONDS = 2.5

MONTHS = {m.lower(): i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], start=1)}


class BlockedError(RuntimeError):
    """Raised when the site refuses us (403/429/captcha) — stop, don't retry."""


@dataclass
class AdbEntry:
    adb_id: str                 # wiki page title, stable identifier
    name: str = ""
    gender: str = ""            # M / F / '' if not stated
    birth_date: str = ""        # ISO yyyy-mm-dd
    birth_time: str = ""        # HH:MM (local civil time as recorded)
    place: str = ""
    lat: float | None = None
    lon: float | None = None
    tz_offset_hours: float | None = None   # UTC offset in hours (east +)
    tz_note: str = ""           # raw timezone string from the page
    rodden: str = ""
    marriage_dates: list[str] = field(default_factory=list)   # ISO day-precision
    marriage_events_raw: list[str] = field(default_factory=list)
    source_url: str = ""
    scraped_at: str = ""


# --------------------------------------------------------------------------
# Pure parsers (offline-testable)
# --------------------------------------------------------------------------

def parse_coord(token: str) -> float | None:
    """'37n52' -> 37.8667; '122w16' -> -122.2667; '2e20' -> 2.3333.

    ADB writes degrees + minutes (minutes may carry a decimal, e.g. 48n51.5).
    """
    m = re.fullmatch(r"\s*(\d{1,3})([nsewNSEW])(\d{1,2}(?:\.\d+)?)?\s*", token)
    if not m:
        return None
    deg = int(m.group(1))
    hemi = m.group(2).lower()
    mins = float(m.group(3)) if m.group(3) else 0.0
    val = deg + mins / 60.0
    if hemi in ("s", "w"):
        val = -val
    return round(val, 6)


def parse_place(text: str) -> tuple[str, float | None, float | None]:
    """'Berkeley, California, 37n52, 122w16' -> (place, lat, lon)."""
    parts = [p.strip() for p in text.split(",")]
    lat = lon = None
    place_parts = []
    for p in parts:
        c = parse_coord(p)
        if c is None:
            place_parts.append(p)
        elif re.search(r"[nsNS]", p):
            lat = c
        else:
            lon = c
    return ", ".join(place_parts), lat, lon


def parse_timezone(text: str) -> tuple[float | None, str]:
    """'PDT h7w (is daylight saving time)' -> (-7.0, raw); 'IST h5:30e' -> (+5.5, raw).

    ADB encodes the actual UTC offset in force at birth as hH[:MM][e|w],
    so no historical-timezone database is needed.
    """
    raw = " ".join(text.split())
    m = re.search(r"h(\d{1,2})(?::(\d{2}))?\s*([ew])", raw, re.IGNORECASE)
    if not m:
        # LMT entries look like 'LMT m77w03 (is local mean time)' — offset from longitude
        lm = re.search(r"m(\d{1,3})([ew])(\d{2})?", raw, re.IGNORECASE)
        if lm:
            deg = int(lm.group(1)) + (int(lm.group(3)) if lm.group(3) else 0) / 60.0
            off = deg / 15.0
            if lm.group(2).lower() == "w":
                off = -off
            return round(off, 4), raw
        return None, raw
    off = int(m.group(1)) + (int(m.group(2)) if m.group(2) else 0) / 60.0
    if m.group(3).lower() == "w":
        off = -off
    return round(off, 4), raw


def parse_birth_datetime(text: str) -> tuple[str, str]:
    """'15 August 1972 at 02:53 (= 02:53 AM)' -> ('1972-08-15', '02:53').

    Returns ('','') when unparseable; time '' when no birth time is given.
    """
    raw = " ".join(text.split())
    m = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{3,4})", raw)
    if not m:
        return "", ""
    month = MONTHS.get(m.group(2).lower())
    if not month:
        return "", ""
    date_iso = f"{int(m.group(3)):04d}-{month:02d}-{int(m.group(1)):02d}"
    tm = re.search(r"at\s+(\d{1,2}):(\d{2})", raw)
    time_s = f"{int(tm.group(1)):02d}:{tm.group(2)}" if tm else ""
    return date_iso, time_s


def parse_rodden(text: str) -> str:
    """'Quoted BC/BR, Rodden Rating AA' -> 'AA'."""
    m = re.search(r"Rodden\s+Rating\s+(AA|A|B|C|DD|X|XX)\b", text, re.IGNORECASE)
    return m.group(1).upper() if m else ""


def parse_event_date(raw: str) -> str:
    """Extract a day-precision ISO date from an event line, else ''.

    'Relationship : Marriage 29 June 2005 (Jennifer Garner)' -> '2005-06-29'
    'Relationship : Marriage 1975' -> ''  (year-only: not usable for timing)
    """
    m = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", raw)
    if not m:
        return ""
    month = MONTHS.get(m.group(2).lower())
    if not month:
        return ""
    try:
        return dt.date(int(m.group(3)), month, int(m.group(1))).isoformat()
    except ValueError:
        return ""


MARRIAGE_EVENT_RE = re.compile(r"relationship\s*:\s*marriage(?!\s*end)", re.IGNORECASE)


def parse_person_page(html: str, adb_id: str) -> AdbEntry:
    """Parse one ADB person page into an AdbEntry (missing fields left blank)."""
    soup = BeautifulSoup(html, "lxml")
    e = AdbEntry(adb_id=adb_id, source_url=f"{WIKI}/{adb_id}")

    h1 = soup.find(id="firstHeading")
    if h1:
        e.name = h1.get_text(" ", strip=True)

    # The birth-data block is a table/dl of "label: value" rows near the top.
    def row_value(label: str) -> str:
        node = soup.find(string=re.compile(rf"^\s*{label}\s*$", re.IGNORECASE))
        if node:
            # value usually lives in the next table cell / sibling element
            cell = node.find_parent(["th", "td", "dt"])
            if cell:
                nxt = cell.find_next_sibling(["td", "dd"])
                if nxt:
                    return nxt.get_text(" ", strip=True)
        # fallback: 'label: value' inside one element
        node = soup.find(string=re.compile(rf"{label}\s*:", re.IGNORECASE))
        if node:
            return re.sub(rf".*?{label}\s*:\s*", "", str(node), flags=re.IGNORECASE).strip()
        return ""

    gender = row_value("Gender")
    if gender:
        e.gender = gender.strip()[:1].upper()

    born = row_value("born on")
    e.birth_date, e.birth_time = parse_birth_datetime(born)

    place = row_value("Place")
    if place:
        e.place, e.lat, e.lon = parse_place(place)

    tz = row_value("Timezone")
    if tz:
        e.tz_offset_hours, e.tz_note = parse_timezone(tz)

    e.rodden = parse_rodden(row_value("Data source") or soup.get_text(" ", strip=True)[:4000])

    # Events section: list items mentioning 'Relationship : Marriage'
    for li in soup.find_all("li"):
        txt = li.get_text(" ", strip=True)
        if MARRIAGE_EVENT_RE.search(txt):
            e.marriage_events_raw.append(txt)
            d = parse_event_date(txt)
            if d and d not in e.marriage_dates:
                e.marriage_dates.append(d)
    return e


def entry_ok(e: AdbEntry) -> tuple[bool, str]:
    """Study inclusion filter: AA/A, timed birth, geo-resolved, day-precision marriage."""
    if e.rodden not in ("AA", "A"):
        return False, f"rodden={e.rodden or 'missing'}"
    if not e.birth_date or not e.birth_time:
        return False, "no timed birth"
    if e.lat is None or e.lon is None or e.tz_offset_hours is None:
        return False, "unresolved place/timezone"
    if not e.marriage_dates:
        return False, "no day-precision marriage date"
    return True, ""


# --------------------------------------------------------------------------
# HTTP layer
# --------------------------------------------------------------------------

class AdbClient:
    def __init__(self, rate: float = RATE_SECONDS):
        self.sess = requests.Session()
        self.sess.headers["User-Agent"] = USER_AGENT
        self.rate = rate
        self._last = 0.0

    def _throttle(self):
        wait = self.rate + random.uniform(0, 0.5) - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.monotonic()

    def get(self, url: str, **kw) -> requests.Response:
        self._throttle()
        r = self.sess.get(url, timeout=30, **kw)
        if r.status_code in (403, 429):
            raise BlockedError(
                f"HTTP {r.status_code} from {url} — the site is refusing us. "
                "Stopping as instructed; do not retry without checking with the user.")
        r.raise_for_status()
        if "captcha" in r.text[:2000].lower():
            raise BlockedError(f"Captcha page served at {url} — stopping.")
        return r

    def category_members(self, category: str) -> list[str]:
        """All page titles in a category, via the MediaWiki API (paginated),
        falling back to HTML category pages if the API is closed."""
        titles: list[str] = []
        cont: dict = {}
        try:
            while True:
                params = {"action": "query", "list": "categorymembers",
                          "cmtitle": f"Category:{category}", "cmlimit": "500",
                          "cmtype": "page", "format": "json", **cont}
                data = self.get(API, params=params).json()
                titles += [m["title"] for m in
                           data.get("query", {}).get("categorymembers", [])]
                cont = data.get("continue") or {}
                if not cont:
                    return titles
        except BlockedError:
            raise
        except Exception as exc:                       # API closed → HTML fallback
            print(f"  [api unavailable: {exc!r} — falling back to HTML category pages]")
        url: str | None = f"{WIKI}/Category:{category}"
        titles = []
        while url:
            soup = BeautifulSoup(self.get(url).text, "lxml")
            body = soup.find(id="mw-pages") or soup
            for a in body.find_all("a", href=re.compile(r"^/astro-databank/")):
                href = a["href"].split("/astro-databank/", 1)[1]
                if not href.startswith(("Category:", "Special:", "Help:", "index.php")):
                    titles.append(href)
            nxt = body.find("a", string=re.compile(r"next\s*(page|200)", re.IGNORECASE))
            url = BASE + nxt["href"] if nxt and nxt.has_attr("href") else None
        return list(dict.fromkeys(titles))

    def person_html(self, title: str) -> str:
        cache = HTML_CACHE / (re.sub(r"[^A-Za-z0-9_,().-]", "_", title) + ".html")
        if cache.exists():
            return cache.read_text(encoding="utf-8")
        html = self.get(f"{WIKI}/{title.replace(' ', '_')}").text
        HTML_CACHE.mkdir(parents=True, exist_ok=True)
        cache.write_text(html, encoding="utf-8")
        return html


# --------------------------------------------------------------------------
# CSV output — raw data is append-only, never overwritten
# --------------------------------------------------------------------------

CSV_FIELDS = ["adb_id", "name", "gender", "birth_date", "birth_time", "place",
              "lat", "lon", "tz_offset_hours", "tz_note", "rodden",
              "marriage_dates", "marriage_events_raw", "source_url", "scraped_at"]


def append_rows(entries: list[AdbEntry], path: Path = RAW_CSV):
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    seen = set()
    if not new:
        with path.open(newline="", encoding="utf-8") as f:
            seen = {row["adb_id"] for row in csv.DictReader(f)}
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if new:
            w.writeheader()
        for e in entries:
            if e.adb_id in seen:
                continue
            row = asdict(e)
            row["marriage_dates"] = ";".join(e.marriage_dates)
            row["marriage_events_raw"] = " | ".join(e.marriage_events_raw)
            w.writerow(row)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--category", default=DEFAULT_CATEGORY)
    ap.add_argument("--limit", type=int, default=200,
                    help="max accepted entries to collect (pilot: 150-200)")
    ap.add_argument("--samples", type=int, default=0,
                    help="fetch only N accepted entries and print them (review mode)")
    args = ap.parse_args(argv)

    client = AdbClient()
    print(f"Listing category '{args.category}' …")
    try:
        titles = client.category_members(args.category)
    except BlockedError as exc:
        print(f"\nBLOCKED: {exc}", file=sys.stderr)
        return 2
    except requests.RequestException as exc:
        print(f"\nNETWORK FAILURE reaching astro.com: {exc}\n"
              "If running in a sandboxed environment, check that the network "
              "policy allows www.astro.com.", file=sys.stderr)
        return 3
    print(f"  {len(titles)} pages in category")
    if not titles:
        print("Category empty/not found — check the exact category title on the wiki.",
              file=sys.stderr)
        return 1

    target = args.samples or args.limit
    accepted: list[AdbEntry] = []
    rejected: dict[str, int] = {}
    try:
        for i, title in enumerate(titles):
            if len(accepted) >= target:
                break
            adb_id = title.replace(" ", "_")
            try:
                entry = parse_person_page(client.person_html(adb_id), adb_id)
            except BlockedError:
                raise
            except Exception as exc:
                rejected["fetch/parse error"] = rejected.get("fetch/parse error", 0) + 1
                print(f"  [{i+1}] {adb_id}: ERROR {exc!r}")
                continue
            entry.scraped_at = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
            ok, why = entry_ok(entry)
            if ok:
                accepted.append(entry)
                print(f"  [{i+1}] + {entry.name} ({entry.rodden}) "
                      f"marriages={entry.marriage_dates}")
            else:
                rejected[why] = rejected.get(why, 0) + 1
    except BlockedError as exc:
        print(f"\nBLOCKED mid-run: {exc}", file=sys.stderr)
        append_rows(accepted)   # keep what we have — raw data is never lost
        print(f"Saved {len(accepted)} entries collected before the block.")
        return 2

    append_rows(accepted)
    print(f"\nAccepted {len(accepted)} entries → {RAW_CSV}")
    if rejected:
        print("Rejected:", json.dumps(rejected, indent=2))
    if args.samples:
        print("\n===== SAMPLE ENTRIES FOR REVIEW =====")
        for e in accepted:
            print(json.dumps(asdict(e), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
