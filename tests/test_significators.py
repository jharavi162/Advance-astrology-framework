"""Phase 2 — significator dictionary: pick a domain from any theme word."""

from advance_astrology import Planet
from interpreter.event_evidence import DOMAIN_PROFILES, build_panel
from interpreter.significators import THEME_LEXICON, resolve


def test_synonyms_resolve_to_seeded_domains():
    # Hindi/Hinglish + English synonyms map onto the curated seeded domains
    assert resolve("shaadi").name == "marriage"
    assert resolve("vivah").name == "marriage"
    assert resolve("naukri").name == "career"
    assert resolve("santaan").name == "children"
    assert resolve("videsh").name == "foreign"
    assert resolve("vahan").name == "vehicle"


def test_lexicon_theme_builds_a_full_profile():
    prof = resolve("gaadi")                      # vehicle
    assert prof.name == "vehicle"
    assert prof.houses == (4,)
    assert prof.natural_karaka == Planet.VENUS
    assert prof.varga == 16
    # registered, so the generative panel judges it like any other matter
    assert "vehicle" in DOMAIN_PROFILES
    assert build_panel(prof)


def test_every_lexicon_theme_is_resolvable_and_complete():
    for canon, spec in THEME_LEXICON.items():
        prof = resolve(canon)
        assert prof.houses, f"{canon} has no houses"
        assert prof.fulfil_houses, f"{canon} has no fulfilment houses"
        assert prof.negate_houses, f"{canon} has no negation houses"
        assert 1 <= prof.varga <= 60


def test_divorce_domain_resolves_with_kp_groups():
    # Divorce fulfils on the marriage-negation group and is denied by the
    # marriage-sustenance group (KP), with Saturn as the separative karaka.
    for q in ("divorce", "talaq", "divorce hua ya nahi", "rishta toota kya"):
        prof = resolve(q)
        assert prof.name == "divorce", q
    prof = resolve("divorce")
    assert set(prof.fulfil_houses) == {1, 6, 10}
    assert set(prof.negate_houses) == {2, 7, 11}
    assert prof.natural_karaka == Planet.SATURN
    assert "UL" in prof.arudhas and prof.varga == 9


def test_freeform_question_matches_words_not_substrings():
    # A full-sentence question resolves on word boundaries: "career" must NOT be
    # mis-mapped to vehicle via the substring "car", and the right domain wins.
    assert resolve("career kaisa rahega").name == "career"
    assert resolve("is native ki shaadi kab hui").name == "marriage"
    assert resolve("property kab milegi").name == "property"


def test_unknown_word_derives_from_house_significations():
    # 'scandal' is not curated, but the 8th-house significations catch it
    prof = resolve("scandal")
    assert 8 in prof.houses
    assert prof.fulfil_houses and prof.negate_houses


def test_unmappable_word_raises():
    import pytest
    with pytest.raises(ValueError):
        resolve("qwertyzxcv")
