"""Regression tests for the domain-general event-evidence builder."""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from advance_astrology import VedicChart
from interpreter.event_evidence import (
    DASHA_SYSTEMS, DOMAIN_PROFILES, FAMILIES, WITNESSES, Witness, WindowEvidence,
    _paddhati, _score_rows, build_panel, candidate_map, register_witness,
    render_domain, reversal_map, scan_domains, standing_balance,
)

UTC = timezone.utc


def _chart():
    return VedicChart.create(
        when=datetime(1991, 4, 4, 6, 23, tzinfo=ZoneInfo("Asia/Kolkata")),
        latitude=23.63, longitude=85.52, ayanamsa="lahiri")


def test_every_domain_builds_without_error():
    v = _chart()
    start = datetime(2024, 1, 1, tzinfo=UTC)
    end = datetime(2025, 1, 1, tzinfo=UTC)
    for name, profile in DOMAIN_PROFILES.items():
        rows = candidate_map(v, profile, start, end)
        assert rows, f"{name} produced no candidate windows"
        for r in rows:
            assert r.domain_score >= 0
            assert r.domain_score <= r.convergence + 1e-9  # shared Lagna node only adds


def test_marriage_band_is_lit_around_known_wedding():
    """Jan-2024 wedding must fall inside a Lagna-materialised, lord-double-transit
    band — the engine should bound the right ~12-month window."""
    v = _chart()
    rows = candidate_map(v, DOMAIN_PROFILES["marriage"],
                         datetime(2023, 6, 1, tzinfo=UTC),
                         datetime(2024, 5, 1, tzinfo=UTC))
    around = [r for r in rows if datetime(2023, 8, 1, tzinfo=UTC) <= r.start
              <= datetime(2024, 3, 1, tzinfo=UTC)]
    assert around, "no rows around the wedding band"
    # Lagna double-activated and the 7th-lord under double transit through the band
    assert all(r.lagna_activators for r in around)
    assert any(r.lord_double_transit for r in around)


def test_remarriage_caught_despite_dark_lagna():
    """The Jan-2027 court remarriage has a dark Lagna (low-key) but must still
    surface via the Venus stack / Saham / Sudarśana — domain_score >= 3."""
    v = _chart()
    rows = candidate_map(v, DOMAIN_PROFILES["marriage"],
                         datetime(2027, 1, 1, tzinfo=UTC),
                         datetime(2027, 3, 1, tzinfo=UTC))
    # the wedding PD is the Venus stack (Ve>Ra>Ve) opening late January
    venus_pd = [r for r in rows if r.chain[2] == "Ve"]
    assert venus_pd, "Venus pratyantar (the remarriage trigger) not found"
    best = max(venus_pd, key=lambda r: r.domain_score)
    assert best.domain_score >= 3
    assert best.karaka_sukshma  # Venus also surfacing at sūkṣma


def test_career_dusthana_is_change_not_loss():
    """This native NEVER had a job loss/break — only changes upward. A
    6/8/12-from-10th activation must classify as CHANGE/UPGRADE (fulfilment
    co-occurs), never a pure LOSS/BREAK."""
    v = _chart()
    rev = reversal_map(v, DOMAIN_PROFILES["career"],
                       datetime(2019, 1, 1, tzinfo=UTC),
                       datetime(2024, 12, 31, tzinfo=UTC))
    assert not [r for r in rev if r.kind == "LOSS/BREAK"], \
        "career wrongly flagged a loss — there was none"
    assert [r for r in rev if r.kind == "CHANGE/UPGRADE"], \
        "the 2021-22 upward job-change should register as CHANGE/UPGRADE"


