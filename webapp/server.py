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
        dasha=_dasha_tree(v),
        vargas={str(n): _varga(v, n) for n in (9, 10, 2, 4, 7)},
        panchanga=dict(tithi=getattr(pan.tithi, "name", str(pan.tithi)),
                       nakshatra=str(pan.nakshatra), yoga=str(pan.yoga),
                       karana=str(pan.karana), vara=str(pan.vara)),
    )


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


class H(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        b = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

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
