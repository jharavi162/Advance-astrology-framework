"""Zero-dependency web frontend for the Advance-Astrology engine.

Run:  python -m webapp.server   (then open http://localhost:8000)

Pure stdlib http.server — no Flask/React/build step. Serves one HTML page and a
small JSON API that calls the SAME engine (VedicChart + interpreter) the CLI uses.
Panels: natal chart (South-Indian), planet table, house-lords, Vimśottari daśā
(mahā timeline + current chain), divisional charts (D9/D10/D…), Pañcāṅga, and the
domain event-evidence pack (salience ledger) on demand.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from zoneinfo import ZoneInfo

from advance_astrology import VedicChart, Planet
from advance_astrology.constants import SIGNS
from advance_astrology.nakshatra import nakshatra_of

HERE = os.path.dirname(os.path.abspath(__file__))
GRAHAS = [Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY, Planet.JUPITER,
          Planet.VENUS, Planet.SATURN, Planet.RAHU, Planet.KETU]
ABBR = {Planet.SUN: "Su", Planet.MOON: "Mo", Planet.MARS: "Ma", Planet.MERCURY: "Me",
        Planet.JUPITER: "Ju", Planet.VENUS: "Ve", Planet.SATURN: "Sa",
        Planet.RAHU: "Ra", Planet.KETU: "Ke"}


def _chart(q):
    when = datetime.strptime(q["when"][0], "%Y-%m-%d %H:%M").replace(
        tzinfo=ZoneInfo(q.get("tz", ["Asia/Kolkata"])[0]))
    v = VedicChart.create(when=when, latitude=float(q["lat"][0]),
                          longitude=float(q["lon"][0]),
                          ayanamsa=q.get("ayanamsa", ["lahiri"])[0])
    # Nāḍī kalatra-kāraka is gender-aware (Venus male / Mars female)
    v.gender = q.get("gender", [""])[0]
    return v, when


def _dig(v, p):
    s = str(v.dignity(p))
    return s.split(":")[-1].strip() if ":" in s else s


def _planets(v):
    out = []
    for p in GRAHAS:
        lon = float(v.longitudes[p])
        try:
            retro = bool(v.natal.placements[p].retrograde)
        except Exception:
            retro = False
        out.append(dict(name=p.value, ab=ABBR[p], sign=int(v.signs[p]),
                        sign_name=SIGNS[v.signs[p]], deg=round(lon % 30, 2),
                        house=int(v.house_of(p)), nak=nakshatra_of(lon).name,
                        dignity=_dig(v, p), retro=retro))
    return out


def _varga(v, n):
    vc = v.varga(n)
    cells = [[] for _ in range(12)]
    for p in GRAHAS:
        cells[int(vc.signs[p])].append(ABBR[p])
    return dict(asc=int(vc.ascendant_sign), cells=cells)


def _dasha_tree(v):
    """Full-life Vimśottari: every mahādaśā with its antardaśās (no as-of cut)."""
    out = []
    for m in v.dasha("vimshottari", levels=2):
        out.append(dict(
            lord=m.lord.value, start=m.start.date().isoformat(),
            end=m.end.date().isoformat(),
            sub=[dict(lord=a.lord.value, start=a.start.date().isoformat(),
                      end=a.end.date().isoformat()) for a in (m.sub_periods or [])]))
    return out


def _pt(lon):
    s = int(lon // 30) % 12
    return dict(sign=s, sign_name=SIGNS[s], deg=round(lon % 30, 2))


def _arudhas(v):
    return {k: dict(sign=s, sign_name=SIGNS[s % 12]) for k, s in v.arudhas().items()}


def _upagrahas(v):
    return {k: _pt(float(x)) for k, x in v.calculated_upagrahas().items()}


def _special_lagnas(v):
    return {k: _pt(float(x)) for k, x in v.special_lagnas().items()}


def _dasha_top(v):
    return [dict(lord=d.lord.value, start=d.start.date().isoformat(),
                 end=d.end.date().isoformat())
            for d in v.dasha("vimshottari", levels=1)]


HOUSE_SYSTEMS = ("placidus", "whole_sign", "equal", "porphyry", "regiomontanus")


def _kp_cusps(v, system="placidus"):
    """Bhāva table for the chosen house system: cusp · sign · sign/star/sub lord."""
    from advance_astrology.vedic.chalit import sidereal_cusps
    from advance_astrology.vedic.kp import kp_chain
    cu = sidereal_cusps(v, system)
    out = []
    for h in range(1, 13):
        lon = float(cu[h]); s = int(lon // 30) % 12; kc = kp_chain(lon)
        out.append(dict(house=h, sign=s, sign_name=SIGNS[s], deg=round(lon % 30, 2),
                        sign_lord=kc.sign_lord.value, star_lord=kc.star_lord.value,
                        sub_lord=kc.sub_lord.value))
    return out


def _chalit(v, system="placidus"):
    """Planets whose cusp-based (Chalit) house differs from the Rāśi house, for
    the chosen house system."""
    from advance_astrology.vedic.chalit import sidereal_cusps
    from advance_astrology.houses import house_of
    from advance_astrology.angles import to_zodiac
    cu = sidereal_cusps(v, system)
    out = []
    for p in GRAHAS:
        lon = float(v.longitudes[p])
        rashi = (to_zodiac(lon).sign_index - v.ascendant_sign) % 12 + 1
        ch = house_of(lon, cu)
        if ch != rashi:
            out.append(dict(ab=ABBR[p], planet=p.value, rashi=rashi, chalit=ch))
    return out


def _aspects(v):
    """Graha dṛṣṭi: each graha's aspected rāśis/bhāvas (with its special aspects)
    and which grahas fall under that aspect."""
    from advance_astrology.vedic.aspects import graha_aspect_houses
    asc = int(v.ascendant_sign)
    sign_of = {p: int(v.signs[p]) for p in GRAHAS}
    out = []
    for p in GRAHAS:
        src = sign_of[p]
        casts = []
        for dist in graha_aspect_houses(p):
            tgt = (src + dist - 1) % 12
            bhava = (tgt - asc) % 12 + 1
            on = [ABBR[q] for q in GRAHAS if sign_of[q] == tgt and q != p]
            casts.append(dict(dist=dist, sign=tgt, sign_name=SIGNS[tgt],
                              bhava=bhava, on=on))
        out.append(dict(ab=ABBR[p], planet=p.value, casts=casts))
    return out


# --------------------------------------------------------------------------- #
# Engine-stack date-scan — the daśā clock + KP + Nāḍī bundled as DATA. Run as a
# background job (kept from the old design) so the client starts a job and polls;
# the engine stack is fast, so most scans return almost immediately.
# --------------------------------------------------------------------------- #
_SCANS: dict = {}
# Only ONE scan computes at a time. On a small (free) instance parallel scan
# threads saturate the CPU and the HTTP server can't even serve the page — the
# app looks "stuck at loading". Later jobs wait at the gate (status "queued").
_SCAN_GATE = threading.Lock()


def _scan_worker(job, params, domain, start, end, step_days):
    _SCANS[job]["status"] = "queued"
    with _SCAN_GATE:
        _SCANS[job]["status"] = "running"
        _run_scan(job, params, domain, start, end, step_days)


def _run_scan(job, params, domain, start, end, step_days):
    """Engine-stack date-scan (data-only): the daśā clock's candidate windows
    (bhāva double-transits + significator antardaśās) tagged with the running
    chain + KP fulfil/negate + the Nāḍī kāraka/chain. No salience/verdict math —
    the AI reads the data. Keeps the _SCANS[job] shape the frontend polls."""
    try:
        from interpreter.significators import resolve
        from interpreter.engines import samanvaya
        v = _chart_from(params)
        if v is None:
            raise ValueError("chart params invalid")
        now = datetime.now(timezone.utc)
        if domain == "__macro__":
            from interpreter.domains import DOMAIN_PROFILES
            from interpreter.engines import ENGINES
            ranked = []
            for name, prof in DOMAIN_PROFILES.items():
                b = samanvaya(v, prof, start, end, intent="timing")
                dt = b.get("dasha_timing")
                kp = ENGINES["kp"].evaluate(v, prof, start, end)
                trigs = list(dt.transit_triggers) if dt else []
                upcoming = [t for t in trigs if t[1] >= now] or trigs
                nxt = upcoming[0] if upcoming else None
                promise = ("promised" if (kp and kp.hits_fulfil)
                           else "afflicted" if (kp and kp.hits_negate) else "mixed")
                ranked.append(dict(
                    domain=name, verdict=promise, triggers=len(trigs),
                    next_trigger=(nxt[0].strftime("%Y-%m-%d") if nxt else ""),
                    trigger=(nxt[2] if nxt else "")))
            ranked.sort(key=lambda r: -r["triggers"])
            _SCANS[job] = dict(status="done", macro=True, domain="macro",
                               windows=ranked[:9], scanned=len(ranked),
                               step=step_days, ts=time.time())
            return
        prof = resolve(domain)
        from interpreter.engines import ENGINES
        b = samanvaya(v, prof, start, end, intent="timing")
        dt, na = b.get("dasha_timing"), b.get("nadi")
        kp = ENGINES["kp"].evaluate(v, prof, start, end)   # promise/quality (KP is not routed for timing)

        def _chain_at(when):
            if not dt or not dt.vimshottari:
                return ""
            p = min(dt.vimshottari, key=lambda p: abs((p.start - when).days))
            return f"{p.md}>{p.ad}"

        def _kp_at(when):
            if not kp or not kp.windows:
                return ""
            w = min(kp.windows, key=lambda w: abs((w.when - when).days))
            return f"{w.fulfil}/{w.negate}"

        windows = []
        for s, e, what in (dt.transit_triggers if dt else []):
            windows.append(dict(date=s.strftime("%Y-%m-%d"), chain=_chain_at(s),
                                kp=_kp_at(s), trigger=what, kind="double-transit"))
        for p in (dt.vimshottari if dt else []):
            if p.active:
                windows.append(dict(date=p.start.strftime("%Y-%m-%d"),
                                    chain=f"{p.md}>{p.ad}", kp=_kp_at(p.start),
                                    trigger="daśā onset: " + ", ".join(p.active),
                                    kind="dasha-onset"))
        windows.sort(key=lambda w: w["date"])
        verdict = ("promised" if (kp and kp.hits_fulfil)
                   else "afflicted/denied" if (kp and kp.hits_negate) else "mixed")
        nadi = dict(karaka=(na.descriptor_karaka if na else ""),
                    nature=("; ".join(na.nature) if (na and na.nature) else "clean"),
                    chain=[dict(planet=m.planet, degree=m.degree, relation=m.relation,
                                when=m.when, signifies=m.signifies)
                           for m in (na.chain if na else [])])
        _SCANS[job] = dict(status="done", domain=prof.name, windows=windows[:30],
                           scanned=len(windows), step=step_days, verdict=verdict,
                           nadi=nadi, ts=time.time())
    except Exception as e:
        _SCANS[job] = dict(status="error", error=f"{type(e).__name__}: {e}",
                           ts=time.time())


_SCAN_KEYS: dict = {}


def _kick_scan(params, domain, start, end, step_hint=30):
    """Start (or REUSE) a salience scan; returns the job id. Identical requests
    within ~15 min share one job, so repeated chat questions don't pile up
    duplicate CPU-heavy scans."""
    key = (tuple(params.get(k, "") for k in
                 ("when", "tz", "lat", "lon", "ayanamsa", "gender")),
           domain.lower(), start.date().isoformat(), end.date().isoformat())
    old = _SCAN_KEYS.get(key)
    if old and old in _SCANS and _SCANS[old].get("status") in ("queued", "running",
                                                               "done"):
        return old
    # The scan's cost scales with the span (each node scans the ephemeris across
    # it), so ADAPT the step: sample ~24 points max so the job stays bounded.
    span_days = max(1, (end - start).days)
    step = max(step_hint, span_days // 24)
    step = max(15, min(120, step))
    job = uuid.uuid4().hex[:12]
    _SCANS[job] = dict(status="running", ts=time.time())
    _SCAN_KEYS[key] = job
    # prune old finished jobs (keep the store small)
    for j, s in list(_SCANS.items()):
        if s.get("status") != "running" and time.time() - s.get("ts", 0) > 900:
            _SCANS.pop(j, None)
    threading.Thread(target=_scan_worker,
                     args=(job, params, domain, start, end, step),
                     daemon=True).start()
    return job


def scan_start(q):
    """Kick off a salience date-scan; returns a job id to poll."""
    domain = (q.get("domain", [""])[0] or "").strip()
    if not domain:
        return dict(error="domain missing")
    try:
        start = datetime.strptime(q["start"][0], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end = datetime.strptime(q["end"][0], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except Exception:
        return dict(error="start/end (YYYY-MM-DD) required")
    params = {k: q.get(k, [""])[0]
              for k in ("when", "tz", "lat", "lon", "ayanamsa", "gender")}
    step_hint = int(q.get("step", ["30"])[0] or "30")
    return dict(job=_kick_scan(params, domain, start, end, step_hint))


def scan_status(q):
    job = q.get("job", [""])[0]
    return _SCANS.get(job, dict(status="unknown"))


def cusps_json(q):
    """Bhāva table + Chalit shifts for a chosen house system (/api/cusps)."""
    v, _ = _chart(q)
    system = q.get("houses", ["placidus"])[0]
    if system not in HOUSE_SYSTEMS:
        system = "placidus"
    return dict(system=system, cusps=_kp_cusps(v, system),
                chalit=_chalit(v, system))


def _points(v):
    """Sensitive points to plot/show: Bhṛgu Bindu, Indu Lagna, Sahams, kārakas."""
    bb = v.bhrigu_bindu(); il = int(v.indu_lagna()) % 12
    sah = {k: dict(sign=int(s.sign_index) % 12,
                   sign_name=SIGNS[int(s.sign_index) % 12],
                   deg=round(float(s.longitude) % 30, 2), lord=s.lord.value)
           for k, s in v.sahams().items()}
    ck = {role: p.value for role, p in v.chara_karakas().items()}
    return dict(bhrigu_bindu=_pt(bb),
                indu_lagna=dict(sign=il, sign_name=SIGNS[il]),
                sahams=sah, chara_karakas=ck)


def _strengths(v):
    """Ṣaḍbala (rūpa/ratio), Iṣṭa-Kaṣṭa, avasthās, and detected yogas."""
    sb = v.shadbala(); ik = v.ishta_kashta()
    bal = [dict(ab=ABBR[p], planet=p.value, rupa=round(s.total_rupa, 2),
                req=round(s.required_rupa, 2), pct=round(s.ratio * 100),
                strong=bool(s.is_strong)) for p, s in sb.items()]
    iks = [dict(ab=ABBR[p], planet=p.value, ishta=round(x.ishta, 1),
                kashta=round(x.kashta, 1)) for p, x in ik.items()]
    av = {}
    for p in GRAHAS:
        try:
            av[ABBR[p]] = v.avasthas(p)
        except Exception:
            pass
    yg = [dict(name=y.name, kind=y.kind, desc=y.description) for y in v.yogas()]
    return dict(shadbala=bal, ishta_kashta=iks, avasthas=av, yogas=yg)


VARGAS = (2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60)


def natal_json(q):
    v, when = _chart(q)
    cells = [[] for _ in range(12)]
    for p in GRAHAS:
        cells[int(v.signs[p])].append(ABBR[p])
    pan = v.panchanga()
    lagnesh = v.house_lord(1)
    return dict(
        input=dict(when=q["when"][0], lat=q["lat"][0], lon=q["lon"][0],
                   ayanamsa=q.get("ayanamsa", ["lahiri"])[0]),
        lagna=int(v.ascendant_sign), lagna_name=SIGNS[v.ascendant_sign],
        lagnesh=lagnesh.value,
        d1=dict(asc=int(v.ascendant_sign), cells=cells),
        planets=_planets(v),
        house_lords={h: v.house_lord(h).value for h in range(1, 13)},
        dasha=_dasha_top(v),
        arudhas=_arudhas(v), upagrahas=_upagrahas(v), special=_special_lagnas(v),
        vargas={str(n): _varga(v, n) for n in VARGAS},
        cusps=_kp_cusps(v), chalit=_chalit(v), sarva=v.sarvashtakavarga(),
        points=_points(v), strengths=_strengths(v), aspects=_aspects(v),
        panchanga=dict(tithi=getattr(pan.tithi, "name", str(pan.tithi)),
                       nakshatra=str(pan.nakshatra), yoga=str(pan.yoga),
                       karana=str(pan.karana), vara=str(pan.vara)),
    )


def transit_json(q):
    """Gochar: transiting planet positions on a chosen date, to plot from the
    natal Lagna."""
    v, _ = _chart(q)
    d = (q.get("date", [""])[0] or datetime.now().strftime("%Y-%m-%d"))
    when = datetime.strptime(d, "%Y-%m-%d").replace(hour=12, tzinfo=timezone.utc)
    pos = v.transits().positions(when)
    pl = []
    for p in GRAHAS:
        lon = float(pos[p]); s = int(lon // 30) % 12
        pl.append(dict(ab=ABBR[p], sign=s, sign_name=SIGNS[s], deg=round(lon % 30, 2)))
    return dict(date=d, lagna=int(v.ascendant_sign), planets=pl)


def dasha_json(q):
    """Lazy daśā drill: path = dot-separated indices (maha.antar.pratyantar).
    Returns the children of the node at that path (antar / pratyantar / sūkṣma)."""
    v, _ = _chart(q)
    raw = q.get("path", [""])[0]
    path = [int(x) for x in raw.split(".") if x.strip() != ""]
    periods = v.dasha("vimshottari", levels=len(path) + 1)
    lst = periods
    for idx in path:
        lst = lst[idx].sub_periods or []
    return dict(sub=[dict(lord=d.lord.value, start=d.start.date().isoformat(),
                          end=d.end.date().isoformat()) for d in lst])


CHAT_SYSTEM = (
    "You are an expert Vedic (Jyotish) astrologer and analyst. A deterministic "
    "engine has ALREADY computed the chart given below as JSON — treat every "
    "position, degree, lord, daśā date, cusp sub-lord, bala, yoga and saham in it "
    "as GROUND TRUTH. NEVER recompute, override or contradict those numbers, and "
    "never invent a position/degree/date that isn't given. Be specific, multivalent "
    "and concise: cite houses, lords, kārakas, cusp sub-lords, Ṣaḍbala and daśā when "
    "you reason. For timing, work from the Vimśottari mahādaśā chain plus the "
    "relevant Sahams. Draw on your own classical knowledge (BPHS, Phaladeepika, "
    "Saravali, Jaimini Sūtras, KP, etc.) to interpret — but if the chart JSON "
    "doesn't contain something, say so rather than guessing. "
    "Answer in the user's language (Hinglish is fine). "
    "ALWAYS end EVERY reply with a final section headed '📝 सरल सारांश' — 2 to 4 "
    "short lines in very simple Hinglish/Hindi that a non-astrologer easily "
    "understands: seedhe-seedhe kya answer hai (haan/nahi, kab, kaisa rahega), "
    "bina jyotish jargon ke. Yeh section hamesha sabse aakhir me ho."
)
CHAT_NARRATOR = (
    "ENGINE TRIANGULATION MODE: for this question the engine has ALREADY resolved "
    "the matter's significators and committed a deterministic read below — its net "
    "STANDING-WITNESS balance (blessed vs afflicted), the exact nodes that fired "
    "with weights, the PROMISE verdict, and the TEMPO (early / late / with-friction). "
    "Treat this as ground truth and build your answer on it: state whether the matter "
    "is promised and blessed or afflicted, WHY (name the fired nodes), and the tempo. "
    "IMPORTANT: this fast read carries the PROMISE and TEMPO but NO event date — it "
    "does not tell you WHEN. So for 'kab' (timing) do NOT present a single confident "
    "dated window as if it were computed. Instead: (a) name the daśā/antardaśā "
    "periods that are astrologically SUPPORTIVE (using ONLY the exact dates in the "
    "Vimśottari list below — never a date not in it), respecting past-vs-future per "
    "the TIME CONTEXT, and (b) if the engine's date-scan was auto-started for this "
    "question, close by saying the committed verdict (YES/NO + window) is being "
    "computed and will follow in a moment. NEVER ask the user to run a scan — it "
    "runs automatically. Do NOT invent nodes, yogas or exact dates beyond the engine "
    "read and the daśā list. If a Salience-scan result is present, do NOT just "
    "recite its ranked windows as the answer — feed them into THE TIMING METHOD "
    "below to converge on the date. Each scan window may carry "
    "the engine's OUTCOME-READ ('outcome': CHANGE/UPGRADE · LOSS/BREAK · "
    "transition-watch, plus a domain 'verdict' blessed/afflicted/mixed): state the "
    "outcome TYPE from it — e.g. upgrade-type vs loss/break-type event — but never "
    "assert a concrete real-world outcome (like 'divorce happened') beyond that "
    "type. If the scan carries a committed 'call', use its ANSWER (YES/NO — did "
    "the matter happen) + confidence to OPEN your reply (e.g. 'HAAN — hui hai'), "
    "but treat the call's 'window'/date as only the salience / KP-fulfilment "
    "FAVOURITE, NOT the final date. RE-DERIVE the date via THE TIMING METHOD below; "
    "if the method's day differs from the call's window — which is COMMON for an "
    "afflicted / break-prone matter, because salience under-ranks the true "
    "separative window — LEAD with the method's date and note the call's window "
    "was the clean-window bias. "
    "(The 'pinpoint' days are the engine's CANONICAL Nāḍī/BNN funnel (R.G. Rao): "
    "PRIMARY gate = Guru(jeeva) contacting the kāraka or the 7th-from-kāraka, plus "
    "Śani karma-approval (Jupiter+Saturn together = strongest); Śukra/Maṅgal "
    "degree-locks only REFINE the day — these are the step-4 degree-locks of the "
    "method below, not a standalone answer.) "
    "THE TIMING METHOD — the ONE way to answer 'when' (do NOT recite each system's "
    "separate date as rival verdicts; the systems are SUPPORT for one converged "
    "call). THEME-FIRST SUB-PERIOD: (1) read the "
    "matter's KARMIC THEME first from the standing verdict + Nāḍī nature — is the "
    "union LASTING/blessed or SEPARATIVE / break-prone? (2) find the TIMER by "
    "ROLE-DENSITY, NOT by a hard-coded planet: the scan carries 'significators' — "
    "the grahas RANKED by how many of the matter's roles each carries (7th-lord, "
    "7th CUSP SUB-LORD, kalatra-kāraka, spouse/gender kāraka [Mars=husband ♀], "
    "Darakaraka, in/aspecting-7th, 2nd/11th-lord, Lagna-lord — a planet counts "
    "even if its house-significations omit the 7th). The TOP role-density graha is "
    "the matter's timer: its daśā PERIOD frames the event — its MAHĀDAŚĀ if that "
    "is running, else its ANTAR/PRATYANTAR inside whatever MD runs (e.g. a top "
    "significator Venus that is not in its own MD still delivers marriage in its "
    "Venus-antardaśā within another MD). The ACTIVATOR sub-period is usually the "
    "spouse/gender kāraka or the Lagna-lord (self). Do NOT assume Venus — read "
    "whichever grahas top the 'significators' list; a window whose period-lords "
    "are none of the top significators cannot carry the event however it scores; "
    "(3) let the THEME pick the "
    "sub-period (pratyantara) inside it — a break-prone matter fires under a "
    "SEPARATIVE sub-lord (a node Rāhu/Ketu, or Saturn); a lasting one under a "
    "BENEFIC sub-lord (Jupiter/Venus); the event comes in the sub-period whose "
    "lord's NATURE matches the karma, not the 'nicest' one; (4) take the "
    "HIGHEST-score BNN pinpoint that falls in that significator + theme-matched "
    "sub-period (where the SAME significators trine/contact — including the "
    "SPOUSE/gender kāraka on its own natal degree, e.g. a female's husband-kāraka "
    "Mars returning to its natal degree) as the day — TRUST it over the salience "
    "ranking and the call's window; (5) verify with KP "
    "but READ IT THROUGH THE THEME — when the kāraka (Venus/7th) is signified and "
    "BNN has locked the day, a KP NEGATION-lean (6/8/12 lit) is NOT a denial, it "
    "is the SIGNATURE of a troubled/break-prone union (it happened, and it was "
    "built to strain). Do NOT down-rank or reject a kāraka-lit, BNN-locked, "
    "theme-matched day just because its KP fulfilment count is low. (Derive the "
    "theme from the chart alone — NEVER from a known outcome date; no calibration.) "
    "A window's 'systems' count = its convergence strength (more independent "
    "systems agreeing = surer); where the evidence genuinely splits into two "
    "theme-matched clusters, give primary + secondary rather than a false single "
    "date. "
    "INPUTS TO THE METHOD ABOVE (not separate answers): the scan's 'pinpoint' days "
    "are the BNN degree-locks for step 4 (smaller 'orb' = tighter lock = stronger; "
    "highest score first). The 'convergence' days carry a 'direction' (union = a "
    "benefic/lasting sub-period fired; break = a separative sub-period; troubled = "
    "strained) — use them to CONFIRM which theme-matched sub-period in step 3 "
    "carries the event, not as a rival day-list. NEVER claim a single day is THE "
    "event unless the user confirmed it — the engine reports where the positioning "
    "is strongest, it does not assume the date. "
    "CANONICAL MARRIAGE-TIMING STEP-ORDER (validated across charts — follow it "
    "exactly for a marriage 'kab' question): "
    "STEP 0 (promise, KP): 7th-cusp sub-lord signifies 2/7/11 → marriage happens; "
    "1/6/10/12 → denied/delayed. "
    "STEP 1 (MD, by AGE): among the mahādaśās running in the ADULT/marriageable "
    "band (use the native's age — NOT just the last few years), take the MD whose "
    "lord carries a 7th-ROLE: PLACED in the 7th, OR the 7th-lord, OR the 7th-cusp "
    "sub-lord. (A graha in the 7th is as strong a timer as the 7th-lord.) "
    "STEP 2 (AD): candidates in priority — 7th-occupants → 7th-lord → 7th-cusp "
    "sub-lord → Lagna-lord → Rāśi (Moon-sign) lord → Venus (kalatra-kāraka); take "
    "the one whose AD falls in the age-appropriate band. Use KP NEGATION only as a "
    "DISAMBIGUATOR for an INDIRECT/weak contender (a planet with no 7th-role, e.g. "
    "a general kāraka sitting in a dusthāna 6/8/12) — there, if it signifies no "
    "2/7/11 and sits in a dusthāna, it brings talk/proposals but WEAK conversion, "
    "so deprioritise it. Do NOT use negation to eliminate a STRONG Parashari role "
    "(7th-occupant / 7th-lord / cusp-sub-lord): those deliver even if they signify "
    "negation, because the MD carries the promise. "
    "TIE-BREAK between TWO-or-more STRONG AD candidates (both carry real 7th-roles "
    "and fit the age): (a) drop any candidate whose AD falls at an age the chart's "
    "own tempo contradicts (a 'late' chart rejects a too-early AD); (b) look at "
    "each AD-lord's OCCUPIED house — a graha gives its OCCUPIED house's results in "
    "its own period (BPHS), so even a 7th-LORD sitting in a dusthāna (6/8/12) "
    "delivers that dusthāna's results in its AD (disputes/obstacles/loss) and its "
    "marriage-CONVERSION is weak — e.g. a 7th-lord in the 6th gives conflict-"
    "results, talks without the wedding; (c) then confirm SEQUENTIALLY in time "
    "order with the 2b materialised-vs-broke check: test the earlier candidate's "
    "window first — if marriage-fulfilment is ABSENT there (engagement/talks "
    "only), move to the NEXT candidate and re-check. Conversion is proven by "
    "FULFILMENT in the window, never by the role alone. A planet with NO role at "
    "all in that chart (not lagna/rāśi-lord, not cusp-sub-lord, not in/aspecting "
    "the 7th) is simply ignored as an AD candidate. "
    "STEP 2b (MATERIALISED-vs-BROKE filter — when several ADs 'hit'): proposals/"
    "talks come in ALL the hit-ADs; only ONE converts. For each candidate AD run "
    "the rupture/negation check (the scan's reversal read): "
    "(i) marriage-FULFILMENT (2/7/11 significators lit + a BNN lock) ABSENT while "
    "only separative 6/8/12 fire → BROKEN engagement / talks that failed → REJECT "
    "that AD (e.g. a high-BNN window that the reversal read flags LOSS/BREAK with "
    "fulfilment≈0 is a rishtā that broke, NOT the wedding); "
    "(ii) marriage-FULFILMENT PRESENT → a marriage DID happen there — and if a "
    "separative/rupture signature CO-OCCURS, that is NOT a rejection, it means the "
    "marriage is DIVORCE-BOUND/troubled (the seed of separation sits at the wedding "
    "itself — e.g. a Rāhu/Ketu-PD wedding). NEVER reject a fulfilment-lit window "
    "just because it also carries a break-signature. Reject only PURE rupture "
    "WITHOUT fulfilment. "
    "STEP 3 (PD): priority again by 7th-role; but a SEPARATIVE-node pratyantara "
    "(Rāhu/Ketu) very often TRIGGERS the actual event (seen repeatedly) — do not "
    "dismiss it. Pick the PD by BNN (highest degree-lock). The Jupiter+Saturn "
    "DOUBLE-TRANSIT on the 7th house/lord is a CONFIRMING bonus, NOT a required "
    "gate — marriages fire without it; never push the date later just to catch a "
    "double-transit. "
    "STEP 4 (Sūkṣma): the BNN degree-lock (Jupiter-jeeva + the spouse/gender "
    "kāraka's own-degree return) fixes the exact day inside the chosen PD. "
    "DECISION-ORDER GUARDS (each of these has caused a verified wrong-date miss — "
    "enforce them): "
    "(G1) STRUCTURE FIRST, SCORE LATER: never pre-select the band/AD because it "
    "has the highest convergence, salience or KP-count and then fit the steps to "
    "it — the roles (STEP 1-2) and the rupture-filter (2b) choose the candidates; "
    "scores/BNN only pick the day among the SURVIVORS. An AD whose lord has NO "
    "7th-role does not become the answer merely by out-scoring a role-carrying "
    "AD (e.g. a Lagna-lord+Rāśi-lord AD outranks a no-role AD even at lower "
    "convergence). "
    "(G2) run STEP 2b on ALL competing ADs side-by-side (not only the early "
    "ones): report each candidate's LOSS/BREAK count; the clean fulfilment-lit AD "
    "wins over a rupture-flagged one. "
    "(G3) a transit that covers MORE THAN ONE candidate AD cannot tie-break "
    "between them (e.g. a year-long Jupiter stay / double-transit spanning both) "
    "— never cite it as the reason for choosing one of them. "
    "(G4) compare BNN degree-locks ACROSS all surviving candidate ADs — never "
    "only inside a pre-chosen band; the whole-span strongest lock in a surviving "
    "AD is the day-anchor. "
    "(G5) KP-count is for the PROMISE (STEP 0) and the indirect-contender "
    "disambiguation (STEP 2) — never a ranking metric for picking the date. "
    "AUDIT-TRAIL FORMAT for a marriage-'kab' answer (keep this presentation "
    "shape): 1) Chart Evidence (lagna, 7th house/lord, karakas, running MD); "
    "2) Promise & Tempo (STEP 0 + early/late + quality); 3) Candidate scan — a "
    "TABLE of ALL candidate ADs with columns: window, 7th-role (or 'none'), "
    "rupture-flag (LOSS/BREAK count), verdict keep/reject WITH the reason; "
    "4) Pinpoint — PD + the BNN locks compared across survivors; 5) Core "
    "Synthesis (one committed window/date + quality + confidence + which steps "
    "converged). State explicitly WHY each rejected AD was rejected. "
    "If "
    "the call carries a 'next' window, state it as the engine's committed "
    "UPCOMING window. CRITICAL KP rule: AFFLICTION ≠ DENIAL. An afflicted/"
    "troubled standing describes the event's QUALITY (troubled/with-friction), "
    "NEVER whether it happened — existence comes only from the call's promise/"
    "denial + elapsed-window logic. Do not hedge a committed call. HONESTY RULE: "
    "questions the engine cannot decide mechanically — SAME person vs a NEW "
    "person, kaun/kis se, anything about a third party without their chart — "
    "answer briefly and label that part '(interpretive — engine-committed "
    "nahi)'; never present it as an engine verdict. "
    "NĀḌĪ VERDICT (give it for EVERY question, any domain, trine/golden-relation "
    "method): the engine read carries a 'NĀḌĪ (BNN...)' line with the matter's "
    "kāraka and its nature. ALWAYS include a short 'Nāḍī:' verdict — for a "
    "'kaisa/nature' question state that nature line (Rahu-saṅga = sudden/"
    "unconventional, Ketu-saṅga = delay/break-prone, vakri = repeat-pattern, or "
    "clean = smooth); for a 'kab/when' question give the day-level 'pinpoint' "
    "date(s) if the scan carries them. This Nāḍī voice is independent of KP/"
    "Jaimini — present it as its own line, not merged into them. "
    "NĀḌĪ CHAIN: the read also carries a 'NĀḌĪ CHAIN' — the hero (kāraka) and the "
    "planets conjunct/trine (1/5/9) it, in DEGREE ORDER. Narrate this as the "
    "Bhrigu-Nandi STORY, left→right: a member tagged [pre] (lower degree than the "
    "hero) already acted BEFORE the event / was pre-existing; [post] (higher "
    "degree) unfolds AFTER it. Apply each planet's significations from the chain "
    "(e.g. Ketu=break/cut, Rahu=foreign/inter-caste/affair, Jupiter=blessing/"
    "expansion, Saturn=delay/karmic, Mercury=business/communication, "
    "Moon=instability/mood) and a '(R)' vakri member = repeat/revisit. Weave it "
    "into one flowing sentence-story, not a dry list. "
    "SECOND / NEXT PARTNER: if the domain is a 'second-…' / 'third-…' matter "
    "(the engine has shifted it to the Nth-marriage axis — 9th house for the "
    "2nd spouse, per the 3rd-from-7th rule), say so. ALSO read the BNN chain per "
    "the transcript: a benefic AFTER the hero — especially one that follows a "
    "Ketu-cut in the chain — is the NEXT/second partner, and Rahu just ahead of "
    "the hero = multiple relationships / remarriage after a break. Keep the "
    "house-based read (Vedic) and the chain-based read (BNN) as two independent "
    "voices; do not merge them."
)
GEMINI_MODELS = {"gemini-2.0-flash", "gemini-2.5-flash", "gemini-1.5-flash"}


def _chart_from(c):
    """Rebuild a VedicChart from the chat request's chart params (safe/None)."""
    if not c or not c.get("when"):
        return None
    try:
        return _chart({k: [str(c.get(k, ""))]
                       for k in ("when", "tz", "lat", "lon", "ayanamsa",
                                 "gender")})[0]
    except Exception:
        return None


