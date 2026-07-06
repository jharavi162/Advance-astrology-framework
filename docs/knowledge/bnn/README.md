# BNN knowledge base — distilled from the source book

Source: **`docs/bhrigu-nandi-nadi.pdf`** — *Bhrigu Nandi Nadi* by R.G. Rao (327 pp,
text-PDF). This folder is the **progressive distillation** of that book into a
structured, reusable knowledge base — read once, kept permanently, referenced by
the engine + the AI narrator (so the raw 327-page PDF is never re-read every time).

Division of labour (per CLAUDE.md):
- Anything **calculable** (a house/kāraka/rule that reduces to true-false or a
  number) → goes into the **engine/data** with a regression test.
- **Interpretation** (meaning, judgment) → stays here as reference for the AI.

Files (added pass by pass):
- `00_significations.md` — the kārakatwa dictionary (grah kāraka per matter +
  the reading procedure); rāśi notes secondary (BNN is kāraka-first).
- `01_timing_method.md` — how BNN times events (Jupiter transit, Saturn, karakas).
- `02_marriage.md` — marriage timing, quality, multiple/widowhood, partner
  description; ends with 3 approval-gated candidate quality-nodes.
- (later) `03_profession.md`,
  `04_children.md`, `05_education.md`, `06_disease_longevity.md`, `07_wealth.md`, …

Status: **timing (1) + significations (2) + marriage (3) distilled.**
Remaining per-domain chapters pending.

## TODO (pending — do when asked)
- Distil the per-domain chapters, in order: `03_profession.md`,
  `04_children.md`, `05_education.md`, `06_disease_longevity.md`,
  `07_wealth.md`. Data/rules → engine (+tests); interpretation → these docs.
- Decide on the 3 candidate marriage-quality nodes proposed at the end of
  `02_marriage.md` (jīva-12th-from-kāraka; kāraka-12th-from-descriptor;
  kāraka-conjunct-separator) — approval-gated, not yet wired.
- Fine-tune (also deferred): natal-anchor the transit Venus≈Jupiter refine
  (currently chart-independent); validate dates once ground truth is shared.
