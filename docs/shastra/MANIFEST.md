# Śāstra reference library — MANIFEST

Canonical primary sources per school, so every engine node / pattern claim can be
checked against the text itself (CLAUDE.md: "name the classical source for each").

**Storage split:** PDFs live in the owner's Google Drive folder (`astro-shastra/`),
NOT in git (size + copyright). This manifest is the index; when a rule needs
verification, read the PDF from Drive via the Google Drive connector. Small
public-domain text extracts may be added under `docs/shastra/extracts/`.

**Environment note (2026-07-08):** this repo's remote-execution egress policy
blocks archive.org/sacred-texts/wisdomlib downloads, so the PDFs must be
downloaded by the owner and uploaded to Drive. Links below are verified.

## Tier 1 — public domain, download from archive.org → Drive

| # | Text (school) | Edition to get | Link |
|---|---|---|---|
| 1 | **Bṛhat Jātaka** — Varāhamihira (classical natal) | trans. N. Chidambaram Iyer, 1885, Foster Press Madras | [archive.org/details/wg1079](https://archive.org/details/wg1079) (alt: [brihatjatakavar00iyergoog](https://archive.org/details/brihatjatakavar00iyergoog)) |
| 2 | **Bṛhat Saṁhitā** — Varāhamihira (saṁhitā/omens/transits) | trans. N. Chidambaram Iyer, 1884 | [archive.org/details/bihatsahitvarah00iyergoog](https://archive.org/details/bihatsahitvarah00iyergoog) |
| 3 | **Jaimini Sūtram** (Jaimini school: kārakas, arudhas, rāśi daśās) | trans. B. Suryanarain Rao, 1955 5th ed. (rev. B.V. Raman) | [archive.org/details/Jaiminisutras1955EditionByBSRao](https://archive.org/details/Jaiminisutras1955EditionByBSRao) (alt: [in.ernet.dli.2015.486584](https://archive.org/details/in.ernet.dli.2015.486584)) |
| 4 | **Bṛhat Jātaka** (2nd trans., fuller notes) | trans. V. Subrahmanya Sastri, 2nd ed. | [archive.org/details/BrihatJataka2ndEd.ByVSubrahmanyaSastri](https://archive.org/details/BrihatJataka2ndEd.ByVSubrahmanyaSastri) |
| 5 | **Phaladīpikā** — Mantreśvara (Parāśari phala + kāraka doctrine) | trans. V. Subrahmanya Sastri, 1937 | archive.org search: `Phaladeepika Subrahmanya Sastri` |
| 6 | **Jātaka Pārijāta** — Vaidyanātha Dīkṣita | trans. V. Subrahmanya Sastri (3 vols) | archive.org search: `Jataka Parijata Subrahmanya Sastri` |
| 7 | **Uttara Kālāmṛta** — Kālidāsa (significations tables) | trans. V. Subrahmanya Sastri | archive.org search: `Uttara Kalamrita Sastri` |
| 8 | **Bṛhat Pārāśara Horā Śāstra** (Sanskrit mūla) | Sanskrit ed. (Khemraj/Venkateshwar or DLI scan) | archive.org search: `Brihat Parashara Hora Sastra sanskrit` |
| 9 | **Sārāvalī** — Kalyāṇavarman (Sanskrit mūla) | Sanskrit ed. (DLI scan) | archive.org search: `Saravali Kalyanavarman sanskrit` |
| 10 | **Tājika Nīlakaṇṭhī** — Nīlakaṇṭha (Tājika/varṣaphala, sahams) | Sanskrit/Hindi ed. (DLI scan) | archive.org search: `Tajika Nilakanthi` |
| 11 | **Muhūrta Cintāmaṇi** — Rāma Daivajña (electional) | Sanskrit/Hindi ed. (DLI scan) | archive.org search: `Muhurta Chintamani` |

## Tier 2 — in copyright: buy/consult print, do NOT store in git or shared Drive

| Text | Why we need it | Status |
|---|---|---|
| **BPHS** trans. R. Santhanam (Ranjan, 1984, 2 vols) | the working English BPHS (daśā-phala, varga rules) | © — print |
| **Sārāvalī** trans. R. Santhanam | English Sārāvalī | © — print |
| **KP Readers I–VI** — K.S. Krishnamurti | sub-lord theory, 2-7-11 significators, transit rule (our N5 channel) | © — print |
| **Bhrigu Nandi Nadi** — R.G. Rao | BNN kāraka doctrine (Venus♂/Mars♀, Guru-jeeva) | © — print |
| **Praśna Mārga** trans. B.V. Raman | praśna + timing | © — print |
| **Jaimini Maharishi's Upadesa Sutras** — Sanjay Rath | UL/A7 double-transit doctrine (our Arudha-dt node) | © — print |
| **Predicting Marriage** — K.N. Rao school | marriage-timing case method | © — print |

## Workflow

1. Owner downloads Tier-1 PDFs (links above) → uploads to Drive folder `astro-shastra/`.
2. Enable the **Google Drive connector** for the Claude chat/session
   (it is installed for the org but must be toggled on per chat).
3. During analysis, the AI reads the needed chapter from Drive before wiring or
   asserting any rule; the citation (text + chapter/śloka) goes into
   `docs/RULE_CHANGELOG.md` as usual.
4. Public-domain extracts that get used repeatedly may be saved as markdown under
   `docs/shastra/extracts/<text>/<chapter>.md` (small, greppable, in git).