def _dasha_tree_text(v):
    """Full-life Vimśottari mahā→antar with engine-exact dates, compact text."""
    lines = []
    for m in v.dasha("vimshottari", levels=2):
        lines.append(f"{m.lord.value} {m.start.date()}→{m.end.date()}")
        for a in (m.sub_periods or []):
            lines.append(f"  {m.lord.value[:2]}-{a.lord.value} "
                         f"{a.start.date()}→{a.end.date()}")
    return "\n".join(lines)


# Timing-question detection for the chat's AUTO salience scan: does the question
# ask WHEN, and does its tense point at the past (event may already have happened)?
_TIMING_RE = re.compile(
    r"(kab|when|kis\s+(saal|varsh|year)|timing|window|date|hogi|hoga|hui|hua|"
    r"milegi|milega|banega|banegi|payega|payegi|rahega|rahegi|hone\s*wala|"
    r"hone\s*wali|kitne\s+(din|mahine|saal))", re.I)
_PAST_RE = re.compile(
    r"(hui|hua|hue|huye|ho\s+(gaya|gayi|gaye|chuk\w*)|chuki|chuka|chuke|"
    r"\btha\b|\bthi\b|already|when\s+did|happened)", re.I)
_YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2})\b")
_REL_PAST_RE = re.compile(
    r"(pichh?le|beete|last)\s+(\d{1,2})\s*(saal|varsh|years?|yrs?)", re.I)
