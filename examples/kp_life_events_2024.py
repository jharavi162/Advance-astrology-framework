"""KP (Krishnamurti Paddhati) workup for 2024 events.

KP logic used here:
  * Cuspal sub-lord (CSL) of a house is the final arbiter of whether that
    matter fructifies, and which houses it signifies decide the outcome.
  * An event in the running Dasha/Bhukti/Antara fructifies when those lords are
    significators of the houses ruling the matter.
  * The sub-lord of a planet routes its results to the houses that sub-lord
    signifies (KP's "a planet gives the results of its sub-lord").

Run from the repository root:

    python examples/kp_life_events_2024.py
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from advance_astrology import VedicChart
from advance_astrology.constants import SIGNS, Planet
from advance_astrology.dasha import current_dasha
from advance_astrology.vedic.kp import kp_chain, ruling_planets

TZ = ZoneInfo("Asia/Kolkata")
WHEN = datetime(1991, 4, 4, 6, 23, tzinfo=TZ)
LAT, LON = 23.6307, 85.5119          # Ramgarh, Jharkhand
YEAR = 2024

# House groups for common life matters (KP).
MATTERS = {
    "Marriage / partner":   [2, 7, 11],
    "Career / job change":  [2, 6, 10, 11],
    "Wealth / gains":       [2, 6, 10, 11],
    "Property / vehicle":   [4, 11, 12],
    "Childbirth":           [2, 5, 11],
    "Foreign / relocation": [3, 9, 12],
}


def fmt(planet):
    return planet.value


def main():
    v = VedicChart.create(when=WHEN, latitude=LAT, longitude=LON,
                          name="Native", ayanamsa="kp")  # KP uses KP ayanamsa
    kp = v.kp_significators()

    print("=" * 70)
    print("KP CHART — ayanamsa: KP (Krishnamurti)")
    print(f"  Lagna: {SIGNS[v.ascendant_sign]}")

    # --- Cuspal sub-lords ------------------------------------------------ #
    print("\n--- Cuspal Sub-Lords (CSL) and what each cusp signifies ---")
    for h in range(1, 13):
        chain = kp_chain(kp.cusps[h])
        csl = chain.sub_lord
        sig = kp.planet_signifies(csl)
        print(f"  Cusp {h:>2}: CSL {csl.value:<8} "
              f"(star {chain.star_lord.value})  signifies houses {sig}")

    # --- Planet KP chains + significators -------------------------------- #
    print("\n--- Planet chains (sign/star/sub/sub-sub) + houses signified ---")
    for p in [Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
              Planet.JUPITER, Planet.VENUS, Planet.SATURN,
              Planet.RAHU, Planet.KETU]:
        ch = kp_chain(v.longitudes[p])
        sig = kp.planet_signifies(p)
        print(f"  {p.value:<8} {ch.sign_lord.value}/{ch.star_lord.value}/"
              f"{ch.sub_lord.value}/{ch.sub_sub_lord.value:<8}  "
              f"houses {sig}")

    # --- House significators for key matters ----------------------------- #
    print("\n--- House significators (KP strength order) ---")
    for h in (2, 4, 5, 7, 10, 11, 12):
        sigs = kp.house_significators(h)
        print(f"  House {h:>2}: " + ", ".join(s.value for s in sigs))

    # --- Ruling planets -------------------------------------------------- #
    print("\n--- Natal Ruling Planets ---")
    for k, p in ruling_planets(v).items():
        print(f"  {k:<16} {p.value}")

    # --- 2024 dasha chain via KP significators --------------------------- #
    print("\n" + "=" * 70)
    print(f"2024 DASHA LORDS → houses they signify (KP)")
    periods = v.dasha("vimshottari", levels=3, cycles=1)
    start = datetime(YEAR, 1, 1, tzinfo=TZ)
    end = datetime(YEAR + 1, 1, 1, tzinfo=TZ)
    prev = None
    d = start
    while d < end:
        chain = current_dasha(periods, d)
        key = tuple(p.lord for p in chain)
        if key != prev:
            prev = key
            lords = [p.lord for p in chain]
            houses = sorted(set().union(*(set(kp.planet_signifies(l))
                                          for l in lords)))
            label = "/".join(l.value for l in lords)
            # Which matters are lit up?
            lit = [m for m, hs in MATTERS.items()
                   if set(hs) & set(houses) and
                   # require at least 2 of the matter's houses among lords
                   len(set(hs) & set(houses)) >= 2]
            print(f"  {d:%Y-%m-%d}  {label:<22} houses {houses}")
            if lit:
                print(f"               → matters: {', '.join(lit)}")
        d += timedelta(days=1)

    # --- Per-matter verdict via cuspal sub-lord -------------------------- #
    print("\n" + "=" * 70)
    print("CUSPAL SUB-LORD VERDICT per matter (does the CSL back the houses?)")
    for matter, hs in MATTERS.items():
        prime = hs[-1] if matter != "Marriage / partner" else 7
        # primary cusp for the matter
        cusp = {"Marriage / partner": 7, "Career / job change": 10,
                "Wealth / gains": 11, "Property / vehicle": 4,
                "Childbirth": 5, "Foreign / relocation": 12}[matter]
        csl = kp_chain(kp.cusps[cusp]).sub_lord
        sig = kp.planet_signifies(csl)
        backs = set(sig) & set(hs)
        verdict = "FAVOURED" if backs else "weak"
        print(f"  {matter:<22} cusp {cusp:>2} CSL {csl.value:<8} "
              f"signifies {sig} → {verdict}")


if __name__ == "__main__":
    main()
