# Triangulation Rule-Change Log

Every change to the prediction rules is recorded here with its **classical
(śāstra) justification** — *never* "this made the output match a known event."
This protects the no-calibration premise: rules are fixed by tradition, and the
blind past-event test is used only to detect coverage/logic bugs, not to fit
the native's history.

Format per entry: what changed · why (śāstra) · source · failure-mode it
addresses (coverage vs discrimination).

---

## 2026-06-23 — Four user-approved timing NODES (gochara-from-Moon, fulfil-house DT, KP star-transit, Tājika Varṣeśa/Muntha)

- **Change:** Added four new TIMING witnesses to `event_evidence.py` (each one
  `register_witness(...)` + a populated `WindowEvidence` field + a ledger column;
  domain-general, reading the domain's houses/fulfil-set, never a native):
  1. **Gochara from the Moon (Chandra-lagna double-transit)** — the Jupiter+Saturn
     joint activation of the matter's house reckoned **from the natal Moon**, not
     only from the Lagna. Weight 1.0.
  2. **Fulfilment-houses double-transit (+lords)** — the double-transit run on the
     domain's *other* fulfilment houses and their lords (e.g. the 3rd & 12th for
     relocation), not the primary house alone. Weight 0.7.
  3. **KP transit: slow planet in a significator's star** — Jupiter/Saturn
     transiting a nakṣatra whose star-lord signifies the domain's fulfilment houses
     (KP transit theory; nakṣatra-lord computed from the Vimśottari cycle). Weight 0.7.
  4. **Tājika Varṣeśa/Muntha signifies the matter** — the annual chart's Muntha in a
     fulfilment house OR the Varṣeśa (year-lord) / Muntha-lord signifying the
     matter's houses. Weight 0.6.
  These were **proposed by the AI and approved by the user** per the CLAUDE.md node
  policy (a node changes how every chart is judged ⇒ approval first). Regression
  test `test_new_timing_nodes_registered_and_computed` added; existing invariants
  (`domain_score ≥ 0`, `≤ convergence`) preserved (new nodes vote pro-only).
