# Interpretation-Style Improvement Log

This log records **how to read and narrate** the Engine's evidence better — *not*
changes to any calculation, and *not* fitting rules to a native's history.

> **No-calibration premise (same as `RULE_CHANGELOG.md`).** Every entry here is a
> *generalizable interpretation rule* triggered by a blind past-event review.
> The blind test is used only to catch **narration/polarity mistakes** (the
> numbers and timing were right; the *reading* of them was wrong). No engine math
> and no per-native fact is encoded. Each lesson must apply to *any* chart.

Format per entry: symptom (what the narration got wrong) · root cause ·
**improved interpretation rule** · how to operationalise it from the existing
matrix.

---

## 2026-06-21 — Relationship-domain narration: six polarity/segmentation fixes

A marriage/relationship blind review showed the **windows were timed correctly**
(the dāśā/gochara/Sūkṣma hot-dates matched real inflection points), but the
*interpretation style* over-read activation as fulfilment and merged distinct
relationships into one arc. The six lessons below are domain-general for any
"relationship over a period" question.

### 1. Activation ≠ positive outcome — read polarity from Track-B weight, not from the dāśā label
- **Symptom:** A "7th-lord / marriage-kāraka dāśā window" was narrated as a
  *peak / formalization*, when structurally it was a **stall or break**.
- **Root cause:** Treating any marriage-significator period as a *fulfilment*
  signal. A dāśā only marks that the matter is **active/eventful** — the *sign*
  of the event comes from Track-B.
- **Improved rule:** When Track-B is structurally heavy — e.g. an **effective
  8th-house Argala on the 7th**, a **debilitated/combust 7th-lord or Dārakāraka**,
  a **detachment Mahādaśā (Ketu) umbrella**, or **nodal pressure on the 2/8
  axis** — a "marriage window" must be read as *activation that may STALL or
  END*, never assumed positive. Activation is a magnitude; Track-B sets the
  sign.
- **Operationalise:** Before labelling a window positive, count Track-B hits
  already in the matrix (Argala `*` from 6/8/12 onto the 7th; Iṣṭa/Kaṣṭa of the
  7th-lord; Avasthā mood; node transit house). If Track-B ≥ Track-A, narrate
  "eventful but unstable", not "fulfilment".

### 2. Don't fuse distinct relationships into one arc — an AD-lord flavour change can be a RESET
- **Symptom:** Two different relationships across the window were narrated as a
  single continuous arc (romance → commitment → formalization).
- **Root cause:** Assuming consecutive marriage-windows belong to the *same*
  partner/relationship.
