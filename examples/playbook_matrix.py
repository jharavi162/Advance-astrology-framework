"""Phase I 'Matrix Assembly' from the Architectural Playbook.

Demonstrates that the engine now produces every computational input the
triangulation playbook depends on: the per-planet structural profile (functional
nature, Jaimini karaka, Shadbala, Ishta/Kashta, avastha), Bhava-Chalit shifts,
Ashtakavarga, KP sub-lords, and the transit/Gochara layer.

    python examples/playbook_matrix.py
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from advance_astrology import VedicChart, Planet, to_zodiac
from advance_astrology.constants import SIGNS
from advance_astrology.vedic.jaimini import KARAKA_ABBR

WHEN = datetime(1990, 5, 15, 14, 30, tzinfo=ZoneInfo("America/New_York"))
LAT, LON = 40.7128, -74.0060


def main():
    v = VedicChart.create(when=WHEN, latitude=LAT, longitude=LON)

    karakas = {p: name for name, p in v.chara_karakas().items()}
    nature = v.functional_nature()
    shadbala = v.shadbala()
    ishta = v.ishta_kashta()
    chalit = v.bhava_chalit()

    print("PER-PLANET STRUCTURAL PROFILE")
    print("=" * 78)
    header = f"{'Planet':<8}{'Position':<22}{'Func':<11}{'Karaka':<7}{'Ṣaḍbala':<9}{'Iṣṭa/Kaṣṭa':<13}{'Chalit'}"
    print(header)
    print("-" * 78)
    for p in [Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
              Planet.JUPITER, Planet.VENUS, Planet.SATURN]:
        sb = shadbala[p]
        ik = ishta[p]
        ch = chalit[p]
        chalit_note = f"H{ch.rashi_house}→H{ch.chalit_house}" if ch.shifted else f"H{ch.rashi_house}"
        print(f"{p.value:<8}"
              f"{str(to_zodiac(v.longitudes[p])):<22}"
              f"{nature[p]:<11}"
              f"{KARAKA_ABBR.get(karakas.get(p,''),'-'):<7}"
              f"{sb.total_rupa:>5.2f}rū  "
              f"{ik.ishta:>4.0f}/{ik.kashta:<4.0f}    "
              f"{chalit_note}")

    print("\nMACRO TIMEKEEPERS (current periods)")
    print("=" * 78)
    now = datetime.now(timezone.utc)
    print("  Vimshottari:", " > ".join(d.lord.value for d in v.current_dasha("vimshottari", now)))
    nd = [d for d in v.narayana_dasha() if d.start <= now < d.end]
    if nd:
        print(f"  Narayana   : {nd[0].note} ({nd[0].lord.value})")
    cd = [d for d in v.chara_dasha() if d.start <= now < d.end]
    if cd:
        print(f"  Chara      : {cd[0].note} ({cd[0].lord.value})")

    print("\nGOCHARA — STRUCTURAL HEAVYWEIGHTS")
    print("=" * 78)
    tr = v.transits()
    for p, info in tr.slow_movers(now).items():
        print(f"  {p.value:<8} {info['sign']:<12} "
              f"H{info['house_from_lagna']} (lagna) / H{info['house_from_moon']} (moon)  "
              f"SAV={info['sav']}")
    ss = tr.sade_sati(now)
    print(f"  Sade Sati: {'ACTIVE — ' + ss['phase'] if ss['active'] else 'inactive'} "
          f"(Saturn in {ss['saturn_sign']})")

    print("\nKP SUB-LORD CHAINS (negation tool)")
    print("=" * 78)
    for p in [Planet.SUN, Planet.MOON, Planet.VENUS, Planet.SATURN]:
        print(f"  {p.value:<8} {v.kp_chain(p)}")
    kps = v.kp_significators()
    print(f"  7th-house significators: "
          f"{', '.join(x.value for x in kps.house_significators(7))}")

    print("\nASHTAKAVARGA (SAV per sign)")
    print("=" * 78)
    sav = v.sarvashtakavarga()
    print("  " + "  ".join(f"{s[:3]}:{b}" for s, b in zip(SIGNS, sav)))


if __name__ == "__main__":
    main()