def test_marriage_divorce_is_loss_remarriage_is_change():
    """The Feb-2026 divorce is a genuine LOSS/BREAK; the Jan-2027 remarriage is a
    CHANGE/UPGRADE — judged from the timing (AD/PD) lords, not the standing MD."""
    v = _chart()
    rev = reversal_map(v, DOMAIN_PROFILES["marriage"],
                       datetime(2025, 1, 1, tzinfo=UTC),
                       datetime(2027, 3, 1, tzinfo=UTC))
    losses = [r for r in rev if r.kind == "LOSS/BREAK"]
    assert any(r.start.year == 2026 or (r.start.year == 2025 and r.start.month >= 8)
               for r in losses), "the divorce window must surface as LOSS/BREAK"
    jan27 = [r for r in rev if r.start.year == 2027 and r.start.month == 1]
    assert jan27 and any(r.kind == "CHANGE/UPGRADE" for r in jan27), \
        "the remarriage must surface as CHANGE/UPGRADE, not loss"


def test_standing_witness_pattern_is_multinodal():
    """Loss-vs-upgrade must be a multi-nodal NATAL pattern, not dasha alone. The
    career house is natally blessed (exalted Jupiter aspects the 10th, Śaśa
    rāja-yoga, strong lord) ⇒ strongly PRO; marriage is more afflicted ⇒ lower."""
    v = _chart()
    career, _ = standing_balance(v, DOMAIN_PROFILES["career"])
    marriage, fired = standing_balance(v, DOMAIN_PROFILES["marriage"])
    assert career >= 1.0, "blessed career house should read PRO/upgrade"
    assert career > marriage, "career should out-bless marriage natally"
    # the benefic-dṛṣṭi node (Jupiter aspecting the 10th) must be among the firing
    cnames = [n for n, _ in standing_balance(v, DOMAIN_PROFILES["career"])[1]]
    assert any("benefic-dṛṣṭi" in n for n in cnames)


def test_dasha_is_just_one_node_among_timing_witnesses():
    """The daśā must be ONE node among the timing witnesses, not a privileged
    scorer — its votes flow through the same registry as transit/KP/Lagna/etc."""
    timing = [w for w in WITNESSES if w.layer == "timing"]
    names = [w.name for w in timing]
    assert any("daśā" in n for n in names), "daśā must be a registered timing node"
    assert len(timing) >= 8, "timing should be a panel of many nodes, not just daśā"
    # and the window score is the convergence of those nodes (daśā not special)
    v = _chart()
    rows = candidate_map(v, DOMAIN_PROFILES["marriage"],
                         datetime(2023, 8, 1, tzinfo=UTC),
                         datetime(2023, 10, 1, tzinfo=UTC))
    assert rows and isinstance(rows[0].firing_nodes(), list)


def test_witness_registry_is_dynamic():
    """A new node = one register_witness() call (no logic rewrite)."""
    before = len(WITNESSES)
    register_witness("unit-test-node", "standing", 0.1, lambda v, p: 0.0)
    try:
        assert len(WITNESSES) == before + 1
    finally:
        WITNESSES.pop()  # keep global state clean for other tests


def test_new_timing_nodes_registered_and_computed():
    """The four user-approved nodes (gochara-from-Moon, fulfilment-house
    double-transit, KP star-transit, Tājika Varṣeśa/Muntha) must be registered
    timing witnesses and populated on every candidate window."""
    names = [w.name for w in WITNESSES if w.layer == "timing"]
    for needle in ("gochara from Moon", "fulfilment-houses double-transit",
                   "KP transit:", "Tājika Varṣeśa/Muntha"):
        assert any(needle in n for n in names), f"missing node: {needle}"
    v = _chart()
    rows = candidate_map(v, DOMAIN_PROFILES["relocation"],
                         datetime(2024, 5, 1, tzinfo=UTC),
                         datetime(2025, 2, 1, tzinfo=UTC))
    assert rows
    for r in rows:  # every new field is a real bool, computed (not left None)
        assert isinstance(r.gochara_from_moon, bool)
        assert isinstance(r.fulfil_house_dt, bool)
        assert isinstance(r.kp_star_transit, bool)
        assert isinstance(r.tajika_sig, bool)
    # nodes that fire in this relocation band (not dead code)
    assert any(r.fulfil_house_dt for r in rows)
    assert any(r.kp_star_transit for r in rows)
    # gochara-FROM-MOON (Janma-rāśi double-transit) fires in a confirmed window —
    # marriage 7th-from-Moon gets the Jup+Sat joint hit Aug-2016..Jan-2017
    mrows = candidate_map(v, DOMAIN_PROFILES["marriage"],
                          datetime(2016, 8, 1, tzinfo=UTC),
                          datetime(2016, 12, 1, tzinfo=UTC))
    assert any(r.gochara_from_moon for r in mrows)


