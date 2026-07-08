# Marriage-trigger pattern study — 50 Rodden-rated charts

**Data:** `dataset.json` — 50 public figures, birth time AA (37) or A (13), with
verified public wedding dates. **Method:** `run_marriage_study.py` evaluates the
engine's `marriage` event-evidence panel at each wedding date (tight ±12h window →
the pratyantar clip lands the evaluation on the day). `control.py` repeats it at
200 random adulthood dates kept clear of the real weddings, to separate *triggers*
from *ambient* firing. Outputs: `results.json`, `control.json`.

## Headline

The naive reading — "13–20 nodes fire at every wedding" — is misleading. Once you
subtract the **baseline** (how often each node fires on a *random* date), most of
that is ambient. This is exactly what the framework's own info-weighting/salience
layer is built to discount.

### The common backbone (present in ~90–98% of charts — but also on most dates)

These are **necessary context, not the trigger** (lift ≈ 0):

- multi-daśā significator running (Ashtottari 98%, Chara 94%, Yogini 94%, Nārāyaṇa 96%…)
- Jaimini **Arudha/Upapada-axis** active — 96% at weddings, but **100% on random
  dates** (fires essentially always ⇒ zero discriminating information)
- Laghu-Pārāśarī daśā-lord valence (90/90), KP fulfilment≥negation (56/56),
  Lagna materialization (58/59)
- Vimśottari MD>AD>PD **signifies marriage** (2/7/11 lord, Venus, or Dārā-kāraka)
  in **88%** — real, but the chain signifies the matter on most dates too.

### The actual discriminators (elevated at weddings vs baseline)

| trigger node | wedding | random | **lift** |
|---|---:|---:|---:|
| Nāḍī: **Śani (Saturn) karma-sanction** — Saturn touches kāraka / fulfilment houses | 52% | 39% | **+13** |
| **Bhṛgu Bindu** activated by a slow mover (Moon–Rāhu midpoint) | 62% | 52% | **+10** |
| **Double-transit from the Moon** (Chandra-lagna) | 16% | 7% | **+9** |
| **Bhinnāṣṭakavarga delivery** (kāraka in a bindu-bearing kakṣyā) | 98% | 90% | **+8** |
| **Varṣaphal Muntha** on the 7th (Tājika annual) | 14% | 7% | **+7** |
| daśā **kāraka at sūkṣma** (micro-trigger) | 52% | 46% | **+6** |
| Sudasā (Jaimini Śrī) significator running | 98% | 92% | **+6** |
| **double-transit on 7th house/lord** (classic Jup+Sat) | 24% | 18% | **+6** |
| fulfilment-houses (2/7/11) double-transit + lords | 36% | 32% | **+4** |

Composite: a wedding date carries **4.5** of these nine on average vs **3.8** on a
random date. **Suppressed** at weddings: Sade-Sati/Kaṇṭaka (−13) and a Tājika
Varṣeśa mismatch — i.e. Saturn's *stress* transit from the Moon works *against*
marriage timing.

## Same pattern, different drivers

The *slots* are shared; the *fillers* vary chart to chart:

- **Who is the running marriage significator:** Venus/kalatra 40% · Dārā-kāraka
  36% · 7th-lord 28% · 11th-lord 32% · 2nd-lord 20% — no single planet dominates;
  the role is filled by whichever planet plays it natally.
- **Which slow planet lights the 7th/Upapada:** Jupiter on UL 19/50 · Saturn on UL
  12/50 · Saturn on 7th 20/50 · Jupiter on 7th 17/50 — roughly even. Sometimes
  Jupiter's blessing, sometimes Saturn's sanction; the *event* needs one of them,
  not a fixed one.
- **Convergence:** mean **6.4 of 7** independent daśā systems agree at the wedding
  (49/50 have ≥5) — but this near-saturation is *also* why daśā-agreement alone
  can't be the trigger; the discriminators above are what move.

## Honest caveats

- Lifts are **modest (+5 to +13 pts)** on n = 50 vs 200 — directional, not
  statistically settled. A larger control (10+ dates/native) would firm this up.
- Natal **standing balance** averaged **−0.94** (only 2/50 "blessed"); many of
  these unions later ended — consistent with the framework timing the *event* on
  the timing panel, not on a rosy natal promise.
- No Indian natives (no birth-certificate-grade times exist publicly), so this is
  a Western-record sample; caste/rectified Indian data would add noise, not rigor.

---

# Round 2 — chart-specific "marriage circuit" study (`circuit_study.py`)

