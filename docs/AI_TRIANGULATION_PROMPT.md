# AI TRIANGULATION FRAMEWORK

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
>
> **This document is your DIRECTOR.** For any astrological analysis, execute every
> phase below in order, from here. Do not improvise outside it and do not stop
> early.

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
6. **Compute every event independently; never let a known or previously-derived
   fact anchor another.** When you already know (or have just estimated) one
   life-event — for example that the native is divorced, or that some earlier
   event fell in a certain year — you must NOT reason backwards from it to place
   a second event ("the divorce was in 2026, so the marriage must have been
   around 2021"). That is narrative-coherence reasoning, and it silently
   corrupts the chart's independent testimony. Each event is to be timed *only*
   from its own promising significators, its own daśā activations, and its own
   transit triggers, computed from scratch. A coherent life-story may *emerge*
   after all events are independently timed, but it must never be *assumed*
   beforehand and used to bend any single calculation. If a known fact and the
   independent calculation disagree, report the disagreement honestly — do not
   retrofit.

---

## THE CARDINAL RULE (the mistake to never repeat)
An answer from **one or two methods** (e.g. only natal chart + Vimśottari Daśā)
is **INVALID**, however plausible it sounds. A prediction is valid only when
**several INDEPENDENT astrological systems converge** on it. Vimśottari may
*raise* a candidate; **Jaimini + Gochara + Varga + KP + Aṣṭakavarga + Varṣaphal**
must *confirm or kill* it.

Treat **every** timekeeper and every factor — including the **daśā** — as just
**one node among many**, never a privileged judge. The daśā does not *decide* an
event; it is one witness whose vote joins those of the gochara double-transit, the
KP significators, the Lagna/Lagnesh materialization, the BNN and Kakṣyā triggers,
the Saham, the Sudarśana, the Varṣaphal, AND the standing natal pattern (the
benefic/malefic dṛṣṭi on the house, the lord's dignity, the rāja-yogas, Argala,
Aṣṭakavarga). The verdict is the *weighted convergence of all these nodes*. The
engine's `event_evidence` registry holds them as one open list of witnesses
(`register_witness(...)`), the daśā included — so add or re-weight a node as data,
and never let the daśā, or any single node, pronounce the answer alone.

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

### THE ONE FRONT DOOR — `VedicChart`
There is a **single entry point** for every calculation: the `VedicChart` class
in `advance_astrology/vedic/chart.py`. Build the chart once, then pull anything
from that one object — it internally uses all the calculation modules (transits,
vargas, shadbala, kp, jaimini, ashtakavarga, avastha, chalit, yogas, varshaphal,
dashas, sahams). You never call those modules directly.

```python
from advance_astrology import VedicChart
v = VedicChart.create(when=BIRTH_DT, latitude=LAT, longitude=LON, ayanamsa="lahiri")
#   (use ayanamsa="kp" when you specifically need KP positions)

# pull whatever the question needs, e.g.:
v.shadbala(); v.ishta_kashta(); v.avasthas(p); v.functional_nature()
v.argala(h); v.chara_karakas(); v.arudhas(); v.bhrigu_bindu()
v.varga(9); v.varga(10); v.varga(30)            # divisional charts
v.current_dasha("vimshottari", when)              # MD/AD/PD
v.current_dasha("vimshottari", when, levels=5)    # drill to Sukshma/Prana (event-DAY precision)
v.narayana_dasha(); v.chara_dasha(); v.sudasa_dasha()
v.house_lord(h); v.house_lords()                  # Parashari house rulers (one call)
v.sarvashtakavarga(); v.bhinnashtakavarga(p)
v.kp_chain(p); v.kp_significators(); v.bhava_chalit(); v.graha_aspects()
v.varshaphal(YEAR)                               # Tajika annual: Varsha-lagna + Muntha
tr = v.transits()
tr.slow_movers(when); tr.house_windows(p, h, start, end)
tr.conjunction_windows(p, natal_long, start, end)   # BNN degree triggers
tr.kakshya_windows(p, start, end)                   # Kaksya timing windows
tr.transit_aspects(when)                            # gochar drishti: houses each transit ASPECTS
tr.aspects_house(when, h)                           # which transits aspect a given house
tr.double_transit_windows(h, start, end)            # Jupiter+Saturn JOINT activation of a bhava
tr.double_transit_on_sign(lord_sign, start, end)    # ...and of the bhava-LORD's sign (test BOTH)
v.current_chara_dasha(when, levels=2)               # active Jaimini rashi MAHA + ANTARDASHA
v.sahams()                                          # Tajika sensitive points (domain Sahams) + their lords
v.sudarshana(when)                                  # Sudarshana Chakra: Lagna/Moon/Sun tri-wheel (year+month)
```

**Shortcut:** `python -m interpreter.build_matrix --when ... --lat ... --lon ...`
prints most natal + period calculations in one block — a good starting dump;
then fetch the remaining specifics (KP / BNN / Kakṣyā / Varṣaphal) from `VedicChart`.

**MANDATORY mechanical pass — run the domain-general evidence builder FIRST, then
synthesize.** Before reasoning to a date, run
`python -m interpreter.event_evidence --domain <matter|scan> --when ... --lat ...
--lon ... --start ... --end ...` (or append `--events <matter|scan>` to
`build_matrix`). It computes, for the asked life-area and across the FULL span,
the complete triangulation evidence the playbook below demands — Promise & Tempo
(Ṣaḍbala, Iṣṭa/Kaṣṭa, Avasthā, varga-dignity, Argala, SAV), and a per-window
ledger of KP fulfil/negate, the kāraka at sūkṣma, Lagna/Lagnesh materialization,
the Jupiter+Saturn double-transit on the house AND its lord, the BNN and Kakṣyā
triggers, the domain Saham, Sudarśana and Varṣaphal-Muntha — plus the REVERSAL
timed as its own event. This exists because the recurring failure is the AI
*forgetting to compute* one of these and then fixating on a single rule; the
builder guarantees the evidence is complete. Domains are an open `dict`
(`DOMAIN_PROFILES` / `register_domain(...)`) — add a life-area as a data row, do
not hard-code. The builder gives EVIDENCE, never the verdict: you must still read
it multivalently (a node = the event's TYPE, a dark Lagna = lower materialization-
intensity not denial, a converged reversal is not vetoed by one strong benefic),
exactly as Phase 4 directs.

### ⚠️ FILES TO IGNORE FOR THE VERDICT
Do **not** take your conclusion from `interpreter/predict.py` or
`advance_astrology/vedic/triangulate.py`. That is an older *fixed-domain* engine
whose triangulation we have replaced — **YOU do the triangulation** using this
framework. Those files may be read only as a source of raw numbers, never as the
decision-maker.

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

### 4A-bis. First map the FULL candidate set across the span, THEN converge
Before committing to any single date, lay out *every* window across the relevant
span — and, for a retrodiction of something that has already happened, across
the **whole life** — in which the domain's significators are even partially lit.
Build this as an explicit ledger: for each candidate window write down the
Vimśottari MD-AD-PD then running, the Jaimini Chara/Nārāyaṇa rāśi *and* its
antardaśā, the slow-gochara picture, and whether the double-transit condition
(see 4C-6) is satisfied. The reason this step is mandatory is that ordinary daśā
plus single-planet transit will almost always produce several plausible windows,
and stopping at the first one that "looks right" is the single most common cause
of a wrong year. Only once the complete ledger exists do you apply the
discriminators — the double transit on the house *and* its lord, agreement
across multiple daśā systems, the domain Saham and its dispositor, and Sudarśana
corroboration — to collapse the many candidates down to the one window that the
largest number of *independent* systems jointly endorse. The pinpoint is the
product of **elimination across a full map**, never of latching onto the
earliest lit window.

### 4A-ter. Judge the PROMISE and the TEMPO before you time anything
For whatever domain is asked, first establish whether the matter is promised at
all and, if it is, whether the chart inclines it to arrive *early*, *on time*,
*late*, or to be *denied / repeatedly broken* — because this tempo decides which
of the mapped windows is even eligible to carry the event. Read the dignity and
avasthā of the kāraka and of the house-lord, the benefic-versus-malefic pressure
on the matter's house and on its Arudha, and especially the influence of Saturn
and the nodes: Saturn aspecting or occupying the matter's house, or an afflicted
Arudha sitting in a dusthāna, is a classic **delay-and-difficulty** signature,
whereas an unafflicted, well-supported lord and kāraka incline the event early
and smoothly. State this tempo explicitly in your working and let it *weight* the
window-selection — never force an "early" reading onto a chart whose every slow
factor is signalling delay, and never insist on a late date when the promise is
strong and unobstructed.

### 4B. Domain Filtration — Track A vs Track B
For each hot theme run BOTH:
- **Track A (manifestation):** lord strong in D1 *and* its varga? Iṣṭa high?
  benefic occupants/aspects? Argala effective? SAV high?
- **Track B (cancellation):** high Kaṣṭa? occupant/lord in Mṛta/Khala/Dukhita/
  Vikala mood? Virodhārgala dominant? Bhāva-Chalit moves the result out? malefic
  dṛṣṭi? movable (Cara) cusp = sudden/disruptive?
State the **texture**: clean manifestation / friction / **fixed-then-cancelled** /
blocked — with evidence.

⚠️ **A transition through the 6/8/12-FROM-the-matter's-house is NOT automatically
a loss — disambiguate a positive CHANGE/UPGRADE from a true LOSS/BREAK.** The
dusthāna-from-the-house (the houses that *end the present instance* of the matter)
lights up for BOTH outcomes, because leaving a thing and bettering a thing share
the same "ending of the current state" signature: a job-change to a superior post,
a move to a better home, or a remarriage all activate exactly the houses a job-
loss, an eviction or a divorce would. The decider is whether the matter's
**fulfilment signature co-occurs in the same window** — read from the *timing*
lords (the antara/pratyantara/sūkṣma), NOT from a standing mahādaśā that may be the
matter's own lord and therefore permanently lit. When the rupture houses AND the
fulfilment houses are *both* lit, the event is a **CHANGE/UPGRADE** (the old ended
and something better was gained); when the rupture houses are lit while fulfilment
is **absent** and the Lagna is dark under malefics/nodes, it is a genuine
**LOSS/BREAK**. Never report the dusthāna activation as a loss without first
checking for this co-occurrence — calling a promotion-by-job-change a "career
loss," or a divorce-and-remarriage a permanent "end of marriage," is the same
single-signature error in another costume. Time the reversal as its own event,
but label its *nature* by this fulfilment test.
Crucially, upgrade-vs-loss is a **multi-nodal pattern, not a daśā verdict**: weigh
the matter's whole STANDING natal testimony together — every benefic and malefic
*dṛṣṭi* on the house (e.g. an exalted Jupiter aspecting the 10th), the lord's
dignity and strength, any rāja/dhana yoga on the house or its lord, the Argala and
the SAV — as a balance of independent witnesses. A house that is natally *blessed*
(benefics aspecting, a dignified lord, a rāja-yoga) rarely *breaks* — it upgrades
through the same dusthāna window — whereas an afflicted one can truly break. Read
the convergence of all these nodes, never one. (The engine's `event_evidence`
witness-registry computes this standing balance for you; add a node as one
`register_witness(...)` entry rather than hard-coding.)

### 4C. Multi-Paddhati Confirmation & Timing — ALL SIX ARE MANDATORY
1. **Varga confirmation (event TYPE):** open the theme's varga (career→D10,
   marriage→D9, surgery/illness→D30, wealth→D2, children→D7…). Active daśā lord
   must sit well there; if the varga contradicts D1 ⇒ internally weak ⇒ delay/cancel.