- **Why (śāstra):** (1) Classical gochara phala is judged primarily **from the
  Janma Rāśi (Moon)** — Phaladeepika and Saravali state transit results from the
  Moon; the engine previously reckoned the double-transit only from the Lagna, an
  incomplete reading (the Moon is also the relocation kāraka). (2) A change of
  residence is bhāvāt-bhāvam — leaving the 4th lights the 3rd (movement) and 12th
  (distant/native-place exit); these fulfilment houses deserve the same
  double-transit test as the primary. (3) KP times an event when a planet transits
  the **sign and star of a favourable significator** (Krishnamurti); the slow
  planets set the broad band. (4) Tājika reads the year through the Muntha and the
  Varṣeśa (Nīlakaṇṭha's *Tājika Nīlakaṇṭhī*).
- **Source:** Phaladeepika & Saravali (Gochara from the Moon); BPHS bhāvāt-bhāvam;
  KP Readers IV–VI (transit-of-significators / star theory); Tājika Nīlakaṇṭhī.
- **Failure-mode addressed:** Coverage/discrimination — the panel was Lagna-only
  for the double-transit and ignored the Moon-based gochara, the fulfilment-house
  movers, the KP star-transit and the annual Varṣeśa. (Surfaced by a relocation
  retrodiction whose true date sat outside the Lagna-only double-transit band.)
  **No calibration:** nodes added because the śāstra prescribes them, not to fit
  the known date; the new nodes do not, by themselves, relabel that window.
- **Deferred (logged, engine lacks it):** the **Muddā (Tājika varṣa) daśā** — the
  annual sub-period system — is not yet implemented in the engine; the Tājika node
  uses Muntha/Varṣeśa significations for now. Add Muddā daśā as its own entry when
  built (would need user approval as a new daśā computation).

## 2026-06-23 — Add `relocation` (change-of-residence / base) life-area as DATA

- **Change:** Registered a new `relocation` domain row in `event_evidence.py`
  `_SEED` (no engine math touched, per the CLAUDE.md routing table — a new
  life-area is DATA): `houses=[4]` (the base/home bhāva), `fulfil_houses=[3,4,11,12]`
  (3 = movement/short relocation, 4 = the new dwelling, 11 = settling/gain, 12 =
  leaving the native place / distant residence), `negate_houses=[1,6,8]` (staying
  rooted / obstacles to a move), `karakas=["Matrikaraka"]`, `natural_karaka=Moon`
  (mind/dwelling/changes-of-place), `arudhas=["A4"]` (the perceived home), `varga=4`
  (Chaturthāṃśa — home/fixed-residence). No Saham (the engine's Saham set has no
  residence/travel point — left `None`).
- **Why (śāstra):** The 4th bhāva is sukha-sthāna / vāsa-sthāna — home, base, fixed
  residence and native land; the Moon is its movable kāraka (mind, dwelling,
  restlessness, changes of place) and the Matṛkāraka the Jaimini significator of
  the 4th. A change of base is read as the 4th's bhāvāt-bhāvam transition — leaving
  the present dwelling lights 3/8/12-from-the-4th while the new base + gain are the
  4th, 11th and 12th (distance) — exactly the reversal block's CHANGE/UPGRADE test.
  The Chaturthāṃśa (D4) is the classical varga confirming residence/property.
- **Source:** BPHS bhāva significations (4th = sukha/vāsa, Moon kāraka); Jaimini
  Matṛkāraka; KP change-of-residence house doctrine (3/9/12 with 4/11); D4 varga.
- **Failure-mode addressed:** Coverage — relocation questions previously had no
  domain row and could only be answered via the generic `scan`; now the full
  triangulation pack (promise/tempo, ledger, double-transit on the 4th and its
  lord, reversal-as-change) is computed for residence changes like any other matter.

## 2026-06-22 — Unify TIMING factors (daśā included) into the witness registry

- **Change:** The per-window scoring no longer uses a hard-coded vote formula; the
  timing factors are now **registered timing-witnesses** in the same open registry
  as the standing nodes — the daśā (kāraka-in-chain, kāraka-at-sūkṣma), KP, the
  double-transit, BNN, Kakṣyā, Saham, Sudarśana, Varṣaphal and the (shared) Lagna
  node. `WindowEvidence.domain_score`/`convergence` are the weighted convergence of
  these nodes, and the output lists the firing nodes for the top window. The daśā
  is thus literally *one node among many*, not a privileged scorer. Prompt's
  Cardinal Rule updated to say so; tests + changelog added.
- **Why (śāstra):** No single timekeeper decides an event — Parāśara/Jaimini hold
  the daśā as one pramāṇa that must be corroborated by gochara, the vargas, KP,
  Aṣṭakavarga and the bhāva's own standing strength. Privileging the daśā is the
  cardinal mistake the playbook already forbids; this makes the *code* honour it.
- **Source:** BPHS (daśā as one of many pramāṇas; gochara/aṣṭakavarga corroboration
  doctrine); the project's Cardinal Rule.
- **Failure-mode addressed:** Discrimination/architecture — the daśā was still a
  separate hard-coded path; it is now one entry in the same node registry, so the
  verdict is a true multi-nodal convergence and nodes stay fully extensible.

## 2026-06-22 — Witness/Node registry: upgrade-vs-loss as multi-nodal convergence

- **Change:** Added an open `Witness` registry to `event_evidence.py` — each node
  is a declarative testimony that votes a signed strength × weight, and a verdict
  is their weighted convergence, never one rule. Seeded STANDING (natal) witnesses
  on the matter's house: benefic/malefic dṛṣṭi, lord dignity+strength, rāja-yoga
  (lord dignified in kendra/trikoṇa), occupant nature, Argala net, SAV. The
  loss-vs-upgrade `kind` now folds this `standing_balance` in: a natally *blessed*
  house (e.g. exalted Jupiter aspecting the 10th + Śaśa yoga, balance +1.60 here)
  upgrades through a dusthāna window rather than breaking; an afflicted one
  (marriage, −0.40) can truly break. `register_witness(...)` makes nodes dynamic.
  Prompt updated; tests + changelog added.
- **Why (śāstra):** Manifestation/cancellation is decided by the *aggregate* of a
  house's testimony — occupants, aspects, lord, yogas, Argala, Aṣṭakavarga — not
  by a single significator or the daśā alone. A house blessed by benefic dṛṣṭi and
  a dignified lord/rāja-yoga resists destruction (BPHS bhāva-bala and yoga
  doctrine); the running daśā then merely *times* a change within that blessing.
- **Source:** BPHS (bhāva-bala, graha-dṛṣṭi, Pañca-Mahāpuruṣa/Rāja yogas,
  Aṣṭakavarga); Jaimini Argala.
- **Failure-mode addressed:** Discrimination — upgrade-vs-loss was resting on too
  few nodes (KP-centric); it is now the convergence of the full standing pattern,
  and the node-set is an open registry (extensible without code rewrites).

## 2026-06-22 — Distinguish CHANGE/UPGRADE from LOSS/BREAK in the reversal

- **Change:** The reversal block of `event_evidence.py` no longer labels every
  6/8/12-from-the-house (dusthāna-from-matter) activation a "loss." It now
  classifies each window: **CHANGE/UPGRADE** when the fulfilment signature
  co-occurs, **LOSS/BREAK** only when fulfilment is absent and the Lagna is dark
  under malefics/nodes. Fulfilment co-occurrence is read from the TIMING lords
  (AD/PD), not the standing mahādaśā (else a domain-lord MD masks everything).
  Added the matching descriptive rule to `AI_TRIANGULATION_PROMPT.md` Track B and
  two regression tests.
- **Why (śāstra):** Leaving a thing and bettering a thing share the "end of the
  present state" signature — a job-change to a superior post, a move to a better
  home, or a remarriage activate the same 6/8/12-from-house as a job-loss,
  eviction or divorce. KP times a *change of service* by the 5th/9th (end of
  current job) together with the 10th/11th/6th (the new, better job); the
  fulfilment houses are the discriminator between an upgrade and a loss.
- **Source:** KP service-change doctrine (6th/10th/11th vs 5th/9th); BPHS
  bhāvāt-bhāvam (house-from-house) reckoning.
- **Failure-mode addressed:** Discrimination — a real upward job-change for this
  native was being mislabelled a "career loss/break"; the fulfilment test fixes
  it while still flagging the genuine divorce (Feb-2026) as a LOSS/BREAK.

## 2026-06-22 — Learning-routing process recorded in CLAUDE.md

- **Change:** Added a root `CLAUDE.md` (auto-loaded every session) that fixes
  WHERE each new learning goes: deterministic checks → CODE
  (`interpreter/event_evidence.py`) + a regression test; new life-area or its
  houses/kāraka/saham → DATA (`DOMAIN_PROFILES` / `register_domain`);
  interpretive judgment → PROMPT (`AI_TRIANGULATION_PROMPT.md`); a true known
  event → TEST fixture. No engine math altered.
- **Why (method):** Repeated prompt-only patches do not guarantee correctness
  and bloat the director file. Routing the *mechanical* half to code (always
  computed, never forgotten) while keeping only genuine judgment in the prompt
  is what gives a guarantee and keeps the prompt lean. Every code-learning is
  locked with a test.
- **Source:** This project's own miss-analysis (a wedding date missed because
  the AI fixated on single rules and skipped computations); the Architectural
  Playbook's engine-vs-AI division of labour.
