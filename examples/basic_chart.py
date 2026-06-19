"""Worked example: compute a Western and a Vedic chart for the same birth.

Run from the repository root:

    python examples/basic_chart.py
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from advance_astrology import NatalChart, Planet, to_zodiac

# Birth data ---------------------------------------------------------------- #
WHEN = datetime(1990, 5, 15, 14, 30, tzinfo=ZoneInfo("America/New_York"))
LAT, LON = 40.7128, -74.0060  # New York City


def western():
    print("=" * 60)
    print("WESTERN TROPICAL CHART (Placidus houses)")
    print("=" * 60)
    chart = NatalChart.create(
        when=WHEN, latitude=LAT, longitude=LON, name="Example Native",
        zodiac="tropical", house_system="placidus",
    )
    print(chart.summary())

    print("\nHouse cusps:")
    for h in range(1, 13):
        print(f"  House {h:>2}: {to_zodiac(chart.cusps[h])}")

    print("\nMajor aspects:")
    for a in chart.aspects(
        only=["Conjunction", "Opposition", "Trine", "Square", "Sextile"]
    ):
        print(f"  {a}")

    print("\nElement balance:", chart.element_balance())
    print("Modality balance:", chart.modality_balance())


def vedic():
    print("\n" + "=" * 60)
    print("VEDIC SIDEREAL CHART (Lahiri ayanamsa, whole-sign houses)")
    print("=" * 60)
    chart = NatalChart.create(
        when=WHEN, latitude=LAT, longitude=LON, name="Example Native",
        zodiac="sidereal", house_system="whole_sign", ayanamsa="lahiri",
    )
    print(chart.summary())

    moon = chart.get(Planet.MOON)
    print(f"\nMoon nakshatra: {moon.nakshatra}")

    print("\nVimshottari Mahadashas:")
    for d in chart.vimshottari_dasha(levels=1):
        print(f"  {d}")

    print("\nActive dasha chain today:")
    for d in chart.current_dasha(datetime.now(timezone.utc)):
        level = {1: "Mahadasha", 2: "Antardasha", 3: "Pratyantardasha"}[d.level]
        print(f"  {level:>16}: {d}")


if __name__ == "__main__":
    western()
    vedic()
