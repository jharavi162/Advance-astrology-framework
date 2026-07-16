"""Daśā timing engine — DATA ONLY.

The event clock, per the corrected division of labour: this engine reports
*which event-significators are running* in the Vimśottari and Jaimini-Chara
daśās over a span, plus the Gochara double-transit windows — and nothing else.
It computes **no score and no verdict**. The AI reads the data and times the
event (e.g. "the 7th-lord's antardaśā opens here → marriage window").

Why this engine, not KP, for timing (established by blind test): KP's cuspal
sub-lord is a promise/quality instrument; the *clock* is the daśā of the event's
own significators — the 7th-lord and its dispositor for marriage, confirmed by
the Jupiter+Saturn double-transit on the bhāva and its lord.

Significators are derived transparently from the domain (house-lords + their
dispositors + kāraka + Darakaraka) — domain-general, never a hard-coded native.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from advance_astrology import Planet
from advance_astrology.constants import RULERSHIPS, SIGNS


@dataclass(frozen=True)
class Significator:
    label: str                 # "7th-lord", "disp(7th-lord)", "kāraka:Venus", "Darakaraka"
    planet: Planet


@dataclass(frozen=True)
class VimPeriod:
    """One Vimśottari antardaśā, annotated with which significators are its
    MD or AD lord. `onset` marks the AD's start — events cluster at AD onsets."""
    start: datetime
    end: datetime
    md: str
    ad: str
    active: tuple[str, ...]    # significator LABELS running as MD or AD lord


@dataclass(frozen=True)
class CharaPeriod:
    start: datetime
    end: datetime
    sign: str
    roles: tuple[str, ...]     # classical marriage-timing roles this sign plays


@dataclass(frozen=True)
class DashaTimingReport:
    domain: str
    significators: tuple[Significator, ...]
    vimshottari: tuple[VimPeriod, ...]
    chara: tuple[CharaPeriod, ...]
    transit_triggers: tuple[tuple[datetime, datetime, str], ...]  # (start, end, what)

    def active_windows(self, label: str) -> list[VimPeriod]:
        """Convenience for the AI: every antardaśā in which `label` is running."""
        return [p for p in self.vimshottari if label in p.active]


def _dispositor(v, planet: Planet) -> Planet:
    return RULERSHIPS[SIGNS[v.signs[planet]]]


def _significators(v, profile) -> list[Significator]:
    """Derive the event's timing significators from the domain, transparently.
    Marriage-class matters also carry the spouse kārakas (Darakaraka; Jupiter is
    the husband-kāraka for a female, Venus the wife-kāraka)."""
    sig: list[Significator] = []
    seen: set = set()

    def add(label, planet):
        if planet and (label, planet) not in seen:
            seen.add((label, planet))
            sig.append(Significator(label, planet))

    for h in profile.houses:
        lord = v.house_lord(h)
        add(f"{_ord(h)}-lord", lord)
        add(f"disp({_ord(h)}-lord)", _dispositor(v, lord))
    if profile.natural_karaka:
        add(f"kāraka:{profile.natural_karaka.value}", profile.natural_karaka)
    # spouse matters: Darakaraka + gender-aware partner kāraka
    is_marriage = (profile.base_domain or profile.name) in ("marriage", "divorce")
    if is_marriage or 7 in profile.houses:
        dk = v.chara_karakas().get("Darakaraka")
        add("Darakaraka", dk)
        g = (getattr(v, "gender", "") or "").lower()
        add("kāraka:Jupiter(spouse)" if g.startswith("f") else "kāraka:Venus(spouse)",
            Planet.JUPITER if g.startswith("f") else Planet.VENUS)
    return sig


def _ord(h: int) -> str:
    return {1: "1st", 2: "2nd", 3: "3rd"}.get(h, f"{h}th")


def _overlaps(a_start, a_end, b_start, b_end) -> bool:
    return a_start < b_end and b_start < a_end


class DashaTimingEngine:
    """Data-only event-clock engine (the `Engine` contract's `evaluate`, but the
    result is raw daśā DATA, not a scored timeline)."""

    name = "dasha_timing"

    def evaluate(self, v, profile, start: datetime, end: datetime) -> DashaTimingReport:
        sig = _significators(v, profile)
        by_planet: dict = {}
        for s in sig:
            by_planet.setdefault(s.planet, []).append(s.label)

        # --- Vimśottari MD>AD, annotated with running significators ---------- #
        vim: list[VimPeriod] = []
        for md in v.dasha("vimshottari", levels=2):
            if not _overlaps(md.start, md.end, start, end):
                continue
            for ad in (md.sub_periods or []):
                if not _overlaps(ad.start, ad.end, start, end):
                    continue
                labels = []
                for lord in (md.lord, ad.lord):
                    labels += by_planet.get(lord, [])
                vim.append(VimPeriod(ad.start, ad.end, md.lord.value, ad.lord.value,
                                     tuple(dict.fromkeys(labels))))

        # --- Jaimini Chara rāśi daśā, annotated with marriage-timing roles --- #
        asc = v.ascendant_sign
        seventh_sign = SIGNS[(asc + 6) % 12]
        dk = v.chara_karakas().get("Darakaraka")
        dk_sign = SIGNS[v.signs[dk]] if dk else None
        chara: list[CharaPeriod] = []
        for cp in _chara_periods(v):
            if not _overlaps(cp["start"], cp["end"], start, end):
                continue
            roles = []
            if cp["sign"] == seventh_sign:
                roles.append("7th-from-Lagna")
            if dk_sign and cp["sign"] == dk_sign:
                roles.append("holds Darakaraka")
            chara.append(CharaPeriod(cp["start"], cp["end"], cp["sign"], tuple(roles)))

        # --- Gochara double-transit triggers on the bhāva and its lord ------- #
        tr = v.transits()
        triggers: list = []
        for h in profile.houses:
            for w in tr.double_transit_windows(h, start, end):
                triggers.append((w.start, w.end, f"double-transit on H{h}"))
            lord = v.house_lord(h)
            lord_house = (v.signs[lord] - asc) % 12 + 1
            for w in tr.double_transit_windows(lord_house, start, end):
                triggers.append((w.start, w.end,
                                 f"double-transit on {_ord(h)}-lord ({lord.value}, H{lord_house})"))
        triggers.sort()

        return DashaTimingReport(
            domain=profile.name, significators=tuple(sig),
            vimshottari=tuple(vim), chara=tuple(chara),
            transit_triggers=tuple(triggers))


def _chara_periods(v) -> list[dict]:
    """Chara antardaśā-level rāśi periods (sign + span), robust to sub_periods
    absence — falls back to MD-level rāśi periods."""
    out = []
    tops = v.chara_dasha(levels=2)
    for md in tops:
        subs = getattr(md, "sub_periods", None)
        if subs:
            for ad in subs:
                out.append(dict(sign=_sign_of(ad), start=ad.start, end=ad.end))
        else:
            out.append(dict(sign=_sign_of(md), start=md.start, end=md.end))
    return out


def _sign_of(period) -> str:
    """Chara periods carry the sign name in `.note`; fall back to `.lord`."""
    note = getattr(period, "note", None)
    if isinstance(note, str) and note in SIGNS:
        return note
    lord = getattr(period, "lord", None)
    return getattr(lord, "value", str(note))
