"""Comprehensive Vedic (Jyotish) example.

Run from the repository root:

    python examples/vedic_chart.py
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from advance_astrology import VedicChart, to_zodiac
from advance_astrology.constants import SIGNS
from advance_astrology.vedic.jaimini import KARAKA_ABBR
from advance_astrology.vedic.vargas import SHODASHAVARGA, VARGA_NAMES

WHEN = datetime(1990, 5, 15, 14, 30, tzinfo=ZoneInfo("America/New_York"))
LAT, LON = 40.7128, -74.0060


def sign(idx_or_lon, is_longitude=False):
    return SIGNS[to_zodiac(idx_or_lon).sign_index] if is_longitude else SIGNS[idx_or_lon]


def main():
    v = VedicChart.create(when=WHEN, latitude=LAT, longitude=LON,
                          name="Example", ayanamsa="lahiri")

    print(v.summary())

    print("\n--- Panchanga ---")
    print(v.panchanga())

    print("\n--- Chara Karakas (Jaimini) ---")
    for name, planet in v.chara_karakas().items():
        print(f"  {KARAKA_ABBR[name]:>4} {name:<14} {planet.value}")
    print(f"  Karakamsha (AK in D9): {sign(v.karakamsha())}")

    print("\n--- Arudha Padas ---")
    ar = v.arudhas()
    print("  " + "  ".join(f"{k}:{sign(val)}" for k, val in
                           list(ar.items())[:12]))
    print(f"  Arudha Lagna: {sign(v.arudha_lagna())}")

    print("\n--- Shodasavarga (all 16 divisional ascendants) ---")
    for d in SHODASHAVARGA:
        vc = v.varga(d)
        print(f"  D{d:<2} {VARGA_NAMES[d]:<22} Asc: {sign(vc.ascendant_sign)}")

    print("\n--- Sarvashtakavarga (bindus per sign) ---")
    sav = v.sarvashtakavarga()
    print("  " + "  ".join(f"{s[:3]}:{b}" for s, b in zip(SIGNS, sav)))
    print(f"  Total: {sum(sav)}")

    print("\n--- Yogas ---")
    for y in v.yogas():
        print(f"  {y}")

    print("\n--- Dashas (current period chains) ---")
    now = datetime.now(timezone.utc)
    for system in ("vimshottari", "ashtottari", "yogini"):
        chain = v.current_dasha(system, now)
        crumbs = " > ".join(f"{d.lord.value}" for d in chain)
        print(f"  {system.capitalize():<12} {crumbs}")
    print("  Chara (Jaimini) mahadashas:")
    for d in v.chara_dasha()[:5]:
        print(f"    {d.note:<12} {d}")

    print("\n--- Special Lagnas & Upagrahas ---")
    for name, lon in v.special_lagnas().items():
        print(f"  {name.capitalize():<8} Lagna: {to_zodiac(lon)}")
    for name, lon in v.calculated_upagrahas().items():
        print(f"  {name:<12} {to_zodiac(lon)}")

    print("\n--- Compatibility (Guna Milan) with another chart ---")
    other = VedicChart.create(
        when=datetime(1992, 8, 21, 9, 15, tzinfo=ZoneInfo("Asia/Kolkata")),
        latitude=28.6139, longitude=77.2090,
    )
    print(VedicChart.compatibility(v, other))


if __name__ == "__main__":
    main()
