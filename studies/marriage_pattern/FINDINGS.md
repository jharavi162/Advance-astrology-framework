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
