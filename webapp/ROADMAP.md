# Frontend — phased plan & notes

The frontend is built in **phases**. This file records the agreed direction so any
future session continues the same way (read this before changing `webapp/`).

## Current state — Phase 0 (MVP, shipped)
- `webapp/server.py` (stdlib `http.server`, zero deps) + `webapp/index.html` (one page).
- Panels: Rāśi (D1) South-Indian chart · planet table · house-lords · Vimśottari
  mahādaśā timeline + active chain · divisional charts (D9/D10/D2/D4/D7) · Pañcāṅga ·
  on-demand domain event-evidence pack (salience ledger; any word → significators).
- **Mobile-responsive** (iPhone/iPad): columns stack < 860px, 16px inputs (no iOS
  zoom), touch-sized buttons, chart scales.

## NOTE 1 — Backend will keep changing; keep the frontend DECOUPLED
- The **`/api/*` JSON contract is the only seam.** The HTML/JS is a thin client —
  it never imports engine code, it only fetches JSON. So when the backend evolves
  (new nodes, new daśās, KP changes, new domains), the change flows to the frontend
  **only through the JSON shape** — update the endpoint's dict + the render fn, not a
  rewrite. Keep all engine calls inside `server.py` (`natal_json` / `events_json`).
- Rule: a backend change should require touching at most (a) the relevant
  `*_json()` builder in `server.py` and (b) its render function in `index.html`.

## NOTE 2 — Target layout: chart/calcs on the LEFT, CHAT with Claude on the RIGHT
- The destination UX is **two-pane**: left = chart + all calculations (what we have
  now); right = a **chat space** where the user talks to Claude to *understand and
  analyse the calculations shown on the left*.
- The chat must be **context-aware of the left pane**: the current chart's natal
  JSON + the visible event-ledger should be passed to the model as context so the
  conversation is grounded in the exact numbers on screen (not a generic chat).
- Implementation when we get there: **React or Flask is fine** (no need to stay on
  stdlib). Likely React front + a small API that (a) serves the engine JSON and
  (b) proxies a chat endpoint to Claude with the left-pane context injected.

## Phase backlog (rough order)
1. **Phase 1 — two-pane shell + chat:** add the right-side chat pane; wire it to an
   LLM endpoint with the left-pane chart/ledger as grounded context. (React or Flask.)
2. **Phase 2 — richer panels:** North-Indian chart option; Jaimini (chara-kārakas,
   Arudha/UL); KP cusp sub-lord table; aspects/dṛṣṭi lines; more vargas; Aṣṭakavarga.
3. **Phase 3 — daśā explorer:** scrub a date to see the active chain across ALL
   catalogue systems (Vimśottari/Yoginī/Aṣṭottarī/Muddā/Chara/Nārāyaṇa/Sudasā) + the
   gochara of the day; click a salience window to expand its firing nodes.
4. **Phase 4 — muhurta tool:** day/time scan UI (the muhurta logic we prototyped).

## Run it
```
python -m webapp.server        # → http://localhost:8000   (PORT=xxxx to change)
```

### Testing on an iPhone / iPad
The server binds `0.0.0.0`, so any device that can reach the host works:
- **Same Wi-Fi (simplest):** run on a laptop, find its LAN IP (`ipconfig getifaddr en0`
  on macOS), then on the phone open `http://<laptop-ip>:8000`.
- **From this remote container:** use the environment's port-preview/forward for
  port 8000 (open that URL on the phone), **or** a tunnel, e.g.
  `cloudflared tunnel --url http://localhost:8000` → gives an https URL openable on
  any phone.
- The UI is responsive, so it renders cleanly on phone/tablet screens.
