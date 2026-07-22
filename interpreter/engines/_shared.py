"""Shared computation the engines reuse — the Vimśottari timing spine and the KP
sub-chart. Moved here so `interpreter/engines/` stands entirely on its own,
depending only on `advance_astrology` (the ephemeris core), never on the legacy
`event_evidence` monolith. Never recomputes a number the engine already owns.
"""

from __future__ import annotations

from datetime import datetime

from advance_astrology import VedicChart

_KP_VIEW_CACHE: dict = {}


def kp_view(v):
    """KP must be judged on the **KP ayanāṃśa** with **Placidus** cusps — a
    distinct sub-chart from the main (Lahiri/whole-sign) one. Built once per
    native and cached; returns ``(kp_chart, KPSignificators)``."""
    key = id(v)
    if key not in _KP_VIEW_CACHE:
        vkp = VedicChart.create(when=v.when_utc, latitude=v.natal.latitude,
                                longitude=v.natal.longitude, ayanamsa="kp")
        _KP_VIEW_CACHE[key] = (vkp, vkp.kp_significators())
    return _KP_VIEW_CACHE[key]


def kp_score(kps, planet, profile):
    """(fulfil, negate) = how many of the planet's KP significations fall in the
    matter's fulfilment vs negation houses."""
    h = set(kps.planet_signifies(planet))
    return len(h & profile.fulfil_houses), len(h & profile.negate_houses)


def chain_lords(v, when, levels=3):
    """The running Vimśottari MD>AD>PD lords at `when`."""
    return [c.lord for c in v.current_dasha("vimshottari", when, levels=levels)]


def pratyantar_midpoints(v, start, end) -> list:
    """Deterministic evaluation dates: the MIDPOINT of every Vimśottari
    pratyantar intersecting [start, end] (clipped) — a stable grid whose landing
    spot inside each pratyantar is not an accident of scan parameters."""
    out = []
    for m in v.dasha("vimshottari", levels=3):
        if m.end <= start or m.start >= end:
            continue
        for a in (m.sub_periods or []):
            if a.end <= start or a.start >= end:
                continue
            for p in (a.sub_periods or []):
                if p.end <= start or p.start >= end:
                    continue
                s2, e2 = max(p.start, start), min(p.end, end)
                out.append(s2 + (e2 - s2) / 2)
    return sorted(out)