- **Failure-mode addressed:** Process — prevents future learnings from landing
  in the wrong layer (the root cause of single-rule fixation and prompt bloat).

## 2026-06-22 — Domain-general event-evidence engine + interpretive-stance rules

- **Change:** Added `interpreter/event_evidence.py` — a domain-agnostic
  triangulation builder (Promise & Tempo from Ṣaḍbala/Iṣṭa-Kaṣṭa/Avasthā/varga/
  Argala/SAV; a full-span per-window ledger of KP, sūkṣma kāraka, Lagna/Lagnesh
  materialization, Jupiter+Saturn double-transit on house AND lord, BNN, Kakṣyā,
  Saham, Sudarśana, Varṣaphal-Muntha; and the reversal timed as its own event).
  Domains are an open `dict`. Added the "interpretive stance" rules to the prompt
  (no single factor is a veto; significations are multivalent — TYPE not yes/no;
  each paddhati answers a different sub-question; separate event from aftermath;
  full-span lord double-transit; soften the KP gate). `build_matrix --events`.
- **Why (śāstra):** A prediction is valid only when several independent systems
  converge; the matter materialises through the Lagna/Lagnesh, is desired by the
  Moon, and is promised by its house/kāraka — and a malefic/node shapes an
  event's TYPE rather than denying it. A reversal (divorce/job-loss) is a
  positively-timed event with its own significators, not the mere absence of the
  first.
