"""Coverage matrix + completeness gate — keeps the matrix and the live witness
panel in sync, so a 'node miss' becomes a visible RED item, never silent."""

from interpreter.coverage import (
    COVERAGE, audit, coverage_summary, red_items, wired_items,
)


def test_every_wired_claim_has_a_live_witness():
    """A matrix item that CLAIMS 'wired' must map to a real witness in the panel
    (catches drift — a renamed/removed witness breaks the claim loudly)."""
    problems = audit()["claims_without_witness"]
    assert not problems, f"wired claims with no witness: {problems}"


def test_every_witness_is_documented_in_the_matrix():
    """The reverse guard — no witness may exist that the matrix does not record.
    Adding a node without a matrix entry FAILS here, so gaps can't go silent."""
    problems = audit()["witnesses_not_in_matrix"]
    assert not problems, f"witnesses missing from COVERAGE matrix: {problems}"


def test_matrix_statuses_are_valid_and_red_is_acknowledged():
    for item in COVERAGE:
        assert item.status in {"wired", "red", "interpretive"}
        if item.status == "wired":
            assert item.witness, f"{item.technique}: wired but no witness substring"
    # the known gaps are explicitly listed (acknowledged, not forgotten)
    assert red_items(), "expected the audit to record some RED gaps"


def test_coverage_summary_names_the_red_gaps():
    s = coverage_summary()
    assert "COVERAGE" in s and "RED" in s
    # a couple of the known gaps must be named so they're visible in every pack
    assert "Nārāyaṇa daśā" in s
    assert "Bhāva-Chalit" in s or "Sade-Sati" in s
