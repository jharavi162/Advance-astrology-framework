# CLAUDE.md — how this repo evolves (read every session)

## Division of labour
- The ENGINE (`advance_astrology/`) computes; never recompute/guess a number.
- The AI THINKS: triangulate + synthesize. No calibration, no hindsight,
  no native-specific hardcoding ever.

## Where a NEW LEARNING goes (classify FIRST, then place)
| Learning kind | Destination | Example |
|---|---|---|
| Mechanical/deterministic check the engine can compute | **CODE** `interpreter/event_evidence.py` (+ a regression TEST) | Lagna materialization, sūkṣma drill, double-transit, BNN, reversal |
| New life-area, or its houses/kāraka/saham/varga | **DATA** `DOMAIN_PROFILES` / `register_domain()` — one row | adding a domain |
| "How to INTERPRET" judgment, not reducible to a bool | **PROMPT** `docs/AI_TRIANGULATION_PROMPT.md` (descriptive, event-agnostic) | node = TYPE; dark Lagna = intensity; don't fixate on one rule |
| A true known event to never regress | **TEST** `tests/` fixture | Jan-2024 / Feb-2026 / Jan-2027 |

Rule: push as much as possible into CODE+DATA (guarantee); PROMPT only for genuine
judgment; every code-learning gets a test. Log each change in
`docs/RULE_CHANGELOG.md`.

## Evolve the engine yourself — don't work around a missing piece (EVERY SESSION)
If a question needs a **domain** or a **node/witness** that the engine does not yet
have, **add it to the engine and merge it to `main`** — never hand-wave around the
gap or answer from a missing capability. Two cases, two approval levels:
- **DOMAIN missing** (a new life-area or its houses/kāraka/saham/varga — e.g.
  `relocation`): add the one `DOMAIN_PROFILES` / `register_domain()` data row
  **autonomously** (no approval needed), then run the pack and answer.
- **NODE/WITNESS or mechanical check missing** (a new `register_witness(...)`, a new
  deterministic check, a new timing factor in `event_evidence.py`): it is the AI's
  **standing responsibility to proactively IDENTIFY** — from astrological research
  and the best classical texts (BPHS, Phaladeepika, Saravali, Jaimini Sūtras,
  Tājika, KP/Krishnamurti, Sanjay Rath/K.N. Rao) — which additional node(s) a given
  assessment genuinely needs, **name the classical source for each**, and **present
  them to the user for approval FIRST** (a node changes how every chart is judged).
  Only after approval, add it **with a regression test**. The node must stay
  domain-general (read the domain's houses/kāraka, never hard-code a native).
- **COVERAGE matrix is the anti-miss guard.** A "node miss" is usually a
  *computed-but-unwired* quantity (the engine calculates it, but no witness reads
  it). `interpreter/coverage.py` is the single source of truth (technique × wired?);
  two tests keep it in sync with the live panel (no wired-claim without a witness; no
  witness without a matrix entry), and every pack prints `coverage_summary()` with
  the RED gaps. **Whenever you add an engine capability or a witness, update the
  matrix** — and prefer closing a RED item (wire a computed-but-unwired quantity)
  over inventing a brand-new computation.
- **Always**: after adding either, **merge the change into `main`** (do not leave
  engine evolution stranded on a feature branch) and **log it in
  `docs/RULE_CHANGELOG.md`** with its śāstra justification. No calibration/hindsight
  — add the piece because the śāstra/question needs it, never to fit a known date.

## Procedure for any astrology question
1. Run the mechanical pack FIRST:
   `python -m interpreter.event_evidence --domain <matter|scan> --when ... --start ... --end ...`
2. Then synthesize MULTIVALENTLY per `docs/AI_TRIANGULATION_PROMPT.md` — never let
   one rule/system be sole judge.

## Key files
- `docs/AI_TRIANGULATION_PROMPT.md` — the analysis director (interpretive).
- `interpreter/event_evidence.py` — domain-general mechanical evidence builder.
  Nodes are an open registry; `register_family`/`build_panel` generate the whole
  element×technique panel per domain; `DASHA_SYSTEMS` is the daśā catalogue;
  `salience` ranks windows (convergence-gating + information-weighting).
- `interpreter/significators.py` — the DICTIONARY: `resolve(word)` maps any theme
  word (Hinglish ok) to a `DomainProfile`, so the CLI takes `--domain <any word>`.
- `interpreter/coverage.py` — the COVERAGE MATRIX (technique × wired?) + completeness
  gate; keeps misses visible as RED items. Update it when adding capabilities/nodes.
- `interpreter/build_matrix.py` — natal+period dump (`--events` appends the pack).
- `advance_astrology/vedic/chart.py` — `VedicChart`, the single calculation door.
