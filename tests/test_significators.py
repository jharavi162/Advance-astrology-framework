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


def test_unknown_word_derives_from_house_significations():
    # 'scandal' is not curated, but the 8th-house significations catch it
    prof = resolve("scandal")
    assert 8 in prof.houses
    assert prof.fulfil_houses and prof.negate_houses


def test_unmappable_word_raises():
    import pytest
    with pytest.raises(ValueError):
        resolve("qwertyzxcv")
