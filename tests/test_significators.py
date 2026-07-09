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


def test_engagement_domain_reads_courtship_group_not_marriage_group():
    # Engagement = the PROMISE of marriage. KP reads it on the 5-7-11 courtship/
    # agreement group (5th love-affair that ripens, 7th partner, 11th desire
    # secured) and denies it with the union-dusthānas 6-8-12 — deliberately NOT
    # the 1/6/10 marriage-negation set, so an engagement is not falsely negated
    # by a concurrent divorce (whose fulfilment houses ARE 1/6/10).
    for q in ("engagement", "sagai", "mangni", "roka", "betrothal"):
        assert resolve(q).name == "engagement", q
    prof = resolve("engagement")
    assert set(prof.fulfil_houses) == {5, 7, 11}
    assert set(prof.negate_houses) == {6, 8, 12}
    assert prof.natural_karaka == Planet.VENUS
    assert prof.base_domain == "marriage" and prof.varga == 9
    # the distinguishing 5th (courtship) is present, and it does NOT collide with
    # the divorce fulfilment axis (1/6/10) the way the plain marriage meter does.
    assert 5 in prof.fulfil_houses
    assert not (set(prof.negate_houses) & {1, 10})
    marriage = resolve("marriage")
    assert set(prof.fulfil_houses) != set(marriage.fulfil_houses)
    assert build_panel(prof)


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


def test_ordinal_meta_rule_shifts_by_third_from_previous():
    # 2nd spouse = 9th (7 + 2), 3rd = 11th; generic serial rule: 2nd child = 7th.
    m2 = resolve("second marriage")
    assert m2.houses == (9,) and m2.base_domain == "marriage"
    assert m2.natural_karaka == Planet.VENUS and m2.varga == 9
    assert resolve("dusri shaadi").houses == (9,)
    assert resolve("teesri shaadi").houses == (11,)          # 7 + 4
    assert resolve("doosra bachcha").houses == (7,)          # children 5 + 2
    # a bare 'doosri partner' still lands on the marriage axis (not a stray house)
    dp = resolve("doosri partner life me kya aa chuki h")
    assert dp.houses == (9,) and dp.natural_karaka == Planet.VENUS
    # a plain (1st) matter is NOT shifted
    assert resolve("meri shaadi kab hui").houses == (7,)
    assert resolve("career kaisa rahega").houses == (10,)


def test_second_marriage_nadi_karaka_is_gender_aware():
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from advance_astrology import VedicChart
    from interpreter.event_evidence import nadi_karaka
    v = VedicChart.create(
        when=datetime(1991, 4, 4, 6, 23, tzinfo=ZoneInfo("Asia/Kolkata")),
        latitude=23.63, longitude=85.52, ayanamsa="lahiri")
    prof = resolve("second marriage")
    v.gender = "male"
    assert nadi_karaka(v, prof) == Planet.VENUS
    v.gender = "female"
    assert nadi_karaka(v, prof) == Planet.MARS
