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
import threading
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
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
    return VedicChart.create(when=when, latitude=float(q["lat"][0]),
                             longitude=float(q["lon"][0]),
                             ayanamsa=q.get("ayanamsa", ["lahiri"])[0]), when


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
# Salience date-scan (the heavy triangulation timeline) — run as a background job
# because candidate_map is ~2s/window (a multi-year span takes 1–2 min), far too
# slow for a synchronous request. Client starts a job and polls for the result.
# --------------------------------------------------------------------------- #
_SCANS: dict = {}


def _scan_worker(job, params, domain, start, end, step_days):
    try:
        from interpreter.event_evidence import candidate_map
        from interpreter.significators import resolve
        v = _chart_from(params)
        if v is None:
            raise ValueError("chart params invalid")
        prof = resolve(domain)
        rows = candidate_map(v, prof, start, end, step_days=step_days)
        top = sorted(rows, key=lambda x: (-x.salience, x.start))[:8]
        windows = [dict(date=r.start.strftime("%Y-%m-%d"), chain=">".join(r.chain),
                        salience=round(r.salience, 3), systems=r.systems_firing,
                        convergence=round(r.convergence, 1),
                        kp=f"{r.kp_fulfil}/{r.kp_negate}",
                        nodes=[n for n, _ in r.firing_nodes()][:6]) for r in top]
        _SCANS[job] = dict(status="done", domain=prof.name, windows=windows,
                           scanned=len(rows), step=step_days, ts=time.time())
    except Exception as e:
        _SCANS[job] = dict(status="error", error=f"{type(e).__name__}: {e}",
                           ts=time.time())


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
    # The scan's cost ≈ number of distinct pratyantar-daśā periods sampled, and
    # each is skyfield-heavy. On a slow (free) instance a fine step over a multi-year
    # span never finishes. So ADAPT the step to the span: sample ~24 points max,
    # which bounds the work (coarser dates, but the scan actually completes).
    span_days = max(1, (end - start).days)
    step = max(int(q.get("step", ["30"])[0] or "30"), span_days // 24)
    step = max(15, min(120, step))
    params = {k: q.get(k, [""])[0] for k in ("when", "tz", "lat", "lon", "ayanamsa")}
    job = uuid.uuid4().hex[:12]
    _SCANS[job] = dict(status="running", ts=time.time())
    # prune old finished jobs (keep the store small)
    for j, s in list(_SCANS.items()):
        if s.get("status") != "running" and time.time() - s.get("ts", 0) > 900:
            _SCANS.pop(j, None)
    threading.Thread(target=_scan_worker,
                     args=(job, params, domain, start, end, step),
                     daemon=True).start()
    return dict(job=job)


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


def _summary(pack):
    """Hide the per-window CANDIDATE LEDGER (Multi-system toggle OFF)."""
    out, skip = [], False
    for ln in pack.splitlines():
        if "CANDIDATE LEDGER" in ln:
            skip = True
            out.append("  [per-window ledger hidden — Multi-system OFF]")
            continue
        if "TOP-RANKED WINDOWS" in ln:
            skip = False
        if not skip:
            out.append(ln)
    return "\n".join(out)


def events_json(q):
    from interpreter.event_evidence import render_domain
    from interpreter.significators import resolve
    v, _ = _chart(q)
    prof = resolve(q["domain"][0])
    start = datetime.strptime(q["start"][0], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end = datetime.strptime(q["end"][0], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    pack = render_domain(v, prof, start, end)
    if q.get("mode", ["full"])[0] != "full":
        pack = _summary(pack)
    return dict(domain=prof.name, pack=pack)


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
    "Answer in the user's language (Hinglish is fine)."
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
    "the TIME CONTEXT, and (b) tell the user that the actual ranked dated windows "
    "come from the 🔮 Salience scan (and to scan PAST years if the event may already "
    "have happened). Do NOT invent nodes, yogas or exact dates beyond the engine "
    "read and the daśā list. If a Salience-scan result is present in the context, "
    "narrate THOSE ranked windows as the timing answer."
)
GEMINI_MODELS = {"gemini-2.0-flash", "gemini-2.5-flash", "gemini-1.5-flash"}


def _chart_from(c):
    """Rebuild a VedicChart from the chat request's chart params (safe/None)."""
    if not c or not c.get("when"):
        return None
    try:
        return _chart({k: [str(c.get(k, ""))]
                       for k in ("when", "tz", "lat", "lon", "ayanamsa")})[0]
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


def _engine_read(v, question):
    """Fast deterministic triangulation read for a question's domain — the natal
    standing-witness balance + fired nodes + promise/tempo (NO slow timeline scan).
    Returns (domain_name, text) or (None, None) if the question maps to no domain."""
    try:
        from interpreter.significators import resolve
        prof = resolve(question)
    except Exception:
        return None, None
    try:
        from interpreter.event_evidence import (standing_balance,
                                                promise_and_tempo, _fmt_tempo)
        bal, fired = standing_balance(v, prof)
        pt = promise_and_tempo(v, prof)
    except Exception:
        return None, None
    verdict = ("blessed/PRO (tends to upgrade, not break)" if bal >= 1.0
               else "afflicted (loss/obstruction possible)" if bal < 0 else "mixed")
    nk = prof.natural_karaka.value if prof.natural_karaka else "-"
    lines = [f"domain={prof.name} | houses={prof.houses} karakas={prof.karakas}+{nk} "
             f"saham={prof.saham} varga=D{prof.varga}",
             f"STANDING-WITNESS net balance = {bal:+.2f} → {verdict}",
             "fired nodes (node: weight):"]
    for nm, c in sorted(fired, key=lambda x: -abs(x[1])):
        lines.append(f"  {'+' if c > 0 else '-'} {nm}: {c:+.2f}")
    lines += _fmt_tempo(pt)
    # A tier-3 derived domain is named after the raw query — show a tidy label.
    label = prof.name if len(prof.name) <= 20 else "house " + "/".join(
        str(h) for h in prof.houses)
    return label, "\n".join(lines)


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
    if v is not None and last_user:
        dom, read = _engine_read(v, last_user)
        if read:
            engine_domain = dom
            sys += ("\n\n" + CHAT_NARRATOR
                    + "\n\nENGINE TRIANGULATION (ground truth — narrate, don't "
                    f"recompute):\n{read}"
                    + "\n\nVIMŚOTTARI DAŚĀ (engine-exact mahā→antar — use ONLY "
                    "these dates for any daśā/antardaśā you cite; never state a "
                    f"daśā date not in this list):\n{_dasha_tree_text(v)}")
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
        return dict(error=_explain_gemini_error(code, msg))
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
                note=note)


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
            if u.path == "/api/events":
                return self._send(200, json.dumps(events_json(q)))
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