- **Source:** BPHS (Ṣaḍbala, Avasthā, Vargas, Sahams); KP significator theory;
  classical double-transit (Gochara) doctrine; Jaimini (Arudha, chara-kāraka).
- **Failure-mode addressed:** Coverage (whole toolkit now always computed) and
  discrimination (multivalent reading + reversal-as-own-event stop single-rule
  fixation). Limitation logged: cross-domain `scan` normalisation is v1.

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

## 2026-06-19 — Time-localization: sliding sub-window timeline

- **Change:** `VedicChart.triangulate_timeline` + `Triangulator.timeline` and
  `TimelineResult`/`TimelineEvent`/`Sample`. Refactored the engine so STATIC
  (lifelong) witnesses compute once and only DYNAMIC witnesses re-run per
  sub-window. Slides a short window (default 183d, step 30d) across the span,
  builds each domain's activation series, and detects events as contiguous
  above-baseline runs (plateaus collapsed, valleys separate events). Each event
  gets precise slow-gochara trigger windows from the scanner. Output grouped by
  theme so one can "narrow to a domain" and read its candidate event dates.
- **Why (śāstra):** Playbook §3 is a TIMELINE engine ("analyse the last N years");
  a single aggregate window cannot localize discrete events. Per-domain peak
  detection against each domain's own baseline answers "when did THIS theme fire",
  rather than letting the two highest natal-promise domains monopolise a
  cross-domain lead (the discrimination failure observed in the first build).
- **Source:** Architectural Playbook §3 (Macro-scan over a timeline) + §3 Step-3
  (Kakṣyā / gochara timing narrowing).
- **Failure-mode addressed:** Discrimination/timing — turns "career is a live
  theme over 6 years" into "career peaks ~2022-03 and ~2024-11", which is the
  precise-prediction target.
- **Known limitation:** event *texture* currently reads "clean manifestation"
  for most themes (obstruction witnesses fire rarely); cancellation-signature
  sensitivity is the next calibration area, to be driven by blind testing.
- **Tests:** `test_triangulation_timeline_localizes_events`.

## 2026-06-19 — Tier-2 wiring (1/4): texture witnesses (avastha, aspects, chalit)

- **Change:** Three new witness families in `triangulate.py`: `w_avastha`
  (Dīptādi mood blockade), `w_aspect` (graha dṛṣṭi onto domain houses),
  `w_chalit` (Bhāva-Chalit Placidus result-shift). All STATIC (natal) families,
  cached once in `__init__`.
- **Why (śāstra):** §3 Step-2 mandates "Mood and Avastha Blockades" (a Khala/
  Vikala/Dukhita lord corrupts the promise — the cancellation signature),
  "Aspectual Geometry" (benefic vs malefic dṛṣṭi shaping the house), and
  "Placidus Shift Corrections" (§2.5 — result-house migration). All three were
  computed by the engine but absent from triangulation.
