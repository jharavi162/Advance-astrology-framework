"""Phase I Matrix Assembly for the Architectural Playbook.

Read-only consumer of the engine's public API. It does NOT alter any
calculation — it gathers every computational input the triangulation
playbook (Section 2) depends on and renders it as a clean, deterministic
text block suitable for feeding to an interpretation layer.

    python -m interpreter.build_matrix \
        --when "1991-04-04 06:23" --tz Asia/Kolkata \
        --lat 23.63 --lon 85.52 --place "Ramgarh, Jharkhand" \
        --sex male --name "Native"
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from advance_astrology import VedicChart, Planet, to_zodiac
from advance_astrology.constants import SIGNS
from advance_astrology.vedic.jaimini import KARAKA_ABBR
from advance_astrology.vedic.vargas import SHODASHAVARGA, VARGA_NAMES

# Planet order used throughout (9 grahas).
GRAHAS = [Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY, Planet.JUPITER,
          Planet.VENUS, Planet.SATURN, Planet.RAHU, Planet.KETU]
# Sapta/ashta-graha for strength tables (nodes have no Shadbala).
SEVEN = [Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY, Planet.JUPITER,
         Planet.VENUS, Planet.SATURN]


def _sign(idx: int) -> str:
    return SIGNS[idx]


def _h(lines: list[str], title: str) -> None:
    lines.append("")
    lines.append(f"## {title}")


def build_matrix(when_local: datetime, lat: float, lon: float,
                 place: str, sex: str, name: str, ayanamsa: str) -> str:
    v = VedicChart.create(when=when_local, latitude=lat, longitude=lon,
                          name=name, ayanamsa=ayanamsa)
    now = datetime.now(timezone.utc)
    nat = v.natal
    L: list[str] = []

    # ---- 2.1 Foundational coordinates -----------------------------------
    L.append("# NATIVE MATRIX DATABANK (Playbook Section 2 — Phase I)")
    L.append("")
    L.append(f"- Name / Sex      : {name or '(unnamed)'} / {sex}")
    L.append(f"- Birth (local)   : {when_local:%Y-%m-%d %H:%M %Z}  @ {place}")
    L.append(f"- Birth (UTC)     : {v.when_utc:%Y-%m-%d %H:%M} UTC")
    L.append(f"- Coordinates     : lat {lat}, lon {lon}")
    L.append(f"- Ayanamsa        : {ayanamsa} ({v.ayanamsa:.4f}°)")
    asc = to_zodiac(v.ascendant)
    asc_nak = nat.ascendant_nakshatra if hasattr(nat, "ascendant_nakshatra") else None
    L.append(f"- Lagna (Asc)     : {asc}  [{_sign(v.ascendant_sign)}]")

    _h(L, "2.1 Nava-Graha Positional Geometry")
    L.append(f"{'Planet':<8}{'Longitude':<22}{'Nakshatra (pada/lord)':<30}"
             f"{'House':<6}{'R':<3}{'Dignity'}")
    L.append("-" * 90)
    for p in GRAHAS:
        pl = nat.get(p)
        nk = pl.nakshatra
        retro = "R" if pl.retrograde else ""
        L.append(f"{p.value:<8}{str(to_zodiac(v.longitudes[p])):<22}"
                 f"{nk.name + ' (' + str(nk.pada) + '/' + nk.lord.value + ')':<30}"
                 f"H{v.house_of(p):<5}{retro:<3}{v.dignity(p)}")

    # ---- 2.2 Lordships, functional nature, karakas ----------------------
    _h(L, "2.2 Functional Governance & Jaimini Karakas")
    nature = v.functional_nature()
    karakas = {p: nm for nm, p in v.chara_karakas().items()}
    marakas = v.marakas()
    L.append(f"{'Planet':<8}{'Functional':<12}{'Jaimini Karaka':<22}{'Maraka?'}")
    L.append("-" * 60)
    for p in GRAHAS:
        kn = karakas.get(p, "")
        ktxt = f"{KARAKA_ABBR.get(kn, '-')} ({kn})" if kn else "-"
        mk = "yes" if p in marakas else ""
        L.append(f"{p.value:<8}{nature.get(p, '-'):<12}{ktxt:<22}{mk}")
    L.append(f"\nAtmakaraka: {v.atmakaraka().value}   "
             f"Karakamsha (AK in D9): {_sign(v.karakamsha())}")

    # ---- 2.4 Bala & Avastha ---------------------------------------------
    _h(L, "2.4 Shadbala, Ishta/Kashta, Avastha, Vaiseshikamsa")
    sb = v.shadbala()
    ik = v.ishta_kashta()
    L.append(f"{'Planet':<8}{'Shadbala':<11}{'Ratio':<8}{'Strong':<8}"
             f"{'Ishta':<7}{'Kashta':<8}{'Baladi/Jagrad/Deeptadi':<32}"
             f"{'Combust':<9}{'Vaisesika'}")
    L.append("-" * 110)
    for p in SEVEN:
        s = sb[p]
        k = ik[p]
        av = v.avasthas(p)
        moods = f"{av['baladi']}/{av['jagradadi']}/{av['deeptadi']}"
        L.append(f"{p.value:<8}{s.total_rupa:>6.2f}rū  {s.ratio:>6.2f}  "
                 f"{('yes' if s.is_strong else 'no'):<8}"
                 f"{k.ishta:>5.0f}  {k.kashta:>5.0f}  {moods:<32}"
                 f"{av['combust']:<9}{v.vaiseshikamsa(p)}")

    # ---- 2.5 Bhava-Chalit (Placidus shift) ------------------------------
    _h(L, "2.5 Bhava-Chalit (Placidus shift detection)")
    chalit = v.bhava_chalit()
    shifts = [c for c in chalit.values() if c.shifted]
    if shifts:
        for c in shifts:
            L.append(f"  {c.planet.value:<8} Rashi H{c.rashi_house} "
                     f"→ Chalit H{c.chalit_house}  (environment "
                     f"H{c.rashi_house}, physical results H{c.chalit_house})")
    else:
        L.append("  No house shifts between Rashi and Placidus-Chalit.")

    # ---- 2.6 Ashtakavarga -----------------------------------------------
    _h(L, "2.6 Ashtakavarga (SAV per sign + BAV per planet)")
    sav = v.sarvashtakavarga()
    L.append("  SAV: " + "  ".join(f"{s[:3]}:{b}" for s, b in zip(SIGNS, sav))
             + f"   (total {sum(sav)})")
    L.append("")
    for p in SEVEN:
        bav = v.bhinnashtakavarga(p)
        L.append(f"  BAV {p.value:<8} " +
                 " ".join(f"{s[:3]}:{b}" for s, b in zip(SIGNS, bav)))

    # ---- Special refraction points --------------------------------------
    _h(L, "2.6 Special Refraction Points (Arudha / Upapada / Bhrigu Bindu)")
    ar = v.arudhas()
    L.append("  Arudhas: " + "  ".join(f"{k}:{_sign(val)}" for k, val in ar.items()))
    L.append(f"  Arudha Lagna (AL): {_sign(v.arudha_lagna())}")
    if "UL" in ar:
        L.append(f"  Upapada Lagna (UL): {_sign(ar['UL'])}")
    L.append(f"  Bhrigu Bindu: {to_zodiac(v.bhrigu_bindu())}")
    for nm, lon in v.calculated_upagrahas().items():
        if nm.lower() in ("gulika", "mandi"):
            L.append(f"  {nm}: {to_zodiac(lon)}")
    L.append("  Special Lagnas: " +
             "  ".join(f"{nm}:{to_zodiac(lon)}" for nm, lon in v.special_lagnas().items()))

    # ---- 2.3 Varga architecture -----------------------------------------
    _h(L, "2.3 Shodasavarga (16 divisional ascendants)")
    for d in SHODASHAVARGA:
        vc = v.varga(d)
        L.append(f"  D{d:<3}{VARGA_NAMES[d]:<24} Asc: {_sign(vc.ascendant_sign)}")

    # ---- Aspects --------------------------------------------------------
    _h(L, "Graha Drishti (Parashari special aspects)")
    vedic_set = set(GRAHAS)
    for a in v.graha_aspects():
        if a.planet not in vedic_set:          # drop non-Vedic outer planets
            continue
        L.append(f"  {a.planet.value:<8} in {_sign(a.from_sign):<12} "
                 f"aspects {_sign(a.to_sign):<12} ({a.distance}th)")

    # ---- Section 3 timekeepers: Dashas ----------------------------------
    _h(L, "Section 3 — Chronological Timekeepers (current periods)")
    for system in ("vimshottari", "ashtottari", "yogini"):
        chain = v.current_dasha(system, now)
        L.append(f"  {system.capitalize():<12} " +
                 " > ".join(d.lord.value for d in chain))
    nd = [d for d in v.narayana_dasha() if d.start <= now < d.end]
    if nd:
        L.append(f"  Narayana    {nd[0].note} ({nd[0].lord.value})  "
                 f"{nd[0].start:%Y-%m-%d}→{nd[0].end:%Y-%m-%d}")
    cd = [d for d in v.chara_dasha() if d.start <= now < d.end]
    if cd:
        L.append(f"  Chara       {cd[0].note} ({cd[0].lord.value})  "
                 f"{cd[0].start:%Y-%m-%d}→{cd[0].end:%Y-%m-%d}")

    # ---- Slow gochara ---------------------------------------------------
    _h(L, "Section 3 — Structural Heavyweights (slow gochara, today)")
    tr = v.transits()
    for p, info in tr.slow_movers(now).items():
        L.append(f"  {p.value:<8}{info['sign']:<12} "
                 f"H{info['house_from_lagna']} (lagna) / "
                 f"H{info['house_from_moon']} (moon)   SAV={info['sav']}")
    ss = tr.sade_sati(now)
    L.append(f"  Sade Sati: {'ACTIVE — ' + ss['phase'] if ss['active'] else 'inactive'} "
             f"(Saturn in {ss['saturn_sign']})")

    # ---- KP chains ------------------------------------------------------
    _h(L, "Section 3 — KP Stellar Significator Chains (negation tool)")
    for p in GRAHAS:
        L.append(f"  {p.value:<8} {v.kp_chain(p)}")
    kps = v.kp_significators()
    L.append("  House significators (Vedic grahas only):")
    for hno in range(1, 13):
        sigs = [x for x in kps.house_significators(hno) if x in vedic_set]
        L.append(f"    H{hno:<2} {', '.join(x.value for x in sigs)}")

    # ---- Yogas & Panchanga ----------------------------------------------
    _h(L, "Yogas")
    for y in v.yogas():
        L.append(f"  {y}")
    _h(L, "Panchanga")
    for line in str(v.panchanga()).splitlines():
        L.append("  " + line)

    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description="Assemble the Phase I playbook matrix.")
    ap.add_argument("--when", required=True, help='Local birth datetime "YYYY-MM-DD HH:MM"')
    ap.add_argument("--tz", default="Asia/Kolkata", help="IANA timezone, e.g. Asia/Kolkata")
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--place", default="")
    ap.add_argument("--sex", default="")
    ap.add_argument("--name", default="")
    ap.add_argument("--ayanamsa", default="lahiri")
    ap.add_argument("--out", default="", help="Optional output file")
    args = ap.parse_args()

    when_local = datetime.strptime(args.when, "%Y-%m-%d %H:%M").replace(
        tzinfo=ZoneInfo(args.tz))
    text = build_matrix(when_local, args.lat, args.lon, args.place,
                        args.sex, args.name, args.ayanamsa)
    if args.out:
        with open(args.out, "w") as fh:
            fh.write(text)
        print(f"Wrote matrix to {args.out} ({len(text)} chars)")
    else:
        print(text)


if __name__ == "__main__":
    main()
