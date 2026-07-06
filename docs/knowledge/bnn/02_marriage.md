# BNN — Marriage (pass 3, per-domain)

Source: **`docs/bhrigu-nandi-nadi.pdf`**, R.G. Rao. Line refs (Lnnnn) are into
the extracted text, for traceability. This chapter is the **narrator reference**
for marriage; the *calculable* rules already in the engine are flagged, and the
genuinely-missing calculable ones are listed at the end as **candidate nodes
(approval-gated)** — none added silently, none tuned to a date.

BNN reads marriage **kāraka-first** (see `00_significations.md`):
- **Venus = the marriage/spouse event-kāraka for BOTH sexes** (the "seed", the
  union). This is *the* marriage timer-target.
- **Jupiter = the Jīva/timer** — his transit *contacts* over Venus (and the
  spouse-descriptor) fix the **age** of marriage.
- In a **female** chart, **Mars additionally describes the husband** (his rank,
  nature, condition); in a male chart Venus also colours the wife.

---

## 1. TIMING — when marriage fructifies

- **Jupiter contacts Venus, or enters Venus's own sign (Libra/Taurus) →
  marriage / negotiations.** *"After transiting Gemini, Jupiter … contacts
  Venus in Virgo … marriage is likely to take place"* (Chart I, L238); the
  entry into Libra (Venus's house) triggers *"marriage negotiations"* (L228).
- **Age is counted by Jupiter's successive rounds** from birth — the year
  Jupiter's transit reaches the marriage-kāraka/its house in a given round is
  the marriage age (e.g. *"married in his 27th year … when Jupiter transits
  Ketu"* L1372; *"Female native will be married in her 18th year"* L1085;
  *"married at 30-31"* L1916).
- **Saturn's sanction** (the karma-hand) + Venus's involvement co-confirm; the
  **Moon** is the fast day-hand once the year is set.
- ✅ **Engine already wires this:** `nadi_jeeva` = transit Jupiter conj/trine the
  Nāḍī kāraka (Venus for the marriage class, via `nadi_timing_karaka`);
  `nadi_karma` = Saturn sanction; Moon-hand in `day_convergence`. Golden
  relations = conjunction + 1/5/9 trine; the 7th is dṛṣṭi (see
  `01_timing_method.md`).

---

## 2. QUALITY / direction of the married life

- **Jupiter in the 12th from Venus → an UNHAPPY first marriage** (the jīva sits
  in the "loss" house from the marriage-kāraka): *"Jupiter in 12th to Venus
  indicates unhappy first marriage — thereafter he will be happy"* (L757).
- **Venus in the 12th from Mars → DELAY in marriage** (the event-kāraka in the
  loss-house from the descriptor): *"Venus in 12th to Mars denotes delay in
  marriage … the native will marry last"* (L4292).
- **Venus conjunct a separator/malefic → the partner/union suffers:**
  - Venus + **Ketu** → the wife/partner faces **abortions / progeny trouble**
    (*"She will face abortions as Venus is conjunct Ketu"* L1372).
  - Venus + **Rahu** → **estrangement**, the wife leaves and returns only on a
    later favourable Jupiter transit (L322–323).
  - Venus with malefics adjacent → **wife sickly / suffering** (L452, L489).
- **Female — husband's condition is read from Mars:** Mars **exalted** →
  husband holds a **high post** (L6245, L10999); Mars **debilitated/afflicted**
  → husband troubled / low conduct (L9844). Venus still times the marriage;
  Mars grades the husband.

## 3. MULTIPLE marriages / widowhood

- **Two marriages/wives** are shown when the union-kāraka is **split or
  flanked**: *"planets between Venus and Mars → two wives"* (L7555);
  **Moon in the 6th to Venus → two marriages** (L1148). (Serial spouses shift by
  the ordinal rule — see below.)
- **Widowhood / loss of spouse** — afflicted Venus/Mars axis: *"This indicates a
  widow"* (L563); *"When Jupiter transits Libra … the native will become a
  widow"* (L3739); *"lost their husbands because of the placement of Venus"*
  (L5509).
- ✅ **Engine already wires:** the **ordinal meta-rule** (2nd spouse = 9th house,
  Nth shifts by 2×(N−1)) in `significators.py`; the **rupture/separator** timing
  (`nadi_rupture`: Śani + Rāhu/Ketu) for a break; divorce as its own domain.

---

## 4. The partner's description

Read the **sign and company of the union-kāraka** and the **7th-from it**:
- kāraka in a benefic/dignified sign, benefic company → a good-natured, well-off
  partner; *"the partner will be a religious lady and beautiful"* (L1372, from
  Venus's company).
- the 7th-from-kāraka (dṛṣṭi) and any exchange (parivartana) with another lord
  ties in that lord's matters (e.g. Venus⇄Mercury → an artistic/educated match).
- This is **AI judgment** (narration), not a boolean — kept here as reference.

---

## Division of labour & candidate nodes (approval-gated)

**Already DATA/nodes in the engine (no change needed):** marriage kāraka = Venus;
Jupiter-jīva × Venus timing; Saturn sanction; Moon day-hand; ♀ husband-kāraka =
Mars (`_w_female_husband_karaka`); ordinal 2nd-spouse = 9th; rupture timing;
divorce domain.

**Calculable, now WIRED (user-approved 2026-07-06).** All three are the
**domain-general** form of a BNN rule (they read the matter's kāraka/descriptor,
never a native), soft & quality-only (never positive, never a veto), and none is
tuned to any date. Each is a `register_witness(... "standing" ...)` with a
regression test + coverage-matrix row, merged to `main`:

1. ✅ **"Jīva in 12th-from-kāraka" — quality-drag** (`_w_jiva_12th_from_karaka`,
   −0.6). Natal Jupiter in the 12th sign from the domain kāraka ⇒ diminished
   enjoyment of that matter (BNN: Jupiter 12th-to-Venus = unhappy marriage,
   L757). Dormant when the kāraka IS Jupiter.
2. ✅ **"Kāraka in 12th-from-descriptor" — delay**
   (`_w_karaka_12th_from_descriptor`, −0.5). Event-kāraka in the 12th from the
   matter's descriptor graha ⇒ the matter is delayed (BNN: Venus 12th-to-Mars =
   delayed marriage, L4292). Dormant when event-kāraka == descriptor (e.g. a
   male's marriage, or non-marriage matters with no distinct descriptor).
3. ✅ **"Kāraka conjunct a separator (Rāhu/Ketu)" — afflicted union**
   (`_w_karaka_conjunct_separator`, −0.6). The event-kāraka in a node's company
   ⇒ estrangement / progeny-trouble flavour (BNN: Venus+Ketu, Venus+Rahu,
   L1372/L322) — scoped to the kāraka, finer than the generic occupant-nature.

> These are **quality/standing** signals (they shade the verdict's *nature* via
> `standing_balance`), not timers — they never move a date, only colour how the
> matter is enjoyed. Regression test:
> `test_bnn_quality_standing_witnesses_registered_and_fire`.