_REL_FUT_RE = re.compile(
    r"(agle|aane\s*wale|next)\s+(\d{1,2})\s*(saal|varsh|years?|yrs?)", re.I)
_FUT_RE = re.compile(
    r"(hogi|hoga|milegi|milega|banega|banegi|payega|payegi|rahega|rahegi|"
    r"aayega|aayegi|hone\s*wal[ai]|\bwill\b|\bfuture\b|aage)", re.I)
# Open "which life-events happened?" question → multi-domain MACRO scan.
_MACRO_RE = re.compile(
    r"(kya\s*kya|hot\s*events?|big\s*events?|bade\s*events?|"
    r"events?\s*(kya|hue|huye|honge)|kya\s*(hua|hue|huye|hoga|honge)|"
    r"life\s*events?|what\s*happened|sabse\s*(bada|bade)\s*event)", re.I)


def _auto_scan_window(question, today, born=None):
    """(start, end) for the auto scan. Priority: explicit years ("2015 se 2018" →
    that range, span capped at 6 yrs) → STORY-mode (past narrative + future ask →
    last 2 yrs THROUGH next 3 yrs, one span) → relative ranges ("pichle 3 saal" /
    "agle 2 saal") → tense.

    For a PAST-tense question with the birth date known, scan the ADULT band BY
    AGE (from age 18 to today) rather than a flat last-4-years — a life event
    like marriage can have happened long ago, and capping at 4 yrs silently
    misses it (e.g. a wedding 10 yrs back). `_kick_scan` adapts the step to keep
    even a wide span bounded, so the AI can then place the exact daśā (MD by age
    → AD → PD → BNN) inside the correct band."""
    years = sorted(int(y) for y in _YEAR_RE.findall(question))
    if years:
        y0, y1 = years[0], min(years[-1], years[0] + 6)
        return (datetime(y0, 1, 1, tzinfo=timezone.utc),
                datetime(y1, 12, 31, tzinfo=timezone.utc))
    if _PAST_RE.search(question) and _FUT_RE.search(question):
        # "…hua tha / tal gayi … ab aage kab hogi?" → one span covering both,
        # so the verdict reads the delivered/contested past AND the next window.
        return today - timedelta(days=2 * 365), today + timedelta(days=3 * 365)
    m = _REL_PAST_RE.search(question)
    if m:
        n = min(int(m.group(2)), 6)
        return today - timedelta(days=n * 365), today
    m = _REL_FUT_RE.search(question)
    if m:
        n = min(int(m.group(2)), 6)
        return today, today + timedelta(days=n * 365)
    if _PAST_RE.search(question):
        # AGE-appropriate band: from adulthood (age 18) to today, so an event
        # years ago is inside the scan. Cap the span at 24 yrs to stay bounded.
        if born is not None:
            adult = datetime(born.year + 18, born.month, min(born.day, 28),
                             tzinfo=timezone.utc)
            start = max(adult, today - timedelta(days=24 * 365))
            if start <= today - timedelta(days=365):
                return start, today
        return today - timedelta(days=4 * 365), today
    return today, today + timedelta(days=3 * 365)


