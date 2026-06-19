"""Multi-technique triangulation of the 2024 standout event.

Cross-checks one verdict across five independent lenses:

  1. Gochara   — Guru/Shani transit over natal points; double-transit; Sade Sati
  2. Shadbala  — which grahas are strong + Iṣṭa/Kaṣṭa (benefic vs malefic yield)
  3. Bhava-Chalit — 7th-house occupants/lord and any Rāśi→Chalit shift
  4. Vargas    — D9 (marriage), D7 (children), D10 (career), D60 (overall)
  5. BNN       — Bhrigu Nandi Nadi: Atmakaraka, same-sign yogas, Guru gochar
                 over the Kalatra-karaka (Venus) — the Nadi marriage trigger

Run from the repository root:

    python examples/triangulate_2024.py
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from advance_astrology import VedicChart
from advance_astrology.constants import SIGNS, Planet
from advance_astrology.vedic.jaimini import KARAKA_ABBR
from advance_astrology.vedic.vargas import build_varga

TZ = ZoneInfo("Asia/Kolkata")
WHEN = datetime(1991, 4, 4, 6, 23, tzinfo=TZ)
LAT, LON = 23.6307, 85.5119          # Ramgarh, Jharkhand
YEAR = 2024

# Jupiter's special aspects: 5th, 7th, 9th (sign distances 4, 6, 8).
JUP_ASPECT_DIST = (4, 6, 8)


def sign_name(i):
    return SIGNS[i]


def main():
    v = VedicChart.create(when=WHEN, latitude=LAT, longitude=LON,
                          name="Native", ayanamsa="lahiri")
    asc = v.ascendant_sign
    print("LAGNA:", SIGNS[asc], " | Moon:", SIGNS[v.signs[Planet.MOON]])

    # ================================================================== #
    # 1. GOCHARA — Guru / Shani over natal points across 2024
    # ================================================================== #
    print("\n" + "=" * 68)
    print("1) GOCHARA — Guru(Jupiter) & Shani(Saturn) transit hits, 2024")
    tr = v.transits()
    start = datetime(YEAR, 1, 1, tzinfo=TZ)
    end = datetime(YEAR + 1, 1, 1, tzinfo=TZ)

    venus_sign = v.signs[Planet.VENUS]
    moon_sign = v.signs[Planet.MOON]
    seventh_sign = (asc + 6) % 12
    # Guru gochar: sign each month + does it conjunct/aspect natal Venus/7th?
    print("  Jupiter (Guru) gochar over the year:")
    d = start
    prev_sign = None
    while d < end:
        js = tr.transit_sign(d, Planet.JUPITER)
        if js != prev_sign:
            prev_sign = js
            hits = []
            if js == venus_sign:
                hits.append("CONJ natal Venus")
            if (js - venus_sign) % 12 in JUP_ASPECT_DIST:
                hits.append("aspects natal Venus")
            if (js - seventh_sign) % 12 == 0:
                hits.append("in 7th house")
            if (js - seventh_sign) % 12 in JUP_ASPECT_DIST:
                hits.append("aspects 7th house")
            tag = ("  ← " + ", ".join(hits)) if hits else ""
            print(f"    {d:%Y-%m}  Jupiter in {SIGNS[js]:<11}"
                  f" (H{(js-asc)%12+1} from lagna){tag}")
        d += timedelta(days=5)

    # Tight degree conjunctions (Guru/Shani) to all natal points.
    print("  Degree-tight hits (orb<=1.5):")
    seen = set()
    d = start
    while d < end:
        for hit in tr.conjunctions(d, orb=1.5,
                                   planets=[Planet.JUPITER, Planet.SATURN]):
            k = (hit.transit, hit.natal)
            if k not in seen:
                seen.add(k)
                print(f"    ~{d:%Y-%m}  {hit.transit.value} conj natal "
                      f"{hit.natal.value}")
        d += timedelta(days=7)

    # ================================================================== #
    # 2. SHADBALA — strengths + Ishta/Kashta
    # ================================================================== #
    print("\n" + "=" * 68)
    print("2) SHADBALA — graha strength & Iṣṭa/Kaṣṭa yield")
    sb = v.shadbala()
    ik = v.ishta_kashta()
    for p in sorted(sb, key=lambda x: sb[x].total_rupa, reverse=True):
        i = ik[p]
        flag = "STRONG" if sb[p].is_strong else "weak"
        bias = "benefic" if i.ishta >= i.kashta else "malefic"
        print(f"  {p.value:<8} {sb[p].total_rupa:5.2f} rūpa "
              f"({sb[p].ratio*100:5.0f}% req, {flag:<6})  "
              f"Iṣṭa {i.ishta:4.1f}/Kaṣṭa {i.kashta:4.1f} → {bias}")

    # ================================================================== #
    # 3. BHAVA-CHALIT — 7th house reality check
    # ================================================================== #
    print("\n" + "=" * 68)
    print("3) BHAVA-CHALIT — house shifts (Rāśi vs Placidus)")
    ch = v.bhava_chalit()
    for p, c in ch.items():
        if c.shifted:
            print(f"    {p.value:<8} Rāśi H{c.rashi_house} → Chalit H{c.chalit_house}")
    occ7 = [p.value for p in v.planets_in_house(7)]
    print(f"  7th-house (Rāśi) occupants: {occ7 or '—'}")
    print(f"  Planets aspecting 7th: "
          f"{[p.value for p in v.planets_aspecting(7)]}")

    # ================================================================== #
    # 4. VARGAS — D9 / D7 / D10 / D60
    # ================================================================== #
    print("\n" + "=" * 68)
    print("4) VARGAS — divisional confirmation")
    for d_, label in ((9, "Navamsha D9 (marriage/dharma)"),
                      (7, "Saptamsha D7 (children)"),
                      (10, "Dashamsha D10 (career)"),
                      (60, "Shashtiamsha D60 (overall)")):
        vc = build_varga(d_, v.ascendant, v.longitudes)
        ven_house = vc.house_of(Planet.VENUS)
        asc7 = (vc.ascendant_sign + 6) % 12
        sev_occ = [p.value for p in vc.planets_in_sign(asc7)]
        print(f"  {label}: Asc {SIGNS[vc.ascendant_sign]:<11} "
              f"Venus in {SIGNS[vc.signs[Planet.VENUS]]} (H{ven_house}); "
              f"7th-sign occupants: {sev_occ or '—'}")

    # ================================================================== #
    # 5. BNN — Bhrigu Nandi Nadi
    # ================================================================== #
    print("\n" + "=" * 68)
    print("5) BNN (Bhrigu Nandi Nadi)")
    ak = v.atmakaraka()
    print(f"  Atmakaraka (soul): {ak.value}")
    print("  Chara Karakas:")
    for name, planet in v.chara_karakas().items():
        print(f"    {KARAKA_ABBR[name]:>4} {name:<14} {planet.value}")

    # Same-sign conjunctions (BNN reads combined karakatva).
    print("  Same-sign conjunctions (karaka fusion):")
    by_sign = {}
    for p, s in v.signs.items():
        by_sign.setdefault(s, []).append(p)
    for s, ps in by_sign.items():
        if len(ps) > 1:
            print(f"    {SIGNS[s]:<11}: {', '.join(x.value for x in ps)}")

    # BNN marriage trigger: Guru gochar conjunct/aspecting Venus (Kalatra karaka).
    print("  BNN marriage trigger — Guru gochar vs Venus (wife karaka):")
    d = start
    flagged = False
    prev = None
    while d < end:
        js = tr.transit_sign(d, Planet.JUPITER)
        rel = (js - venus_sign) % 12
        state = None
        if rel == 0:
            state = "Guru OVER Venus sign (peak marriage yoga)"
        elif rel in JUP_ASPECT_DIST:
            state = "Guru aspects Venus sign"
        if state and state != prev:
            prev = state
            flagged = True
            print(f"    {d:%Y-%m}: {state}")
        d += timedelta(days=10)
    if not flagged:
        print("    (no direct Guru–Venus activation this year)")


if __name__ == "__main__":
    main()
