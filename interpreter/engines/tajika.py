"""Tājika (annual / Varṣaphal) engine — DATA ONLY.

For each year in the span it reports the annual chart's timing data: the Muntha
house and its lord, the Varṣa-lagna and its lord (the year-lord), and the
matter's Sāham (Vivāha for marriage, Karma for career…) — sign and lord. It
flags, as raw data, whether the Muntha falls in one of the matter's fulfilment
houses that year. No score, no verdict; the AI reads which annual chart supports
the matter and cross-checks the daśā window.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from advance_astrology.constants import SIGNS

# Matter → its Tājika Sāham (the annual sensitive point for that theme).
DOMAIN_SAHAM = {
    "marriage": "Vivaha", "divorce": "Vivaha", "second-marriage": "Punarvivaha",
    "career": "Karma", "wealth": "Artha", "children": "Putra",
    "education": "Vidya", "illness": "Roga",
}


@dataclass(frozen=True)
class YearData:
    year: int
    muntha_house: int
    muntha_lord: str
    muntha_in_fulfil: bool          # raw flag: Muntha in a fulfilment house this year
    varsha_lagna: str
    year_lord: str                  # Varṣa-lagna lord (Varṣeśa proxy)
    saham: str | None               # the matter's sāham name
    saham_sign: str | None
    saham_lord: str | None


@dataclass(frozen=True)
class TajikaReport:
    domain: str
    saham_name: str | None
    years: tuple[YearData, ...]


class TajikaEngine:
    name = "tajika"

    def evaluate(self, v, profile, start: datetime, end: datetime) -> TajikaReport:
        base = profile.base_domain or profile.name
        saham_name = DOMAIN_SAHAM.get(profile.name) or DOMAIN_SAHAM.get(base)
        sahams = v.sahams()
        years = []
        for y in range(start.year, end.year + 1):
            vp = v.varshaphal(y)
            saham_sign = saham_lord = None
            if saham_name and saham_name in sahams:
                sh = sahams[saham_name]
                saham_sign = SIGNS[sh.sign_index]
                saham_lord = getattr(sh.lord, "value", None)
            years.append(YearData(
                year=y,
                muntha_house=vp.muntha_house,
                muntha_lord=getattr(vp.muntha_lord, "value", "?"),
                muntha_in_fulfil=vp.muntha_house in profile.fulfil_houses,
                varsha_lagna=SIGNS[vp.varsha_lagna_sign],
                year_lord=getattr(vp.lagna_lord, "value", "?"),
                saham=saham_name, saham_sign=saham_sign, saham_lord=saham_lord))
        return TajikaReport(domain=profile.name, saham_name=saham_name,
                            years=tuple(years))
