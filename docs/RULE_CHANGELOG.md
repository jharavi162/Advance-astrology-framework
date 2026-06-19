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

## 2026-06-19 — Add Sudasā (Sri) rashi dasha

- **Change:** New `jaimini.sudasa_dasha` + `VedicChart.sudasa_dasha`; wired into
  the matrix's Jaimini timekeepers next to Nārāyaṇa and Chara.
- **Why (śāstra):** The playbook (§3 Step 1) names Sudasā as a parallel rashi
  dasha to cross-vote for "Hot Themes," specifically the wealth/prosperity
  witness. Sudasā uses the Chara progression and durations but is **seeded from
  the Sree Lagna** (the classical prosperity reference) instead of the natal
  Lagna. Direction zodiacal for an odd seed sign, reverse for even; span = Chara
  count (signs to lord − 1).
- **Source:** Sanjay Rath, *Jaimini Maharishi's Upadesa Sutras* (Sudasa / Sri
  dasa); K.N. Rao on Jaimini rashi dashas.
- **Failure-mode addressed:** Coverage — a third independent rashi-dasha vote for
  the macro-scan, raising convergence resolution for wealth-domain events.
- **Variant note:** Some traditions reckon Sudasā always zodiacally; we follow
  the odd/even directional rule shared with Chara for consistency. Flagged here
  so it can be revisited if blind testing implicates the direction.
- **Tests:** `test_sudasa_dasha_twelve_signs`.

## 2026-06-19 — Forward activation-window scanner (§3 Step-3 timing engine)

- **Change:** New `Transits.scan_windows` (generic bisecting window finder) plus
  three concrete finders — `conjunction_windows`, `house_windows`,
  `kakshya_windows` — and an `ActivationWindow` dataclass, in
  `advance_astrology/vedic/transits.py`. Boundaries refined to ~1-day resolution.
- **Why (śāstra):** Section 3 Step 3 of the playbook requires pinning an event's
  timing to a narrow window via two classical triggers: the **Bhrigu-Nandi-Nāḍī
  degree-to-degree transit conjunction** (`conjunction_windows`) and the
  **Aṣṭakavarga Kakṣyā narrowing** — a planet delivers results only while
  transiting a 3°45′ Kakṣyā that carries a bindu (`kakshya_windows`). House
  ingress windows (`house_windows`) support the slow-gochara macro-scan (Step 1).
- **Source:** Playbook §3 Step 3.3–3.4; Aṣṭakavarga Kakṣyā method (classical);
  Bhrigu-Nandi-Nāḍī transit triggers.
- **Failure-mode addressed:** Discrimination/timing — generalizes the inline
  ingress bisection into a reusable primitive the convergence engine will call to
  *date* an activated theme, not just detect it.
- **Tests:** `test_scan_windows_trivial`, `test_house_windows_well_formed`,
  `test_conjunction_window_finds_and_bounds`.

## 2026-06-19 — Convergence engine (multi-paddhati triangulation)

- **Change:** New `advance_astrology/vedic/triangulate.py` (`Domain`, `Vote`,
  `DomainScore`, `Triangulator`, `Triangulation`) + `VedicChart.triangulate`.
  Scores ten śāstra-mapped life-event domains over a time window from ten
  witness families (natal lords, occupants, Argala, kārakas, varga confirmation,
  SAV, Vimśottari, rashi daśās, gochara, KP), producing a ranked blind dossier
  with texture, confidence and candidate timing.
- **Why (śāstra):** Implements Playbook §3–§4: Step-1 macro-scan (dasha + rashi
  dasha + gochara cross-votes), Step-2 manifestation-vs-cancellation filtration
  (lord strength, Iṣṭa/Kaṣṭa, occupant nature, Argala/Virodhārgala), Step-3 varga
  confirmation + timing. Domain house/kāraka/negation/varga maps follow classical
  significations (e.g. marriage 2/7/11 fulfilment, 1/6/10 negation, D9, Venus/DK;
  surgery D30/Mars/6-8). Fulfilment vs negation house sets per playbook §3 Step-3.
- **Source:** Architectural Playbook §3–§4; BPHS bhāva significations; KP
  fulfilment/negation house doctrine; Jaimini kāraka scheme.
- **Failure-mode addressed (the central one):** *Discrimination.* A first naïve
  build scored ALL ten domains at 0.82–0.96 over a 6-year window — the predicted
  "everything lights up" failure. Fixed by (a) splitting STATIC natal promise
  from DYNAMIC window-activation, (b) **gating** activation by a positive natal
  promise (a domain the chart does not promise cannot fire on transit alone),
  and (c) ranking by **field-relative salience** (min-max normalised) so the
  output separates instead of saturating. Confidence is therefore *relative
  salience within the window*, NOT a calibrated probability — consistent with the
  no-calibration premise.
- **Determinism:** One mechanical assembly; identical inputs → identical ranking
  (asserted in tests). No constant is fit to any chart's history; all weights are
  documented methodological choices above.
- **Known limitation (logged, not hidden):** over long windows many domains stay
  "active" because life genuinely has many themes across years; sharp single-event
  calls need short windows. Next step: automatic sliding sub-window segmentation
  so a multi-year sweep reports *when* each domain peaks.
- **Tests:** `test_triangulation_ranks_and_discriminates`.
