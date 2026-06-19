"""2024 life-events workup for a single nativity.

Builds the Vedic chart, walks the Vimshottari dasha chain across 2024, tracks
the slow movers (Saturn/Jupiter/Rahu-Ketu), Sade Sati, and degree-tight
transit conjunctions to natal points, then surfaces the standout window.

Run from the repository root:

    python examples/life_events_2024.py
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from advance_astrology import VedicChart, to_zodiac
from advance_astrology.constants import SIGNS, Planet
from advance_astrology.dasha import current_dasha
from advance_astrology.nakshatra import nakshatra_of

# --- Birth data ----------------------------------------------------------- #
TZ = ZoneInfo("Asia/Kolkata")
WHEN = datetime(1991, 4, 4, 6, 23, tzinfo=TZ)
LAT, LON = 23.6307, 85.5119          # Ramgarh, Jharkhand
NAME = "Native"

YEAR = 2024


def chain_str(chain):
    return " > ".join(d.lord.value for d in chain)


def main():
    v = VedicChart.create(when=WHEN, latitude=LAT, longitude=LON,
                          name=NAME, ayanamsa="lahiri")

    print("=" * 64)
    print(v.summary())

    moon_lon = v.longitudes[Planet.MOON]
    nak = nakshatra_of(moon_lon)
    print(f"\n  Janma Nakshatra: {nak.name} (pada {nak.pada}), "
          f"lord {nak.lord.value}")
    print(f"  Lagna lord house / Moon sign: {SIGNS[v.signs[Planet.MOON]]}")

    # --- Vimshottari across 2024 ----------------------------------------- #
    print("\n" + "=" * 64)
    print(f"VIMSHOTTARI DASHA THROUGH {YEAR}")
    periods = v.dasha("vimshottari", levels=3, cycles=1)

    # Active chain at the start of the year, and every change during the year.
    probe = datetime(YEAR, 1, 1, tzinfo=TZ)
    print(f"\n  On {YEAR}-01-01:  {chain_str(current_dasha(periods, probe))}")

    # Walk daily-ish to catch antardasha / pratyantardasha changes in 2024.
    start = datetime(YEAR, 1, 1, tzinfo=TZ)
    end = datetime(YEAR + 1, 1, 1, tzinfo=TZ)
    prev = None
    print("\n  Period changes during the year:")
    d = start
    while d < end:
        chain = current_dasha(periods, d)
        key = tuple(p.lord for p in chain)
        if key != prev:
            print(f"    {d:%Y-%m-%d}  {chain_str(chain)}")
            prev = key
        d += timedelta(days=1)

    # --- Slow movers + Sade Sati, sampled across the year ---------------- #
    print("\n" + "=" * 64)
    print("GOCHARA — slow movers & Sade Sati (sampled quarterly)")
    tr = v.transits()
    for m in (1, 4, 7, 10):
        when = datetime(YEAR, m, 15, tzinfo=TZ)
        ss = tr.sade_sati(when)
        sm = tr.slow_movers(when)
        print(f"\n  {when:%Y-%m}:  Sade Sati: "
              f"{'YES — ' + ss['phase'] if ss['active'] else 'no'} "
              f"(Saturn in {ss['saturn_sign']})")
        for p, info in sm.items():
            print(f"    {p.value:<8} {info['sign']:<12} "
                  f"H{info['house_from_lagna']} (lagna) / "
                  f"H{info['house_from_moon']} (moon)  SAV={info['sav']}")

    # --- Tight transit conjunctions to natal points --------------------- #
    print("\n" + "=" * 64)
    print("TIGHT TRANSIT HITS to natal points (Jupiter/Saturn/Rahu/Ketu, orb<=1.5)")
    movers = [Planet.JUPITER, Planet.SATURN, Planet.RAHU, Planet.KETU]
    d = start
    seen = set()
    while d < end:
        for hit in tr.conjunctions(d, orb=1.5, planets=movers):
            tag = (hit.transit, hit.natal)
            if tag not in seen:
                seen.add(tag)
                print(f"    ~{d:%Y-%m}  transit {hit.transit.value} "
                      f"conjunct natal {hit.natal.value}")
        d += timedelta(days=10)


if __name__ == "__main__":
    main()
