# Project Plan — Advance Astrology Triangulation Engine

> Living roadmap. Whenever we resume, **start here.** Update the checkboxes as
> work lands. Authoritative companions: `docs/ARCHITECTURAL_PLAYBOOK.pdf` (the
> method) and `docs/RULE_CHANGELOG.md` (every rule change + its śāstra citation).

**Branch:** `claude/astrology-engine-6fhgjl`
**Goal:** a deterministic, **calibration-free** engine that, by considering every
relevant classical element and triangulating their convergence, makes accurate
*blind* predictions of life events — validated against the native's real past
without ever feeding the answers back in.

---

## The contract (non-negotiable principles)
1. **No calibration.** Never fit weights/thresholds to known events. Validation is
   blind: engine commits first, native compares privately.
2. **Śāstra-justified fixes only.** Every rule change must be defensible from
   classical authority, **never** "this made the output match." Logged in
   `RULE_CHANGELOG.md` with citation.
3. **Rank-and-discriminate, not just detect.** Convergence must rank the true
   domain *above* false ones; "some element points there" is not enough.
4. **Determinism.** One mechanical assembly, identical every run; no hindsight.
5. **Output ceiling = karmic category.** Commit to one most-likely event but also
   name the category and any astrologically-tied alternative.

---

## Architecture (decided 2026-06-19) — IMPORTANT
The triangulation is now done by the **AI**, not by Python:
- **Python (`advance_astrology`) = calculator only.** Accurate, unchanged. The
  single front door is **`VedicChart`** (`advance_astrology/vedic/chart.py`).
- **AI = the triangulation brain.** It follows **`docs/AI_TRIANGULATION_PROMPT.md`**
  (its DIRECTOR): understand the question → pull all calculations from the engine
  → select question-relevant evidence (any system) → triangulate (KP/BNN/Kakṣyā
  mandatory) → commit to one precise, falsifiable call.
- **Retired as a baseline:** the old fixed-domain `advance_astrology/vedic/
  triangulate.py` + `interpreter/predict.py`. Kept in the repo as a deterministic
  reference / calculation source, but **NOT** the decision-maker for readings.
- **User's starter prompt:** `docs/MY_PROMPT.md` (copy-paste to begin a reading).

---

## ✅ DONE (built, tested, pushed)
- [x] Engine foundations: Argala (incl. 8→6 secondary), Sudasā daśā, forward
      activation-window **scanner** (house / BNN conjunction / Kakṣyā).
- [x] **Convergence engine** (`VedicChart.triangulate`) — 19 witness families,
      static *promise* vs dynamic *activation*, promise-gating, field-relative
      salience, Track-A/B texture.
- [x] **Time-localization** (`VedicChart.triangulate_timeline`) — sliding
      sub-window, per-domain peak detection, precise gochara/BNN/Kakṣyā triggers.
- [x] **Varṣaphal** (Tājika annual chart) witness — solar return + Muntha.
- [x] **Tier-2 fully wired**: avasthā, dṛṣṭi, Bhāva-Chalit, yogas, arudha,
      chara-kāraka placement, Vimśopaka, maraka, full KP sub-lord verdict.
- [x] **Blind-prediction CLI** (`python -m interpreter.predict`).
- [x] **Playbook v2 + PDF** (`docs/ARCHITECTURAL_PLAYBOOK.pdf`) + generator.
- [x] **Rule-change log** discipline (`docs/RULE_CHANGELOG.md`).
- [x] Engine accuracy: 113 tests green; NASA/JPL DE421 ephemeris; Lahiri + KP
      ayanāṁśa; whole-sign + Placidus.

---

## ⏳ PENDING

### P0 — The blind test (gating step; native's action)
- [ ] Run `interpreter.predict` over a known span; compare theme peaks/dates/
      texture against real life events **without revealing the answers**.
- [ ] Report back only *"these themes/dates land, these miss."*
- [ ] For each miss, diagnose: **coverage gap** (add a deferred element) vs
      **logic/weight gap** (fix combination) — then fix śāstra-first, log it.

### P1 — Texture / cancellation sensitivity (driven by P0 misses)
- [ ] Sharpen Track-B (obstruction) so "fixed-then-cancelled" vs "clean" separates
      reliably. Currently the soft spot. Tune only from real misses, śāstra-cited.

### P2 — Tier-3 classical completeness (add only if a P0 miss implicates it)
- [ ] Deeper Vimśottari levels (Sūkṣma / Prāṇa) — finer timing.
- [ ] Kālachakra / Sthira / Shoola daśās — extra independent daśā cross-votes.
- [ ] Tārā-bala + nakṣatra-transit refinements.
- [ ] A1–A12 arudha-padas extended use (beyond the primary pada).
- [ ] Additional sphuṭas (Mṛtyu / Brahma / Yama, etc.).
- [ ] Full Tājika year-lord (Pañcādhikārī / Pañca-vargīya bala), Sahams, Muddā daśā.

### P3 — Delivery / UX (parked by user — "later")
- [ ] NLP / natural-language prose layer that *reads* the deterministic dossier
      (never recomputes numbers).
- [x] Paste-ready AI **narrator** prompt for the blind test
      (`python -m interpreter.predict … --prompt`): wraps the engine's committed
      output with strict "explain-only, do-not-recompute, do-not-invent-events"
      rules + the Section-6 template. The engine remains the predictor; the AI
      only narrates.
- [ ] Optional: automatic geocoding (place → lat/lon); currently manual.

---

## How to run (quick reference)
```bash
# Blind prediction (timeline + aggregate dossier)
python -m interpreter.predict --when "1991-04-04 06:23" --tz Asia/Kolkata \
  --lat 23.62 --lon 85.48 --place "Ramgarh" --name Native --years 6 --asof 2026-06-19

# Regenerate the playbook PDF after editing interpreter/playbook.txt
python scripts/make_playbook_pdf.py

# Tests
python -m pytest -q
```

## Decision log (key choices already made)
- Coordinates: manual lat/lon for now (no geocoder).
- Confidence = **relative salience** within a window, *not* a calibrated probability.
- Tie-breaking: commit to one event, but also name category + tied form.
- Playbook `playbook.txt` stays **gitignored** (IP); the **PDF is committed** to the
  repo at the user's request.
