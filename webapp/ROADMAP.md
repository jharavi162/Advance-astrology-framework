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

## NOTE 2 — In-browser Claude chat was DROPPED (see why) → deterministic panels instead
- We tried an in-browser chat to Claude. **Blocker:** a direct browser call needs a
  paid Anthropic **API key** (`sk-ant-…`) — a claude.ai *subscription* cannot drive
  it. So the chat is not usable for the owner and was removed.
- **Replacement (shipped):** the right pane is now all-deterministic, engine-only
  panels (no external calls, no key): **Bhāva & cusps (KP)** table (Placidus cusp ·
  sign · sign/star/sub lord + Bhāva-Chalit shifts), **Bala & yogas** (Ṣaḍbala bars ·
  Iṣṭa/Kaṣṭa · detected yogas · avasthās), **Jaimini & sensitive points** (chara
  kārakas · Bhṛgu Bindu · Indu Lagna · Sahams). Plus chart layer toggles for
  Arudhas, Upagrahas, Points (BB/IL/Saham) and Aṣṭakavarga bindus.
- **Chat is back via a free provider (shipped):** option (a) above, with **Google
  Gemini** (free tier, key from aistudio.google.com). The key is a **server-side env
  var `GEMINI_API_KEY`** (never in the browser); `POST /api/chat` (`chat_json` in
  server.py) proxies to Gemini and injects the chart JSON as grounding so the model
  reasons only from engine-computed numbers. The deterministic panels stay — chat is
  additive. Set the key in Render → Environment (see `render.yaml` envVars).
- **No web search.** We tried Google Search grounding but the free tier gives it a
  separate, tiny quota and a pure AI-Studio key (no billing) rejects it — so it was
  removed; the model interprets from its own knowledge + the chart only. (NOTE: a
  429 is then a *plain model* free-tier rate/daily limit, not a search issue —
  `chat_json` explains RPM vs RPD and falls back to gemini-2.0-flash on 429.)
- **Engine-grounded chat (shipped, hybrid):** the chat is now wired to the
  engine's own triangulation. The frontend sends the chart params with each
  message; `chat_json` resolves the question to a domain (`significators.resolve`)
  and, if it maps, runs the **fast** deterministic read — `standing_balance` (net
  pro/anti witness pattern + the exact fired nodes & weights) + `promise_and_tempo`
  (promise verdict, tempo early/late/friction, kāraka strength). That read is
  injected as GROUND TRUTH and the system prompt switches to NARRATOR mode (explain
  the engine's verdict + daśā; don't invent nodes/dates). Non-domain questions
  (e.g. "personality") fall back to plain chart interpretation.
  - **Why not the full salience timeline synchronously:** `candidate_map` scans the
    ephemeris across the span — too slow for a chat turn even after the transit
    position memo (engine, 2026-07-02) made it ~3.8× faster.
  - **AUTO salience integration (shipped):** a timing question ("kab hui/hogi…")
    now auto-kicks the salience scan in the background (`_kick_scan`, with reuse of
    identical jobs) — past-tense → last 4 yrs, future → next 3 yrs. The chat answers
    instantly from the fast read; when the scan lands, the frontend renders the
    ranked windows and asks Gemini for a follow-up narration grounded on them
    (`last_salience_scan` in context). The manual Scan button stays for custom
    ranges.
- Alternative still open: option (b), the engine's own `triangulate()`/
  `event_evidence` pack as a deterministic "Praśna" panel (no LLM at all).

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
