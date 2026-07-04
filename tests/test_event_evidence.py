"""Regression tests for the domain-general event-evidence builder."""

from datetime import datetime, timedelta, timezone
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


def test_reversal_kind_is_mechanical_change_vs_loss():
    """The reversal classifier is a pure function of the witness counts — NOT tied
    to any native's known dates: rupture lit + fulfilment (or a blessed standing) ⇒
    CHANGE/UPGRADE; rupture lit + fulfilment absent + dark Lagna + non-positive
    standing ⇒ LOSS/BREAK."""
    from interpreter.event_evidence import ReversalRow
    base = dict(start=datetime(2020, 1, 1, tzinfo=UTC), chain=["Ve", "Ra", "Ve"],
                separators_running=True, break_house_dt=True, reversal_saham_dt=False)
    upgrade = ReversalRow(kp_rupture=2, lagna_dark_with_malefic=False,
                          kp_fulfil=2, standing=0.0, **base)
    loss = ReversalRow(kp_rupture=3, lagna_dark_with_malefic=True,
                       kp_fulfil=0, standing=-0.4, **base)
    assert upgrade.kind == "CHANGE/UPGRADE"
    assert loss.kind == "LOSS/BREAK"


def test_blessed_house_dusthana_classifies_as_change_not_loss():
    """A natally BLESSED house (benefic dṛṣṭi + dignified lord + rāja-yoga) should
    classify a 6/8/12-from-house activation as CHANGE/UPGRADE, never a pure
    LOSS/BREAK — the principle, demonstrated on the (blessed) career house. No
    native event-date is asserted."""
    v = _chart()
    rev = reversal_map(v, DOMAIN_PROFILES["career"],
                       datetime(2019, 1, 1, tzinfo=UTC),
                       datetime(2024, 12, 31, tzinfo=UTC))
    assert not [r for r in rev if r.kind == "LOSS/BREAK"]
    assert [r for r in rev if r.kind == "CHANGE/UPGRADE"]


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
    # liveness needs a band wide enough that the deterministic pratyantar
    # midpoints intersect the nodes' activation windows
    rows = candidate_map(v, DOMAIN_PROFILES["relocation"],
                         datetime(2023, 1, 1, tzinfo=UTC),
                         datetime(2025, 6, 1, tzinfo=UTC))
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
    # liveness needs a band wide enough that the deterministic pratyantar
    # midpoints intersect the nodes' activation windows
    rows = candidate_map(v, DOMAIN_PROFILES["relocation"],
                         datetime(2023, 1, 1, tzinfo=UTC),
                         datetime(2025, 6, 1, tzinfo=UTC))
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


# --- outcome-precision witnesses (approved 2026-07-02) ----------------------- #
def test_outcome_witnesses_registered_and_bounded():
    names = {w.name for w in WITNESSES}
    assert "2nd-from-Arudha sustenance (Jaimini)" in names
    assert "vakri (retrograde) significator" in names
    assert "daśā-lord functional valence (Laghu Pārāśarī)" in names
    v = _chart()
    for w in WITNESSES:
        if w.layer != "standing":
            continue
        if "Arudha sustenance" in w.name or "vakri" in w.name:
            for prof in DOMAIN_PROFILES.values():
                val = w.vote(v, prof)
                assert -1.0 <= val <= 1.0, f"{w.name}/{prof.name} out of range"


def test_arudha_sustenance_needs_arudhas():
    # A profile without arudhas must vote 0 (no fabricated testimony).
    v = _chart()
    w = next(x for x in WITNESSES if "Arudha sustenance" in x.name)
    prof = next((p for p in DOMAIN_PROFILES.values() if not p.arudhas), None)
    if prof is not None:
        assert w.vote(v, prof) == 0.0


def test_vakri_witness_never_positive():
    # Retrogradation is a reversal/friction texture — the vote is 0 or negative.
    v = _chart()
    w = next(x for x in WITNESSES if "vakri" in x.name)
    for prof in DOMAIN_PROFILES.values():
        assert w.vote(v, prof) <= 0.0


def test_functional_valence_flows_into_windows():
    # candidate_map sets a signed func_valence in [-1, 1] on every window, and the
    # timing witness surfaces it in the ledger (sign = outcome direction).
    v = _chart()
    rows = candidate_map(v, DOMAIN_PROFILES["career"],
                         datetime(2024, 1, 1, tzinfo=UTC),
                         datetime(2025, 1, 1, tzinfo=UTC), step_days=45)
    assert rows
    assert all(-1.0 <= r.func_valence <= 1.0 for r in rows)
    w = next(x for x in WITNESSES if "functional valence" in x.name)
    for r in rows:
        assert w.vote(r) == r.func_valence
    # the node groups inside the dasha paddhati (not a fake independent system)
    assert _paddhati(w.name) == "dasha"


