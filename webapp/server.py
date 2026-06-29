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
import urllib.error
import urllib.request
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
        points=_points(v), strengths=_strengths(v),
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
    "relevant Sahams. "
    "You MAY use Google Search to look up astrological PRINCIPLES, classical-text "
    "references (BPHS, Phaladeepika, Saravali, Jaimini Sūtras, KP, etc.) and "
    "general interpretation — but only to interpret the engine's numbers, never to "
    "fetch or replace the chart's own positions/dates. When you use a web source, "
    "briefly name it. Answer in the user's language (Hinglish is fine)."
)
GEMINI_MODELS = {"gemini-2.0-flash", "gemini-2.5-flash", "gemini-1.5-flash"}


def chat_json(body):
    """Server-side proxy to Google Gemini. The API key lives in the GEMINI_API_KEY
    env var (never in the browser); the chart JSON is injected as grounding."""
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
    contents = [dict(role=("user" if m.get("role") == "user" else "model"),
                     parts=[dict(text=str(m.get("content", "")))])
                for m in messages]
    payload = dict(system_instruction=dict(parts=[dict(text=sys)]),
                   contents=contents,
                   generationConfig=dict(maxOutputTokens=1600, temperature=0.6))
    if body.get("web", True):
        # Grounding with Google Search — gives Gemini live internet access. The
        # tool name differs between the 1.5 and 2.x model families.
        payload["tools"] = [{"google_search_retrieval": {}}
                            if model.startswith("gemini-1.5")
                            else {"google_search": {}}]
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent")
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            j = json.loads(r.read())
    except urllib.error.HTTPError as e:
        return dict(error=f"Gemini HTTP {e.code}: {e.read().decode()[:300]}")
    except Exception as e:
        return dict(error=f"{type(e).__name__}: {e}")
    try:
        cand = j["candidates"][0]
        parts = cand["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts).strip()
    except Exception:
        cand, text = {}, ""
    sources = []
    for ch in (cand.get("groundingMetadata", {}).get("groundingChunks") or []):
        w = ch.get("web") or {}
        if w.get("title") or w.get("uri"):
            sources.append(dict(title=w.get("title", ""), uri=w.get("uri", "")))
    return dict(text=text or "(empty response — model ne kuch return nahi kiya)",
                sources=sources)


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
