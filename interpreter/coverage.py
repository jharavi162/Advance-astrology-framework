"""COVERAGE MATRIX + completeness gate.

The recurring "node miss" was a *silent* gap: the engine computed a quantity but no
witness read it, and nothing made that visible. This module is the single source of
truth — every classical technique × is-it-wired? — so a gap becomes a **RED
checklist item**, never a silent miss. Two tests keep the matrix and the live
witness panel in sync:
  • no item may CLAIM "wired" without a real witness in `build_panel` (catches drift),
  • no witness may exist that the matrix does not document (catches a new node added
    without being recorded).
And every event pack prints its own `coverage_summary()` so the AI/user SEE what is
NOT covered at the moment of committing an answer.

Status legend:
  wired       — a registered witness consumes the engine quantity.
  red         — engine COMPUTES it but no witness reads it yet (a known gap).
  interpretive— not reducible to a mechanical timing/standing vote (AI judgment).
"""

from __future__ import annotations

from dataclasses import dataclass

from interpreter.event_evidence import DOMAIN_PROFILES, build_panel


@dataclass(frozen=True)
class CoverageItem:
    technique: str
    engine: str          # the VedicChart capability that computes it
    witness: str         # substring of the wired witness name ("" if not wired)
    status: str          # "wired" | "red" | "interpretive"


# --------------------------------------------------------------------------- #
# THE MATRIX — keep in sync with the witness panel (tests enforce both ways).
# --------------------------------------------------------------------------- #
COVERAGE: list[CoverageItem] = [
    # ---- STANDING (natal promise / affliction) ---------------------------- #
    CoverageItem("Ṣaḍbala / dignity of lord", "shadbala/dignity", "house-lord-dignity", "wired"),
    CoverageItem("Benefic dṛṣṭi on house", "graha_aspects", "benefic-dṛṣṭi", "wired"),
    CoverageItem("Malefic dṛṣṭi on house", "graha_aspects", "malefic-dṛṣṭi", "wired"),
    CoverageItem("Occupant nature", "planets_in_house", "occupant-nature", "wired"),
    CoverageItem("Rāja/Dhana yoga (lord dignified in kendra/trikoṇa)", "yogas/dignity", "rāja-yoga", "wired"),
    CoverageItem("Argala / Virodhārgala", "argala", "argala-net", "wired"),
    CoverageItem("Sarvāṣṭakavarga of house", "sarvashtakavarga", "SAV-of-house", "wired"),
    CoverageItem("Avasthā moods", "avasthas", "avasthā affliction", "wired"),
    CoverageItem("Vaiśeṣikāṃśa multi-varga grade", "vaiseshikamsa/all_vargas", "Vaiśeṣikāṃśa", "wired"),
    CoverageItem("Maraka affliction", "marakas", "maraka", "wired"),
    # ---- TIMING ----------------------------------------------------------- #
    CoverageItem("Vimśottari daśā (kāraka in chain)", "current_dasha", "kāraka in MD", "wired"),
    CoverageItem("Vimśottari sūkṣma drill", "current_dasha levels=5", "kāraka at sūkṣma", "wired"),
    CoverageItem("KP cusp/period significators", "kp_significators", "KP fulfilment", "wired"),
    CoverageItem("Lagneśa in daśā", "house_lord+current_dasha", "Lagneśa in daśā", "wired"),
    CoverageItem("Jupiter+Saturn double-transit (house/lord)", "transits.double_transit_*", "double-transit (house/lord)", "wired"),
    CoverageItem("Domain Saham double-transit", "sahams", "domain Saham", "wired"),
    CoverageItem("BNN degree conjunction", "transits.conjunction_windows", "BNN", "wired"),
    CoverageItem("Kakṣyā narrowing", "transits.kakshya_windows", "Kakṣyā", "wired"),
    CoverageItem("Varṣaphal Muntha", "varshaphal", "Varṣaphal Muntha", "wired"),
    CoverageItem("Sudarśana Chakra", "sudarshana", "Sudarśana", "wired"),
    CoverageItem("Lagna materialization", "transits.transit_sign", "Lagna materialization", "wired"),
    CoverageItem("Gochara from the Moon", "transits + Moon sign", "gochara from Moon", "wired"),
    CoverageItem("Fulfilment-houses double-transit", "transits.double_transit_*", "fulfilment-houses double-transit", "wired"),
    CoverageItem("KP transit-of-significator star", "transits.positions + nakṣatra", "KP transit:", "wired"),
    CoverageItem("Tājika Varṣeśa / Muntha-lord", "varshaphal", "Tājika Varṣeśa", "wired"),
    CoverageItem("Jaimini Arudha-axis gochara", "arudhas", "Arudha-axis", "wired"),
    CoverageItem("Bhṛgu Bindu activation", "bhrigu_bindu", "Bhṛgu Bindu", "wired"),
    CoverageItem("Yoginī daśā", "dasha('yogini')", "daśā[yogini]", "wired"),
    CoverageItem("Aṣṭottarī daśā", "dasha('ashtottari')", "daśā[ashtottari]", "wired"),
    CoverageItem("Muddā (Varṣa-Vimśottari) daśā", "mudda_dasha", "daśā[muddā]", "wired"),
    CoverageItem("Chara (Jaimini rāśi) daśā", "current_chara_dasha", "daśā[chara]", "wired"),
    # ---- RED — engine computes it, NO witness reads it yet ----------------- #
    CoverageItem("Nārāyaṇa daśā", "narayana_dasha", "", "red"),
    CoverageItem("Sudasā (Śrī) daśā", "sudasa_dasha", "", "red"),
    CoverageItem("Bhāva-Chalit result-house shift", "bhava_chalit", "", "red"),
    CoverageItem("Sade-Sati / Kaṇṭaka (Saturn-from-Moon)", "transits.sade_sati", "", "red"),
    CoverageItem("Functional benefic/malefic weighting", "functional_nature", "", "red"),
    CoverageItem("Full yoga-engine mapping (beyond rāja-yoga)", "yogas", "", "red"),
    CoverageItem("Bhinnāṣṭakavarga of house/lord", "bhinnashtakavarga", "", "red"),
    CoverageItem("Indu Lagna / special lagnas", "special_lagnas/indu_lagna", "", "red"),
    CoverageItem("Karakāṃśa (AK in D9)", "karakamsha", "", "red"),
    CoverageItem("Kala-vela upagrahas (Dhūma/Vyatīpāta…)", "calculated_upagrahas", "", "red"),
    # ---- INTERPRETIVE — not a mechanical vote (AI judgment) --------------- #
    CoverageItem("Pañcāṅga subtleties", "panchanga", "", "interpretive"),
    CoverageItem("Compatibility / synastry", "compatibility", "", "interpretive"),
]


