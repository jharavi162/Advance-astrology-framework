# Triangulation Rule-Change Log

Every change to the prediction rules is recorded here with its **classical
(śāstra) justification** — *never* "this made the output match a known event."
This protects the no-calibration premise: rules are fixed by tradition, and the
blind past-event test is used only to detect coverage/logic bugs, not to fit
the native's history.

Format per entry: what changed · why (śāstra) · source · failure-mode it
addresses (coverage vs discrimination).

---

## 2026-06-19 — Wire Argala + Indu Lagna witnesses into the matrix

- **Change:** Surface Jaimini Argala (intervention) per bhava and Indu Lagna
  (wealth lagna) in the Phase-I matrix databank. Read-only; no engine math
  altered.
- **Why (śāstra):** Argala measures *support vs obstruction* on any house/sign
  — the cleanest classical pair for the playbook's manifestation-vs-cancellation
  logic. Primary argala from the 2nd/4th/11th, secondary from the 5th, each
  countered (Virodha Argala) from the 12th/10th/3rd/9th respectively. Indu Lagna
  is the classical Dhana (wealth) reference point.
- **Source:** Jaimini Sūtras; B.V. Raman, *Studies in Jaimini Astrology*;
  Sanjay Rath, "Argala — Planetary Intervention" (srath.com).
- **Failure-mode addressed:** Coverage — these classical witnesses were computed
  by the engine but never entered triangulation.
- **Purity fix:** Argala restricted to the 9 grahas (Jaimini excludes the outer
  planets Uranus/Neptune/Pluto).

### Known gap to address in the engine (logged, not yet changed)
- `advance_astrology/vedic/jaimini.py: ARGALA_HOUSES` encodes secondary argala
  only from the 5th (counter 9th). Classical Jaimini also gives **secondary
  argala from the 8th, countered by the 6th**. Adding 8→6 is a śāstra-grounded
  completion, to be done as a dedicated engine change with its own entry here.