2. **KP sub-lord verdict (the decider):** read the *houses each period lord
   itself signifies* (`KPSignificators.planet_signifies(p)`) **and the matter's
   cusp sub-lord** (`kp_chain(cusp).sub_lord`). Fulfilment houses ⇒ it happens;
   negation houses ⇒ it breaks; **BOTH ⇒ fixed-then-cancelled.**
   ⚠️ **Do NOT** substitute a period lord's *sub-lord's* houses for the lord's
   own significations — that conflates two different KP objects and will mislead
   the verdict. A matter is *promised* when its cusp sub-lord signifies the
   matter's houses (e.g. 7th-cusp sub-lord → 2/7/11 ⇒ marriage promised); it is
   *timed* when the running D-B-A lords also signify those houses.
   ⚠️ Equally important is what you must NOT do with KP: never treat a running
   period-lord that merely *fails to signify* the matter's houses as though it
   *negates* them. A daśā level — especially an antara or pratyantara — that is
   silent on the matter (signifying neither its fulfilment houses nor its
   negation houses) is **transparent, not obstructive**, and must be allowed to
   pass the matter through. The promise is owned by the cusp sub-lord; the timing
   is supplied by whichever level of the running chain — mahādaśā, antara,
   pratyantara, **or the sūkṣma/prāṇa** — does signify the houses, while the other
   levels need only refrain from active negation. It is therefore a method error
   to hard-gate an entire period out of contention just because its
   antara/pratyantara lord is mute on the matter; if the mahādaśā lord or the
   sūkṣma carries the houses and nothing in the chain signifies the negation
   houses, the period stays fully eligible to deliver the event. Always drop to
   the sūkṣma before rejecting a candidate date.