def _engine_read(v, question):
    """Deterministic grounding for the AI from the data-only engine stack — KP
    promise/quality + the daśā clock (significators + bhāva double-transits) +
    Jaimini + Nāḍī. No convergence math; the AI narrates. Returns
    (domain_label, text) or (None, None) if the question maps to no domain."""
    try:
        from interpreter.significators import resolve
        from interpreter.engines import samanvaya
        prof = resolve(question)
    except Exception:
        return None, None
    now = datetime.now(timezone.utc)
    start, end = now - timedelta(days=6 * 365), now + timedelta(days=4 * 365)
    try:
        b = samanvaya(v, prof, start, end, question=question)
    except Exception:
        return None, None
    L = [f"domain={prof.name} | houses={prof.houses} | intent={b.intent}"]
    kp = b.get("kp")
    if kp:
        promise = ("promised (sub-lord signifies fulfil %s)" % list(kp.hits_fulfil)
                   if kp.hits_fulfil else
                   "denied/afflicted (sub-lord signifies only negation %s)"
                   % list(kp.hits_negate) if kp.hits_negate else "unclear")
        L.append(f"KP (promise/quality): H{prof.houses[0]}-cusp sub-lord "
                 f"{kp.cusp_sublord} signifies {list(kp.cusp_signifies)} → {promise}")
    dt = b.get("dasha_timing")
    if dt:
        L.append("SIGNIFICATORS (the clock): " + ", ".join(
            f"{s.label}={s.planet.value}" for s in dt.significators))
        act = [p for p in dt.vimshottari if p.active]
        if act:
            L.append("significator antardaśās: " + "; ".join(
                f"{p.start.date()}→{p.end.date()} {p.md}>{p.ad} [{','.join(p.active)}]"
                for p in act[:8]))
        if dt.transit_triggers:
            L.append("bhāva double-transits (PRIMARY triggers — a window on the "
                     "matter's house is a candidate date): " + "; ".join(
                         f"{s.date()}→{e.date()} {w}"
                         for s, e, w in dt.transit_triggers[:6]))
    ja = b.get("jaimini")
    if ja:
        x = []
        if ja.upapada_sign:
            x.append(f"UL={ja.upapada_sign}")
        if ja.domain_arudha:
            x.append("Arudha " + str(ja.domain_arudha))
        if ja.chara_karakas:
            x.append("chara-kāraka " + str(ja.chara_karakas))
        if x:
            L.append("JAIMINI: " + " | ".join(x))
    na = b.get("nadi")
    if na:
        L.append(f"NĀḌĪ (BNN): kāraka={na.descriptor_karaka}; nature="
                 + ("; ".join(na.nature) or "clean (smooth/straightforward)"))
        if na.chain:
            L.append("NĀḌĪ chain (degree-order = chronology, read left→right): "
                     + "  →  ".join(
                         f"{m.planet} {m.degree}° {m.relation}"
                         f"[{'HERO' if 'HERO' in m.when else 'pre' if 'before' in m.when else 'post'}]"
                         f" — {m.signifies}" for m in na.chain))
    label = prof.name if len(prof.name) <= 20 else "house " + "/".join(
        str(h) for h in prof.houses)
    return label, "\n".join(L)


