"""Jaimini engine — DATA ONLY.

Reports the Jaimini view of a matter: the Arudhas (image/manifestation), the
chara-kārakas (spouse/career/… significators), the Kārakāṃśa, the Argala
(intervention) on the matter's house, and the Chara rāśi-daśā windows that
activate the matter's Arudha / house / Upapada. No score, no verdict — the AI
reads the Jaimini testimony and weighs it against the other schools.

Marriage note: the **Upapada (UL)** and **2nd-from-UL** are the Jaimini marriage
axis; the **Darakaraka** is the spouse. These are surfaced as data, never judged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from advance_astrology.constants import SIGNS


@dataclass(frozen=True)
class ArgalaOnHouse:
    house: int
    causer_count: int
    counterer_count: int
    net_open: bool             # intervention stronger than its counter?


@dataclass(frozen=True)
class CharaWindow:
    start: datetime
    end: datetime
    sign: str
    roles: tuple[str, ...]     # which Jaimini role(s) this rāśi plays for the matter


@dataclass(frozen=True)
class JaiminiReport:
    domain: str
    arudhas: dict                       # raw {A1..A12, AL, UL} -> sign index
    domain_arudha: dict                 # {"A{h}": sign_name} for the matter's houses
    upapada_sign: str | None            # UL sign (marriage axis); None if n/a
    chara_karakas: dict                 # {karaka_name: planet_value} relevant to matter
    karakamsha_sign: str
    argala: tuple[ArgalaOnHouse, ...]   # intervention on the primary house
    chara_windows: tuple[CharaWindow, ...]
    notes: tuple[str, ...] = field(default_factory=tuple)


_MARRIAGE = {"marriage", "divorce"}


class JaiminiEngine:
    name = "jaimini"

    def evaluate(self, v, profile, start: datetime, end: datetime) -> JaiminiReport:
        asc = v.ascendant_sign
        arudhas = v.arudhas()
        ck = v.chara_karakas()
        is_marriage = (profile.base_domain or profile.name) in _MARRIAGE or 7 in profile.houses

        # Arudha of each of the matter's houses (A7 for marriage, A10 for career…)
        domain_arudha = {f"A{h}": SIGNS[arudhas[f"A{h}"]]
                         for h in profile.houses if f"A{h}" in arudhas}
        ul_sign = SIGNS[arudhas["UL"]] if is_marriage and "UL" in arudhas else None

        # chara-kārakas the matter reads (its named kāraka + Darakaraka for spouse)
        rel = list(profile.karakas)
        if is_marriage:
            rel.append("Darakaraka")
        chara_karakas = {k: ck[k].value for k in dict.fromkeys(rel) if k in ck}

        # Argala on the primary house — data, not a verdict
        argala = []
        for a in v.argala(profile.houses[0]):
            cc, xc = len(a.causers), len(a.counterers)
            argala.append(ArgalaOnHouse(a.house, cc, xc, cc > xc))

        # Chara rāśi-daśā windows that activate the matter's Jaimini signs
        target_signs: dict = {}
        for h in profile.houses:
            target_signs.setdefault(SIGNS[(asc + h - 1) % 12], []).append(f"{h}th-from-Lagna")
        for label, sgn in domain_arudha.items():
            target_signs.setdefault(sgn, []).append(f"Arudha {label}")
        if ul_sign:
            target_signs.setdefault(ul_sign, []).append("Upapada (UL)")
            target_signs.setdefault(SIGNS[(arudhas["UL"] + 1) % 12], []).append("2nd-from-UL")

        chara_windows = []
        for cp in _chara(v):
            if cp["start"] < end and start < cp["end"] and cp["sign"] in target_signs:
                chara_windows.append(CharaWindow(
                    cp["start"], cp["end"], cp["sign"],
                    tuple(target_signs[cp["sign"]])))

        return JaiminiReport(
            domain=profile.name, arudhas=dict(arudhas),
            domain_arudha=domain_arudha, upapada_sign=ul_sign,
            chara_karakas=chara_karakas, karakamsha_sign=SIGNS[v.karakamsha()],
            argala=tuple(argala), chara_windows=tuple(chara_windows))


def _chara(v) -> list[dict]:
    out = []
    for md in v.chara_dasha(levels=2):
        subs = getattr(md, "sub_periods", None) or [md]
        for p in subs:
            note = getattr(p, "note", None)
            sign = note if isinstance(note, str) and note in SIGNS else \
                getattr(getattr(p, "lord", None), "value", str(note))
            out.append(dict(sign=sign, start=p.start, end=p.end))
    return out