def test_domain_verdict_follows_the_decision_rule():
    """The verdict layer is a deterministic function of promise/denial + elapsed
    convergence windows — verify the RULE, not a hardcoded outcome."""
    from interpreter.event_evidence import domain_verdict, promise_and_tempo
    v = _chart()
    start = datetime(2023, 7, 1, tzinfo=UTC)
    end = datetime(2026, 7, 1, tzinfo=UTC)
    asof = end
    for name in ("marriage", "career"):
        prof = DOMAIN_PROFILES[name]
        rows = candidate_map(v, prof, start, end, step_days=45)
        vd = domain_verdict(v, prof, rows, asof)
        # SIMPLE verdict vocabulary (user rollback 2026-07-04): no completion
        # grades — attempted/contested language must never come back.
        assert vd.answer in ("YES", "NO (denied)", "NOT-YET", "UNCERTAIN")
        assert vd.confidence in ("HIGH", "MEDIUM", "LOW")
        pt = promise_and_tempo(v, prof)
        elapsed = [r for r in rows
                   if (asof - r.start).days >= 30 and r.systems_firing >= 2]
        if pt.promised and elapsed:
            best = max(elapsed, key=lambda r: r.salience)
            assert vd.answer == "YES"
            assert vd.best_window == f"{best.start:%Y-%m-%d}"
        # quality is stated but never used to flip existence
        assert "quality" not in vd.answer


def test_domain_verdict_not_yet_when_nothing_elapsed():
    from interpreter.event_evidence import domain_verdict, promise_and_tempo
    v = _chart()
    prof = DOMAIN_PROFILES["marriage"]
    rows = candidate_map(v, prof, datetime(2027, 1, 1, tzinfo=UTC),
                         datetime(2028, 1, 1, tzinfo=UTC), step_days=45)
    # asof BEFORE the scanned span: nothing has elapsed
    vd = domain_verdict(v, prof, rows, datetime(2026, 1, 1, tzinfo=UTC))
    if promise_and_tempo(v, prof).promised:
        assert vd.answer == "NOT-YET"


def test_rupture_matter_verdict_uses_reversal_timer():
    """Divorce-class domains time the BREAK with reversal rows, not the
    axis-fulfilment scan (which also spikes for the union itself)."""
    from interpreter.event_evidence import domain_verdict, promise_and_tempo
    from interpreter.significators import resolve
    v = _chart()
    prof = resolve("divorce")
    assert prof.rupture_matter and prof.base_domain == "marriage"
    start = datetime(2022, 1, 1, tzinfo=UTC)
    end = datetime(2026, 7, 1, tzinfo=UTC)
    # the break is timed by the UNDERLYING matter's reversal (marriage), so the
    # rupture profile's inverted KP groups can't double-invert the semantics
    rrows = reversal_map(v, DOMAIN_PROFILES[prof.base_domain], start, end,
                         step_days=45)
    vd = domain_verdict(v, prof, [], end, rrows=rrows)
    pt = promise_and_tempo(v, prof)
    hits = [r for r in rrows
            if (end - r.start).days >= 30 and r.kind == "LOSS/BREAK"]
    if pt.promised and hits:
        assert vd.answer == "YES"
        best = max(hits, key=lambda r: (r.rupture_score, r.start))
        assert vd.best_window == f"{best.start:%Y-%m-%d}"
        assert vd.systems == best.rupture_score
    if pt.promised and not hits:
        assert vd.answer == "NOT-YET"
    # rupture path must never fall through to the fulfilment-elapsed rule
    assert vd.answer in ("YES", "NOT-YET", "NO (denied)", "UNCERTAIN")


def test_verdict_boundary_and_next_window():
    """A forward scan's boundary row (starting AT asof) must not count as
    delivered evidence; the strongest window after asof is committed as
    next_window."""
    from interpreter.event_evidence import domain_verdict, promise_and_tempo
    v = _chart()
    prof = DOMAIN_PROFILES["marriage"]
    asof = datetime(2027, 1, 1, tzinfo=UTC)
    rows = candidate_map(v, prof, asof, asof + timedelta(days=3 * 365),
                         step_days=45)
    vd = domain_verdict(v, prof, rows, asof)
    if promise_and_tempo(v, prof).promised:
        assert vd.answer == "NOT-YET"      # nothing matured before asof
    upcoming = [r for r in rows if r.start > asof]
    if upcoming:
        nxt = max(upcoming, key=lambda r: r.salience)
        assert vd.next_window == f"{nxt.start:%Y-%m-%d}"