def wired_items() -> list[CoverageItem]:
    return [i for i in COVERAGE if i.status == "wired"]


def red_items() -> list[CoverageItem]:
    return [i for i in COVERAGE if i.status == "red"]


def interpretive_items() -> list[CoverageItem]:
    return [i for i in COVERAGE if i.status == "interpretive"]


def panel_witness_names(domain: str = "marriage") -> list[str]:
    return [w.name for w in build_panel(DOMAIN_PROFILES[domain])]


def audit() -> dict:
    """Cross-check the matrix against the live panel (both directions)."""
    names = panel_witness_names()
    claims_without_witness = [
        i.technique for i in wired_items()
        if not any(i.witness in n for n in names)]
    wired_substr = [i.witness for i in wired_items()]
    witnesses_not_in_matrix = [
        n for n in names if not any(s and s in n for s in wired_substr)]
    return {"claims_without_witness": claims_without_witness,
            "witnesses_not_in_matrix": witnesses_not_in_matrix}


def coverage_summary() -> str:
    w, r, ip = len(wired_items()), len(red_items()), len(interpretive_items())
    gaps = ", ".join(i.technique for i in red_items())
    return (f"  COVERAGE: {w} wired · {ip} interpretive · {r} RED gaps "
            f"(not yet wired — read multivalently): {gaps}")
