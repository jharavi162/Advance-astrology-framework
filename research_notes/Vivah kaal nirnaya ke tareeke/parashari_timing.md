# Parashari-school classical rules for TIMING a marriage (when, not whether)

Scope: timing rules only (daśā/antardaśā selection, age-of-marriage verses, transit rules) from BPHS, Phaladeepika (PD), Saravali, Brihat Jataka (BJ), Uttara Kalamrita (UK), Jataka Parijata (JP), Sarvartha Chintamani (SC). No rule has been applied to any chart.

Source editions actually read (primary-text OCR, grepped locally; the URLs are the archive.org items these OCR files come from):
- **BPHS**: R. Santhanam translation, Vol. I/II (local OCR `brihatparasarahorashastrabyr.santhanam.txt`). [archive.org item](https://archive.org/details/brihatparasarahorashastrabyr.santhanam)
- **PD**: V. Subrahmanya Sastri, 2nd ed. 1950 (local OCR). [archive.org item](https://archive.org/details/Phaladeepika2ndEd.1950ByVSubrahmanyaSastri)
- **UK**: Kalidasa, trans. P.S. Sastri (local OCR). [archive.org item](https://archive.org/details/uttkalamrita-kalidas-ps-sastri)
- **BJ**: Varahamihira, trans. Surya Narain Rao, ed. B.V. Raman (local OCR). [archive.org item](https://archive.org/details/cycx_brihat-jataka-of-varaha-mihira-ed-by-venkata-raman-trans-by-surya-narain-rao-195)
- **JP**: Vaidyanatha, trans. V. Subrahmanya Sastri, Vol. II (downloaded `_djvu.txt`). [archive.org](https://archive.org/details/JatakaParijataVolIIOfIIByVSubrahmanyaSastri)
- **SC**: Venkatesha Daivajna, Sanskrit with Hindi ṭīkā by Mahidhar Sharma (Venkateshwar Press; downloaded `_djvu.txt`). [archive.org](https://archive.org/details/sarvartha-chintamani-mahidhar-sharma_202210)
- The archive.org item `in.ernet.dli.2015.241659`, catalogued as "Sarvartha Chintamani" in English, is a **different book** (Upakhyanamala, stories). It is useless for this purpose. [archive.org](https://archive.org/details/in.ernet.dli.2015.241659)
- **Saravali**: the only English OCR I could reach (Kalyana Varma's Saravali, chapters 1-10, local file) stops before the bhāva chapters. The Santhanam Saravali `_djvu.txt` on archive.org ([item](https://archive.org/details/saravaliofkalyanavarmasanthanamr.astrology_202003_28_Z)) is unusable Devanagari OCR garbage, byte-identical in size to the local `saravali.txt`. **No Saravali timing rule could be verified** (see Gaps).

Computability legend: **D** = deterministic, with every input coming from the chart or ephemeris. **D\*** = deterministic once a convention is fixed (for example "benefic house" or the "figure" of a planet). **I** = interpretive.

---

## Q1. Which daśā / antardaśā lords give marriage? (exact verses)

### Takeaway
The classical consensus across PD, JP, BPHS and UK puts marriage in the daśā/bhukti of a planet tied to the 7th bhāva: its occupant, its aspector, its lord, the lord associated with Venus, and so on, with Venus and the Moon as kārakas. JP adds a ranked fallback list and a rule for where inside the daśā the event falls: start, middle or end. BPHS supplies many conditional "marriage in antardaśā X of daśā Y" statements (lord in kendra/trikoṇa, own or exaltation sign) and a 7th-sign Chara-daśā rule.

### Cited Findings
**Phaladeepika (Mantreśvara), Adh. X (Kalatra-bhāva)**
- **PD X.13 (daśā rule):** "The acquisition of a wife may happen during the Dasa period of the planet (1) posited in the 7th house, (2) aspecting the 7th house or (3) owning the 7th house. The same may also happen, when the lord of the Lagna in his orbit comes to the Rasi representing the 7th house." Inputs: 7th occupants, aspectors of the 7th (graha dṛṣṭi), 7th lord, transit of the lagna lord. Computability: **D** for the candidate set; the transit clause is **D**. — [PD 1950, Adh. X sl. 13, p.109](https://archive.org/details/Phaladeepika2ndEd.1950ByVSubrahmanyaSastri)
- **PD X.14 (daśā + Jupiter transit):** "Find which of the two in the following two pairs is stronger: (1) the lords of the Rasi and Navamsa occupied by the lord of the 7th house; (2) Venus and the Moon. During the Dasa-period of that planet when Jupiter passes through a sign triangular to the Rasi or Navamsa occupied by the lord of the 7th, the marriage may be declared to take place." Inputs: D1 and D9 dispositors of the 7th lord, Venus, Moon, a strength comparison (ṣaḍbala or similar), Jupiter's transit. Computability: **D\***. The text says "stronger" without naming a metric, so the strength convention must be chosen. — [PD Adh. X sl. 14, p.110](https://archive.org/details/Phaladeepika2ndEd.1950ByVSubrahmanyaSastri)
- **PD XX.8 (daśā of the 7th lord):** "During the Dasa-period of the lord of the 7th house, the person born acquires new clothes, jewels, new bed, etc. He will … fully enjoy all pleasures in the company of his beloved … and perform marriages or similar auspicious festivities in his family and undertake pleasure-trips." Computability: **D** (7th lord's daśā window). — [PD Adh. XX sl. 8](https://archive.org/details/Phaladeepika2ndEd.1950ByVSubrahmanyaSastri)
- **PD XIX.26 (Venus mahādaśā):** "During the Dasa of Venus there will be acquisition of wife, jewels, clothes …". **PD XX.35 (Venus bhukti in Rāhu daśā):** "Acquisition of a wife, comforts of the couch, horses … will mark the Bhukti of Venus in Rahu's Mahadasa." Computability: **D**. — [PD Adh. XIX sl. 26; Adh. XX sl. 35, p.231](https://archive.org/details/Phaladeepika2ndEd.1950ByVSubrahmanyaSastri)
- **PD XX.33-36 (general daśā/transit modifiers that apply to every bhāva, marriage included):** The daśā lord, when transiting its own, exaltation or friendly sign, promotes the bhāva it represents, "provided the said planet is endowed with full strength at the birth time". A weak, combust or debilitated daśā lord "during his transit through any house cause[s] the total destruction of that Bhava" (sl. 35). Results are happy when the transiting Moon is in the daśā lord's exaltation or friendly sign, or in the 3rd, 6th, 10th, 11th, a trine or the 7th from the daśā lord (sl. 36). Computability: **D**. — [PD Adh. XX sl. 34-36](https://archive.org/details/Phaladeepika2ndEd.1950ByVSubrahmanyaSastri)

**Jataka Parijata (Vaidyanātha), Adh. XIV (7th bhāva)**. The chapter index lists sl. 28-29 as "Methods of finding out the period favorable to marriage", sl. 30 as "at which portion of the Dasa … the happy event may take place" and sl. 31 as "the periods when the acquisition of a wife becomes possible".
- **JP XIV.28 (Sastri's translation):** "The acquisition of a wife may happen during the Da[sa] …". The OCR breaks off here. The index shows this verse parallels PD X.13 (7th-occupant, aspector or lord). — [JP Vol II, Adh. XIV sl. 28, p.859-860](https://archive.org/details/JatakaParijataVolIIOfIIByVSubrahmanyaSastri)
- **JP XIV.29 (ranked candidate list):** "If the lord of the 7th bhava be associated with Venus, its Dasa and Bhukti may lead to marriage. Failing that, the Dasa and Bhukti of the lord of the Rasi occupied by the planet owning the 2nd bhava may have marriage-producing efficacy. The Dasa and Bhukti of the lords of the 10th and the 4th bhavas come next in order [OCR partly garbled; reading inferred]. Lastly, note the planet associated with the lord of the 7th bhava or the one occupying it. During the Dasa and Bhukti of one of these, marriage may take place." Sastri's note: "each succeeding alternative arises because of the weakness, etc., of the planet concerned." Inputs: 7th lord + Venus conjunction, 2nd lord's dispositor, 10th/4th lords (uncertain reading), conjoined planets and 7th occupants. Computability: **D** for the candidate list; the order of precedence depends on strength, so **D\***. — [JP Vol II, Adh. XIV sl. 29, p.860-861](https://archive.org/details/JatakaParijataVolIIOfIIByVSubrahmanyaSastri)
- **JP XIV.30 (where inside the daśā):** "If the planet powerful for producing marriage be benefic and in a benefic house, it will bring on the happy event at the commencement of its Dasa. If the planet, being itself benefic, should occupy a malefic house, the marriage … will take place in the middle of its Dasa. If the planet and the house it occupies be both malefic, the event in question will happen at the end of its Dasa. But if the planet … occupy a benefic house and be in conjunction with a benefic planet at the same time, its influence for good will prevail during the whole of its Dasa period." Inputs: natural benefic/malefic status of the planet, benefic/malefic sign (the sign lord's nature), conjunctions. Computability: **D\*** ("benefic house" probably means a sign owned by a benefic). — [JP Vol II, Adh. XIV sl. 30, p.861](https://archive.org/details/JatakaParijataVolIIOfIIByVSubrahmanyaSastri)
- **JP Adh. XVII sl. 64-65 (Chakra-daśā):** "During the ripening of the [Chakradasa] of the 7th Rasi may be expected marriage; the joy with a wedded consort; the birth of a son … When the 7th Rasi is benefic and is occupied by a benefic planet, the good effects spoken of will [be full]." Computability: **D** (sign-daśā of the 7th rāśi). — [JP Vol II, Adh. XVII sl. 64-65](https://archive.org/details/JatakaParijataVolIIOfIIByVSubrahmanyaSastri)

**BPHS (Santhanam)**
- **BPHS ch. 46 sl. 143-144 (Chakra/rāśi daśā of the 7th sign):** "Marriage, conjugal happiness, being blessed with children … are the effects in the Chakra Dasha of the sign in the seventh house. The beneficial results will be experienced in full if the sign be a benefic one. Meagre good effects … in the case of a malefic sign." Computability: **D**. — [BPHS Santhanam ch. 46 sl. 143-144, p.435](https://archive.org/details/brihatparasarahorashastrabyr.santhanam)
- **BPHS ch. 49 (rāśi-daśā by sign owned or occupied):** "In the Dasha of the rashi owned or occupied by Venus, there will be acquisition of learning, marriage and gain of wealth." Computability: **D**. — [BPHS ch. 49](https://archive.org/details/brihatparasarahorashastrabyr.santhanam)
- **BPHS ch. 46 (Kālacakra "movement" note):** "There may be gains of comforts and property and marriage if the movement be from Sagittarius to Scorpio." Computability: **D** (needs a Kālacakra daśā implementation). — [BPHS ch. 46](https://archive.org/details/brihatparasarahorashastrabyr.santhanam)
- **BPHS ch. 48, translator's note (Santhanam, NOT Parāśara):** "the 7th house indicates marriage amongst other things. If the lord of the 7th is well placed, there will be auspicious celebrations during his Dasha." — [BPHS ch. 48 note](https://archive.org/details/brihatparasarahorashastrabyr.santhanam)
- **BPHS ch. 32 (Dārakāraka):** When two planets tie in longitude, "there will be shortage of planet for Dara Karakatwa. The constant indicator Venus should then be considered in the matter of marriage etc. as coming under Dara Karaka." This verse makes the Jaimini-style Dārakāraka (lowest-degree chara kāraka) the marriage significator, with Venus as the fallback. Computability: **D**. — [BPHS ch. 32](https://archive.org/details/brihatparasarahorashastrabyr.santhanam)
- **BPHS antardaśā verses that explicitly name marriage.** Each is conditional; all computability is **D** once kendra/trikoṇa, own/exaltation and "from the daśā lord" are computed:
  - Moon AD in Sun MD, if the Moon is in a kendra or trikoṇa: "Functions like marriage etc. … There will be marriage of the native". — [ch. 52 sl. 4-6](https://archive.org/details/brihatparasarahorashastrabyr.santhanam)
  - Jupiter AD in Sun MD, if Jupiter is in a kendra or trikoṇa, in exaltation, in his own sign or in his own varga: "Marriage of the native …". — [ch. 52 sl. 32-33](https://archive.org/details/brihatparasarahorashastrabyr.santhanam)
  - Saturn AD in Sun MD, if Saturn is in a kendra or trikoṇa: "auspicious functions like marriage etc., at home". — [ch. 52 sl. 40-42](https://archive.org/details/brihatparasarahorashastrabyr.santhanam)
  - Mercury AD in Sun MD (kendra/trikoṇa context): "Marriage, offering of oblations …". — [ch. 52 sl. 52-53](https://archive.org/details/brihatparasarahorashastrabyr.santhanam)
  - Venus AD in Sun MD, if Venus is in a kendra or trikoṇa: "Marriage and happiness as desired from wife …". — [ch. 52 sl. 65-68](https://archive.org/details/brihatparasarahorashastrabyr.santhanam)
  - Jupiter AD in Moon MD, if Jupiter is in the 3rd or 11th from the daśā lord (Moon): "celebrations like marriage". Mercury AD in Moon MD (kendra/trikoṇa): "Effects like marriage". — [ch. 53 (sl. ~42-43 for Mercury)](https://archive.org/details/brihatparasarahorashastrabyr.santhanam)
  - Moon AD in Mars MD, if the Moon is exalted, in her own sign, in a kendra, or in the 9th/4th/10th/lagna with those houses' lords, and waxing for full effect: "celebrations of auspicious functions like marriage". — [ch. 54 sl. 70-73](https://archive.org/details/brihatparasarahorashastrabyr.santhanam)
  - Saturn AD in Rāhu MD, if Saturn is in a kendra or trikoṇa, exalted, in his own sign, in mūlatrikoṇa, or in the 3rd/11th: "celebration of marriage etc., at home". Mercury AD in Rāhu MD (sl. 30-33), and Mercury in a kendra or the 11th/3rd/9th/10th from Rāhu (sl. 34-35): "marriage". — [ch. 55 sl. 21-24, 30-35](https://archive.org/details/brihatparasarahorashastrabyr.santhanam)
  - Venus AD in Saturn MD, if Venus is in a kendra, trikoṇa or the 11th with or aspected by benefics: "Effects like marriage, birth of a son …". The verse adds: "If during the period of Antardasa, Jupiter be favourable in transit, there will be dawn of fortune." — [ch. 57 sl. 24-27½](https://archive.org/details/brihatparasarahorashastrabyr.santhanam)
  - Moon AD in Mercury MD, if the Moon is in a kendra or trikoṇa, exalted, in her own sign with Jupiter's aspect, or a yogakāraka: "marriage, birth of a son". Jupiter AD in Mercury MD (kendra/trikoṇa/11th, own or exaltation sign): "marriage etc. at home". — [ch. 58 sl. 26-27, 56-58](https://archive.org/details/brihatparasarahorashastrabyr.santhanam)
  - Mercury AD in Ketu MD: "functions like marriage suddenly". Sun AD in Venus MD (exalted, own sign, kendra/trikoṇa, 2nd/11th): "happiness from wife … marriage". — [ch. 59 sl. 69-71; ch. 60 sl. 13-15](https://archive.org/details/brihatparasarahorashastrabyr.santhanam)

**Uttara Kalamrita (Kālidāsa), Ch. VI (results of daśās), P.S. Sastri p.156-157**
- "Guru and Shukra in their mutual major and sub-periods will make the native a king or a minister. They give wealth, happiness with wife and children. But they must be in benefic houses, strong, and … with or aspected by benefics. The native … performs marriage and other similar auspicious things." The converse: when Jupiter and Venus are 6/8 or 2/12 from each other, or joined with or aspected by malefics, "during their major and sub-periods they will bring about separation from wife (or husband)". A similar verse for Mars and Jupiter, if strong, gives "marriages and other auspicious functions". Computability: **D** for the daśā pair and their mutual position; "strong / benefic houses" is **D\***. — [UK (P.S. Sastri) Ch. VI, p.156-157](https://archive.org/details/uttkalamrita-kalidas-ps-sastri)

**Sarvartha Chintamani (Venkaṭeśa), 7th-bhāva chapter, sl. 20 (Mahidhar Sharma ed. p.~121)**
- "कलत्रकारकश्चन्द्रो ज्ञो गुर्वाथवा भृगुः । मध्ये बलिष्ठो यस्तेषां तस्मात्सर्वं निरूपयेत्". Hindi ṭīkā: the 7th-bhāva kāraka may be Moon, Mercury, Venus or Jupiter, and "whichever of them is strongest, from that judge the entire marriage yoga". This verse selects the kāraka used for daśā and timing. Computability: **D\*** (strength metric unspecified). — [SC, Mahidhar Sharma ed., saptama-bhāva adhyāya sl. 20](https://archive.org/details/sarvartha-chintamani-mahidhar-sharma_202210)
- SC's daśā chapters also list vivāha among the effects of benefic daśā/antara. One example: Jupiter's daśā when Jupiter is in a benefic ṣaṣṭyaṃśa gives "यज्ञ तथा विवाहकर्म". The ṣaṣṭyaṃśa condition makes this **D** only with an exact birth time. — [SC daśā adhyāya (Hindi ṭīkā)](https://archive.org/details/sarvartha-chintamani-mahidhar-sharma_202210)

### Inferences
- The union of the PD X.13, X.14 and JP XIV.29 lists gives the classical Parāśarī **candidate set of marriage daśā/bhukti lords**: 7th occupants; aspectors of the 7th; 7th lord; Venus, especially when conjoined with the 7th lord; Moon; the D1 and D9 dispositors of the 7th lord; the dispositor of the 2nd lord; planets conjoined with the 7th lord. BPHS adds the **Dārakāraka** (ch. 32), the **7th sign's Chara/Chakra daśā** and the **Venus-owned or occupied sign's rāśi daśā**. UK adds **Jupiter–Venus mutual daśā/bhukti**. SC adds the strongest of the four kalatra-kārakas. All of these are mechanical sets.
- The **lagna lord**, sometimes cited by later authors, appears in these texts only as a transiting body (PD X.13) or as a reference point for transits (PD X.12, JP XIV.31). In the verses read, it is not named as a daśā lord giving marriage.
- **JP XIV.30** is a computable "where inside the daśā" rule (onset, middle or end). Its benefic/malefic matrix is deterministic, so it suits engine DATA.
- The BPHS antardaśā verses read as generic "auspicious functions like marriage" outcomes gated by dignity or placement. They support marriage in a period but are not specific to marriage, so their weight is interpretive.

### Gaps
- JP XIV.28's verse body is lost in the OCR. That it parallels PD X.13 is inferred from the chapter index and PD, not read directly.
- The second clause of JP XIV.29 (10th/4th lords) is partly garbled. It should be checked against a clean copy.
- PD X.14 and SC sl. 20 never say which strength measure decides "stronger".

---

## Q2. BPHS 'Time of Marriage' age verses (ch. 18 "Effects of the Seventh House", sl. 22-34) — every age rule with its condition

### Takeaway
BPHS ch. 18 sl. 22-34 gives 13 yoga → age rules, ranging from age 5 or 9 up to 31 or 33, plus a three-marriage rule (sl. 40-41) and spouse-loss ages (sl. 35-39). Santhanam calls these indicators of early versus delayed marriage, not literal ages. Every condition is a pure chart-geometry test, so the conditions are deterministic. Using the output is interpretive.

### Cited Findings
All from [BPHS Santhanam ch. 18 "Effects of the Seventh House", pp.124-127](https://archive.org/details/brihatparasarahorashastrabyr.santhanam). Each condition is **D** unless marked otherwise.

| Śl. | Condition (Santhanam's wording) | Age(s) |
|---|---|---|
| 22 | "If the 7th lord is in a benefic house … while Venus is exalted or is in own sign" (**D\***: "benefic house") | 5 or 9 |
| 23 | "If the Sun is in 7th while his dispositor is conjunct Venus" | 7 or 11 |
| 24 | "Venus in the 2nd while 7th lord in the 11th" | 10 or 16 |
| 25 | "Venus is in an angle from the ascendant while the ascendant lord is in Capricorn/Aquarius" | 11th year |
| 26 | "Venus is in an angle from the ascendant while Saturn is in the 7th counted from Venus" | 12 or 19 |
| 27 | "Venus be in the 7th from Moon while Saturn is in the 7th from Venus" | 18th year |
| 28 | "the 2nd lord is in the 11th while the ascendant lord is in the 10th" | 15th year |
| 29 | "An exchange between the lords of the 2nd and the 11th" | 13 years after birth |
| 30 | "Venus is in the 7th from the 8th house (i.e. the 2nd from ascendant), while his dispositor is conjunct Mars" | 22nd/27th year |
| 31 | "the 7th lord be in the 12th while the natal ascendant lord is in the 7th in Navamsha" | 23rd/26th year |
| 32 | "the 8th lord is in the 7th as Venus is in Navamsha ascendant" | 25th or 33rd year |
| 33 | "Venus be in the 9th from the 9th (i.e. in the 5th house), while Rahu is in one of the said houses (i.e. in the 5th/9th)" | 31st or 33rd year |
| 34 | "Venus is in the ascendant while the 7th lord is in the 7th itself" | 30 or 27 |

- Santhanam's note on sl. 22: "The age of marriage indicated in the text will not be practical in all cases in modern social conditions. These will simply help in knowing of early or belated marriages." On sl. 30: "The Yogas given from this shloka through shloka 34 will delay one's marriage." — [BPHS ch. 18 notes, p.125](https://archive.org/details/brihatparasarahorashastrabyr.santhanam)
- **Three marriages, sl. 40-41:** "Should the Moon be in the 7th from Venus while Mercury is in the 7th from the Moon and the 8th lord is in the 5th (from the ascendant), there will be marriage in the 10th year followed by another in the 22nd year and yet another in the 33rd year." — [BPHS ch. 18 sl. 40-41, p.127-128](https://archive.org/details/brihatparasarahorashastrabyr.santhanam)
- **Spouse-loss ages, sl. 35-39** (relevant to remarriage timing): 7th lord debilitated + Venus in 8th → loss of wife in the 18th or 33rd year; 7th lord in 8th + 12th lord in 7th → 19th year; Rāhu in 2nd + Mars in 7th → "within three days of marriage"; Venus in 8th with its dispositor in a Saturn sign → 12th or 21st year; lagna lord debilitated + 2nd lord in 8th → 13th year. — [BPHS ch. 18 sl. 35-39, p.127](https://archive.org/details/brihatparasarahorashastrabyr.santhanam)
- **Plurality of wives, sl. 19-21** (whether, not when): 7th lord debilitated, or in a malefic sign with a malefic, while the 7th or the 7th navāṃśa belongs to a eunuch planet → two wives. Mars + Venus in the 7th, or Saturn in the 7th with the lagna lord in the 8th → three. — [BPHS ch. 18 sl. 19-21, p.124](https://archive.org/details/brihatparasarahorashastrabyr.santhanam)

### Inferences
- Several conditions can fire in the same chart, and the rules are not mutually exclusive. Only conflicting age pairs come out, so in practice these work as an early, normal or late classifier (sl. 22-29 early, sl. 30-34 late, per Santhanam).
- Each age pair (e.g. 22/27) maps to a year window, such as the 22nd year of age = 21-22 completed. Santhanam alternates between "at the age of" and "in the Nth year". The convention needs fixing; Indian usage normally reads "Nth year" as age N-1 to N.

### Gaps
- I did not check whether other BPHS translations (e.g. G.C. Sharma) number these verses differently, or give different ages.

---

## Q3. PD ch. 20/26, UK, Saravali, JP, SC, BJ — transit and other timing rules

### Takeaway
The transit trigger common to PD and JP is **Jupiter (or Venus, or the 7th lord) transiting a sign trine to the rāśi or navāṃśa of the lagna lord or the 7th lord**, usually inside a qualifying daśā. JP also gives a numeric "figures" method (sum of lords → sign for Jupiter's transit), a Moon+Jupiter rule (2nd from the lagna lord's navāṃśa lord, a sign held by the 7th lord or Venus, or a mutual kendra) and an age formula (8 + the 7th sign's number). PD ch. 26's Moon-based gochara gives only general 7th-house Jupiter results. SC gives early/late-marriage yogas. BJ contributes no explicit timing rule.

### Cited Findings
**Phaladeepika**
- **PD X.12 (transit):** "The marriage may be expected to come off when Venus or the lord of the 7th house in his orbit passes through a Sign which is triangular to the Rasi or Navamsa occupied by the Lord of the Lagna." Inputs: D1 and D9 sign of the lagna lord, transits of Venus and the 7th lord. Computability: **D**. — [PD Adh. X sl. 12, p.109](https://archive.org/details/Phaladeepika2ndEd.1950ByVSubrahmanyaSastri)
- **PD X.13 (transit clause):** marriage "when the lord of the Lagna in his orbit comes to the Rasi representing the 7th house". **D**. — [PD Adh. X sl. 13](https://archive.org/details/Phaladeepika2ndEd.1950ByVSubrahmanyaSastri)
- **PD X.14:** Jupiter transiting a trine to the D1/D9 sign of the 7th lord, during the daśā of the stronger candidate (quoted in Q1). **D\***. The index of the 1950 edition marks X-14 as "Time of marriage guessed through [Jupiter]'s transit". — [PD index, "Time of marriage … X-14"](https://archive.org/details/Phaladeepika2ndEd.1950ByVSubrahmanyaSastri)
- **PD XXVI.19 (gochara from the Moon):** "When Jupiter transits the 7th house, the person will travel on an auspicious undertaking, will be happy with his wife and will be blessed with children." Jupiter is good in the 2nd, 5th, 7th, 9th and 11th from the Moon (sl. 2, 7). **PD XXVI.21:** Venus transiting the 7th from the Moon gives "trouble to wife", so the 7th is not a favourable transit house for Venus. **PD XXVI.32:** favourable transits "become void of effect if they happen to be at the time in their depression or inimical houses or be in an eclipsed state". Computability: **D**, but these are general gochara results, not marriage-specific timing. — [PD Adh. XXVI sl. 2, 7, 19, 21, 32, p.290-295](https://archive.org/details/Phaladeepika2ndEd.1950ByVSubrahmanyaSastri)
- **PD XXVI (vedha):** "A marriage celebrated during a Vedha will not be happy." This is a muhūrta rule, not a natal timing rule. — [PD Adh. XXVI](https://archive.org/details/Phaladeepika2ndEd.1950ByVSubrahmanyaSastri)
- **PD X.11 (spouse's sign, related):** the spouse's janma rāśi is a trine to the D1/D9 sign of the lagna lord or the 7th lord, or the exaltation or debilitation sign of those lords, or "that Rasi which contains the largest number of benefic dots in the Moon's Ashtakavarga". **PD XXIII.12:** use the sign with the most bindus in Venus's Aṣṭakavarga for the wife. Computability: **D** (aṣṭakavarga). — [PD Adh. X sl. 11; Adh. XXIII sl. 12](https://archive.org/details/Phaladeepika2ndEd.1950ByVSubrahmanyaSastri)

**Jataka Parijata, Adh. XIV**
- **JP XIV.27 (numeric "figures" sum → Jupiter transit):** "Add together the figures for the lords of the Lagna and the 7th bhava. Find the Rasi, etc., indicated by the result. When Jupiter traverses the Rasi, etc., above found, the astrologer may predict a person's marriage. The time of marriage may also be determined in the same way in respect to the total of the figures for the ruler of the stars occupied by the Moon and the lord of the 7th bhava." The verse also counts wives from Jupiter's navāṃśa: a friend's navāṃśa → one wife; Jupiter's own → 2 or 3 (OCR reads "2 or 8"; probably 3); his exaltation → many. Computability: **D\***. "Figures" most likely means the planets' longitudes (sphuṭa) added modulo 360°, which yields a sign and navāṃśa (Sastri's "Rasi, etc."); that reading is my interpretation and is not stated in the OCR. — [JP Vol II, Adh. XIV sl. 27, p.859](https://archive.org/details/JatakaParijataVolIIOfIIByVSubrahmanyaSastri)
- **JP XIV.27, Sastri's supplementary verse:** "The marriage may be expected to come off when Venus or the lord of the 7th house in its orbit transits through a sign which is triangular to the Rasi or Navamsa owned by the lord of the Lagna." This is the same rule as PD X.12. — [JP Vol II, p.859](https://archive.org/details/JatakaParijataVolIIOfIIByVSubrahmanyaSastri)
- **JP XIV.31 (Moon + Jupiter transits):** "the acquisition of a wife may take place when the Moon and Jupiter in their progress arrive at the 2nd place from the lord of the Navamsa occupied by the lord of the Lagna … The same event may also happen when Jupiter reaches a sign occupied by the lord of the 7th bhava or Venus. A third possibility is when the Moon and Jupiter occupy a Kendra [from each other]." Computability: **D**. — [JP Vol II, Adh. XIV sl. 31, p.861-862](https://archive.org/details/JatakaParijataVolIIOfIIByVSubrahmanyaSastri)
- **JP XIV.32 (age formula):** "An auspicious time for men's marriage … occurs in the year of their life indicated by the number made up of 8 and the figure denoting the order from Mesha of the sign representing the 7th bhava". Sastri's gloss places it after upanayana. In other words, age = 8 + (sign number of the 7th house, Aries = 1). Computability: **D**. — [JP Vol II, Adh. XIV sl. 32, p.862](https://archive.org/details/JatakaParijataVolIIOfIIByVSubrahmanyaSastri)

**Uttara Kalamrita**
- The only daśā rule I found is the Jupiter–Venus and Mars–Jupiter mutual-period rule in Ch. VI, p.156-157 (quoted in Q1). P.S. Sastri's commentary (not Kālidāsa's verses) repeatedly names "the significator of marriage" (Venus) in case charts. — [UK Ch. VI](https://archive.org/details/uttkalamrita-kalidas-ps-sastri)

**Sarvartha Chintamani, 7th-bhāva chapter, sl. 59-66 (early/late marriage), Mahidhar Sharma ed. pp.126-127**
- **sl. 59:** "दारेश्वरे सन्निहिते विलग्ने नाथस्य बाल्ये परिणीतमाहुः। लग्नात्कलत्राच्छुभखेचरेन्द्रे समीपराशौ यदि तत्तथैव". The Hindi ṭīkā reads: if the 7th lord is close to the lagna lord (the ṭīkā says "in the same aṃśa, near"), marriage is in childhood (bālya). The same holds if benefics are in signs adjacent to the lagna or the 7th. Computability: **D\*** ("near" needs an orb). — [SC sl. 59](https://archive.org/details/sarvartha-chintamani-mahidhar-sharma_202210)
- **sl. 60:** the lagna, 2nd and 7th have benefics and benefic vargas, and their lords are aspected or joined by benefics → early marriage. **D**. — [SC sl. 60](https://archive.org/details/sarvartha-chintamani-mahidhar-sharma_202210)
- **sl. 61:** the 7th lord is in pārāvatāṃśa or another higher vaiśeṣikāṃśa, the 2nd lord is strong, and the lagna lord is in a mṛdu ṣaṣṭyaṃśa → early marriage. **D** (needs vaiśeṣikāṃśa and an exact ṣaṣṭyaṃśa). — [SC sl. 61](https://archive.org/details/sarvartha-chintamani-mahidhar-sharma_202210)
- **sl. 65-66:** "क्रूरे कलत्रेशयुते त्रिकोणे तत्कारके पापसमन्विते वा। कुटुम्बराशौ यदि वात्र माने दूरे विवाहात्कथयन्ति सन्तः" (sl. 65). The wording "dūre vivāhāt" points to marriage being delayed: a malefic with the 7th lord in a trine, or the kāraka with a malefic in the 2nd or 10th; sl. 66 adds a malefic in the 10th, 2nd or 9th with the 7th afflicted. **Conflict:** Mahidhar Sharma's Hindi ṭīkā instead reads both verses as "fortune rises long after marriage" (विवाहसे बहुत दिनों पीछे भाग्य उदय), carrying on the bhāgya theme of sl. 62-64. The Sanskrit and the ṭīkā disagree. — [SC sl. 65-66](https://archive.org/details/sarvartha-chintamani-mahidhar-sharma_202210)

**Brihat Jataka**
- BJ ch. XXIV (Strī-jātaka) gives no marriage-timing rule. The editor notes that Varāhamihira wrote a separate *Vivāha-paṭala* (Bṛhat and Laghu, cited by Bhaṭṭotpala) that is not extant in this edition: "When there is any difference between the combinations sketched here during the marriage time and those explained in Vivahapatalam, the latter must be given credit." — [BJ (Surya Narain Rao/Raman) ch. XXIV notes](https://archive.org/details/cycx_brihat-jataka-of-varaha-mihira-ed-by-venkata-raman-trans-by-surya-narain-rao-195)
- Santhanam's BPHS ch. 80 note: "According to Brihat Jataka the yogas mentioned above become applicable in connection with the time of marriage, the time of selecting a girl, the time of her gift, and the time when a query is made regarding her. Jataka Parijata has expressed the same view". JP's Strī-jātaka chapter (Vol II, p.~1000+) has: "time of their birth, the time of their marriage, the time of [query]". This is a "which chart to read" rule (birth, varaṇa, query or marriage moment), not a natal timing trigger. — [BPHS ch. 80 note](https://archive.org/details/brihatparasarahorashastrabyr.santhanam); [JP Vol II](https://archive.org/details/JatakaParijataVolIIOfIIByVSubrahmanyaSastri)
- Raman's BJ note on widowhood timing (ch. XXIV) reads the age from the navāṃśa lord of the 8th lord as "the period or the sub-period of the lord of the navamsa occupied by the lord of the 8th … after the marriage". This is the editor's daśā reinterpretation of a "planetary age" verse. — [BJ ch. XXIV notes](https://archive.org/details/cycx_brihat-jataka-of-varaha-mihira-ed-by-venkata-raman-trans-by-surya-narain-rao-195)

**Aṣṭakavarga (BPHS) — muhūrta, not natal timing**
- BPHS ch. 72 sl. 3-5, 30-31: auspicious functions "like marriage" should be done when the relevant planet transits a sign with more than 30 bindus (aggregate). 25-30 bindus is medium; under 25 is to be avoided. "If a Rasi is not auspicious in Ashtaka Varga, then its auspiciousness should be checked from transit effects." Computability: **D**. — [BPHS ch. 72](https://archive.org/details/brihatparasarahorashastrabyr.santhanam)

**Saravali**
- No verse verified (see Gaps).

### Inferences
- The mechanically computable **transit trigger set** from these texts:
  - (a) Jupiter in a trine (1/5/9) to the D1 or D9 sign of the 7th lord (PD X.14), during a qualifying daśā;
  - (b) Venus or the 7th lord in a trine to the D1 or D9 sign of the lagna lord (PD X.12 = JP);
  - (c) the lagna lord transiting the 7th sign (PD X.13);
  - (d) Jupiter on the sign occupied by the 7th lord or Venus; Moon + Jupiter in the 2nd from the navāṃśa lord of the lagna lord; Moon and Jupiter in mutual kendras (JP XIV.31);
  - (e) Jupiter on the longitude-sum point of lagna lord + 7th lord, or of the Moon's nakṣatra lord + 7th lord (JP XIV.27, under the sphuṭa-sum reading);
  - (f) Jupiter in the 7th from the natal Moon (PD XXVI.19, general).
- The **combined daśā + Jupiter-transit** structure of PD X.14 (daśā of the stronger candidate × Jupiter in a trine to the 7th lord's sign) is the oldest written form of the "daśā + Jupiter-transit" logic used in modern double-transit methods. The Saturn half of the modern "double transit" does not appear in any verse I read; it is a later (K.N. Rao-era) addition (from memory, not verified here).
- PD XXVI.32 and XX.35 supply deterministic **negation gates**: a transit in debilitation, an enemy sign or combustion is void, and a weak daśā lord destroys the bhāva in its transit.

### Gaps
- **Saravali:** no usable English OCR of the bhāva or daśā chapters was reachable. From memory and unverified: Saravali ch. 35 (Kalatra) is mostly about whether marriage happens and the spouse's nature, and its daśā chapters (ch. 41-44) give generic "acquisition of wife" results for Venus's daśā. Treat this as unconfirmed.
- **Uttara Kalamrita:** in the P.S. Sastri OCR I found no explicit "time of marriage" verse in the kalatra or bhāva sections. A clean Sanskrit text (Khaṇḍa IV) should be checked. Some modern writers attribute bhāva-timing rules (daśā of the bhāva lord, its occupant, its navāṃśa lord) to UK; I could not verify this.
- The meaning of JP XIV.27's "figures" (sphuṭa sum vs. sign numbers) is not stated in the OCR text I read.
- **Sarvartha Chintamani:** the chapter number is not visible in the OCR (it is the "सप्तमभावफलविचाराध्याय"). Its daśā-chapter marriage references were only sampled.

---

## Q4. Second-marriage timing rules in these texts

### Takeaway
None of these texts gives a stand-alone "time of the second marriage" algorithm. What they give is: (i) BPHS age triplets for three marriages (10/22/33); (ii) BPHS spouse-loss ages, which bound when a remarriage becomes possible; (iii) JP rules for how many wives, and which planets "destroy" or "sustain" wives; (iv) SC yogas for kalatrāntara (another wife); (v) a dharmaśāstra rule cited in UK that remarriage after a wife's death be in odd years from her death; (vi) the upapada/Dārapada second-marriage logic in UK's commentary, which is Jaimini, outside this scope.

### Cited Findings
- **BPHS ch. 18 sl. 40-41:** Moon 7th from Venus, Mercury 7th from the Moon, 8th lord in the 5th → marriages in the 10th, 22nd and 33rd years. **D**. — [BPHS ch. 18](https://archive.org/details/brihatparasarahorashastrabyr.santhanam)
- **BPHS ch. 18 sl. 35-39:** spouse-loss ages 18/33, 19, "within three days", 12/21, 13 (conditions in the Q2 table notes). **D**. — [BPHS ch. 18](https://archive.org/details/brihatparasarahorashastrabyr.santhanam)
- **JP XIV.25:** the number of wives equals "the number of planets in conjunction with Venus", omitting those in their own or exaltation sign. If the 7th lord is in the 2nd, in a sign owned by Venus, count the planets with Venus or with the 7th lord. **JP XIV.26:** weak planets conjoined with the 7th or 2nd lord that also own the 6th, 8th or 12th: "so many will be the wives to be destroyed by them". Benefic strong planets with those lords give wives "with whom the person born will live happily". A single very strong planet with the 7th or 2nd lord gives one wife. Computability: **D\***. Timing is not stated, but these rules identify the planets whose daśās would carry a loss or a remarriage (my inference). — [JP Vol II, Adh. XIV sl. 25-26, p.857-858](https://archive.org/details/JatakaParijataVolIIOfIIByVSubrahmanyaSastri)
- **JP XIV.27:** the navāṃśa of Jupiter at the Jupiter-transit point gives one wife, 2-3 wives or many (see Q3). — [JP XIV.27](https://archive.org/details/JatakaParijataVolIIOfIIByVSubrahmanyaSastri)
- **SC 7th-bhāva sl. 16-22:**
  - The 12th lord in the 7th with a malefic in the 2nd → two wives (sl. 16).
  - The 7th lord with Saturn, Mars or Rāhu, or in a krūra ṣaṣṭyaṃśa → "कलत्रमरणं वदेत्" (death of wife) (sl. 17).
  - The 7th lord in an enemy or debilitation sign aspected by a benefic, with a malefic in the 7th → "विवाहद्वयमादिशेत्" (two marriages) (sl. 18).
  - The kāraka with malefics, in a debilitation sign or navāṃśa, aspected by malefics → two marriages (sl. 19).
  - Malefic aspect or yoga on the 7th or 2nd with their lords weak → "कलत्रान्तरभाग् भवेत्" (gets another wife) (sl. 21-22).

  Computability: **D** (sl. 17 and 22 need ṣaṣṭyaṃśa). — [SC sl. 16-22](https://archive.org/details/sarvartha-chintamani-mahidhar-sharma_202210)
- **UK (P.S. Sastri), Second Kāṇḍa (dharmaśāstra material), p.~224:** "After a person loses his wife, he can remarry only in the odd years from her death. Where the remarriage takes place in even years, it is not beneficial." This is a social/muhūrta prescription, not a natal predictor. Computability: **D** given the date of death. — [UK p.224](https://archive.org/details/uttkalamrita-kalidas-ps-sastri)
- **UK commentary (P.S. Sastri, Jaimini Arudha material, p.~104):** "the Arudha of the seventh is Mina. Kuja and Rahu are in the eighth indicating the loss of wife. But as the lord of Dara-Pada is exalted, a second marriage is bound to be there." On the upapada (p.~106): "The eighth house of the upapada … refers to the second marriage". This is the Jaimini school, outside Parāśarī scope, and belongs to the commentator's case analysis. — [UK p.104-106](https://archive.org/details/uttkalamrita-kalidas-ps-sastri)
- **PD X.15:** if the 7th lord is in an inimical or debilitation sign, eclipsed, or aspected by malefics, and the 7th has malefics, "there will be loss of wife". This is a promise of loss, not its timing. — [PD Adh. X sl. 15, p.110](https://archive.org/details/Phaladeepika2ndEd.1950ByVSubrahmanyaSastri)

### Inferences
- For a second marriage, the Parāśarī texts give **promise** (JP XIV.25-26, SC sl. 16-22, BPHS sl. 19-21) and a few **fixed-age rules** (BPHS sl. 35-41). Timing would have to reuse the first-marriage machinery (daśā of the candidate set, Jupiter/Venus transit triggers) applied after the separation event. JP XIV.26's "destroying" planets (weak dusthāna lords conjoined with the 7th or 2nd lord) are the natural daśā candidates for the break, and its "sustaining" benefics for the next union. That last step is my inference, not text.

### Gaps
- No verse in BPHS, PD, JP, SC or BJ (as read) explicitly says "the second marriage occurs in the daśā of X". Saravali and UK could not be fully checked.
