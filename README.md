# Advance Astrology Framework

A Python astrology engine built on the [Skyfield](https://rhodesmill.org/skyfield/)
/ JPL ephemeris. It computes natal charts for **both** the Western tropical and
the Vedic sidereal systems from a single, accurate astronomical core.

- 🪐 **Planetary positions** — Sun through Pluto plus the mean lunar nodes
  (Rahu/Ketu), with retrograde detection, from the JPL DE-series ephemeris.
- 🏠 **House systems** — Placidus, Whole Sign, Equal, Porphyry, plus Ascendant,
  Midheaven, Descendant, IC and Vertex.
- 🔗 **Aspects** — major and minor, with configurable orbs and applying/separating
  detection.
- 🕉️ **Vedic / sidereal** — Lahiri, Raman, KP, Fagan/Bradley and other ayanamsas,
  nakshatras with padas, and the full **Vimshottari dasha** timeline.
- 🎯 **Accurate & self-contained** — ships with the `de421` ephemeris
  (1899–2053); no network access required at runtime.

## Installation

```bash
pip install -e .
# or just the runtime dependencies:
pip install -r requirements.txt
```

Python 3.10+ is required.

## Quick start

```python
from datetime import datetime
from zoneinfo import ZoneInfo
from advance_astrology import NatalChart, Planet

chart = NatalChart.create(
    when=datetime(1990, 5, 15, 14, 30, tzinfo=ZoneInfo("America/New_York")),
    latitude=40.7128,
    longitude=-74.0060,         # east positive, west negative
    name="Example Native",
    zodiac="tropical",          # or "sidereal"
    house_system="placidus",    # placidus | whole_sign | equal | porphyry
)

print(chart.summary())

sun = chart.get(Planet.SUN)
print(sun.sign, sun.position.dms, "house", sun.house)

for aspect in chart.aspects(only=["Conjunction", "Trine", "Square"]):
    print(aspect)
```

> **Birth times must be timezone-aware.** Pass a `tzinfo` (e.g. via `zoneinfo`)
> so the UTC instant is unambiguous — naive datetimes are rejected.

## Vedic astrology

```python
chart = NatalChart.create(
    when=when, latitude=lat, longitude=lon,
    zodiac="sidereal", house_system="whole_sign", ayanamsa="lahiri",
)

moon = chart.get(Planet.MOON)
print(moon.nakshatra)                       # e.g. "Uttara Ashadha (pada 4, lord Sun)"

# Vimshottari dasha
for maha in chart.vimshottari_dasha(levels=1):
    print(maha)

# Active period chain on a date (mahadasha → antardasha → pratyantardasha)
for period in chart.current_dasha():
    print(period.level, period)
```

Nakshatra and dasha calculations are always available — even on a tropical
chart — because they are derived from each body's sidereal longitude.

## Architecture

| Module | Responsibility |
| --- | --- |
| `ephemeris.py` | Skyfield/JPL wrapper: positions, speeds, sidereal time, obliquity, lunar node |
| `angles.py` | Angle math and sign/degree/DMS conversion |
| `ayanamsa.py` | Sidereal offset models (Lahiri, Raman, KP, Fagan/Bradley, …) |
| `houses.py` | Ascendant/MC, Placidus, Whole Sign, Equal, Porphyry cusps |
| `aspects.py` | Aspect detection with orbs and applying/separating logic |
| `nakshatra.py` | 27 lunar mansions and padas |
| `dasha.py` | Vimshottari dasha timeline and lookup |
| `chart.py` | `NatalChart` — orchestrates everything |
| `constants.py` | Signs, planets, aspects, nakshatras, rulerships |

## Ephemeris coverage

The bundled `de421` kernel covers **1899-07-28 to 2053-10-08**. For dates
outside that range, download a wider kernel and point the engine at it:

```bash
python scripts/download_ephemeris.py de440s.bsp     # 1849-2150
export ASTRO_EPHEMERIS=$(pwd)/advance_astrology/data/de440s.bsp
```

Or pass it explicitly:

```python
from advance_astrology import Ephemeris, NatalChart
eph = Ephemeris(bsp_path="/path/to/de440.bsp")
chart = NatalChart.create(..., ephemeris=eph)
```

## Examples & tests

```bash
python examples/basic_chart.py
pytest
```

## Roadmap

This is the foundation. Planned additions (and a natural home for the
calculations in your astrology playbook):

- Divisional charts (vargas: D9 Navamsha, D10, …)
- Additional dasha systems (Ashtottari, Yogini)
- Transits, progressions and synastry
- Planetary dignities, combustion, retrograde periods
- True lunar node and additional bodies (Chiron, asteroids)

## License

MIT