3. **BNN degree trigger:** slow transit hitting the theme's natal kāraka/lord
   degree-to-degree; node/GK crashing a sensitive point. **Check the kāraka's
   _dṛṣṭi_, not only its sign-ingress** — e.g. Jupiter need not *enter* the 7th
   to fire marriage; from the 1st it already *aspects* the 7th. Also test the
   slow/dispositor benefics transiting **2nd-from-Upapada** (the Jaimini
   marriage house) and the kāraka conjoining the relevant chara-kāraka (DK for
   spouse) by gochara. A degree-perfect hit may mark a *later* peak, not the
   event day — rank it against the daśā-sūkṣma + Kakṣyā evidence, never above it.
4. **Kakṣyā narrowing:** transit delivers only in a bindu-bearing 3°45′ Kakṣyā ⇒
   narrows timing to a 4–5 day window. A Kakṣyā window already open *around the
   asked date* outranks a tidier window months away — don't chase the prettier
   trigger.
5. **Daśā sūkṣma drill (event-DAY precision):** for a dated event, open
   Vimśottari to the **4th–5th level (Sūkṣma/Prāṇa)**, not just Pratyantar. The
   PD may look inert (e.g. a Rahu PD) while a benefic Sūkṣma (e.g. Jupiter)
   sitting exactly on the date is the real micro-trigger. Stopping at PD is a
   timing error.