def test_candidate_map_is_step_deterministic():
    """Rankings must NOT depend on scan parameters: the same span at different
    step_days gives identical rows (pratyantar-midpoint sampling)."""
    v = _chart()
    prof = DOMAIN_PROFILES["marriage"]
    s, e = datetime(2023, 1, 1, tzinfo=UTC), datetime(2025, 1, 1, tzinfo=UTC)
    a = candidate_map(v, prof, s, e, step_days=45)
    b = candidate_map(v, prof, s, e, step_days=60)
    assert [(r.start, r.salience) for r in a] == [(r.start, r.salience) for r in b]
    ra = reversal_map(v, prof, s, e, step_days=45)
    rb = reversal_map(v, prof, s, e, step_days=60)
    assert [(r.start, r.rupture_score) for r in ra] == \
           [(r.start, r.rupture_score) for r in rb]


# --- NĀḌĪ (BNN) family (user-approved 2026-07-04) ---------------------------- #
def test_nadi_karaka_is_gender_aware_and_data_driven():
    from interpreter.event_evidence import nadi_karaka
    from advance_astrology import Planet
    v = _chart()
    prof = DOMAIN_PROFILES["marriage"]
    v.gender = "male"
    assert nadi_karaka(v, prof) == Planet.VENUS
    v.gender = "female"
    assert nadi_karaka(v, prof) == Planet.MARS
    v.gender = ""
    assert nadi_karaka(v, prof) == Planet.VENUS      # default
    assert nadi_karaka(v, DOMAIN_PROFILES["career"]) == Planet.SATURN
    assert nadi_karaka(v, DOMAIN_PROFILES["children"]) == Planet.JUPITER


def test_nadi_witnesses_registered_and_live():
    names = [w.name for w in WITNESSES]
    assert any("nadi: Guru-jeeva" in n for n in names)
    assert any("nadi: Śani karma-sanction" in n for n in names)
    assert any("nadi: Ketu-saṅga" in n for n in names)
    # independent paddhati for the convergence gate (not lumped into gochara)
    assert _paddhati("nadi: Guru-jeeva activates kāraka (BNN)") == "nadi"
    assert _paddhati("nadi: Śani karma-sanction (BNN)") == "nadi"
    v = _chart()
    v.gender = "male"
    rows = candidate_map(v, DOMAIN_PROFILES["marriage"],
                         datetime(2022, 1, 1, tzinfo=UTC),
                         datetime(2025, 1, 1, tzinfo=UTC), step_days=45)
    assert all(isinstance(r.nadi_jeeva, bool) and isinstance(r.nadi_karma, bool)
               for r in rows)
    assert any(r.nadi_jeeva for r in rows)   # Guru-jeeva fires somewhere
    assert any(r.nadi_karma for r in rows)   # Śani sanction fires somewhere


def test_nadi_pinpoint_mechanics():
    """Funnel returns sorted, in-range, gap-separated day-candidates with named
    hits; deterministic; all layers are votes (score bounded 1..7, no Sun)."""
    from interpreter.event_evidence import nadi_pinpoint
    v = _chart()
    v.gender = "male"
    prof = DOMAIN_PROFILES["marriage"]
    s = datetime(2024, 1, 1, tzinfo=UTC)
    e = datetime(2024, 4, 30, tzinfo=UTC)
    pins = nadi_pinpoint(v, prof, s, e)
    assert pins, "no pinpoint days in an active window"
    dates = [datetime.strptime(p["date"], "%Y-%m-%d").replace(tzinfo=UTC)
             for p in pins]
    assert all(s <= d <= e for d in dates)
    assert all(1 <= p["score"] <= 7 and p["hits"] for p in pins)
    # the Sun plays no part in BNN timing — never a hit
    assert all(not any("Sūrya" in h or "Sun" in h for h in p["hits"])
               for p in pins)
    # min-gap separation
    for a, b in zip(dates, dates[1:]):
        assert (b - a).days >= 7
    # deterministic
    assert pins == nadi_pinpoint(v, prof, s, e)


