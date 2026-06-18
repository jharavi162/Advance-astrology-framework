# Advance Astrology Framework

A comprehensive Python astrology engine built on the
[Skyfield](https://rhodesmill.org/skyfield/) / JPL ephemeris. It computes charts
for **both** the Western tropical and the Vedic sidereal systems from a single,
accurate astronomical core.

- 🪐 **Planetary positions** — Sun through Pluto plus the mean lunar nodes
  (Rahu/Ketu), with retrograde detection, from the JPL DE-series ephemeris.
- 🏠 **House systems** — Placidus, Koch-style Porphyry, Whole Sign, Equal and
  Regiomontanus, plus Ascendant, Midheaven, Descendant, IC and Vertex.
- 🔗 **Aspects** — major and minor, configurable orbs, applying/separating.
- 🕉️ **Vedic / Jyotish (full suite)** — see below.
- 🏛️ **Western (traditional & modern)** — Arabic Parts / Lots, essential
  dignities + almuten, declinations, antiscia, parallels, midpoints, harmonics.
- 🎯 **Accurate & self-contained** — ships with the `de421` ephemeris
  (1899–2053); no network access required at runtime. 86 tests.

## Vedic (Jyotish) capabilities

| Area | What's included |
| --- | --- |
| **Divisional charts** | All 16 Shodasavarga (D1, D2, D3, D4, D7, D9, D10, D12, D16, D20, D24, D27, D30, D40, D45, D60) + Vimshopaka bala |
| **Dasha systems** | Vimshottari, Ashtottari, Yogini, Kalachakra, and Jaimini Chara dasha — all with sub-periods |
| **Jaimini** | Chara Karakas (7/8 scheme), Karakamsha, Argala, Chara dasha |
| **Arudhas** | Arudha Lagna, all bhava arudhas (A1–A12), Upapada |
| **Ashtakavarga** | Bhinnashtakavarga (BAV) + Sarvashtakavarga (SAV) |
| **Dignities** | Exalt/debilitation/moolatrikona/own + natural, temporal & compound relationships |
| **Aspects** | Graha drishti (special aspects) + Rashi drishti |
| **Panchanga** | Tithi, Vara, Nakshatra, Yoga, Karana + planetary hora |
| **Lagnas** | Bhava, Hora, Ghati, Sree, Indu special ascendants |
| **Upagrahas** | Dhuma, Vyatipata, Parivesha, Indrachapa, Upaketu + Gulika/Mandi |
| **Yogas** | Pancha Mahapurusha, Gajakesari, Sunapha/Anapha/Durudhara/Kemadruma, Raja, Viparita Raja, Dhana, Kala Sarpa, … |
| **Avasthas** | Baladi, Jagradadi, Deeptadi states |
| **Compatibility** | Full Ashtakoota / 36-point Guna Milan |

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

`VedicChart` is the high-level Jyotish entry point — a sidereal chart with the
full toolkit attached:

```python
from datetime import datetime
from zoneinfo import ZoneInfo
from advance_astrology import VedicChart

v = VedicChart.create(
    when=datetime(1990, 5, 15, 14, 30, tzinfo=ZoneInfo("America/New_York")),
    latitude=40.7128, longitude=-74.0060, ayanamsa="lahiri",
)
print(v.summary())

# Divisional charts
print(v.navamsha)                 # D9
print(v.varga(10))                # any Dn

# Dashas (any system) and the active chain on a date
for maha in v.dasha("vimshottari", levels=1):
    print(maha)
print(v.current_dasha("yogini"))
print(v.chara_dasha())            # Jaimini sign dasha

# Jaimini, arudhas, ashtakavarga
print(v.chara_karakas())          # AK..DK
print(v.arudhas())                # A1..A12, AL, UL
print(v.sarvashtakavarga())       # 12 sign bindus (sum 337)

# Panchanga, yogas, compatibility
print(v.panchanga())
for y in v.yogas():
    print(y)

other = VedicChart.create(when=..., latitude=..., longitude=...)
print(VedicChart.compatibility(v, other))   # 36-point Guna Milan
```

Nakshatra and sidereal calculations are also available from a tropical
`NatalChart` (each placement exposes `.sidereal_longitude` and `.nakshatra`),
and any sidereal `NatalChart` can be promoted with `chart.to_vedic()`.

## Western traditional techniques

```python
chart = NatalChart.create(when=when, latitude=lat, longitude=lon,
                          house_system="regiomontanus")

print(chart.is_day_chart)
print(chart.lots())                      # Part of Fortune, Spirit, Eros, ...
print(chart.declinations())              # for parallels / contra-parallels
print(chart.essential_dignity(Planet.MARS).almuten())

from advance_astrology.western import declination, midpoints
print(declination.antiscion(chart.get(Planet.SUN).longitude))
print(midpoints.harmonic_chart({Planet.SUN: 40.0}, 9))
```

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
python examples/basic_chart.py     # Western + intro Vedic
python examples/vedic_chart.py      # full Jyotish workup
pytest                              # 86 tests
```

## Roadmap

The core is comprehensive. Natural next additions (and a home for the
calculations in your astrology playbook):

- Shadbala (six-fold strength) and Bhava bala
- Conditional/Sama nakshatra dashas (Shatabdika, Chaturashiti, …)
- Transits (gochara), progressions, solar/lunar returns and synastry
- KP sub-lords and significators
- True lunar node and additional bodies (Chiron, asteroids)

## License

MIT