def test_generative_dasha_family_is_data_driven():
    """Slice 2: the daśā-system catalogue is a generative FAMILY — build_panel
    adds one node per catalogue system on top of the static WITNESSES, and adding
    a system is pure data (one DASHA_SYSTEMS entry), no node hand-registration."""
    assert FAMILIES, "no witness families registered"
    prof = DOMAIN_PROFILES["relocation"]
    panel = build_panel(prof)
    # every static witness is still present, plus one node per catalogue system
    assert len(panel) == len(WITNESSES) + len(DASHA_SYSTEMS)
    pnames = [w.name for w in panel]
    for sysname in DASHA_SYSTEMS:
        assert any(f"daśā[{sysname}]" in n for n in pnames), f"no node for {sysname}"
    # adding a system is data-only: build_panel grows by exactly one, no code change
    import interpreter.event_evidence as ee
    ee._PANEL_CACHE.clear()
    DASHA_SYSTEMS["__unit_test__"] = ee._ring_system("vimshottari")
    try:
        assert len(build_panel(prof)) == len(WITNESSES) + len(DASHA_SYSTEMS)
    finally:
        DASHA_SYSTEMS.pop("__unit_test__")
        ee._PANEL_CACHE.clear()


def test_window_scores_use_the_full_panel_including_families():
    """The per-window scoring must iterate the domain's full panel (families
    included), and the catalogue signals must be computed on each window."""
    v = _chart()
    rows = candidate_map(v, DOMAIN_PROFILES["relocation"],
                         datetime(2024, 5, 1, tzinfo=UTC),
                         datetime(2025, 2, 1, tzinfo=UTC))
    assert rows
    for r in rows:
        assert r.panel is not None and len(r.panel) == len(WITNESSES) + len(DASHA_SYSTEMS)
        # one signal per catalogue system, each a 0/1 float
        assert set(r.signals) == {f"dasha::{n}" for n in DASHA_SYSTEMS}
        # slices 3+4: every row scored with salience + independent-system count
        assert isinstance(r.salience, float) and isinstance(r.systems_firing, int)
    # the generated daśā nodes actually fire somewhere (not dead code) and show up
    # among the firing nodes of some window
    fired = {n for r in rows for n, _ in r.firing_nodes()}
    assert any("daśā[" in n for n in fired)


def test_arudha_axis_node_registered_and_independent_paddhati():
    """Jaimini Arudha-axis gochara (the previously computed-but-UNWIRED Upapada
    axis) is now a registered, domain-general timing node and an INDEPENDENT
    paddhati. MECHANICAL test only — asserts the node exists, computes, fires when
    the slow movers touch the axis, and is its own system. No date is asserted
    (that would be calibration)."""
    names = [w.name for w in WITNESSES if w.layer == "timing"]
    assert any("Arudha-axis" in n for n in names), "Arudha-axis node not registered"
    assert _paddhati("Jaimini Arudha-axis activation (UL / 2nd-from-Arudha)") == "jaimini"
    v = _chart()
    # 2016-08..2017-01: Jupiter+Saturn work the marriage UL-axis (Scorpio/Sagittarius)
    rows = candidate_map(v, DOMAIN_PROFILES["marriage"],
                         datetime(2016, 8, 1, tzinfo=UTC),
                         datetime(2017, 2, 1, tzinfo=UTC))
    assert rows
    for r in rows:
        assert isinstance(r.arudha_axis, bool)        # computed, not left None
    assert any(r.arudha_axis for r in rows)           # fires (not dead code)