def _gemini_post(model, payload, key):
    """POST to Gemini; returns (True, json) or (False, (http_code, message))."""
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent")
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return True, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return False, (e.code, e.read().decode()[:800])
    except Exception as e:
        return False, (0, f"{type(e).__name__}: {e}")


def _explain_gemini_error(code, msg):
    """Turn a raw Gemini error into a short, actionable Hinglish message."""
    detail = msg
    try:
        detail = json.loads(msg).get("error", {}).get("message", msg)
    except Exception:
        pass
    if code == 429:
        if "PerDay" in msg or "per day" in msg.lower():
            scope = "daily (RPD) free-tier limit khatam"
            tip = "Kal try karo, ya AI Studio me billing enable karke higher quota lo."
        elif "PerMinute" in msg or "per minute" in msg.lower():
            scope = "per-minute (RPM) limit hit"
            tip = "~1 minute ruk ke dobara bhejo."
        else:
            scope = "free-tier quota/rate limit"
            tip = "Thodi der baad ya doosre model se try karo."
        import re
        m = re.search(r'retryDelay"?:?\s*"?(\d+)s', msg)
        if m:
            tip += f" (Google suggests ~{m.group(1)}s wait.)"
        return f"Gemini 429 — {scope}. {tip}  [Google: {detail}]"
    return f"Gemini HTTP {code}: {detail}"


