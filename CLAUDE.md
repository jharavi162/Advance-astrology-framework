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

## Procedure for any astrology question
1. Run the mechanical pack FIRST:
   `python -m interpreter.event_evidence --domain <matter|scan> --when ... --start ... --end ...`
2. Then synthesize MULTIVALENTLY per `docs/AI_TRIANGULATION_PROMPT.md` — never let
   one rule/system be sole judge.

## Key files
- `docs/AI_TRIANGULATION_PROMPT.md` — the analysis director (interpretive).
- `interpreter/event_evidence.py` — domain-general mechanical evidence builder.
- `interpreter/build_matrix.py` — natal+period dump (`--events` appends the pack).
- `advance_astrology/vedic/chart.py` — `VedicChart`, the single calculation door.
