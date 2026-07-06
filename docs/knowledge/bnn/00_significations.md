# BNN significations — the kārakatwa dictionary (pass 2)

Source: **`docs/bhrigu-nandi-nadi.pdf`** — *Bhrigu Nandi Nadi*, R.G. Rao.
This is the **interpretive reference** (the AI narrator's judgment layer). The
*calculable* half of it — "which planet is the kāraka of which matter" — is
already **DATA in the engine** (`interpreter/significators.py` THEME_LEXICON +
`event_evidence.DOMAIN_PROFILES`, each carrying `natural_karaka`); this file
does **not** re-implement that, it explains and sources it so a reading can be
narrated. Nothing here is a fitted/calibrated rule — these are the book's own
kārakatwas.

> R.G. Rao's own instruction for reading ANY chart (Preface): *"Take the
> causative i.e. **kāraka planet** of the particular aspect you want to study,
> consider the **adjacent houses** of that planet and the **seventh house
> therefrom**."* And: *"mostly it is the **'Kārakatwa'** that holds the key for
> the reading."* BNN is kāraka-first, not house-lord-first — the graha carries
> the matter, wherever it sits.

---

## 1. Graha kārakatwas (the core dictionary)

Each row: BNN significations · the book's usage · where the engine already
encodes the *calculable* part.

### Jupiter (Guru) — the **Jīva Kāraka** and the universal TIMER
- **Signifies:** the **native himself / the soul (jīva)**; wisdom, dharma,
  the preceptor; **children/progeny** (esp. by contact with Venus); expansion,
  fortune, higher knowledge.
- **Timer role (the heart of BNN):** Jupiter is the **year-hand**. His transit
  *contacts* (conjunction, and the trine/aspect) over the natal planets mark the
  **ages** at which each matter fructifies — "he takes up the regular transits
  of Jupiter from birth and indicates the ages at which the native suffers
  disease, obtains happiness, marriage, birth of children" (Chart I). *"Work
  done is the result of Saturn, the **enjoyment of the result is ascribed to
  Jupiter who represents the soul.**"*
- **Book anchor:** *"'Jīva Kāraka' Jupiter is in Aquarius, Saturn Kāma-kāraka is
  in Pisces."* (explicit label). *"Jupiter represents the native, and in his
  transits he crosses …"* (Chart I).
- **Engine:** `nadi_timing` uses Guru-jīva as the primary year-marker; children
  domain `natural_karaka=Jupiter`; inheritance→Jupiter.

### Saturn (Śani) — **profession / karma**, and the **Kāma Kāraka**
- **Signifies:** **profession, work, service, karma, livelihood**; delay,
  labour, longevity's discipline, the "done work." Also labelled **Kāma-kāraka**
  (desire/karma) alongside Jupiter the Jīva-kāraka.
- **Book anchor:** repeatedly *"Saturn, the significator of profession …"*
  (many charts); *"work done is the result of Saturn."* Livelihood is usually
  judged from **Saturn's movements** ("the question of livelihood is considered
  from Saturn's movements in most of the cases").
- **Engine:** career/profession & debt domains `natural_karaka=Saturn`;
  Saturn is the rupture/separator kāraka in `nadi_rupture`.

### Sun (Sūrya) — **father**, authority, soul-status, fame
- **Signifies:** **father**; government/authority, high position, status,
  vitality. (Father attaining Moksha, etc., read from the Sun.)
- **Book anchor:** *"The significator of father, the Sun …"* (multiple charts).
- **Engine:** fame domain `natural_karaka=Sun`; father read from Sun/9th.

### Moon (Chandra) — **mother**, the **mind**, the day-hand
- **Signifies:** **mother**; the **mind / mental faculty**; the public, fluids,
  comfort. In timing, the Moon is the **fast day-hand** (fine trigger) once
  Jupiter has set the year.
- **Book anchor:** *"the Moon, the significator for mother …"*, *"the Moon, the
  significator of mental faculty …"*
- **Engine:** used as day-granular trigger (`_w`/Moon-hand in day_convergence).

### Mars (Kuja) — **brothers**; the **husband** (female chart); land, energy
- **Signifies:** **brothers/siblings (co-borns)**; **engineering, machinery,
  metals**; **wounds, blood, surgery, accidents**; courage; **immovable
  property / land**; and — in a **female** chart — the **husband** (descriptor).
- **Book anchor:** *"The significator of brothers Mars …"*; *"the significator
  of husband Mars is aspected by …"* (a lady's chart); *"Mars who stands for
  Engineering and Machinery"*; *"Mars in Leo stands for bravery."*
- **Engine:** property→Mars, litigation/surgery→Mars; **female-husband kāraka**
  witness (`_w_female_husband_karaka`); marriage `nadi_karaka` = Mars for ♀.

### Mercury (Budha) — **education, intellect, speech, trade**
- **Signifies:** **education/learning**; intelligence, analysis, speech,
  writing; **arts** (with Venus); commerce/trade/business.
- **Book anchor:** *"Mercury the Kāraka of education …"*, *"Mercury, significator
  of intellect …"*; arts when *"conjunct Mercury in the house of Venus who
  stands for Arts."*
- **Engine:** education `natural_karaka=Mercury`; business→Mercury.

### Venus (Śukra) — **marriage/wife**, the **seed**, luxury, vehicles, arts
- **Signifies:** **spouse & marriage (kalatra)** — the **event-kāraka of
  marriage for BOTH sexes**; the **seed** (progeny cause with Jupiter); love,
  luxury, wealth-comfort, vehicles, arts, refinement.
- **Book anchor:** *"Venus represents the seed"*; marriage read from Venus's
  house (Libra) and Jupiter's contact with Venus (*"Jupiter contacts Venus …
  marriage is likely to take place"*); wife = Venus throughout.
- **Engine:** marriage/romance/vehicle `natural_karaka=Venus`;
  `nadi_timing_karaka` = **Venus for the whole marriage class** regardless of
  gender (the event-kāraka), while Mars stays the ♀ husband-descriptor.

### Rahu — the **mouth**, foreign, sudden/māyā, gas; a **separator**
- **Signifies:** foreign lands/things, the unconventional, sudden rise/fall,
  intoxication, illusion; **windy/gas ailments**; obstruction. A **separative**
  node (breaks contacts).
- **Book anchor:** *"The mouth is represented by Rahu"*; *"Rahu causes gas
  trouble"*; Rahu (always retrograde) times troubles on Jupiter's contact.
- **Engine:** foreign `natural_karaka=Rahu`; Rāhu/Ketu drive `nadi_rupture`.

### Ketu — the **tail**, **Moksha/spirituality**, detachment; a **separator**
- **Signifies:** **liberation/Moksha, spirituality, detachment**, the mystic;
  the "tail," sudden endings. **Separative** node.
- **Book anchor:** *"Moksha (Jupiter–Ketu combination)"*; *"Ketu representing
  tail"*; the planet granting knowledge of salvation.
- **Engine:** spirituality `natural_karaka=Ketu`.

---

## 2. The reading procedure BNN attaches to a kāraka

For any matter, the book reads the **kāraka planet** as the subject and then:
1. the **planets/signs adjacent to** the kāraka (conjunction + the flanking
   signs) — the *company* colours the outcome;
2. the **7th house/sign from the kāraka** — the *facing* influence (this is
   **dṛṣṭi**, a distinct mechanism from the trine/golden relation);
3. **Jupiter's transit contacts** over the kāraka and its company — the **age**
   of fructification;
4. **exchange of signs** (parivartana) between two lords ties their matters
   together (e.g. Mercury⇄Venus → education+arts+marriage linked).

Golden (result-giving) relations in BNN = **conjunction and the 1/5/9 trine**;
the **7th is aspect (dṛṣṭi)** and read separately. (Detailed in
`01_timing_method.md`.)

---

## 3. Rāśi notes (secondary in BNN — contextual, not a fixed table)

BNN is kāraka-first, so signs are read for **flavour** where the text calls it
out, not from a rigid dictionary. Examples the book actually uses:
- **Virgo** — vegetation, crops, agriculture (a kāraka here → farming/land
  produce); also Mercury's exaltation (education takes an "upward turn").
- **Leo** — bravery ("Mars in Leo stands for bravery"); royal, authority.
- **Libra** — Venus's own house → marriage/arts negotiations activate when a
  timer enters it.
- **Capricorn/Aquarius** — Saturn's houses → karma/profession seasons.

Treat any other sign meaning as **AI judgment from the wider corpus** (BPHS
rāśi-svabhāva), not from BNN — BNN itself does not tabulate all twelve.

---

## Division of labour (recorded, per CLAUDE.md)
- **DATA already in engine:** every planet→matter kāraka above is encoded as a
  domain's `natural_karaka` (THEME_LEXICON / DOMAIN_PROFILES). No new code from
  this pass — the dictionary was already consistent with BNN.
- **JUDGMENT (this doc):** the *meaning* behind each kāraka, the reading
  procedure, and the rāśi-flavour notes — reference for the AI narrator.
- **No new node proposed** from pass 2 (significations are data/judgment, not a
  new mechanical timing check). If a later per-domain pass surfaces a genuinely
  missing *calculable* check, it will be proposed for approval with its source
  (per CLAUDE.md), never added silently or to fit a date.