def test_nadi_pinpoint_tiebreak_prefers_tightest_lock():
    """Within an equal-score plateau the returned day must be the one with the
    TIGHTEST combined degree-lock orb (Nāḍī exactness = strength), never just
    the plateau's first calendar day. Verified as a RULE: the funnel's overall
    #1 must equal the best day of the full per-day list under the same key."""
    from interpreter.event_evidence import nadi_pinpoint
    v = _chart()
    v.gender = "male"
    prof = DOMAIN_PROFILES["marriage"]
    s = datetime(2024, 1, 1, tzinfo=UTC)
    e = datetime(2024, 4, 30, tzinfo=UTC)
    allday = nadi_pinpoint(v, prof, s, e, top=10 ** 6, min_gap_days=1)
    assert allday and all("orb" in p for p in allday)
    key = lambda p: (-p["score"], p["orb"], p["date"])
    best = min(allday, key=key)
    pins = nadi_pinpoint(v, prof, s, e)
    assert min(pins, key=key) == best
    # locked days carry a real orb (≤ 2 locks × 3° each); unlocked rank last
    for p in allday:
        locked = any("degree-lock" in h for h in p["hits"])
        assert (p["orb"] <= 9.0) if locked else (p["orb"] == 99.0)


def test_nadi_pinpoint_multi_covers_all_anchor_windows():
    """The multi-window funnel anchors on SEVERAL windows (not just #1) so a
    strong day in any of them surfaces; ranked tightest-lock-first, gap-
    separated across the merged set, capped and deterministic."""
    from interpreter.event_evidence import nadi_pinpoint, nadi_pinpoint_multi
    v = _chart()
    v.gender = "male"
    prof = DOMAIN_PROFILES["marriage"]
    s = datetime(2023, 1, 1, tzinfo=UTC)
    e = datetime(2025, 1, 1, tzinfo=UTC)
    anchors = [datetime(2024, 2, 14, tzinfo=UTC), datetime(2024, 4, 15, tzinfo=UTC)]
    pins = nadi_pinpoint_multi(v, prof, anchors, s, e, top=5)
    assert pins and len(pins) <= 5
    # ranked by (-score, orb) — no lower/looser pin ahead of a higher/tighter one
    keys = [(-p["score"], p["orb"]) for p in pins]
    assert keys == sorted(keys)
    # gap separation ACROSS the merged windows
    ds = sorted(datetime.strptime(p["date"], "%Y-%m-%d") for p in pins)
    for a, b in zip(ds, ds[1:]):
        assert (b - a).days >= 7
    # every returned pin is a real funnel day from SOME anchor window
    union = set()
    for a in anchors:
        for p in nadi_pinpoint(v, prof, a - timedelta(days=45),
                               a + timedelta(days=45)):
            union.add(p["date"])
    assert all(p["date"] in union for p in pins)
    # deterministic
    assert pins == nadi_pinpoint_multi(v, prof, anchors, s, e, top=5)


def test_nadi_rupture_pinpoint_is_separator_driven():
    """The rupture funnel scores ONLY on separators (Śani/Rāhu/Ketu) degree-
    locked on the break-axis; Maṅgal is a trigger that never scores alone, and
    no benefic union-hit (Śukra/Guru) ever appears. Bounded, deterministic,
    gap-separated."""
    from interpreter.event_evidence import nadi_rupture_pinpoint
    from interpreter.significators import resolve
    v = _chart()
    v.gender = "male"
    prof = resolve("divorce")
    s = datetime(2024, 1, 1, tzinfo=UTC)
    e = datetime(2027, 1, 1, tzinfo=UTC)
    pins = nadi_rupture_pinpoint(v, prof, s, e)
    assert pins, "no rupture-pinpoint days in a three-year span"
    dates = [datetime.strptime(p["date"], "%Y-%m-%d").replace(tzinfo=UTC)
             for p in pins]
    assert all(s <= d <= e for d in dates)
    for p in pins:
        # max = Śani 2 + node 2 + Maṅgal 1 + Śani-return 1
        assert 1 <= p["score"] <= 6 and p["hits"]
        sep = any(("karma-cut" in h or "severance" in h) for h in p["hits"])
        mars = any("Maṅgal severer" in h for h in p["hits"])
        # Maṅgal never fires without a separator locked the same day
        assert (not mars) or sep
        # never a union-funnel hit
        assert not any(("Śukra" in h or "Guru" in h) for h in p["hits"])
    for a, b in zip(dates, dates[1:]):
        assert (b - a).days >= 7
    assert pins == nadi_rupture_pinpoint(v, prof, s, e)