Round 1 asked fixed questions. Round 2 (after a rule-catalogue review across
schools: Parāśara, KP, Jaimini, Strī-jātaka, BNN/Nāḍī, Western transits) builds
each chart's OWN circuit — its 7th lord, occupants of the 7th, Venus, Dārā-kāraka,
D9 connections, star-lords, UL, gender-aware kārakas — and evaluates 12 classical
hypotheses at the wedding vs 10 random adult dates per native (500 controls).

## The blunt discovery about daśā rules

Every daśā-based rule as classically stated is AMBIENT — even chart-specific ones:

| hypothesis | wedding | control | lift |
|---|--:|--:|--:|
| MD/AD/PD lord ∈ core circuit (7L/occupant/Venus/DK) | 72% | 75% | −2.6 |
| AD lord specifically ∈ core circuit | 32% | 41% | −8.6 |
| MD/AD lord in D9 circuit | 50% | 51% | −1.0 |
| gender kāraka in chain (M:Venus, F:Jupiter/Mars) | 42% | 46% | −3.8 |
| MD/AD lord in nakshatra of a circuit planet | 60% | 57% | +3.0 |

Why: with 3 chain lords and a 3–6 planet circuit, the chain touches the circuit on
MOST dates of a life. The daśā rule can't pick the date; it's a permission slip
nearly always signed.

## Where the date actually lives: TRANSITS

| hypothesis | wedding | control | lift |
|---|--:|--:|--:|
| **classic double-transit** (Jup AND Sat both on 7th/7L/UL, sign+dṛṣṭi) | **66%** | 50% | **+16.2** |
| transit Jupiter within 6° of descendant/7L/Venus degree | 40% | 30% | +10.2 |
| transit Saturn (sign+dṛṣṭi) on 7th/UL/7th-from-UL | 74% | 65% | +9.2 |
| BNN gender rule: transit Jup conj/trine natal Venus(M)/Mars(F) | 16% | 11% | +5.2 |

Combinations (the "two-key" doctrine):
- any-daśā-link AND double-transit: 58% vs 47% (+11)
- double-transit AND Saturn-gochara: 56% vs 43% (+13.4)

## Rank test — the usable result

Scoring dates by the trigger-weighted composite (double-transit ×2 + Jup-degree +
Sat-gochara + BNN-gender + Jup-gochara·0.5 + daśā-star·0.5), each wedding ranked
against that native's own 10 random dates:

- mean wedding percentile: **61.2** (chance 50) — **permutation p = 0.007**
- wedding above median: 32/50 · top quartile: 23/50 · top-3 of 11 dates: 26/50

So the pattern is REAL (not chance) but PROBABILISTIC: it concentrates probability
~2× around true wedding windows; it does not pinpoint the date. Drivers differ per
chart exactly as predicted: 44 distinct driver-combinations across 50 weddings.

## Caveats
- The trigger weights were chosen on this same sample (n=50) — the p-value is
  honest for "is there signal", optimistic for the exact weights. A fresh sample
  should re-validate.
- Wedding dates are chosen by couples partly FOR auspiciousness (muhūrta) — some
  transit signal may reflect date-selection culture, not destiny.

---

# Round 3 — BLIND forward test (`predict_marriage.py`): the recipe does NOT yet generalize

The predictor applies the validated trigger composite to a fresh chart and emits
top-15% windows over a span. Blind protocol: rankings computed from birth data
only; actual wedding dates revealed after.

Subjects (Rodden A, NOT in the training 50): Bruce Willis (2 weddings, span
1985–2012) and Frank Sinatra (4 weddings, span 1938–1978).