def chat_json(body):
    """Server-side proxy to Google Gemini. The API key lives in the GEMINI_API_KEY
    env var (never in the browser); the engine-computed chart JSON is injected as
    grounding. No web search — the model reasons from its own knowledge + the chart
    (Google Search grounding isn't usable on the free tier)."""
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        return dict(error="GEMINI_API_KEY server par set nahi hai. Render → "
                          "Environment me GEMINI_API_KEY daalo (aistudio.google.com "
                          "se free key).")
    model = body.get("model") or "gemini-2.0-flash"
    if model not in GEMINI_MODELS:
        model = "gemini-2.0-flash"
    ctx = body.get("context") or {}
    messages = body.get("messages") or []
    sys = CHAT_SYSTEM + "\n\nCHART (engine-computed, ground truth):\n" + json.dumps(ctx)
    # Fast engine-triangulation grounding: if the latest question maps to a domain,
    # run the cheap standing-witness + promise/tempo read and switch to narrator mode.
    engine_domain = ""
    last_user = next((m.get("content", "") for m in reversed(messages)
                      if m.get("role") == "user"), "")
    v = _chart_from(body.get("chart"))
    if v is not None:
        today = datetime.now(timezone.utc).date()
        born = v.when_utc.date()
        age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        sys += (f"\n\nTIME CONTEXT: today = {today.isoformat()}; native born "
                f"{born.isoformat()} (~{age} years old NOW). A past-tense question "
                "(\"kab hui / kab hua\") means the event may ALREADY have happened — "
                "weigh past daśā windows up to today and do NOT default to the "
                "future; a future-tense question looks ahead from today.")
    scan_meta = None
    # "(auto)" follow-ups narrate an already-delivered scan — never re-kick one.
    allow_kick = not last_user.startswith("(auto)")
    if v is not None and last_user and _MACRO_RE.search(last_user):
        # Open "kaun-se bade events?" → multi-domain macro scan, not one domain.
        s0, e0 = _auto_scan_window(last_user, datetime.now(timezone.utc), born=born)
        prev = (ctx or {}).get("last_salience_scan") or {}
        if allow_kick and not (prev.get("domain") == "macro"
                               and prev.get("range") == f"{s0.year}–{e0.year}"):
            job = _kick_scan(body.get("chart") or {}, "__macro__", s0, e0)
            scan_meta = dict(job=job, domain="macro", from_y=s0.year, to_y=e0.year)
        engine_domain = "macro (sab life-areas)"
        sys += ("\n\nMACRO MODE: the user asks WHICH life-events stood out in a "
                "window. The engine is ranking ALL life-areas (marriage, career, "
                "children, wealth, mother, father, illness, education, relocation) "
                "by stand-out salience spike in the background. If the context has "
                "a last_salience_scan with per-domain entries, answer FROM it: name "
                "the top areas, their peak month, daśā chain AND each area's "
                "engine outcome-read ('outcome' CHANGE/UPGRADE · LOSS/BREAK · "
                "transition-watch + 'verdict' blessed/afflicted) and its committed "
                "'call' (answer YES/NOT-YET/NO + confidence + window) — lead with "
                "the calls: which areas the engine says DID see an event (YES), "
                "when, and of what TYPE/quality. AFFLICTION ≠ DENIAL: afflicted "
                "means troubled quality, never 'did not happen'. Still never "
                "assert a concrete real-world outcome (e.g. 'divorce'). If the "
                "scan hasn't landed yet, say the multi-domain scan is running and "
                "give only a brief chart-level overview — do NOT guess events."
                + "\n\nVIMŚOTTARI DAŚĀ (engine-exact mahā→antar — use ONLY these "
                f"dates for any daśā you cite):\n{_dasha_tree_text(v)}")
    elif v is not None and last_user:
        dom, read = _engine_read(v, last_user)
        if read:
            engine_domain = dom
            sys += ("\n\n" + CHAT_NARRATOR
                    + "\n\nENGINE TRIANGULATION (ground truth — narrate, don't "
                    f"recompute):\n{read}"
                    + "\n\nVIMŚOTTARI DAŚĀ (engine-exact mahā→antar — use ONLY "
                    "these dates for any daśā/antardaśā you cite; never state a "
                    f"daśā date not in this list):\n{_dasha_tree_text(v)}")
            # AUTO salience scan for timing questions: kick (or reuse) the heavy
            # dated-window scan in the background; the frontend polls the job and
            # asks for a follow-up narration once the engine windows land.
            # Explicit years, past-tense ("ho chuki hai ya nahi?") and future
            # markers all count as a timing ask — any of them kicks the scan
            # that produces the committed verdict call.
            if allow_kick and (_TIMING_RE.search(last_user)
                               or _PAST_RE.search(last_user)
                               or _YEAR_RE.search(last_user)):
                s0, e0 = _auto_scan_window(last_user, datetime.now(timezone.utc), born=born)
                prev = (ctx or {}).get("last_salience_scan") or {}
                same = (prev.get("domain") == dom
                        and prev.get("range") == f"{s0.year}–{e0.year}")
                if not same:   # a new domain OR a new range → fresh scan
                    job = _kick_scan(body.get("chart") or {}, dom, s0, e0)
                    scan_meta = dict(job=job, domain=dom,
                                     from_y=s0.year, to_y=e0.year)
    if scan_meta:
        sys += ("\n\nNOTE: the engine's salience date-scan HAS been auto-started "
                "for this question — the committed verdict (YES/NO + window) will "
                "follow as a separate message in a minute or two. Say so; do not "
                "hedge and do not ask the user to run anything.")
    contents = [dict(role=("user" if m.get("role") == "user" else "model"),
                     parts=[dict(text=str(m.get("content", "")))])
                for m in messages]
    payload = dict(system_instruction=dict(parts=[dict(text=sys)]),
                   contents=contents)
    # On a 429 (free-tier quota), try the other free models before giving up —
    # different models have separate quotas. Stop on success or a non-429 error.
    note = ""
    ok = res = None
    tried = []
    for mdl in (model, "gemini-2.5-flash", "gemini-2.0-flash"):
        if mdl in tried:
            continue
        tried.append(mdl)
        # Thinking tokens count against maxOutputTokens, so give a big total budget
        # (Devanāgarī is token-heavy too). For the 2.5 "thinking" models keep
        # thinking ON — it materially improves the triangulation reasoning — but
        # BOUND it so it can't eat the whole budget and truncate the answer:
        # 4096 for thinking, leaving ~4096 for the visible reply.
        gen = dict(maxOutputTokens=8192, temperature=0.6)
        if mdl.startswith("gemini-2.5"):
            gen["thinkingConfig"] = {"thinkingBudget": 4096}
        payload["generationConfig"] = gen
        ok, res = _gemini_post(mdl, payload, key)
        if ok:
            if mdl != model:
                note = f"{model} pe 429 (quota) — {mdl} se answer diya."
            break
        if res[0] != 429:
            break  # non-quota error (e.g. bad key) — other models won't help
    if not ok:
        code, msg = res
        # Even when the LLM is out of quota, the ENGINE's scan was already
        # kicked — hand its job back so the frontend can still show the
        # deterministic windows + committed CALL (no Gemini needed for those).
        return dict(error=_explain_gemini_error(code, msg), scan=scan_meta)
    j = res
    try:
        cand = j["candidates"][0]
        parts = cand["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts).strip()
    except Exception:
        cand, text = {}, ""
    if cand.get("finishReason") == "MAX_TOKENS":
        note = (note + " · " if note else "") + \
            "⚠ jawab lamba tha aur token-limit pe cut gaya — thoda specific poochho."
    if engine_domain:
        tag = f"🧩 engine triangulation use hui — domain: {engine_domain}"
        note = (note + " · " + tag) if note else tag
    return dict(text=text or "(empty response — model ne kuch return nahi kiya)",
                note=note, scan=scan_meta)


class H(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        b = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_POST(self):
        u = urlparse(self.path)
        try:
            if u.path == "/api/chat":
                n = int(self.headers.get("Content-Length", "0") or "0")
                body = json.loads(self.rfile.read(n) or b"{}")
                return self._send(200, json.dumps(chat_json(body)))
            return self._send(404, json.dumps({"error": "not found"}))
        except Exception as e:
            return self._send(500, json.dumps({"error": f"{type(e).__name__}: {e}"}))

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        try:
            if u.path in ("/", "/index.html"):
                with open(os.path.join(HERE, "index.html"), "rb") as f:
                    return self._send(200, f.read(), "text/html; charset=utf-8")
            # static assets (PWA manifest + icons) — served from the webapp dir
            if u.path in ("/manifest.json", "/icon-192.png", "/icon-512.png",
                          "/apple-touch-icon.png"):
                fn = os.path.basename(u.path)
                ctype = ("application/manifest+json" if fn.endswith(".json")
                         else "image/png")
                with open(os.path.join(HERE, fn), "rb") as f:
                    return self._send(200, f.read(), ctype)
            if u.path == "/api/natal":
                return self._send(200, json.dumps(natal_json(q)))
            if u.path == "/api/dasha":
                return self._send(200, json.dumps(dasha_json(q)))
            if u.path == "/api/transit":
                return self._send(200, json.dumps(transit_json(q)))
            if u.path == "/api/cusps":
                return self._send(200, json.dumps(cusps_json(q)))
            if u.path == "/api/scan":
                return self._send(200, json.dumps(scan_start(q)))
            if u.path == "/api/scan_status":
                return self._send(200, json.dumps(scan_status(q)))
            return self._send(404, json.dumps({"error": "not found"}))
        except Exception as e:
            return self._send(500, json.dumps({"error": f"{type(e).__name__}: {e}"}))

    def log_message(self, *a):
        pass


def main():
    port = int(os.environ.get("PORT", "8000"))
    print(f"Astrology frontend → http://localhost:{port}  (Ctrl-C to stop)")
    ThreadingHTTPServer(("0.0.0.0", port), H).serve_forever()


if __name__ == "__main__":
    main()