- **Source:** BPHS Avasthā/Dīptādi; Parāśarī graha dṛṣṭi; Placidus Bhāva-Chalit.
- **Failure-mode addressed:** *Texture/cancellation* — previously every theme
  read "clean manifestation" because no Track-B obstruction witness fired. Now
  obstruction is non-trivial and textures separate (clean vs friction).
- **Coverage status:** closes 3 of the Tier-2 gaps (avastha, aspects, chalit).

## 2026-06-19 — Tier-2 wiring (2/4): promise witnesses (yogas, arudha, chara-kāraka, Vimśopaka)

- **Change:** Four STATIC witness families in `triangulate.py`: `w_yoga`
  (Rāja/Dhana/Mahāpuruṣa/Gajakesari… mapped to domains), `w_arudha` (occupants
  of the domain's Arudha pada), `w_charakaraka` (Jaimini DK/AmK/etc. placement &
  strength), `w_vimsopaka` (Vaiśeṣikāṃśa multi-varga grade of lord/kārakas).
- **Why (śāstra):** §2.2 chara-kārakas, §2.4 Vimśopaka/Vaiśeṣikāṃśa scales, §2.6
  Arudha manifestation points, and yoga doctrine (Rāja=elevation, Dhana=wealth)
  all bear on a domain's *promise* and were computed but unused.
- **Source:** Jaimini chara-kāraka scheme; BPHS yogas; Vaiśeṣikāṃśa (Pārijāta→
  Śrīdhāma) strength tiers; Arudha pada doctrine.
- **Failure-mode addressed:** Coverage — domain promise was previously judged on
  lord/occupant/argala/karaka/varga/SAV only; now 13 static witnesses inform it.
  Top-domain witness breadth rose from 10 → 15 families.
- **Coverage status:** closes 4 more Tier-2 gaps (yogas, arudha/UL, chara-kāraka
  placement, Vimśopaka).

## 2026-06-19 — Tier-2 wiring (3/4): KP sub-lord verdict + Marakas

- **Change:** `w_kp` upgraded from "is the MD lord among house significators" to
  the proper KP chain — for the active Mahā/Antar lords, take the *sub-lord* of
  their natal longitude (`kp_chain(...).sub_lord`) and read `signifies_any` over
  fulfilment vs negation houses. Fulfil⇒+, negate⇒−, BOTH⇒ the fixed-then-
  cancelled signature (−). New `w_maraka` reinforces adverse-event domains.
- **Why (śāstra):** §3 Step-3.2 names the sub-lord as the "ultimate negation
  tool — manifestation's final verdict"; the previous proxy ignored the
  star→sub chain. Maraka doctrine (§2.2) bears on health/longevity events.
