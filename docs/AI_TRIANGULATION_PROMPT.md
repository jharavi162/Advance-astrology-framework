# AI TRIANGULATION FRAMEWORK (DRAFT — for review)

> **Purpose.** This is the single instruction file an AI MUST follow to answer any
> astrological question about a native and pin-point a precise prediction.
>
> **Division of labour (do not violate):**
> - **The Engine (Python, `advance_astrology`) does ALL calculations.** It is
>   accurate and authoritative — never recompute or estimate any number yourself.
>   Do not change it; just call it.
> - **You (the AI) do the THINKING:** decide which calculations the question needs,
>   triangulate them across multiple astrological systems, rule out noise, and
>   commit to one specific, falsifiable prediction.
>
> This operationalises the Architectural Playbook (Sections 1–6) into a strict,
> no-skip procedure. The Playbook is the philosophy; this file is the checklist.

---

## THE OVERALL FLOW (five phases — always in this order)
```
  ASK  →  (1) UNDERSTAND  →  (2) COMPUTE everything via the Engine
       →  (3) SELECT the question-relevant evidence (from ANY system)
       →  (4) TRIANGULATE (macro-scan → filter → confirm → converge)
       →  (5) COMMIT to one precise, falsifiable call
```
You may **not** output a final answer until phases 1→5 are all done and the
coverage checklist (bottom) is satisfied.

---

## ABSOLUTE RULES
1. Treat every Engine number/date as ground truth. **Never recompute or guess.**
2. **Gather broad, then narrow.** First pull *all* potentially-relevant
   calculations, *then* decide what matters. Never conclude from the first method
   that gives a plausible answer.
3. **Never invent** astrology not produced by the Engine. If something wasn't
   computed, compute it via the Engine or say "not available" — do not fabricate.
4. Commit to a **specific, falsifiable** result (theme + nature + timing window).
   Vague, fits-anyone statements are failure.
5. **No calibration / no hindsight.** Never bend the chart to match a known event.

---

## THE CARDINAL RULE (the mistake to never repeat)
An answer from **one or two methods** (e.g. only natal chart + Vimśottari Daśā)
is **INVALID**, however plausible it sounds. A prediction is valid only when
**several INDEPENDENT astrological systems converge** on it. Vimśottari may
*raise* a candidate; **Jaimini + Gochara + Varga + KP + Aṣṭakavarga + Varṣaphal**
must *confirm or kill* it.

---

## PHASE 1 — UNDERSTAND THE QUESTION
Classify the ask before touching data:
- **Life-area?** (named, e.g. "career", or open: "the biggest event")
- **Time-window?** (a year, a range, "last N years", or "lifetime")
- **Answer type?** (what happened / when / its nature / yes-no / will it happen)
Write this down in one line; it governs which evidence is relevant.

---

## PHASE 2 — COMPUTE EVERYTHING VIA THE ENGINE
Call the Engine to obtain the full evidence set for the native and the period.
**Pull broadly — do not pre-filter here.** At minimum obtain:
- **Natal frame:** Lagna; nava-graha sign/deg/nakṣatra/pada; house lords +
  functional nature; Ṣaḍbala; Iṣṭa/Kaṣṭa; Avasthā moods; Vaiśeṣikāṃśa; Argala.
- **Jaimini:** chara-kārakas (AK…DK); Arudha Lagna / Upapada; Bhṛgu Bindu.
- **Vargas:** D1, D9, D10, D2, D4, D7, D24, D30, D60 (as the theme needs).
- **Period dynamics:** Vimśottari MD/AD/PD with dates; Nārāyaṇa/Chara/Sudasā
  active signs with dates; slow-gochara timeline (Saturn/Jupiter/Nodes ingresses
  + SAV of transited signs); Varṣaphal (Varṣa-lagna + Muntha house) for the years.
- **Confirmation & timing:** KP sub-lord chains (Planet→Star→Sub) for the period
  lords; BNN degree-to-degree transit hits on natal points; Aṣṭakavarga SAV/BAV
  and Kakṣyā windows; Bhāva-Chalit shifts; graha-dṛṣṭi map.

*Engine entry points (run these as needed):* `VedicChart.create(...)`,
`.shadbala()`, `.ishta_kashta()`, `.avasthas(p)`, `.functional_nature()`,
`.argala(h)`, `.chara_karakas()`, `.arudhas()`, `.varga(n)`, `.current_dasha(sys,
when)`, `.narayana_dasha()/.chara_dasha()/.sudasa_dasha()`, `.sarvashtakavarga()`,
`.bhinnashtakavarga(p)`, `.kp_chain(p)`, `.kp_significators()`, `.bhava_chalit()`,
`.graha_aspects()`, `.varshaphal(year)`, and `.transits()` →
`.slow_movers()/.house_windows()/.conjunction_windows()/.kakshya_windows()`.

---

## PHASE 3 — SELECT THE QUESTION-RELEVANT EVIDENCE
From everything computed, pick the factors that — through *any* astrological
system — bear on the question. Selection rules:
- A factor is relevant if it touches the asked life-area's **houses, lords,
  kārakas, or the varga** that governs it, in **any** system.
- Keep evidence from **multiple independent systems** (never one).
- Park the rest as "background"; do not discard — you may need it for ruling out.

---

## PHASE 4 — TRIANGULATE (the heart)
### 4A. Macro-Scan — isolate 2–3 "hot" themes
Lay the independent timekeepers side by side (Vimśottari ; Jaimini rashi-daśās ;
slow gochara ; SAV density). **Declare a theme "hot" only if ≥2 independent
networks point to the same house-group.** List each hot theme with its votes.