- **Improved rule:** When the Antardaśā lord changes from one **KP house-flavour
  to a structurally different one** (see #3) — especially if a **separation
  signature sits between them** (see #4) — treat the AD boundary as a possible
  **new relationship / reset**, not continuation. Offer the multi-relationship
  reading explicitly rather than stitching one story.
- **Operationalise:** Segment the window at AD boundaries; for each segment label
  the relationship *type* from its lord's KP significations; flag a reset wherever
  the type changes or an ending-window (worth #4) falls on the seam.

### 3. Map the KP house-mix to relationship TYPE explicitly (romance vs matrimonial)
- **Symptom:** A matrimonial-flavour, low-romance bond was narrated as the
  "growth of a romance".
- **Root cause:** Reading only "marriage active" without reading *which* houses
  are lit, which encode the *nature* of the bond.
- **Improved rule — state the type from the running lord's own significations:**
  - **5 / 8 / 12 dominant** → love / secret / physically-or-emotionally private /
    **long-distance** affair (5 = attraction, 8 = hidden/intense, 12 = bed/
    distance/foreign/loss).
  - **2 / 7 / 11 dominant** → **formal / arranged / matrimonial / family-sanctioned**
    union (2 = family, 7 = legal partner, 11 = social formalization).
  - A bond can be **emotionally driving yet not romantic** when 2/7 fire without 5
    — say so; do not upgrade it to "romance".
- **Operationalise:** Already available via `KPSignificators.planet_signifies(p)`
  for each segment's lord — quote the house list and name the type.

### 4. Always run an explicit ENDING/separation scan — not only onset & peak windows
- **Symptom:** The arc's *end* (a relationship that fully closed) was not given
  its own window; only beginnings/peaks were dated.
- **Root cause:** Scanning for manifestation triggers only.
- **Improved rule:** For any relationship-over-time question, compute a dedicated
  **separation window** alongside the manifestation windows: 6/8/12 activation of
  the 7th or its lord, **Saturn aspect/transit onto the 7th-lord** (cooling/
  finality), a **node-axis ingress** touching 2/7/8, and afflictions to
  **A7 / UL / Dārakāraka**. Report it as a first-class output: "likely
  cooled/ended around <window>". Closing *triggers* may begin before the actual
  end — distinguish "decline starts" from "fully ended".
- **Operationalise:** Add an ending-scan pass to Phase-4C of the relationship
  reading; rank its windows next to the onset windows.

### 5. A benefic Sūkṣma under a malefic/detachment umbrella = "false dawn", not a peak
- **Symptom:** A tidy **triple-benefic Sūkṣma + Jupiter-in-7th gochara** window
  was ranked the *strongest positive*, but it delivered only a brief re-contact
  that then closed.
- **Root cause:** Letting a pretty micro-trigger outrank the macro umbrella when
  deciding **polarity** (a cousin of the prompt's "degree-perfect BNN" timing
  miss, but for *sign* rather than *date*).
- **Improved rule:** A benefic Sūkṣma/Prāṇa firing **under a detachment
  Mahādaśā (Ketu) or as a 12-dominant Antardaśā begins (Rahu→12)** commonly
  produces a **brief re-opening that fails** ("false dawn"). Rank the **MD/AD
  nature above the Sūkṣma's beauty** when assigning the *sign*; keep the Sūkṣma
  only for the *date*. A benefic trigger times *an event*, which may be a final
  flicker, not fulfilment.
- **Operationalise:** When a benefic micro-window sits inside a malefic umbrella,
  caption it "re-activation, low durability" unless Track-A independently
  outweighs the umbrella.

### 6. An AD change into a 12-dominant lord is a likely CLOSURE marker
- **Symptom:** The transition into a separation-flavoured Antardaśā was noted as a
  "risk" but not as the probable **closure point** of the matter.
- **Root cause:** Under-weighting an AD-lord whose KP significations are
  12-heavy.
- **Improved rule:** When the running Antardaśā rolls into a lord that **signifies
  12 prominently** (loss/separation/exit) over the 7th's matters — especially a
  node — read it as the **likely terminal/closure window** of the current
  relationship segment, and date the "considered closed" status from its onset.
- **Operationalise:** At each AD boundary, check the incoming lord's
  `planet_signifies`; if 12 leads and 2/7/11 are weak, mark "closure-probable
  from <AD start>".

### 7. "Same partner love→marriage" vs "married someone else" — read the bundle LINKAGE, not the timeline
- **Symptom:** When a relationship timeline runs *continuous* up to marriage, the
  narration assumes the **loved partner == the married partner**. But a love arc
  can run unbroken and the *marriage still happen with a different person* — the
  dāśā continuity does not certify partner-identity.
- **Root cause:** Inferring partner-identity from *timeline continuity* instead of
  from whether the **romance bundle and the marriage bundle are structurally
  linked**.
- **Improved rule — triangulate two separate bundles and test their linkage:**
  - **Romance bundle:** 5th house + 5th-lord + **Venus** + A5.
  - **Marriage/spouse bundle:** 7th + **UL & UL-lord** + 2nd-from-UL + **DK** +
    the **gender-correct spouse-kāraka** (Jupiter = husband for a female chart,
    Venus = wife for a male chart).
  - **Same person (love converts to marriage):** the two bundles **link** —
    shared lord, conjunction, sign-exchange, mutual dṛṣṭi, same nakṣatra-lord, or
    DK conjunct/aspecting the UL-lord, and the spouse-kāraka unafflicted.
  - **Different person (married someone else, even on a continuous timeline):**
    the bundles are **disjoint or mutually afflicting** — e.g. the romance-kāraka
    sits *alone* and unconnected while the **spouse-cluster (UL-lord + DK +
    spouse-kāraka) is combust / in dusthāna / Vikala**, with no aspect tying the
    love-significator to the spouse-significators. The love is promised, the
    marriage is promised, but they point at *different* significators.
- **Operationalise:** Compute both bundles; explicitly state whether a linkage
  exists. If the romance-kāraka is strong-and-separate while the spouse-cluster is
  afflicted-and-disjoint, narrate "the loved one may not be the one married /
  love-and-marriage split" as a live branch — do **not** collapse it into one
  partner just because the dāśā ran unbroken.

### 8. Read Shadbala + Iṣṭa/Kaṣṭa + Avasthā *per-kāraka and as a contrast* — and use the gender-correct kāraka
- **Symptom:** Planetary strength was used only qualitatively ("combust",
  "debilitated") in passing; the **husband-kāraka for a female chart (Jupiter)**
  was not foregrounded, and no romance-vs-spouse **strength contrast** was drawn.
- **Root cause:** Treating Shadbala/Iṣṭa/Kaṣṭa/Avasthā as a databank dump rather
  than a discriminator, and defaulting to Venus/7th without switching to the
  **gender-correct** spouse-kāraka.
- **Improved rule:** For every relationship reading, pull **Shadbala, Iṣṭa/Kaṣṭa,
  and Avasthā for each marriage-kāraka separately** and *contrast* them:
  - A **high-Iṣṭa, clean romance-kāraka** beside a **high-Kaṣṭa / Vikala /
    combust spouse-kāraka** is a classic "**love favoured, marriage distressed**"
    split — pairs directly with #7 (loved one ≠ married one, or marriage fails to
    convert).
  - Always select the **gender-correct kāraka**: Jupiter = husband (female
    chart), Venus = wife (male chart); never reduce the spouse-kāraka's condition
    to "combust" without reading its **Avasthā (Vikala/Mṛta/Duḥkhita)** and
    **Kaṣṭa** too.
- **Operationalise:** Already in the matrix (`shadbala()`, `ishta_kashta()`,
  `avasthas(p)`); the fix is to *quote each kāraka's row side-by-side* and let the
  contrast set the texture, not to mention strength only when it is convenient.

---

### Net change to the relationship-reading procedure
For a "relationship events over a period" question, the improved Phase-4/5
narration must: **(a)** segment by AD boundaries and label each segment's *type*
from its KP house-mix (#3), **(b)** allow multiple distinct relationships (#2),
**(c)** set each segment's *sign* from Track-B + the MD/AD umbrella, not the dāśā
label or a pretty Sūkṣma (#1, #5), **(d)** emit explicit **ending/closure
windows** beside onset windows (#4, #6), **(e)** test romance-bundle vs
marriage-bundle **linkage** to decide same-vs-different partner (#7), and
**(f)** drive texture from a **per-kāraka, gender-correct strength contrast**
(Iṣṭa/Kaṣṭa/Avasthā/Shadbala), not from dignity in passing (#8). Timing
methodology is unchanged — only the *reading* of sign, type, segmentation,
partner-identity, and strength is tightened.