| wedding | score percentile in span | in a top-5 window? |
|---|--:|:-:|
| Willis 1987-11-21 | 6 | ✘ |
| Willis 2009-03-21 | 70 | ✘ |
| Sinatra 1939-02-04 | 9 | ✘ |
| Sinatra 1951-11-07 | 9 | ✘ |
| Sinatra 1966-07-19 | 48 | ✘ |
| Sinatra 1976-07-11 | 70 | ✘ (window #5 ended 1976-06-10 — missed by ~4 weeks) |

Mean percentile **35 — at/below chance** on these two charts. The in-sample
edge (61.2 pctl, p=0.007) did NOT transfer.

## Honest reading
1. **The aggregate signal is real; the per-chart recipe is not.** A +10-to-16-pt
   frequency lift across 50 charts is too weak/heterogeneous to rank ONE chart's
   timeline. In-sample weight selection inflated the apparent usability (flagged
   in Round 2's caveats — now demonstrated).
2. **Population mismatch.** Both blind subjects are serial marriers with several
   impulsive weddings (Sinatra married Gardner days after his divorce). The
   training weddings skew toward long-planned first marriages — precisely the
   ones most likely to be (consciously or culturally) scheduled under favorable
   transits. Supports the muhūrta-selection confound.
3. Near-misses (Sinatra's 1976 window off by 4 weeks; a 1964–65 window vs the
   1966 Farrow wedding) are suggestive but score as misses — no partial credit.

## Status
- The engine's new nodes (Arudha double-transit, ♀-Mars Nāḍī channel) remain
  justified: doctrine-sourced, and genuinely elevated AT weddings in-sample.
- A "marriage-date predictor" is NOT validated. Required before any such claim:
  a held-out validation sample (≥50 fresh charts), weights frozen in advance,
  and per-chart score normalization; ideally separate cohorts for planned vs
  impulsive weddings.

---

# Round 4 — nakshatra-lord transit study (`nakshatra_study.py`)

User hypothesis: the fine timing should live at the NAKSHATRA level — transits
through stars whose lords belong to the chart's marriage circuit, and the
daśā-lord's own transit star (KP's transit rule). 12 star-level hypotheses,
50 weddings vs 500 seed-matched controls.

## In-sample: two real star-level channels

| hypothesis | wedding | control | lift |
|---|--:|--:|--:|
| **N5: MD lord's own TRANSIT position in a circuit-lord's star** | 46% | 33% | **+12.6** |
| **N1: transit Jupiter in a circuit-lord's star** | 44% | 32% | **+12.4** |
| C2: slow-planet star-window AND Moon day-key | 30% | 21% | +8.6 |
| N6: AD lord's transit in circuit star | 38% | 34% | +3.8 |

The N5 finding is conceptually important: the daśā finally shows discrimination —
but only through its **transit position** (daśā × gochara cross-term, exactly
KP's "the daśā lord delivers when it transits the star of a significator"), never
through its name alone (all Round-2 daśā-name rules were ambient).

## The day-picker is still unfound

Transit **Moon in a circuit star** (KP day marker): 38% vs 38% — **zero lift** at
the exact wedding day. Sun star: +0.8. Transit-over-natal-stars: ~0. Transit
Venus in circuit star: **−10.4** (if real, Venus's own star-position is
anti-selected at weddings — unexplained; possibly noise). So "which day inside
the window" is NOT answered by luminaries' star positions in this sample.

## Blind check (Willis + Sinatra, 6 weddings)

N5/N1 fired at 1 of 6 blind weddings (~17%, below the 33% baseline); the
augmented composite percentiles: 3, 75, 5, 5, 39, 60 — same non-transfer as
Round 3. Every in-sample channel found so far (sign-level and star-level) fails
on these two serial-marrier charts.

## Standing conclusion after 4 rounds
1. In-sample, wedding dates consistently show +10-16-pt elevated transit
   signatures across independent channels (sign double-transit, Jupiter degree,
   MD-transit-star, Jupiter-star) — too consistent to be pure chance (the
   round-2 permutation test held at p=0.007).
2. No recipe yet transfers to out-of-sample charts. Either the 2 blind charts
   are atypical (impulsive serial marriages), or in-sample lifts are inflated
   by muhūrta-selection + multiple comparisons.
3. Decisive next step is DATA, not more hypotheses: a fresh held-out sample of
   50+ Rodden-rated weddings, current channels frozen, tested once.

---

# Round 5 — first volunteer blind test (Indian chart, anonymized)

The framework's owner volunteered their own chart (details withheld — no native
data in the repo). Protocol: full engine pack + sign-composite + star channels
run over a 19-year span; ranked windows DECLARED before the real date was
revealed.

- Declared: #1 Jul–Oct 2023 · #2 Feb–Oct 2020 · #3 Feb–Apr 2024 · #4 Sep–Nov
  2021 — with an explicit note that 2023→late-2024 formed one extended hot zone.
- Actual wedding: late Jan 2024.
- Blind score of the true date: **84th percentile** of the native's 231-month
  timeline; engine convergence top-decile (between ledger rows 13.75/14.43;
  span peak 16.15 fell ~10 weeks after the wedding). Drivers: Venus-MD(7L+kāraka)
  > lagneśa-AD > Rahu; Jupiter transiting the lagna + Saturn aspect; 7th-axis
  double-transit; MD-lord transit star; Moon in circuit star on the day.
- Verdict: window #1 missed by ~4 months; the date fell 3 days from window #3's
  edge (monthly-grid artifact) inside the declared hot zone. Best blind result
  so far (vs 3/75/5/5/39/60 pctl on the two Western serial-marrier charts) —
  consistent with the muhūrta hypothesis: the method reads PLANNED weddings
  better than impulsive ones.

n = 1; anecdote, not validation. The frozen-channel held-out study (50 fresh
charts) remains the decisive next step.