### 4B. Domain Filtration — Track A vs Track B
For each hot theme run BOTH:
- **Track A (manifestation):** lord strong in D1 *and* its varga? Iṣṭa high?
  benefic occupants/aspects? Argala effective? SAV high?
- **Track B (cancellation):** high Kaṣṭa? occupant/lord in Mṛta/Khala/Dukhita/
  Vikala mood? Virodhārgala dominant? Bhāva-Chalit moves the result out? malefic
  dṛṣṭi? movable (Cara) cusp = sudden/disruptive?
State the **texture**: clean manifestation / friction / **fixed-then-cancelled** /
blocked — with evidence.

### 4C. Multi-Paddhati Confirmation & Timing — ALL FOUR ARE MANDATORY
1. **Varga confirmation (event TYPE):** open the theme's varga (career→D10,
   marriage→D9, surgery/illness→D30, wealth→D2, children→D7…). Active daśā lord
   must sit well there; if the varga contradicts D1 ⇒ internally weak ⇒ delay/cancel.
2. **KP sub-lord verdict (the decider):** read the period lords' sub-lord houses.
   Fulfilment houses ⇒ it happens; negation houses ⇒ it breaks; **BOTH ⇒
   fixed-then-cancelled.**
3. **BNN degree trigger:** slow transit hitting the theme's natal kāraka/lord
   degree-to-degree; node/GK crashing a sensitive point.
4. **Kakṣyā narrowing:** transit delivers only in a bindu-bearing 3°45′ Kakṣyā ⇒
   narrows timing to a 4–5 day window.

### 4D. Convergence, Ranking & Falsification
Count how many independent systems converged per theme; **rank**; the call is the
top-ranked theme. Actively seek contradicting signatures; if strong methods
disagree, lower confidence or rule out. "One factor points here" is never enough.

---

## PHASE 5 — COMMIT (output template, Playbook §6)
- **● Activated Macro-Pattern** — how independent networks isolated the theme.
- **● Structural Micro-Dissection** — Track A vs B; the texture and why.
- **● Cross-Paddhati Verification & Timing** — Varga + KP + BNN + Kakṣyā; the window.
- **● Core Synthesis Summary (blockquote)** — *"<theme>, <texture>, around
  <date/window>"* + confidence + number of systems converged.

---

## MANDATORY COVERAGE CHECKLIST (tick all before answering; mark "data missing" if absent)
- [ ] Vimśottari MD/AD/PD · [ ] Jaimini rashi-daśā · [ ] slow gochara + SAV
- [ ] lord strength + Iṣṭa/Kaṣṭa · [ ] occupants + Avasthā (Track B) · [ ] Argala/Virodhārgala
- [ ] graha-dṛṣṭi · [ ] Bhāva-Chalit · [ ] Varga confirmation
- [ ] **KP sub-lord verdict** · [ ] **BNN trigger** · [ ] **Kakṣyā narrowing**
- [ ] Varṣaphal/Muntha · [ ] convergence counted & rivals ruled out

---

## WORKED EXAMPLE  ⚠️ ARCHETYPE ONLY — shows the PROCEDURE, not a template
> **Never** force a real native's chart to resemble this scenario. This only
> illustrates how the five phases chain together.

**Ask:** "Native ke 2024 mein sabse bada event kya tha?" → Phase 1: life-area
open; window = 2024; want = the single dominant event + nature + timing.

**Phase 2 (compute):** pulled Vimśottari (Venus MD / Saturn AD in 2024), Jaimini
Nārāyaṇa active sign, slow gochara (Saturn over the 10th-from-Lagna), SAV of that
sign, KP sub-lords of Venus & Saturn, BNN hits in 2024, Kakṣyā windows, Varṣaphal
2024 (Muntha house), and D10/D9/D30.

**Phase 3 (select):** several systems touch the **10th / career** — AD lord = 10th
lord; Nārāyaṇa sign holds the Amātyakāraka; Saturn transiting the 10th; Varṣaphal
Muntha in the 10th. A marriage signal exists but from only one system → parked.

**Phase 4 (triangulate):**
- *Macro-scan:* career = 4 independent votes ⇒ HOT; marriage = 1 vote ⇒ ruled out.
- *Filtration:* 10th lord strong in D1 **and** D10 (Track A), but high Kaṣṭa and
  Saturn pressing ⇒ texture = **manifestation with friction**.
- *Confirmation+timing:* D10 lord in a kendra of D10 (confirms career). **KP**
  sub-lord of the AD lord signifies 10/6/11 (fulfilment) **plus** a touch of 12
  (change of place) ⇒ not a mere promotion but a **job/role change**. **BNN:**
  Saturn degree-conjunct the natal 10th lord ~Aug–Sep 2024. **Kakṣyā:** a
  bindu-bearing window in **late August 2024**.
- *Convergence:* 5 independent systems agree.

**Phase 5 (commit):**
> Career — a structural **job/role change** (with friction, not a smooth
> promotion), most likely **late August–September 2024**. Confidence high; 5
> systems converged. Tied nuance: the 12th-house touch leans toward a *new
> employer / relocation* rather than an internal promotion.

*(Note how KP turned a vague "career is active" into "job change vs promotion" —
that confirmation layer is mandatory, never optional.)*

---

## FORBIDDEN BEHAVIOURS
- Answering after only natal + Vimśottari (the cardinal mistake).
- Recomputing or guessing any number instead of asking the Engine.
- Vague Barnum statements that fit any life.
- Forcing the chart to match a known event (no calibration / no hindsight).
- Treating the worked example as a template to fit the native into.
