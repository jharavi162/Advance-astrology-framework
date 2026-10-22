"""Bhāva Bala — the strength of each house (in virūpas; 60 = 1 rūpa).

B.V. Raman, *Graha and Bhava Balas* (ch. IX, after Śrīpati and BPHS): a
bhāva's strength is the sum of three parts —

* **Bhāvādhipati bala** — the Ṣaḍbala piṇḍa of the lord of the sign holding
  the bhāva-madhya;
* **Bhāva digbala** — from the kind of sign the bhāva-madhya falls in (Nara,
  Jalacara, Catuṣpada, Kīṭa): 60 at the bhāva where that kind is strongest
  (Nara 1st, Kīṭa 7th, Catuṣpada 10th, Jalacara 4th), falling 10 per bhāva to
  nil at the opposite one;
* **Bhāva dṛṣṭi bala** — Śrīpati's graded drishti of each graha on the
  bhāva-madhya (with the viśeṣa drishti of Mars, Jupiter, Saturn), Jupiter's
  and Mercury's taken whole and the others' a quarter; benefics add,
  malefics subtract, and Mercury counts as a full benefic here.

Bhāva-madhyas are Śrīpati's: Lagna, MC and their opposites, with each
quadrant trisected.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..angles import norm360
from ..constants import RULERSHIPS, SIGNS, Planet
from ..houses import porphyry_cusps

DRISHTI_GRAHAS = (Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
                  Planet.JUPITER, Planet.VENUS, Planet.SATURN)
# Bhāva at which each kind of sign gives its full digbala.
_DIG_BHAVA = {"nara": 7, "keeta": 1, "chatushpada": 4, "jalachara": 10}
# (Raman's rule subtracts the bhāva number from these: Kīṭa 1, Catuṣpada 4,
# Nara 7, Jalacara 10 — the bhāva of nil strength is opposite the full one.)
_VISESHA = {Planet.MARS: (15.0, ((90, 120), (210, 240))),
            Planet.JUPITER: (30.0, ((120, 150), (240, 270))),
            Planet.SATURN: (45.0, ((60, 90), (270, 300)))}


def sign_kind(lon: float) -> str:
    """Nara, Jalacara, Catuṣpada or Kīṭa, with Dhanus and Makara split in halves."""
    lon = norm360(lon)
    s, deg = int(lon // 30), lon % 30
    if s == 8:                                    # Dhanus: Nara, then Catuṣpada
        return "nara" if deg < 15 else "chatushpada"
    if s == 9:                                    # Makara: Catuṣpada, then Jalacara
        return "chatushpada" if deg < 15 else "jalachara"
    return {2: "nara", 5: "nara", 6: "nara", 10: "nara",
            3: "jalachara", 11: "jalachara", 7: "keeta",
            0: "chatushpada", 1: "chatushpada", 4: "chatushpada"}[s]


def bhava_digbala(bhava: int, madhya: float) -> float:
    d = (_DIG_BHAVA[sign_kind(madhya)] - bhava) % 12
    return 10.0 * (12 - d if d > 6 else d)


def drishti_value(dk: float, aspecting: Planet | None = None) -> float:
    """Śrīpati's drishti (virūpas) at drishti-kendra *dk* = aspected − aspecting,
    plus the viśeṣa drishti of Mars, Jupiter and Saturn."""
    dk = norm360(dk)
    if 30 <= dk < 60:
        v = (dk - 30) / 2
    elif 60 <= dk < 90:
        v = dk - 60 + 15
    elif 90 <= dk < 120:
        v = (120 - dk) / 2 + 30
    elif 120 <= dk < 150:
        v = 150 - dk
    elif 150 <= dk < 180:
        v = (dk - 150) * 2
    elif 180 <= dk <= 300:
        v = (300 - dk) / 2
    else:
        v = 0.0
    extra, arcs = _VISESHA.get(aspecting, (0.0, ()))
    if any(a <= dk < b for a, b in arcs):
        v += extra
    return v


def bhava_drishti_bala(madhya: float, longitudes: dict, moon_waxing: bool) -> dict:
    """Net drishti on a bhāva-madhya, with the benefic and malefic totals."""
    subha = papa = 0.0
    for p in DRISHTI_GRAHAS:
        v = drishti_value(madhya - longitudes[p], p)
        if p not in (Planet.JUPITER, Planet.MERCURY):
            v /= 4.0
        benefic = p in (Planet.JUPITER, Planet.VENUS, Planet.MERCURY) or (
            p is Planet.MOON and moon_waxing)
        if benefic:
            subha += v
        else:
            papa += v
    return dict(subha=subha, papa=papa, net=subha - papa)


def bhava_madhyas(asc: float, mc: float) -> dict[int, float]:
    """Śrīpati bhāva-madhyas (sidereal), 1..12."""
    return porphyry_cusps(asc, mc)


@dataclass(frozen=True)
class BhavaBala:
    bhava: int
    madhya: float
    lord: Planet
    adhipati: float          # lord's Ṣaḍbala piṇḍa (virūpas)
    dig: float
    drishti: float           # net (benefic − malefic)
    subha_drishti: float
    papa_drishti: float

    @property
    def total_virupa(self) -> float:
        return self.adhipati + self.dig + self.drishti

    @property
    def total_rupa(self) -> float:
        return self.total_virupa / 60.0

    def __str__(self) -> str:
        m = norm360(self.madhya)
        return (f"H{self.bhava} madhya {SIGNS[int(m // 30)]} {m % 30:.2f}° "
                f"({sign_kind(m)}), lord {self.lord.value}: {self.total_rupa:.2f} rupa "
                f"[adhipati {self.adhipati:.1f} + dig {self.dig:.0f} + drishti "
                f"{self.drishti:+.1f} (subha {self.subha_drishti:.1f}, papa "
                f"{self.papa_drishti:.1f})]")


def bhava_bala(madhyas: dict[int, float], longitudes: dict,
               shadbala_virupa: dict, moon_waxing: bool) -> dict[int, BhavaBala]:
    out = {}
    for h in range(1, 13):
        m = madhyas[h]
        lord = RULERSHIPS[SIGNS[int(norm360(m) // 30)]]
        dr = bhava_drishti_bala(m, longitudes, moon_waxing)
        out[h] = BhavaBala(h, m, lord, shadbala_virupa[lord], bhava_digbala(h, m),
                           dr["net"], dr["subha"], dr["papa"])
    return out


def compute_bhava_bala(chart) -> dict[int, BhavaBala]:
    """Bhāva Bala of a :class:`VedicChart`."""
    sb = chart.shadbala()
    lon = chart.longitudes
    waxing = norm360(lon[Planet.MOON] - lon[Planet.SUN]) < 180.0
    madhyas = bhava_madhyas(chart.ascendant, chart.natal.angles.midheaven)
    return bhava_bala(madhyas, lon, {p: s.total_virupa for p, s in sb.items()}, waxing)
