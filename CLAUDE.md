# CLAUDE.md — how this repo evolves (read every session)

## Division of labour (the whole design in one line)
- The **ENGINE computes; the AI interprets.** Never recompute/guess a number the
  engine owns. No calibration, no hindsight, no native-specific hardcoding, ever.
- Engines emit **DATA** (significations, daśā windows, transit triggers, annual
  charts) — **no score, no verdict.** The AI reads the data across schools and
  states its own triangulated call. A convergence/salience *number* is never the
  answer (blind testing proved the leaderboard misleads).

## Architecture — the Samanvaya engine stack
```
advance_astrology/            ONE shared ephemeris core (Skyfield) + all calculators
        │                     (vargas, shadbala, KP sub-lords, chara daśā,
        │                      ashtakavarga, transits, sahams, varshaphal …)
interpreter/engines/          isolated per-school engines, one contract, DATA-only
   ├─ kp_engine.py            KP → promise / denial / quality (yes-no)
   ├─ dasha_timing.py         the CLOCK → Vimśottari + Chara + Gochara double-transit
   ├─ jaimini.py              Arudha / Upapada / chara-kāraka / Chara rāśi
   ├─ tajika.py               annual Varṣaphal / Muntha / Sāham
   ├─ router.py               question intent → engine order (timing→clock; yes/no→KP)
   ├─ samanvaya.py            route + run + bundle raw {engine: report} for the AI
   └─ _shared.py              Vimśottari spine + KP sub-chart (engines depend on
                              advance_astrology ONLY — not on the legacy monolith)
interpreter/significators.py  resolve(word) → DomainProfile (the domain dictionary)
```
The engine stack is fully decoupled and is the **official path** for answering
questions. `interpreter/event_evidence.py` + `interpreter/coverage.py` (the old
witness/salience/convergence/verdict monolith) are **DEPRECATED** — kept only
until the webapp's legacy endpoints are migrated; do **not** answer from them or
extend them.

## Procedure for any astrology question
1. `resolve(word)` → the `DomainProfile`.
2. Build the `samanvaya(...)` bundle (or call the relevant engine(s) directly) to
   get each school's **data**.
3. **Interpret** — for a "WHEN" question follow `docs/AI_EVENT_TIMING_GUIDE.md`;
   for judgment/quality follow `docs/AI_TRIANGULATION_PROMPT.md`. Triangulate
   across schools; never let one system be sole judge; the score is never the verdict.

## Where a NEW LEARNING goes (classify FIRST, then place)
| Learning kind | Destination |
|---|---|
| Mechanical/deterministic quantity the engine can compute but no engine yet exposes | **CODE** — add it as DATA on the right engine in `interpreter/engines/` (+ a doctrine/contract TEST, no native dates) |
| New life-area (its houses/kāraka/sāham/varga) | **DATA** — one `register_domain()` / `DomainProfile` row |
| "How to INTERPRET" judgment (not reducible to a bool) | **PROMPT** — `docs/AI_EVENT_TIMING_GUIDE.md` (timing) or `docs/AI_TRIANGULATION_PROMPT.md` (general), descriptive & event-agnostic |
| A true known event to never regress | **TEST** — a mechanical fixture, **no native dates** (blind-test integrity) |

Push mechanics into engine DATA; keep judgment in the guides (the AI's job, not
new engine rules). Log every change in `docs/RULE_CHANGELOG.md` with its śāstra
source. **No calibration** — add a piece because the śāstra/question needs it,
never to fit a known date.

## Evolve the stack yourself — don't work around a gap
- **DOMAIN missing** (a new life-area): add the one `register_domain()` row
  **autonomously**, then answer.
- **A computed-but-unexposed quantity** an engine should surface (a classical
  timer/significator the śāstra calls for): name the **classical source** (BPHS,
  Phaladeepika, Saravali, Jaimini Sūtras, Tājika, KP, Sanjay Rath/K.N. Rao),
  **present it for approval FIRST** (it changes how every chart reads), then add it
  as engine DATA **with a doctrine test**. Keep it domain-general (read the
  domain's houses/kāraka; never hard-code a native).
- After either, **log it in `docs/RULE_CHANGELOG.md`** with the justification.

## Key files
- `docs/AI_EVENT_TIMING_GUIDE.md` — **read for any "WHEN" question.** KP is
  quality/yes-no (never timing); the bhāva double-transit is a PRIMARY trigger;
  don't over-constrain the daśā; read the pratyantar's nature; weak lords deliver
  via their dispositor; events cluster at daśā onsets.
- `docs/AI_TRIANGULATION_PROMPT.md` — the general analysis director (interpretive).
- `interpreter/engines/` — the per-school engines (data-only) + router + Samanvaya.
- `interpreter/significators.py` — `resolve(word)` → `DomainProfile` (Hinglish ok).
- `advance_astrology/vedic/chart.py` — `VedicChart`, the single calculation door.
- *(deprecated)* `interpreter/event_evidence.py`, `interpreter/coverage.py` — the
  legacy convergence monolith; do not extend or answer from it.
