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
- (later) `02_marriage.md`, `03_profession.md`,
  `04_children.md`, `05_education.md`, `06_disease_longevity.md`, `07_wealth.md`, …

Status: **timing method (pass 1) + significations (pass 2) distilled.**
Per-domain chapters pending.

## TODO (pending — do when asked)
- Distil the per-domain chapters, in order: `02_marriage.md`,
  `03_profession.md`, `04_children.md`, `05_education.md`,
  `06_disease_longevity.md`, `07_wealth.md`. Data/rules → engine (+tests);
  interpretation → these docs. (Not automatic — runs in a session when asked.)
- Fine-tune (also deferred): natal-anchor the transit Venus≈Jupiter refine
  (currently chart-independent); validate dates once ground truth is shared.