def test_newly_wired_computed_quantities_are_nodes():
    """Coverage: quantities the engine computed but no witness READ are now wired.
    MECHANICAL — registered + compute + (for the standing affliction ones) behave
    sensibly; no native's date is asserted."""
    snames = [w.name for w in WITNESSES if w.layer == "standing"]
    tnames = [w.name for w in WITNESSES if w.layer == "timing"]
    for needle in ("avasthā affliction", "Vaiśeṣikāṃśa", "maraka"):
        assert any(needle in n for n in snames), f"standing node missing: {needle}"
    assert any("Bhṛgu Bindu" in n for n in tnames)
    assert _paddhati("Bhṛgu Bindu activation (Nāḍī)") == "nadi"
    v = _chart()
    # maraka node is scoped to adverse-longevity matters (primary 6/8) only
    from interpreter.event_evidence import _w_maraka
    assert _w_maraka(v, DOMAIN_PROFILES["career"]) == 0.0      # not a 6/8 matter
    rows = candidate_map(v, DOMAIN_PROFILES["marriage"],
                         datetime(2016, 8, 1, tzinfo=UTC),
                         datetime(2017, 2, 1, tzinfo=UTC))
    assert rows and all(isinstance(r.bb_active, bool) for r in rows)


def test_kp_nodes_use_kp_ayanamsa_and_placidus_cusps():
    """KP must be judged on the Krishnamurti ayanāṃśa with Placidus cusps, NOT the
    main Lahiri/whole-sign chart. MECHANICAL — verifies the KP sub-chart differs in
    ayanāṃśa, is cached, and the cusp sub-lord is read from a real Placidus cusp."""
    from interpreter.event_evidence import _kp_view
    v = _chart()                                   # built with Lahiri
    vkp, kps = _kp_view(v)
    assert abs(vkp.ayanamsa - v.ayanamsa) > 0.05   # KP ayanāṃśa ≠ Lahiri (~8 arc-min)
    assert _kp_view(v)[0] is vkp                    # cached per native
    assert set(kps.cusps) == set(range(1, 13))      # true Placidus cusp dict 1..12


def test_decision_rule_convergence_gate_and_information_weighting():
    """Slices 3+4: salience = info-weighted votes grouped by independent paddhati,
    gated on ≥2 systems converging — NOT a flat sum."""
    assert _paddhati("daśā[yogini]: significator running") == "dasha"
    assert _paddhati("KP fulfilment ≥ negation") == "kp"
    assert _paddhati("double-transit (house/lord)") == "gochara"

    w_dasha = Witness("daśā[x]: significator running", "timing", 1.0,
                      lambda w: 1.0 if w.signals.get("a") else 0.0)
    w_kp = Witness("KP fulfilment ≥ negation", "timing", 1.0,
                   lambda w: 1.0 if w.signals.get("b") else 0.0)
    panel = [w_dasha, w_kp]

    def mk(sig):
        we = WindowEvidence(
            start=datetime(2024, 1, 1, tzinfo=UTC), chain=["Ve"], kp_fulfil=0,
            kp_negate=0, karaka_in_chain=False, karaka_sukshma=False,
            lagnesh_in_chain=False, lagna_activators=[], house_double_transit=False,
            lord_double_transit=False, saham_double_transit=False, bnn=False,
            kakshya=False, varshaphal_muntha=False, chara_ad="",
            sudarshana_hit=False, signals=sig)
        we.panel = panel
        return we

    both, one = mk({"a": 1, "b": 1}), mk({"a": 1, "b": 0})
    _score_rows([both, one])
    # convergence gate: two independent systems firing vs one
    assert both.systems_firing == 2 and one.systems_firing == 1
    assert both.salience > one.salience
    # information-weighting: w_dasha fires in BOTH rows (base-rate 1.0 ⇒ weight 0),
    # so the single-system row is gated to ~0 — a ubiquitous node carries no signal
    assert one.salience == 0.0


def test_render_and_scan_are_strings():
    v = _chart()
    s = datetime(2024, 1, 1, tzinfo=UTC)
    e = datetime(2024, 6, 1, tzinfo=UTC)
    assert "EVENT-EVIDENCE PACK" in render_domain(v, DOMAIN_PROFILES["career"], s, e)
    assert "MACRO-SCAN" in scan_domains(v, s, e)
