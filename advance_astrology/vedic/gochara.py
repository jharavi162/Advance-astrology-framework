"""Gochara doctrine tables — Vedha, Tārā, Murti and Saturn-from-Moon phases.

Pure, chart-independent rules that the :class:`~.transits.Transits` calculator
applies to live transit positions. They return DATA (which house, which tārā,
which planet obstructs) — never a verdict on the native's life.

Sources:
* **Vedha** (gochara obstruction) — Phaladeepika, gochara adhyāya (ch. 26):
  each graha gives good results from specific houses counted from the natal
  Moon, and each good house has a paired *vedha* house; a graha transiting the
  vedha house obstructs the good result. Sun–Saturn and Moon–Mercury do not
  obstruct each other. Rāhu/Ketu are not in the classical table; they follow
  Saturn's houses here, as in later practice, and are not counted as
  obstructors.
* **Tārā** — the ninefold count from the janma nakṣatra (Janma, Sampat, Vipat,
  Kṣema, Pratyari, Sādhaka, Vadha, Mitra, Parama-mitra), as used for tārā-bala
  in the muhūrta texts (e.g. Muhūrta Chintāmaṇi). Vipat, Pratyari and Vadha are
  the inauspicious tārās.
* **Murti** — the traditional "image" of a sign ingress, read from the transit
  Moon's house counted from the natal Moon at the moment of ingress: 1/6/11
  Swarṇa (gold), 2/5/9 Rajata (silver), 3/7/10 Tāmra (copper), 4/8/12 Loha
  (iron). A panchāṅga convention; no single classical verse is cited for it.
* **Saturn from the Moon** — Sāḍhe Sātī (Saturn in the 12th, 1st or 2nd from
  the natal Moon) and Ḍhaiyā (Saturn in the 4th — Kaṇṭaka/Ardhāṣṭama — or the
  8th — Aṣṭama — from the natal Moon).
"""

from __future__ import annotations

from ..constants import Planet

# --------------------------------------------------------------------------- #
# Vedha
# --------------------------------------------------------------------------- #

# planet -> {good house from Moon: its vedha house}
VEDHA = {
    Planet.SUN:     {3: 9, 6: 12, 10: 4, 11: 5},
    Planet.MOON:    {1: 5, 3: 9, 6: 12, 7: 2, 10: 4, 11: 8},
    Planet.MARS:    {3: 12, 6: 9, 11: 5},
    Planet.MERCURY: {2: 5, 4: 3, 6: 9, 8: 1, 10: 8, 11: 12},
    Planet.JUPITER: {2: 12, 5: 4, 7: 3, 9: 10, 11: 8},
    Planet.VENUS:   {1: 8, 2: 7, 3: 1, 4: 10, 5: 9, 8: 5, 9: 11, 11: 3, 12: 6},
    Planet.SATURN:  {3: 12, 6: 9, 11: 5},
}
VEDHA[Planet.RAHU] = dict(VEDHA[Planet.SATURN])
VEDHA[Planet.KETU] = dict(VEDHA[Planet.SATURN])

# Pairs that never obstruct each other (Phaladeepika: father–son, Moon–Mercury).
_NO_VEDHA = {frozenset((Planet.SUN, Planet.SATURN)),
             frozenset((Planet.MOON, Planet.MERCURY))}

# Only the seven grahas obstruct.
_OBSTRUCTORS = (Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
                Planet.JUPITER, Planet.VENUS, Planet.SATURN)


def _blocks(a: Planet, b: Planet) -> bool:
    return a != b and frozenset((a, b)) not in _NO_VEDHA


def vedha(planet: Planet, house_from_moon: int,
          houses_from_moon: dict[Planet, int]) -> dict:
    """Vedha status of *planet* transiting *house_from_moon*.

    ``houses_from_moon`` maps every transiting graha to its house from the
    natal Moon. Returns ``good`` (the house is one of the planet's good houses),
    ``vedha_house`` (its paired obstruction point), ``obstructed_by`` (grahas in
    that point — the good result is blocked) and, for a bad house,
    ``vipareeta_by`` (grahas in the matching good point — the bad result is
    blocked, *vipareeta vedha*).
    """
    table = VEDHA.get(planet, {})
    out = dict(good=house_from_moon in table, vedha_house=None,
               obstructed_by=[], vipareeta_by=[])
    if out["good"]:
        vh = table[house_from_moon]
        out["vedha_house"] = vh
        out["obstructed_by"] = [p for p in _OBSTRUCTORS
                                if houses_from_moon.get(p) == vh
                                and _blocks(planet, p)]
    else:
        reverse = {v: g for g, v in table.items()}
        if house_from_moon in reverse:
            gh = reverse[house_from_moon]
            out["vedha_house"] = gh
            out["vipareeta_by"] = [p for p in _OBSTRUCTORS
                                   if houses_from_moon.get(p) == gh
                                   and _blocks(planet, p)]
    return out


# --------------------------------------------------------------------------- #
# Tārā
# --------------------------------------------------------------------------- #

TARA_NAMES = ["Janma", "Sampat", "Vipat", "Kshema", "Pratyari",
              "Sadhaka", "Vadha", "Mitra", "Parama-mitra"]
_TARA_BAD = {3, 5, 7}


def tara(janma_nakshatra: int, transit_nakshatra: int) -> dict:
    """Tārā of *transit_nakshatra* counted from *janma_nakshatra* (0..26).

    ``number`` is 1..9, ``count`` the raw 1..27 count from the janma
    nakṣatra, ``quality`` one of ``good`` / ``bad`` / ``mixed`` (Janma).
    """
    count = (transit_nakshatra - janma_nakshatra) % 27 + 1
    n = (count - 1) % 9 + 1
    quality = "mixed" if n == 1 else ("bad" if n in _TARA_BAD else "good")
    return dict(number=n, name=TARA_NAMES[n - 1], count=count, quality=quality)


# --------------------------------------------------------------------------- #
# Murti
# --------------------------------------------------------------------------- #

_MURTI = {1: "Swarna", 6: "Swarna", 11: "Swarna",
          2: "Rajata", 5: "Rajata", 9: "Rajata",
          3: "Tamra", 7: "Tamra", 10: "Tamra",
          4: "Loha", 8: "Loha", 12: "Loha"}


def murti(moon_house_from_natal_moon: int) -> str:
    """Murti of a sign ingress from the transit Moon's house (1..12) counted
    from the natal Moon at the ingress instant."""
    return _MURTI[moon_house_from_natal_moon]


# --------------------------------------------------------------------------- #
# Saturn from the Moon
# --------------------------------------------------------------------------- #

def saturn_from_moon(house_from_moon: int) -> dict:
    """Sāḍhe Sātī / Ḍhaiyā status for Saturn in *house_from_moon* (1..12)."""
    sade = {12: "Rising (12th)", 1: "Peak (Janma)", 2: "Setting (2nd)"}
    dhaiya = {4: "Kantaka / Ardhashtama (4th)", 8: "Ashtama (8th)"}
    return dict(house_from_moon=house_from_moon,
                sade_sati=house_from_moon in sade,
                sade_sati_phase=sade.get(house_from_moon),
                dhaiya=house_from_moon in dhaiya,
                dhaiya_kind=dhaiya.get(house_from_moon))