6. **The Double-Transit discriminator (Jupiter + Saturn) — the decisive
   pinpoint when several windows compete.** Because ordinary daśā plus
   single-planet transit will almost always throw up *multiple* plausible
   windows across a life, you need a stronger filter to choose between them, and
   the classical one is the *double transit* of the two slow movers: an event of
   a given domain ripens only when **both Jupiter and Saturn simultaneously
   influence the matter's house AND the lord of that house** — where "influence"
   means either bodily occupation *or* graha-dṛṣṭi, and where you must test **the
   house *and* its dispositor separately**, because very often it is the *lord's*
   sign that receives the clean joint hit while the house itself is touched by
   only one of the two. Concretely, pull `tr.double_transit_windows(house, …)`
   for the matter's bhāva and `tr.double_transit_on_sign(lord_sign, …)` for the
   sign holding that bhāva's lord (and, where it matters, for the kāraka's sign
   too), and treat a window in which *both* lights converge on the
   house-or-its-lord as the true trigger-band, ranking it above any window that
   rests on a single slow transit. Apply this to whatever domain is asked — the
   10th and its lord for career, the 5th and its lord (with Jupiter the
   putra-kāraka) for children, the 2nd/11th and their lords for wealth, the
   6th/8th and their lords for illness — in exactly the way you would use the 7th
   and Venus for marriage.
   Run this double transit on the matter's **lord's sign across the ENTIRE
   relevant span** — the whole forward life for a future event and the whole past
   for a retrodiction — with **no premature cut-off date**, because the clean
   joint Jupiter–Saturn hit on the **lord** very often lands in a different,
   frequently later year than the hit on the **house** itself, and a scan that
   stops early, or that only re-checks the house without re-checking the lord's
   sign over the full remaining span, will silently hide the true trigger band.
   Count the joint influence through **every** form of contact — bodily
   occupation as well as **all** the special dṛṣṭis (Jupiter's 5th/7th/9th and
   Saturn's 3rd/7th/10th), never the 7th aspect alone — so that, for instance, a
   Saturn casting only its 3rd or 10th glance onto the lord's sign while Jupiter
   occupies it still counts as a full double transit.

> **IMPORTANT — these six rules are DOMAIN-GENERAL, not marriage-only.** The
> marriage signatures used above (the 7th cusp sub-lord, 2nd-from-Upapada, and
> the Darakāraka) are merely the *worked illustration* of a principle that you
> must apply to whatever life-area the question is about. The principle, stated
> in full, is this: when you confirm and time any event, do not look only at the
> Parāśarī house and its lord — you must ALSO read the same matter through its
> **Jaimini / Arudha significator and its chara-kāraka**, and treat a transit as
> a trigger when a slow benefic or the matter's kāraka activates *that* point too
> (by occupation, by aspect/dṛṣṭi, or by conjunction with the kāraka). Carry
> this mapping across to every domain, exactly as you would for marriage:
> - **Marriage / spouse** → 7th house + 7th-cusp sub-lord + **2nd-from-Upapada
>   (UL)** + **Darakāraka (DK)**; benefic transit *aspecting* (not only entering)
>   the 7th or 2nd-from-UL is a trigger.
> - **Career / profession / job-change** → 10th house + 10th-cusp sub-lord +
>   **Arudha of the 10th (A10)** + **Amātyakāraka (AmK)**; watch slow movers
>   aspecting the 10th / A10 and the AmK by gochara.
> - **Children / progeny** → 5th house + 5th-cusp sub-lord + **Arudha of the 5th
>   (A5)** + **Putrakāraka (PK)**, cross-checked in the Saptāṃśa (D7).
> - **Wealth / gains** → 2nd & 11th + their cusp sub-lords + **Arudha of the 2nd
>   (A2) / Indu Lagna**, in the Hora (D2).
> - **Mother** → 4th + A4 + **Mātṛkāraka (MK)**; **Father** → 9th + **Pitṛkāraka
>   (PiK)**; **Illness / surgery / longevity** → 6th & 8th + their cusp sub-lords
>   + **Gnatikāraka (GK)** / **Atmakāraka (AK)**, in the Triṃśāṃśa (D30).
>
> So for ANY question: pick the matter's house, its cusp sub-lord, its Arudha,
> and its chara-kāraka FIRST, and only then judge whether the running daśā and
> the gochara (by occupation, aspect, AND conjunction with the kāraka) are
> lighting that whole bundle up. Reading the Parāśarī house alone — for marriage
> OR for anything else — is the same mistake in a different costume.

> **Distinguish the sub-events *within* a single domain, because they are timed
> by different signatures and must not be collapsed into one date.** A life-area
> is rarely one undifferentiated event. Marriage, for instance, has a
> *romance/courtship* dimension (read from the 5th house, Venus, Rahu and the
> 7th) that is genuinely distinct from the *formal/legal union* dimension (read
> from the 7th together with the Upapada, the 2nd, the Darākāraka and Jupiter's
> sanction) — the relationship may begin in one window while the wedding is
> solemnised in another, and calling one of them by the other's name is a real
> error even when the *year* is otherwise right. The same layering applies
> everywhere: a career carries separate *job* versus *business* versus
> *promotion* sub-events; progeny separates *conception* from *birth*; wealth
> separates *steady earning* from *inheritance* from *sudden windfall*. So decide
> first which sub-event the question is actually about, time each sub-dimension
> on its own significators, and report them separately rather than fusing two
> distinct moments into a single claim.

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
- [ ] **KP sub-lord verdict** (planet's *own* significations + cusp sub-lord — not the sub-lord's houses)
- [ ] **BNN trigger** (incl. kāraka *dṛṣṭi* + 2nd-from-Upapada) · [ ] **Kakṣyā narrowing**
- [ ] **Daśā drilled to Sūkṣma/Prāṇa for a dated event** (not just Pratyantar)
- [ ] **Full life-span candidate map built, THEN converged** (not first-plausible)
- [ ] **Double-Transit (Jupiter+Saturn) on the matter's house *and* its lord/kāraka**
- [ ] **Lord's-sign double-transit scanned across the FULL span** (no early cut-off; Saturn 3rd/10th + Jupiter 5th/9th counted, not occupation/7th-aspect alone)
- [ ] **KP gate not over-applied** — a non-signifying AD/PD treated as neutral (not a block); date drilled to sūkṣma before any rejection
- [ ] **Chara/Nārāyaṇa antardaśā** (rāśi sub-period), not just the rāśi mahādaśā
- [ ] **Domain Saham + its dispositor** (Vivāha/Karma/Putra/Roga/Artha… as the theme needs)
- [ ] **Sudarśana Chakra** corroboration (≥2 of the three wheels agreeing)
- [ ] **Promise-and-tempo stated** (early / on-time / late / denied) · **sub-event identified**
- [ ] **Independent computation** — no known or prior-derived event used to anchor another
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

## COMMON TIMING-MISSES (method lessons — not chart templates)
Theme can be right while the *date* is wrong. The recurring causes:
1. **Stopping the daśā at Pratyantar.** Event-day lives in the Sūkṣma/Prāṇa
   level. An "inert" PD often hides the benefic Sūkṣma that actually fires.
2. **Reading transit ingress instead of dṛṣṭi.** A kāraka aspecting the target
   house (e.g. Jupiter from the 1st onto the 7th) fires *before* it bodily
   enters a "textbook" house months later.
3. **Ignoring the Jaimini overlay in gochara.** Kārakas / DK transiting
   **2nd-from-Upapada** is a precise marriage trigger that pure Parāśarī transit
   misses.
4. **Letting a degree-perfect BNN outrank an active Kakṣyā at the asked date.**
   A tidy degree hit can be a *later* peak; the window already open around the
   event usually is the event. Rank Sūkṣma + Kakṣyā + dṛṣṭi above a distant
   degree hit.
5. **A misread KP object** (a lord's sub-lord's houses ≠ the lord's own
   significations) can flip the whole theme. Verify with `planet_signifies`.
6. **Trusting a single slow-transit instead of the double transit, and stopping
   at the first lit window.** A lone Jupiter (or a lone Saturn) over the relevant
   house feels convincing but routinely misfires; the event waits for *both*
   slow movers to converge on the house-or-its-lord. Equally, because daśā throws
   up several candidate windows, picking the earliest plausible one — instead of
   mapping them all and letting the double transit, the rāśi antardaśā, the
   domain Saham and Sudarśana jointly elect the winner — is a recurring source of
   a wrong year.
7. **Anchoring one event on another (hindsight-by-narrative).** Reasoning "the
   later event was in year X, so the earlier one must be around Y" corrupts the
   independent reading. Time each event from its own significators; let the
   life-story emerge, never assume it.
8. **Hard-gating a period out because a sub-period lord is silent.** Demanding
   that the mahādaśā AND the antara AND the pratyantara all signify the matter's
   houses at once is too rigid and routinely throws away the real window. Events
   frequently fire on the mahādaśā (or the cusp sub-lord) plus a benefic
   **sūkṣma**, while the antara/pratyantara are merely neutral. A non-signifying
   period-lord is transparent, not a veto — only an *actively-negating* one
   blocks. Soften the gate, and drill to sūkṣma before rejecting any date.
9. **Truncating the lord's-sign double-transit scan, or testing only the house.**
   The joint Jupiter–Saturn activation of the matter's LORD commonly falls in a
   later year than its activation of the HOUSE, so a scan with an early end-date
   — or one that re-checks the house but forgets to re-scan the lord's sign over
   the full remaining span — will miss the actual trigger. Re-scan the lord's
   sign to the very end of the span, and count Saturn's 3rd/10th and Jupiter's
   5th/9th glances, not occupation or the 7th aspect alone.

## FORBIDDEN BEHAVIOURS
- Answering after only natal + Vimśottari (the cardinal mistake).
- Recomputing or guessing any number instead of asking the Engine.
- Vague Barnum statements that fit any life.
- Forcing the chart to match a known event (no calibration / no hindsight).
- Treating the worked example as a template to fit the native into.
- Anchoring one event's timing on another known/derived event instead of
  computing it independently.
- Committing to a date on a single slow-transit, or on the first lit window,
  without the Jupiter+Saturn double transit and the full-span candidate map.
- Rejecting a daśā period merely because its antara/pratyantara lord does not
  signify the matter's houses (a silent sub-lord is neutral, not a negation), or
  committing to a date without first drilling the running chain to the sūkṣma.
- Truncating the matter's-lord double-transit scan before the end of the span, or
  testing the double transit on the house alone and not also on the lord's sign
  with every form of dṛṣṭi (Saturn's 3rd/10th and Jupiter's 5th/9th included).
