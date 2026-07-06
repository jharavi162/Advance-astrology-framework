# BNN_METHODS.md — Bhrigu-Nandi Nāḍī, the engine's reference

Distilled from a full BNN marriage class (R.G. Rao lineage; user-supplied
transcript, 2026-07-04) plus the user's own doctrine. This is the **reference**
for how the Nāḍī voice reads a chart. Division of labour (per CLAUDE.md):

- The **ENGINE** computes the deterministic pieces — the kāraka, the golden
  relations, the degree-ordered chain, the transit degree-locks. See
  `interpreter/event_evidence.py` (`nadi_karaka`, `nadi_chain`, `nadi_nature`,
  `nadi_pinpoint`, `nadi_rupture_pinpoint`, `_nrel`, `_nadi_sign`).
- The **AI** applies the *significations* and tells the story. It never
  recomputes a position — it reads what the engine hands it.

No calibration, no native-specific hard-coding — the kāraka is always
domain-driven (`nadi_karaka`), never a fixed planet for a fixed person.

---

## 1. Significations (kāraka-tattva) — the vocabulary
Every reading starts from what a planet *signifies* (BNN is signification-first,
not lagna-first):

| Planet | Signifies (relationship/marriage flavour) |
|---|---|
| Sun | authority, govt, father, fame; influential/ego-driven spouse |
| Moon | emotions, mother, instability; caring but changeable, mood-swings |
| Mars | **husband (female chart)**, passion, drive, aggression; the *cutter/executor* |
| Mercury | communication, business, daughter, friends/GF-BF; witty, playful, younger-seeming |
| Jupiter | **jeeva (the native)**, blessing, expansion, teacher; mature/fortunate spouse, abundance |
| Venus | **spouse (male chart)**, love, quality-of-marriage; comfort, romance |
| Saturn | delay, karma, hard work, cold; older/serious spouse, karmic bond |
| Rahu | foreign, inter-caste/community, unconventional; sharp/blunt, **multiple relations / affairs** |
| Ketu | **cut / break / detachment**, mokṣa; separation, disinterest, divorce |

## 2. The hero (pointer) planet
Pick the hero by the question:
- **Marriage** — male chart → **Venus** (spouse); female chart → **Mars** (husband).
- **Career** → Saturn (karma). Children → Jupiter. Etc. (see `NADI_KARAKAS`).
- **Jupiter = jeeva** is always a co-hero for any big life event (it *is* the native).

## 3. The two core relations ("with / holding hands")
Professional standard — **conjunction + the 1/5/9 trine ONLY**. The 7th
(opposition) is **NOT** a BNN golden relation.
- **Conjunction (yuti):** planets in the same sign.
- **Trine (1/5/9):** from a planet, count the 5th and the 9th sign; anything there
  is treated "as with" the planet. (Engine: `_nrel`, `_NADI_REL = {0,4,8}`.)

## 4. Retrograde (vakri) → one sign BACK
A retrograde planet is reckoned **one sign back** before its conjunction/trine is
judged (it walks backwards). Its degree number is kept. Nodes are always taken at
their actual sign. (Engine: `_nadi_sign`.)

## 5. The CHAIN and its degree-order = the story
Collect the hero + every planet conjunct/trine (1/5/9) it, and **order them by
degree**. The degree order **is the chronology**:
- a member with a **lower degree** than the hero acted **before / already**
  (pre-existing);
- a **higher degree** unfolds **after** (post-event).

Read the chain left→right as the life-story and apply each planet's significations.
(Engine: `nadi_chain` returns the ordered chain with per-member `when` = pre / HERO
/ post and its significations.)

Examples from the class:
- hero **Venus → Jupiter** (Jupiter higher) = spouse, then blessing/expansion
  *after* marriage (spouse's fortune rises post-wedding).
- **Jupiter → Mercury behind** (Mercury lower) = a past GF/BF story *before* the
  marriage; also the Jupiter–Mercury pair adds a "child-related story".
- **Moon after the hero** = post-marriage emotional ups-and-downs (not divorce).

## 6. Planet-pair significations (the AI applies these on the chain)
- Mars + Sun → ego-clash, control/power struggle.
- Mars/Venus + Moon → mood-swings, passionate but changeable.
- Mars/Venus + Mercury → witty, business-minded, playful, younger-seeming spouse.
- Mars/Venus + **Jupiter** → good, mature spouse; successful, expanding marriage.
- Mars/Venus + Saturn → delay, cold, karmic-heavy bond, older/serious spouse.
- Mars/Venus + **Rahu** → foreign/inter-caste; if the native does NOT go
  cross-culture/abroad, friction & affairs; blunt, sharp partner.
- Mars/Venus + **Ketu** → **divorce / detachment** — legal or mental break.
- Venus + Rahu **then Mars** ahead → cheating risk (Mars = the biggest concealed
  cheater); Venus + Rahu then **Jupiter** ahead → no cheating.

## 7. Second / multiple partners — the BNN way (NO house)
BNN reads successive/second partners **from the chain sequence**, not a house:
- **Rahu just ahead of the hero** (Venus/Mars) → prone to *multiple relationships*
  / love-affairs; marriages even after a breakup.
- **Ketu behind the hero** (lower degree) → a break happened *before* this
  marriage (a prior relationship/marriage broke, then this one);
  **Ketu ahead of the hero** → a break *after* this marriage.
- So the **benefic that comes after a Ketu-cut in the chain = the next/second
  partner**; the narrator should read post-hero (and post-Ketu) chain members as
  the "life after the first marriage" story.

> House-based second-marriage (see below) is a **Parashari/KP** overlay, separate
> from BNN. The two are kept as independent convergence voices — never merged.

## 8. Timing (transits / gochar) — the funnel
Natal chart shows the promise; **transits decide when**. BNN times with the major
bodies only — **Jupiter (year), Saturn (karma-sanction), Rahu/Ketu, and the fast
7th-lord / Mars / Venus / Moon for month & day** — matched by golden relation and
**degree-to-degree** (the tighter the degree-lock, the surer the trigger). The Sun
is NOT a BNN timing planet. (Engine: `nadi_pinpoint` for unions,
`nadi_rupture_pinpoint` for breaks — separators degree-locked on the break-axis.)

- Jupiter aspecting/over Venus → early marriage; Saturn on Venus → delay.
- Ketu = the one planet that breaks a marriage; Saturn = delay & karmic weight.
