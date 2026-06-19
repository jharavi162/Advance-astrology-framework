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

## 2026-06-19 — Complete secondary Argala (add 8th → counter 6th)

- **Change:** `ARGALA_HOUSES` now `{2:12, 4:10, 11:3, 5:9, 8:6}` — adds secondary
  argala from the 8th house, countered (virodhargala) by the 6th.
- **Why (śāstra):** Argala and its counter form pairs symmetric about the lagna
  axis (2↔12, 4↔10, 5↔9, 11↔3, and **6↔8**). Sanjay Rath's formulation lists
  primary argala from the 2nd/4th/11th and **secondary argala from the 5th and
  8th**, with virodhargala from the 12th/10th/3rd and the 9th/6th. The 8th pair
  was the only one missing.
- **Source:** Sanjay Rath, *Jaimini Maharishi's Upadesa Sutras* (Argala chapter);
  Jaimini Sūtras 1.1.
- **Failure-mode addressed:** Coverage — the 8th-house intervention (sudden /
  transformative support, the classic windfall-vs-crisis witness) was invisible
  to triangulation.
- **Tests:** `test_argala_houses_and_counters`, `test_secondary_argala_from_eighth`.
