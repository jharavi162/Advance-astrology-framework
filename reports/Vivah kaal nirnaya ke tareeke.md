# Daśā, transits and sāham pin down marriage dates

Almost every marriage-timing method in Indian astrology follows the same three steps. First, a **daśā clock** (Vimśottari, Chara/Nārāyaṇa, Pātyāṁśa) opens a period of a few years. Then a **transit trigger** (Jupiter, Venus or the 7th lord moving through a sign tied to the 7th lord, lagna lord, Venus or Upapada) narrows it to a year or a few months. Finally, a **fast-mover check** (the Sun's sign/star/sub in KP, the Moon, or muhūrta rules) brings it down to a day. Nearly all of the inputs can be computed from a sidereal chart plus an ephemeris. The weak spots are a few undefined conventions ("stronger", "benefic house", which Chara daśā variant, the time of judgment in KP), not the arithmetic. The oldest written form of "daśā + Jupiter transit" is **Phaladeepika X.14**. Saturn's half of the popular **double transit appears in none of the classical verses read** and is a 20th-century practitioner rule. A clean classical **second-marriage timing algorithm does not exist**: the texts give the promise of more than one marriage, spouse-loss windows and fixed-age triplets, and the timing itself reuses first-marriage machinery after the break. Two concrete repo issues came out of the research. `advance_astrology/vedic/sahams.py` reverses Vivāha Sāham at night, but Tājika Nīlakaṇṭhī says "सततं" (always the same). The repo's `punarvivaha_saham` has no classical source. Both changes need approval under CLAUDE.md before anyone touches them. No rule here has been applied to any chart.

A note on sources. The research notes worked from OCR copies of archive.org editions: Santhanam's BPHS, Sastri's Phaladeepika (1950), Sastri's Jataka Parijata Vol. II, Mahidhar Sharma's Sarvartha Chintamani, B.S. Rao's Jaimini Sūtras, Sitaram Jha's Tājika Nīlakaṇṭhī, B.V. Raman's *Varshaphal* and the KP Readers. Verse and page numbers below follow those editions. Other editions can number them differently. Saravali could not be verified at all, because no usable OCR was reachable.

## Parāśarī texts give a candidate daśā set, an inside-the-daśā rule and sign-trine transits

**The daśā lords.** Phaladeepika X.13 is the base rule: "The acquisition of a wife may happen during the Dasa period of the planet (1) posited in the 7th house, (2) aspecting the 7th house or (3) owning the 7th house". The same verse adds a transit clause: marriage also comes when the lagna lord transits the 7th sign ([PD 1950, Adh. X sl. 13, p.109](https://archive.org/details/Phaladeepika2ndEd.1950ByVSubrahmanyaSastri)).

Jataka Parijata XIV.29 gives a **ranked fallback list**, where each step applies only if the previous planet is weak:
1. The 7th lord when it is joined with Venus.
2. The dispositor of the 2nd lord.
3. The 10th and 4th lords. The OCR is partly garbled here.
4. Planets conjoined with the 7th lord or sitting in the 7th.

([JP Vol II, Adh. XIV sl. 29, p.860-861](https://archive.org/details/JatakaParijataVolIIOfIIByVSubrahmanyaSastri))

Other texts widen the set:
- BPHS ch. 32 makes the **Dārakāraka** the marriage significator, with Venus as fallback when two planets tie in degree ([BPHS Santhanam ch. 32](https://archive.org/details/brihatparasarahorashastrabyr.santhanam)).
- Uttara Kalamrita Ch. VI gives marriage in the **mutual daśā/bhukti of Jupiter and Venus** when both are strong and well placed. When they are 6/8 or 2/12 from each other, the same periods give separation ([UK, P.S. Sastri, p.156-157](https://archive.org/details/uttkalamrita-kalidas-ps-sastri)).
- Sarvartha Chintamani says to take the strongest of Moon, Mercury, Venus and Jupiter as kalatra-kāraka ([SC saptama-bhāva sl. 20](https://archive.org/details/sarvartha-chintamani-mahidhar-sharma_202210)).
- Phaladeepika XIX.26 and XX.8 name the Venus mahādaśā and the 7th-lord daśā directly ([PD Adh. XIX-XX](https://archive.org/details/Phaladeepika2ndEd.1950ByVSubrahmanyaSastri)).

Put together, this candidate set can be computed fully deterministically. Only its **ordering** needs a strength convention (ṣaḍbala or another), because the texts say "stronger" without naming a metric.

**Where inside the daśā.** Jataka Parijata XIV.30 is the most engine-friendly verse in the whole corpus. It reads the planet's nature together with the nature of the house it occupies:

| Planet | House it occupies | Marriage comes |
|---|---|---|
| Benefic | Benefic house | At the start of its daśā |
| Benefic | Malefic house | In the middle |
| Malefic | Malefic house | At the end |
| Benefic, also conjoined with a benefic | Benefic house | Good throughout the daśā |

([JP XIV.30, p.861](https://archive.org/details/JatakaParijataVolIIOfIIByVSubrahmanyaSastri)). The only convention to fix is what "benefic house" means. Most likely it is a sign owned by a natural benefic.

**Antardaśā verses.** BPHS adds about fifteen of them that name marriage, from ch. 52 to 60. Examples: Venus AD in Saturn MD if Venus is in a kendra, trikoṇa or the 11th; Saturn AD in Rāhu MD if Saturn is in a kendra or trikoṇa, exalted or in its own sign; Moon AD in Mercury MD with Jupiter's aspect ([BPHS ch. 52-60](https://archive.org/details/brihatparasarahorashastrabyr.santhanam)). The conditions are mechanical. The outcome, though, is generic ("auspicious functions like marriage"), so treat these as supporting evidence, not marriage-specific triggers.

**Sign daśās.** BPHS ch. 46 sl. 143-144 gives marriage in the **Chakra daśā of the 7th sign**, full when the sign is benefic. JP XVII.64-65 says the same. BPHS ch. 49 gives marriage in the rāśi daśā of the sign owned or occupied by Venus ([BPHS ch. 46, 49](https://archive.org/details/brihatparasarahorashastrabyr.santhanam)).

**Transit triggers.** In the classical texts these are always **whole-sign, no orb**:
- **PD X.12:** Venus or the 7th lord transits a sign trine to the rāśi or navāṁśa of the lagna lord.
- **PD X.14:** during the daśā of the stronger of (the D1/D9 dispositors of the 7th lord) versus (Venus, Moon), Jupiter transits a sign trine to the rāśi or navāṁśa of the 7th lord ([PD X.12-14](https://archive.org/details/Phaladeepika2ndEd.1950ByVSubrahmanyaSastri)).
- **JP XIV.31:** the Moon and Jupiter reach the 2nd from the navāṁśa lord of the lagna lord; or Jupiter reaches the sign of the 7th lord or Venus; or the Moon and Jupiter stand in mutual kendras.
- **JP XIV.27:** add the "figures" of the lagna lord and the 7th lord, and marriage comes when Jupiter reaches the resulting sign. Most likely this means a longitude sum mod 360°, but the OCR does not say so, so it stays a convention.
- **JP XIV.32:** marriage in the year of age **8 + the sign number of the 7th house** ([JP XIV.27-32, p.859-862](https://archive.org/details/JatakaParijataVolIIOfIIByVSubrahmanyaSastri)).

**Negation gates.** Phaladeepika supplies two. A favourable transit is void when the planet is debilitated, in an enemy sign or eclipsed (PD XXVI.32). A weak, combust or debilitated daśā lord "destroys" the bhāva during its transit (PD XX.35) ([PD](https://archive.org/details/Phaladeepika2ndEd.1950ByVSubrahmanyaSastri)).

**BPHS ch. 18 sl. 22-34 age yogas.** Thirteen pure-geometry yogas give ages: 5/9, 7/11, 10/16, 11, 12/19, 18, 15, 13, 22/27, 23/26, 25/33, 31/33 and 27/30. Sl. 40-41 adds a **three-marriage triplet of 10, 22 and 33** ([BPHS ch. 18, pp.124-128](https://archive.org/details/brihatparasarahorashastrabyr.santhanam)). Santhanam warns that these "will simply help in knowing of early or belated marriages". So the right engine output is an **early/late classifier plus a year band**, not a literal age. "Nth year" should be read as completed age N−1 to N. Sarvartha Chintamani sl. 59-61 adds early-marriage yogas. Its sl. 65-66 is contested: the Sanskrit "dūre vivāhāt" points to delay, but the Hindi ṭīkā reads "fortune rises long after marriage" ([SC sl. 59-66](https://archive.org/details/sarvartha-chintamani-mahidhar-sharma_202210)).

## Jaimini supplies the significators, but its sūtras never name the marriage daśā sign

B.S. Rao's edition of the sūtras was searched thoroughly. It defines the **Upapada** (UL) as "Upapadam padam pitranucharat", the ārūḍha of the 12th. There are two readings of its exception, and they can give different signs. The **2nd from UL** carries the spouse-loss and plurality tests:
- Malefic aspect or yoga on it means the wife dies or he takes pravrajyā (Su. 2), and benefic aspect cancels this (Su. 4).
- Debility there means death of the wife "in that evil period" (Su. 5).
- An exalted planet or navāṁśa there (Su. 6), or the 2nd from UL falling in yugma/Mithuna (Su. 7), means many wives.
- The Ātmakāraka or the sign's own lord there means no wife in later life (Su. 8).

([B.S. Rao, Jaiminisutras 1955, pp.108-116](https://archive.org/details/Jaiminisutras1955EditionByBSRao)). The **only daśā rule in the sūtras** concerns the spouse: "Gurusule kalatrasya", meaning the daśās of the 1st, 5th and 9th signs from Jupiter cause the wife's death (Su. 10-11, pp.159-160). For a second marriage this marks when the first bond ends, not when the next one begins.

**"Which sign's daśā gives marriage" is practitioner doctrine.** The sūtras do not contain it.
- Sanjay Rath: "Predict marriage in the periods of dasa sign of Ketu or Venus" (rule 35). "If the Darakaraka aspects the Dasa Rasi, marriage can be expected" (rule 56). For D9 Nārāyaṇa daśā, start from the 9th of D9 and "marry when the Antardasa has some aspect on the Upapada in the Navamsa". For transit: Jupiter strong in, or aspecting, the 2nd from UL, or on the D9 sign of the 7th lord ([Rath, *Narayana Dasa*](https://scienceoflight.net/wp-content/uploads/extra/Narayana%20Dasa%20by%20Sanjay%20Rath.pdf)).
- Iranganti Rangacharya: an 11-clue list for the MD/AD sign (7th from lagna or AL with benefics or Ketu, the DK's sign in dignity, the UL or its 2nd with benefics or Ketu, the A7, Venus's sign, the 7th from the AK). He also warns that the Chara daśā variant changes which sign carries the marriage: Neelakantha's for a cardinal lagna, Raghava Bhatta/Nrisimha Suri's for ties and female charts ([Saptarishis, Rangacharya](https://saptarishisshop.com/timing-marriage-according-to-jaimini-by-iranganti-rangacharya/)).
- Gautam Dave: Saturn, Mars and Jupiter transits on the UL, AL and 7th, plus DK argala on the Chara MD/AD signs. He claims over 90% success without any blind test ([Saptarishis, Dave](https://saptarishisshop.com/timing-of-marriage-by-transits-and-jaimini-astrology-by-gautam-dave/)).

K.N. Rao's own wording could not be obtained.

**Engine translation.** All of these are deterministic sign and rāśi-dṛṣṭi relations. The engine can emit them as per-daśā-sign flags with no score: contains or is aspected by the DK, is the UL or its 2nd, is the A7, holds Venus or Ketu, is the 7th from the AL or AK. The engine must **name its Chara daśā variant** and its UL convention, because those choices change the output.

## Tājika fixes the marriage year through Vivāha Sāham activation and varṣa 7th-bhāva tests

**The formula.** Tājika Nīlakaṇṭhī, Sāhama verse 17, ends with "सततं विशोध्य मन्दं सितात् स्यात्तु विवाहसद्म". Sitaram Jha's bhāṣya reads it as "always subtract Saturn from Venus (and add the lagna)". So **Vivāha Sāham = Venus − Saturn + varṣa Lagna**, the same by day and night. The general proviso in TN verse 5 also applies: add 30° (saika) when the lagna does not fall between the subtrahend and the minuend ([TN, Jha comm.](https://archive.org/details/nxfu-tajika-neelakanthi-gudhartha-prakashika-commentary)). B.V. Raman agrees: "VIVAHA SAHAM — Day or Night — Sukra's long — Sani's long" ([Raman, *Varshaphal* §64, §73](https://archive.org/details/VarshaphalOrTheHinduProgressedHoroscope)). TN's list of 50 sāhams includes Vivāha, Parastrī and Kanyā, but **has no Punarvivāha**. The nearest related sāham is Anyadāra/Paradāra = Venus − Sun + Asc, always the same. TN treats it as extra-marital, not as a remarriage sāham.

**Activation in the year (TN Sāhama 39).**
- The sāham is joined or aspected by its lord and benefics, with Ithasāla: marriage comes.
- With mixed planets: marriage comes with difficulty.
- With malefics or the **8th lord**: no marriage.

**The varṣa 7th-bhāva rules** (TN Bhāvaphala, 7th house):
- Ithasāla between the varṣa lagna lord and the 7th lord gives gain of a wife (v.4).
- The natal Venus sign falls as the varṣa 7th, or holds the varṣa lagna lord, and marriage (pariṇaya) follows (v.3 and its commentary).
- Jupiter aspecting Venus in the varṣa 7th gives "नवा भार्या", a new wife (v.2).
- Muntha in an adhikārī's place, aspected by Jupiter, "causes marriage" (v.7).
- A wife-sāham aspected by its lord and by Venus causes marriage (v.9-12).

([TN, Jha](https://archive.org/details/nxfu-tajika-neelakanthi-gudhartha-prakashika-commentary))

Muntha itself is computed as (natal lagna sign + completed years) mod 12. A key caution: **Muntha in the 7th is classically adverse** ("कलत्र-बन्धु-व्यसन…", distress to wife and kin). It is not a marriage trigger ([TN Muntha-phala v.9; Raman §45, §56](https://archive.org/details/VarshaphalOrTheHinduProgressedHoroscope)).

**Within-year clocks.** These take the year down to months:
- **Pātyāṁśa daśā.** Sort the planets and lagna by degrees within their sign. Each period is proportional to the degree gap from the previous one, and the smallest degree runs first.
- **Mudda daśā.** Take (janma-nakṣatra number + completed years − 2) mod 9 and run the Vimśottari order compressed into one year. The Jha edition marks this verse as a kṣepaka (later interpolation).

All of this is deterministic once the solar-return moment is computed.

## KP's own founder times marriage to the day, which the repo deliberately does not

K.S. Krishnamurti's KP Reader IV gives a fully mechanical procedure ([KP Readers, archive.org](https://archive.org/details/kp-readers)):

1. **Promise.** The 7th-cusp sub-lord must signify 2, 7 or 11. If it is tied to 4, 6 or 10, marriage is denied (R4 pp.106-107, 122).
2. **Significators.** List the significators of 2, 7 and 11 in this strength order: planets in the stars of occupants, then occupants, then planets in the stars of owners, then owners, then conjoined or aspected planets (R4 p.119). Add 3 and 9 for engagement (R3).
3. **Sub-lord gate.** Drop any significator whose own sub-lord ties it to 1, 6, 10 or 12 (R4 p.119).
4. **Ruling Planets.** Keep the significators that are also **Ruling Planets at the moment of judgment**: day lord, Moon's star and sign lords, lagna's star and sign lords, plus nodes as agents. Reject planets in the star of a retrograde planet (R6 printed p.123).
5. **Period.** Take the Daśā–Bhukti–Antara(–Sūkṣma) of the planets that survive.
6. **Day.** Fix it by moving the right body, following KSK's scaling rule: "in days… take the position of Moon… more than a month, move the Sun… in some years move Jupiter" (R6 printed p.131).

The pattern KSK repeats is the **Sun's sign-lord = bhukti lord, star-lord = antara lord, sub-lord = another significator, inside the antara window** (R4 pp.190, 207). In his second-marriage horary case the **daśā lord's** transit fixes the day instead, with the weekday and Moon cross-checked against the RP (R6 printed pp.165-167). Nodes outrank the planets they represent: first the conjunct planet, then the aspecting one, then the sign lord, and both signs of a dual-owner (R4 pp.98, 122, 209). A retrograde RP gives results only after it turns direct, so station dates matter (R6 printed p.167).

**Deterministic, with one catch.** Every step is computable, but the **RP set depends on a chosen judgment moment**. That makes it a horary-style input, not a natal constant, so the engine must take it explicitly. Judgment also enters in tie-breaks ("the latter is stronger") and in "delay till which bhukti".

This runs straight into the repo's stance. `docs/AI_EVENT_TIMING_GUIDE.md` says "KP is a *quality/yes-no* instrument. Do **not** time an event with it". That is a **project design decision** based on KP's tendency to fire broadly on timing. It is not KSK's doctrine, and the report should say so plainly.

## Gochara, Aṣṭakavarga and kakṣyā turn a year into a 3°45′ slice

**Moon-based gochara (Phaladeepika ch. XXVI).**
- Jupiter is good in the 2nd, 5th, 7th, 9th and 11th from the Moon, unless planets occupy the matching vedha places: 12th, 4th, 3rd, 10th and 8th (sl. 2, 7).
- Jupiter in the 7th from the Moon makes one "happy with his wife" (sl. 19).
- Venus is *not* good in the 7th from the Moon. It gives "trouble to wife" (sl. 21).

([PD Adh. XXVI, pp.290-295](https://archive.org/details/Phaladeepika2ndEd.1950ByVSubrahmanyaSastri))

These are general results, not marriage-specific triggers. They are best used as support for, or a veto on, a daśā window.

**Aṣṭakavarga.**
- BPHS 70.34-36 is the only explicit **marriage** rule: marriage "whenever Venus passes in transit through the rashis which have larger number of rekhas in the Ashtaka Varga of Venus".
- The Śodhya-piṇḍa rule (rekhas in the 7th from Venus × Yoga-piṇḍa, ÷27 → nakṣatra, ÷12 → rāśi) times **distress to the wife** under Saturn's transit, not the wedding.
- For muhūrta: Sarvāṣṭakavarga above 30 is favourable, 25-30 medium and below 25 adverse (BPHS 72.3-5, 30-31). Auspicious work goes in the Sun-month and mean-Jupiter year of the signs with more rekhas in the Sun's BAV (70.19-20).

([BPHS ch. 70, 72](https://archive.org/details/brihatparasarahorashastrabyr.santhanam))

**Kakṣyā.** Phaladeepika XXIII.16-19 gives the precision step. Divide each sign into **8 kakṣyās of 3°45′**, ruled in order by Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon and Lagna. A bindu's fruit comes "in the transit over the particular division owned by the planet that put forth the benefic dot" ([PD XXIII.16-19](https://archive.org/details/Phaladeepika2ndEd.1950ByVSubrahmanyaSastri)). The kakṣyā index is just floor(degree-in-sign ÷ 3.75). For Jupiter that is a slice of a few weeks, longer around a retrograde.

**Double transit.** The research found **no Jupiter + Saturn double transit in PD or BPHS**. Teachers describe the modern form as: a marriage daśā, *and* transit Saturn and Jupiter both aspecting or occupying the 7th house or 7th lord (some add the lagna or Moon), within about 6-12 months, often Saturn first. Some credit it to B.V. Raman, others to K.N. Rao ([dekhopanchang](https://dekhopanchang.com/en/learn/modules/11-3); [onlinejyotish](https://www.onlinejyotish.com/free-astrology/astrology-lessons/lesson_151.php)). Rao's published double-transit book is framed for career ([Exotic India](https://exoticindia.com/book/details/ups-and-downs-in-career-replicable-astrological-techniques-using-transits-of-saturn-and-jupiter-nae715)). Teachers also disagree on the aspect set: one allows 1/3/5/9/11, another only Saturn's 3/7/10 and Jupiter's 5/7/9. A critic notes that Jupiter's four sign-contacts (1/5/7/9) hit the 7th or its lord about a third of the time, so the test discriminates poorly on its own ([IndiaDivine](https://www.indiadivine.org/content/topic/1514904-why-shri-kn-raos-double-transit-doesnt-make-sense/)). It is deterministic once the aspect set is fixed. **Its status is modern, and it should be labelled that way.**

## Nadi, Bhrigu Bindu, Sudarshana and Yogini are clocks of uneven pedigree

**BNN (R.G. Rao's Bhṛgu Nandi Nāḍī).** Venus is the marriage kāraka, with Mars added for a woman's chart. The timer is Jupiter's roughly one-sign-a-year transit contacting Venus: same sign, the 7th from it, trines or the 2nd/12th. A Saturn contact means delay. Degree or star matching is only a refinement ([repo `docs/knowledge/bnn/01_timing_method.md`](/home/user/Advance-astrology-framework/docs/knowledge/bnn/01_timing_method.md); [`docs/BNN_METHODS.md`](/home/user/Advance-astrology-framework/docs/BNN_METHODS.md)). It is deterministic and gives a year. The material is a Nāḍī tradition published in the 20th century, and the quotes come through the repo's distilled notes, not a fresh check of the PDF.

**Bhrigu Bindu.** This is the **shorter-arc midpoint of natal Moon and Rāhu**. Jupiter crossing it is read as a positive window, marriage included, and Saturn crossing it as difficulty. Sources warn against using it without daśā support ([biplov.dev](https://biplov.dev/en/speciallagnas/bhrigubindu); [astroindus](https://astroindus.com/bhrigu-nandi-nadi/bhrigu-bindu/)). It is modern, with no classical verse found, and gives a fully deterministic degree trigger.

**Sudarshana Chakra.** BPHS ch. 74 gives each house, counted from the lagna, Moon and Sun, a one-year daśā in turn. Inside it each house gets a one-month antardaśā, then 2½-day and 12½-ghaṭikā sub-periods, on solar months. Benefics in 1/4/7/10/5/9/8 from the year-house are good, malefics in 3/6/11 are good ([BPHS ch. 74](https://archive.org/details/brihatparasarahorashastrabyr.santhanam)). The framework is classical, but **BPHS gives no marriage rule** for it. Reading marriage from the year-house and its 7th is an inference. The output is deterministic: a year, then a month.

**Yogini daśā.** Practitioners run it as a parallel clock to Vimśottari. The 7th lord's MD/AD/PD are the primary windows, and agreement between the two systems raises confidence ([anvayajyotish](https://anvayajyotish.com/blog/marriage-timing-prediction-vedic-astrology); [dkscore](https://www.dkscore.com/jyotishmedium/marriage-timing-with-yogini-dasha-and-varshaphala-a-step-by-step-vedic-astrology-guide-2261)). It is a classical daśā, but its use for marriage is a modern habit.

**Kālacakra daśā.** BPHS has only one note: marriage when the movement is from Sagittarius to Scorpio ([BPHS ch. 46](https://archive.org/details/brihatparasarahorashastrabyr.santhanam)). No full marriage rule was found.

## Muhūrta rules choose the wedding day; they do not predict it

Muhūrta answers a different question: *on which day should the wedding be held*, not *when will it happen*. The research read the Muhūrta Chintāmaṇi with Pīyūṣadhārā commentary from a local OCR, and no public URL was captured, so these points are less checkable.

**Guru-bala** is counted from the janma-rāśi by gochara. Jupiter in the 4th, 6th or 10th needs pūjā. Jupiter in the 1st, 8th or 12th is rejected even with pūjā by "the ancients". Garga is quoted as saying that for marriage Guru-bala goes by "gochareṇaiva", with **vedha irrelevant**. Rājamārtaṇḍa says to fall back on Aṣṭakavarga-bala when gochara-bala is lacking.

The **eleven vivāha nakṣatras** are Rohiṇī, Mṛgaśirā, Maghā, Uttara Phalgunī, Hasta, Svātī, Anurādhā, Mūla, Uttarāṣāḍhā, Uttara Bhādrapadā and Revatī. They must be nirvedha, checked by the Pañcaśalākā chakra. This list comes from secondary summaries, because the verse text was missing from the local OCR ([drikpanchang](https://www.drikpanchang.com/panchang/nakshatra/auspicious-marriage-nakshatra.html)).

Other day-level filters:
- PD XXVI: "A marriage celebrated during a Vedha will not be happy" ([PD](https://archive.org/details/Phaladeepika2ndEd.1950ByVSubrahmanyaSastri)).
- BPHS 72: the SAV filter on the Moon's sign for Chandra-bala.
- Uttara Kālāmṛta: a dharmaśāstra rule that **remarriage after a wife's death be in odd years from her death** ([UK p.~224](https://archive.org/details/uttkalamrita-kalidas-ps-sastri)).

All of these are deterministic day filters. The folk maxim "Guru-bala for the bride, Sūrya-bala for the groom, Chandra-bala for both" was not found in the text.

## Second marriage: promise and break are textual, the new date is borrowed machinery

Each school separates **promise** (more than one marriage), **break** (death or divorce) and **re-union timing**. Only the first two are well sourced.

- **Parāśarī.** Promise: JP XIV.25-26, where the number of wives equals the planets with Venus, and weak dusthāna lords joined with the 7th or 2nd lord "destroy" wives ([JP](https://archive.org/details/JatakaParijataVolIIOfIIByVSubrahmanyaSastri)). SC sl. 16-22 gives "विवाहद्वयम्" (two marriages) and "कलत्रान्तर" (another wife) yogas ([SC](https://archive.org/details/sarvartha-chintamani-mahidhar-sharma_202210)). BPHS ch. 18 gives the 10/22/33 triplet and the spouse-loss ages of sl. 35-39 ([BPHS](https://archive.org/details/brihatparasarahorashastrabyr.santhanam)).
- **Jaimini.** Plurality from the 2nd from UL. The break in the Guru-Śūla daśās. Rath's Venus/Ketu on the A7/UL axis and his D-20 Nārāyaṇa daśā for the break ([srath.com](https://srath.com/jyoti%E1%B9%A3a/scholar/darapada-and-upapada/)). The popular "second spouse from the 8th of UL" rule is **unverified**. UK's commentator says only that "The eighth house of the upapada … refers to the second marriage", inside a case analysis ([UK p.~106](https://archive.org/details/uttkalamrita-kalidas-ps-sastri)).
- **Tājika.** Reapply the Vivāha Sāham activation in a later year. TN v.2's "नवा भार्या" (new wife).
- **KP.** The only explicit algorithm:
  - Promise: the 7th sub-lord is Mercury, sits in a dual sign, or is in the star of a planet in or owning a dual sign, **and** it signifies 2 or 11 (R6 printed p.165).
  - Timing: significators of **2 and 11**, filtered by RP, after the 1/6/10/12 separation block ends (R4 pp.146-155, 182).
  - The day comes from the Sun's or the daśā lord's transit ([KP Readers](https://archive.org/details/kp-readers)).
  - The "2nd-cusp sub-lord to the 7th means legal remarriage, to the 11th means a liaison" rule comes from a case of unclear authorship in Reader IV, so it is practitioner doctrine.

## Computation checklist

| # | Method (source) | Inputs | Deterministic? | Output |
|---|---|---|---|---|
| 1 | 7th occupant/aspector/lord daśā (PD X.13; JP XIV.28-29) | D1, graha dṛṣṭi, Vimśottari | Yes; ranking needs a strength convention | Year–multi-year window |
| 2 | Stronger of 7L dispositors vs Venus/Moon daśā + Jupiter trine to 7L D1/D9 (PD X.14) | D1, D9, strength metric, Jupiter ephemeris | Yes, once the "stronger" metric is fixed | Year (Jupiter about 1 sign a year) |
| 3 | Start/middle/end of daśā (JP XIV.30) | Planet and sign-lord nature, conjunctions | Yes, once "benefic house" is fixed | Sub-window inside the daśā |
| 4 | BPHS marriage antardaśās (ch. 52-60), Jupiter–Venus mutual periods (UK VI) | Kendra/trikoṇa, dignity, Vimśottari | Yes | Bhukti window (months–years) |
| 5 | Dārakāraka / strongest kalatra-kāraka daśā (BPHS 32; SC 20) | Chara-kāraka degrees, strength | Yes, once a strength metric is fixed | Daśā window |
| 6 | 7th-sign / Venus-sign rāśi or Chakra daśā (BPHS 46, 49; JP XVII) | Sign-daśā implementation | Yes; the variant must be named | Year window |
| 7 | BPHS ch. 18 age yogas, 3-marriage triplet; JP XIV.32 (8 + 7th sign no.) | D1, D9 geometry | Yes | Age-year band / early-late flag |
| 8 | Venus or 7L trine to lagna lord D1/D9; lagna lord in 7th; JP XIV.31 Moon+Jupiter; JP XIV.27 sum point | D1, D9, ephemeris | Yes (XIV.27 needs the "figures" convention) | Month (Venus, 7L), year (Jupiter), day (Moon) |
| 9 | Jupiter/Venus gochara from Moon with vedha (PD XXVI) | Natal Moon, ephemeris | Yes | Year/month support or veto |
| 10 | Venus through high-rekha signs of Venus BAV (BPHS 70.34-36); SAV > 30 | BAV/SAV tables, ephemeris | Yes | Month |
| 11 | Kakṣyā of the bindu-giving planet (PD XXIII.16-19) | Prastāra AV, ephemeris | Yes | Weeks / day window |
| 12 | Jupiter + Saturn double transit on 7th/7L (modern) | Ephemeris, chosen aspect set | Yes, once the aspect set is fixed | 6-12-month window |
| 13 | Jaimini sign flags: DK, UL, 2nd-from-UL, A7, Venus/Ketu, 7th from AL/AK (Rath, Rangacharya) | Chara kārakas, ārūḍhas, rāśi dṛṣṭi, Chara/Nārāyaṇa daśā | Yes; variant + UL convention must be named | MD/AD sign window (years→months) |
| 14 | Guru-Śūla daśās from Jupiter (Jaimini Su. 10-11): spouse loss | Jupiter's sign, rāśi daśā | Yes | Break window (for remarriage) |
| 15 | Vivāha Sāham activation + varṣa 7th tests + Muntha+Jupiter (TN Sāhama 17, 39; Bhāvaphala 7th) | Solar return, Tājika aspects, Ithasāla | Yes | Year |
| 16 | Pātyāṁśa / Mudda daśā in the varṣa (TN; Raman §49) | Varṣa chart degrees; janma-nakṣatra | Yes | Month inside the year |
| 17 | KP: 7th sub-lord promise → 2/7/11 significators → RP → D-B-A-S → Sun/Moon/daśā-lord sign-star-sub transit (KP R4, R6) | Placidus cusps, KP sub table, **judgment moment**, ephemeris | Yes, given a judgment time; tie-breaks are judgment | Day |
| 18 | KP second marriage: dual-sign/Mercury 7th sub-lord + 2/11 significators (R6 p.165) | Same as 17 | Yes | Day (after the separation block) |
| 19 | BNN Jupiter contact on Venus (Mars for a woman), Saturn = delay (R.G. Rao) | D1, Jupiter/Saturn ephemeris | Yes | Year |
| 20 | Bhrigu Bindu: Jupiter crossing the Moon–Rāhu midpoint (modern) | Moon, Rāhu, ephemeris | Yes | Weeks–months |
| 21 | Sudarshana year-house and month-house (BPHS 74; marriage use inferred) | Lagna, Moon, Sun, age, solar months | Yes | Year → month |
| 22 | Yogini daśā of 7L etc. (modern usage) | Janma-nakṣatra | Yes | Daśā window |
| 23 | Muhūrta: Guru-bala, 11 nirvedha nakṣatras, Chandra-bala, SAV, no vedha; odd-year remarriage rule | Janma-rāśi, pañcāṅga, ephemeris | Yes | Specific auspicious days (selection, not prediction) |

## Known source conflicts and open conventions

**Vivāha Sāham, day versus night.** TN Sāhama 17 ("सततं") and Raman §73 ("Day or Night") give **no night reversal**. The repo's `_saham()` docstring says "`A − B + Lagna` by day, `B − A + Lagna` by night", and `vivaha_saham` applies that reversal to the Venus − Saturn formula. `_saham()` also never applies the TN verse 5 / Raman §64 **+30° saika proviso**. CLAUDE.md classes this as a change to a computed quantity, so it must be **presented for approval** and logged in `docs/RULE_CHANGELOG.md` with TN 17 / Raman §73 as the source. Nothing was changed in this research.

**Punarvivāha Sāham.** The repo defines it as Saturn − Venus + Lagna and calls it a "documented variant". **Neither TN's 50-sāham list nor Raman's list contains it**, and no source was found. The closest classical object is Anyadāra (Venus − Sun + Asc), which means another woman, not a remarriage.

**Double transit.** It is absent from PD and BPHS and comes from a modern practitioner. Credit is split between Raman and Rao, the aspect set varies by teacher, and it discriminates poorly on its own. Yet `docs/AI_EVENT_TIMING_GUIDE.md` treats the bhāva double-transit as a PRIMARY trigger. The classical anchor closest to it is PD X.14 (daśā + Jupiter trine), which has no Saturn half.

**KP and timing.** KSK uses KP to time marriage to the day, and even the weekday. The repo's "KP is quality/yes-no, never timing" stance is a design choice made because KP fires broadly. It is defensible, but it is not KSK's doctrine.

**Jaimini.** The sūtras do not name the marriage daśā sign, and every such rule is commentarial. UL has two computations (B.S. Rao's note). "Yugma" is read as Gemini by B.S. Rao, while Santhanam's note gives Taurus as the UL for plurality. The Chara daśā variant changes which sign carries the event.

**Texts and editions.**
- SC sl. 65-66: the Sanskrit reads "delayed marriage", but the Hindi ṭīkā reads "late fortune".
- JP XIV.28 is lost in the OCR, the 10th/4th-lord clause of XIV.29 is garbled, and the "figures" of XIV.27 are undefined.
- The PD X.14 and SC 20 "stronger" never names a metric.
- KP R4 p.183 says "6th cusp", which is almost certainly a slip for "7th".
- R4 mixes KSK's own cases with cases of unclear authorship.

**Still unverified.** Saravali (no usable OCR), K.N. Rao's own Chara-daśā and double-transit wording, the MC vivāha-prakaraṇa verse text, the 8th-from-UL second-spouse rule, and the origin of Bhrigu Bindu.

## Conclusion

The literature is more computable than it looks. What resists automation is not the arithmetic but the **unstated conventions**: which strength decides "stronger", what a "benefic house" is, which Chara daśā, which UL reading, which aspect set for double transit, and what time of judgment for KP. The right engine design (per CLAUDE.md) emits every one of these as **named-convention DATA**: candidate daśā lords with the JP XIV.30 start/middle/end tag, PD X.12/X.14 trine windows, kakṣyā slices, Jaimini sign flags, Tājika sāham-activation flags and KP sign/star/sub hits. It should not merge them into one score. Different methods work at different resolutions (age band, daśā, year, month, kakṣyā, day), so candidate dates come from **intersecting** windows across schools, not from adding votes.

Two findings should change how this repo reads charts. First, the Tājika engine computes Vivāha Sāham differently from its own primary source and carries an unsourced Punarvivāha Sāham. Both are approval-gated fixes, not calibration. Second, the guide's PRIMARY trigger (double transit) is the *least* classical piece in the stack. Meanwhile PD X.14's daśā × Jupiter-trine rule and PD XXIII's kakṣyā are verse-cited and not yet exposed as engine data. For second marriage, the honest position is that śāstra gives the promise and the break. The new date must be found by running the first-marriage machinery again after the break, and the AI should say so instead of claiming a dedicated rule.