- **Source:** Krishnamurti Paddhati sub-lord theory; BPHS maraka rules.
- **Failure-mode addressed:** Discrimination + texture — the sub-lord "both
  fulfil & negation" case is exactly the playbook's "marriage fixed but cancelled"
  detector, now firing (seen on the native's Health/Relocation domains).
- **Coverage status:** closes the KP-sub-lord and maraka Tier-2 gaps. Remaining
  Tier-2: wire Kakṣyā + BNN conjunction + fast-transit triggers into timing (4/4).

## 2026-06-19 — Tier-2 wiring (4/4): precise timing triggers (BNN + Kakṣyā)

- **Change:** `Triangulator._windows_for` now, on event-scale spans (≤400d),
  adds Bhrigu-Nandi-Nāḍī degree-to-degree conjunction windows (slow transit
  within 2° of the domain's natal kārakas/lord) and Saturn Kakṣyā windows, on
  top of the coarse slow-gochara house windows. `with_timing` caps precise
  computation to the top-N events by salience to bound runtime.
- **Why (śāstra):** §3 Step-3.3 (BNN transit triggers) and §3 Step-3.4 (Kakṣyā
  4–5-day narrowing) — the scanner primitives existed but were never invoked by
  the convergence layer.
- **Source:** Playbook §3 Step-3.3–3.4.
- **Failure-mode addressed:** Timing precision — each detected event now carries
  its degree-to-degree and Kakṣyā trigger windows, not just the house-ingress span.
- **Coverage status:** **Tier-2 complete.** All playbook-mandated, already-
  computed witnesses are now wired (17 families + precise timing). Next: Tier-3
  new-computation systems (Varṣaphal, deeper daśā levels, extra daśās, A1–A12).

## 2026-06-19 — Tier-3 (1): Varṣaphal (Tājika annual chart) witness

- **Change:** New `advance_astrology/vedic/varshaphal.py` (`AnnualChart`,
  `solar_return_time`, `annual_chart`) + `VedicChart.varshaphal(year)`. Wired into
  the convergence engine as the DYNAMIC `varshaphal` family (per-year cached):
  the Muntha's house is the year's live theme; Muntha/Varṣa-lagna lords tie it to
  natal domains.
- **Why (śāstra):** Varṣaphal is the classical year-resolution system. The solar
  return is the Sun's return to its natal *sidereal* longitude; the Muntha
  advances one sign per completed year of age from the natal lagna. This adds a
  genuinely new (annual) dimension to the macro-scan, not just another rashi-daśā.
- **Source:** Tājika śāstra (Nīlakaṇṭha's *Tājika Nīlakaṇṭhī*); Varṣaphal /
  Muntha doctrine.
- **Failure-mode addressed:** Coverage + timing — year-level activation that
  Vimśottari/rashi-daśās alone do not isolate.
- **Deferred (logged):** full Pañcādhikārī lord-of-the-year (Pañca-vargīya bala),
  Sahams, and Muddā daśā — the robust outputs (Varṣa lagna, Muntha, lords) are
  wired now; the contested bala-ranking is left for a dedicated entry.
- **Tests:** `test_varshaphal_solar_return_and_muntha`.

## 2026-06-19 — Blind-prediction CLI (interpreter/predict.py)

- **Change:** `python -m interpreter.predict` runs the convergence engine for a
  birth and prints the triangulation timeline (theme peaks + precise gochara/BNN/
  Kakṣyā triggers) plus the aggregate-window dossier. No new rules; a harness.
- **Why:** Makes the no-calibration blind test a single command — the engine
  commits its calls, the native compares against real events, misses point to the
  next śāstra-grounded fix. This is the highest-leverage next step for the goal,
  ahead of further (diminishing-returns) element-completeness work.

## 2026-06-21 — Engine helpers for the new prompt rules (Sūkṣma/Prāṇa, gochar dṛṣṭi, house lord)

- **Change:** (1) `VedicChart.current_dasha(..., levels=N)` — drill Vimśottari to
  Sūkṣma/Prāṇa (level 4–5) in one call. (2) `Transits.transit_aspects(when)` +
  `Transits.aspects_house(when, house)` — gochar dṛṣṭi (which houses a transiting
  planet ASPECTS, Parāśarī special aspects), not just occupation/conjunction.
  (3) `VedicChart.house_lord(h)` + `house_lords()` convenience.
- **Why (śāstra):** The triangulation prompt's timing rules (added separately)
  now mandate event-day daśā drill to Sūkṣma/Prāṇa and reading a kāraka's *dṛṣṭi*
  (e.g. Jupiter aspecting the 7th from the 1st without entering it). The engine
  could compute these only via multi-step assembly; these helpers expose them as
  one call so the AI follows the rule reliably (and does not "stop at Pratyantar"
  or miss a transit aspect).
- **Source:** Parāśarī graha-dṛṣṭi (Mars 4/7/8, Jupiter 5/7/9, Saturn 3/7/10);
  Vimśottari sub-period structure (Sūkṣma/Prāṇa).
- **Tests:** `test_current_dasha_drills_to_sukshma`,
  `test_house_lord_and_house_lords`, `test_transit_aspects_and_aspects_house`.
