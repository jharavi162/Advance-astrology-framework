# Vedic Marriage-Timing Research Pipeline

Research dataset: verified birth charts with known marriage dates → full Vedic
astrological data computed by **this repo's engine** (`advance_astrology/`, single
calculation door `advance_astrology/vedic/chart.py`) → Excel workbook for
pattern analysis. **No planetary number is ever LLM-estimated** — everything
comes from the engine's deterministic computation.

## Repo layout

```
data/raw/          scraped CSVs + cached page HTML  (append-only, never overwritten)
data/processed/    final .xlsx workbook
src/               pipeline modules (scraper, chart batch, excel builder)
docs/              this file + schema documentation
```

## Phase 1 — Data collection (Astro-Databank)

- Source: https://www.astro.com/astro-databank, category **"Relationship : Marriage date"**.
- Inclusion filter: **Rodden Rating AA or A only**, timed birth, resolvable
  place (ADB pages carry lat/long and the historical UTC offset directly —
  no external geocoding or tz database needed), and at least one
  **day-precision** marriage date.
- Etiquette: 2.5 s + jitter between requests; identifiable User-Agent; aborts
  immediately on HTTP 403/429 or a captcha (never hammers the site). Fetched
  HTML is cached under `data/raw/html/` so a re-run never re-downloads.

Run:

```bash
pip install -r requirements-research.txt
python src/adb_scraper.py --samples 5     # review 5 entries first
python src/adb_scraper.py --limit 200     # pilot batch → data/raw/adb_marriage_raw.csv
```

The raw CSV is **append-only** (deduped by `adb_id`); it is committed to git as
the permanent raw record.

### Raw CSV columns

| column | meaning |
|---|---|
| `adb_id` | ADB wiki page title (stable ID; `source_url` reconstructs the page) |
| `name`, `gender` | as recorded on ADB (`M`/`F`) |
| `birth_date`, `birth_time` | local civil date `YYYY-MM-DD` and `HH:MM` as recorded |
| `place`, `lat`, `lon` | birthplace; decimal degrees (N/E positive) parsed from ADB's `40n45, 73w59` notation |
| `tz_offset_hours`, `tz_note` | UTC offset **in force at birth** (ADB's `h5w` / `h5:30e` / LMT notation), plus the raw string |
| `rodden` | `AA` or `A` (others rejected) |
| `marriage_dates` | `;`-joined ISO day-precision marriage dates (year-only events excluded) |
| `marriage_events_raw` | the verbatim event lines, kept for audit |
| `scraped_at` | UTC timestamp |

Parser correctness is locked by `tests/test_adb_scraper_parsers.py`
(fabricated data only — no real natives in tests, preserving blind-test
integrity per CLAUDE.md).

### Environment note

The scraper needs outbound HTTPS to `www.astro.com`. In a sandboxed Claude
Code environment the network policy must allow that host, otherwise the
scraper exits with a clear NETWORK FAILURE message (exit code 3; exit code 2 =
site refused us / captcha — stop and review, do not retry).

## Phase 2 — Chart computation (planned)

Every accepted entry is fed through `VedicChart` (the engine's single
calculation door): UTC instant = local birth time − `tz_offset_hours`;
sidereal (Lahiri) positions, D9, Vimshottari daśās, transits for the marriage
date and a control date — exactly as the engine defines them. No new engine,
no pyswisseph.

## Phase 3 — Excel workbook (planned)

One workbook, 4 sheets linked by `chart_id`: **Charts** (natal), **Dashas**
(running at marriage), **Transits** (marriage date), **Control** (random
non-marriage date, age 21–40, ≥1 y from any marriage). Full column schema is
specified in the project brief and will be documented here as
`docs/SCHEMA.md` when the builder lands.

## Phase 4 — Validation report (planned)

Counts, failures, marriage-age distribution, sanity checks (e.g. % Venus
MD/AD). **No pattern analysis in the pipeline** — data quality only.
