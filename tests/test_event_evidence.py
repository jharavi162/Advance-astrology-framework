"""Regression tests for the domain-general event-evidence builder."""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from advance_astrology import VedicChart
from interpreter.event_evidence import (
    DASHA_SYSTEMS, DOMAIN_PROFILES, FAMILIES, WITNESSES, Witness, WindowEvidence,
    _paddhati, _school, _score_rows, build_panel, candidate_map, register_witness,
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
    hits; deterministic; scores bounded 1..9 (canonical: Guru primary +3/+1,
    Śani +2, three fast refinements +1 each), no Sun."""
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
    assert all(1 <= p["score"] <= 9 and p["hits"] for p in pins)
    # the Sun plays no part in BNN timing — never a hit
    assert all(not any("Sūrya" in h or "Sun" in h for h in p["hits"])
               for p in pins)
    # every pin must carry a slow-planet PRIMARY approval (Guru or Śani), never
    # fast-only — the canonical gate
    assert all(any(("Guru(jeeva) contacts" in h or "Śani karma-approval" in h)
                   for h in p["hits"]) for p in pins)
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
        # canonical mirror: Śani primary +3/+1, node +2, Maṅgal refine +1
        assert 1 <= p["score"] <= 7 and p["hits"]
        sep = any(("Śani (karma) contacts" in h or "severance" in h)
                  for h in p["hits"])
        # every pin carries a separator PRIMARY approval (Śani or node)
        assert sep
        mars = any("Maṅgal" in h for h in p["hits"])
        # Maṅgal never fires without a separator approval the same day
        assert (not mars) or sep
        # never a union-funnel hit (benefic Śukra/Guru)
        assert not any(("Śukra" in h or "Guru" in h) for h in p["hits"])
    for a, b in zip(dates, dates[1:]):
        assert (b - a).days >= 7
    assert pins == nadi_rupture_pinpoint(v, prof, s, e)


def test_nadi_golden_relations_are_1_5_9_only():
    """Professional BNN standard: the golden relations are conjunction + the
    1/5/9 trine ONLY — the 7th (opposition, offset 6) is NOT one."""
    from interpreter.event_evidence import _NADI_REL, _nrel
    assert _NADI_REL == {0, 4, 8}
    assert not _nrel(0, 6)          # 7th is not golden
    assert _nrel(0, 0) and _nrel(0, 4) and _nrel(0, 8)


def test_nadi_sign_shifts_retrograde_one_back():
    from interpreter.event_evidence import _nadi_sign
    # 45° = 15° Taurus (sign 1); direct → sign 1, retrograde → one back (Aries 0)
    assert _nadi_sign(45.0, retrograde=False) == 1
    assert _nadi_sign(45.0, retrograde=True) == 0
    assert _nadi_sign(5.0, retrograde=True) == 11   # wraps Aries → Pisces


def test_nadi_chain_is_degree_ordered_and_golden_to_hero():
    """The chain holds the hero + only planets in a 1/5/9 golden relation to the
    hero's BNN sign, ordered by degree; the hero is marked; before/after tags
    follow the degree vs the hero; deterministic. Retrograde members reckon one
    sign back."""
    from interpreter.event_evidence import (nadi_chain, nadi_karaka, _nadi_sign,
                                            _NADI_REL)
    from advance_astrology import Planet
    v = _chart()
    v.gender = "male"
    prof = DOMAIN_PROFILES["marriage"]
    chain = nadi_chain(v, prof)
    assert chain, "hero is always at least its own chain member"
    # degree-ordered
    degs = [r["degree"] for r in chain]
    assert degs == sorted(degs)
    # exactly one HERO, and it is the kāraka
    heroes = [r for r in chain if "HERO" in r["when"]]
    assert len(heroes) == 1 and heroes[0]["planet"] == nadi_karaka(v, prof).value
    hero_deg = heroes[0]["degree"]
    hero = nadi_karaka(v, prof)
    hero_sign = _nadi_sign(float(v.longitudes[hero]),
                           bool(v.natal.placements[hero].retrograde)
                           and hero not in (Planet.RAHU, Planet.KETU))
    for r in chain:
        # each member is golden to the hero's sign
        p = next(pl for pl in Planet if pl.value == r["planet"])
        retro = r["retrograde"]
        assert ((_nadi_sign(float(v.longitudes[p]), retro) - hero_sign) % 12
                in _NADI_REL)
        # before/after tag consistent with degree vs hero (hero excepted)
        if "HERO" not in r["when"]:
            assert ("before" in r["when"]) == (r["degree"] < hero_deg)
    assert chain == nadi_chain(v, prof)


def test_school_collapses_parashari_subtools_to_one():
    """Convergence must count the 5 INDEPENDENT schools, not fine sub-techniques.
    Vimśottari, gochara, Sudarśana, Aṣṭakavarga all collapse into Parāśari — a
    window lit only by them is ONE school, not three (no false convergence)."""
    from interpreter.event_evidence import _school
    assert _school("daśā: kāraka in MD>AD>PD") == "parashari"
    assert _school("double-transit (house/lord)") == "parashari"
    assert _school("Sudarśana wheel") == "parashari"
    assert _school("Kakṣyā window") == "parashari"
    assert _school("KP fulfilment ≥ negation") == "kp"
    assert _school("Jaimini Arudha-axis activation (UL / 2nd-from-Arudha)") == "jaimini"
    assert _school("daśā[nārāyaṇa]: significator running") == "jaimini"
    assert _school("domain Saham double-transit") == "tajika"
    assert _school("Varṣaphal Muntha") == "tajika"
    assert _school("nadi: Guru-jeeva activates kāraka (BNN)") == "nadi"
    # three Parāśari sub-tools in one window => ONE independent school
    names = ["daśā: kāraka in MD>AD>PD", "double-transit (house/lord)",
             "Sudarśana wheel"]
    assert len({_school(n) for n in names}) == 1


def test_school_report_layer1_breakdown():
    """Layer-1: each of the 5 schools gets its own best window or abstains;
    deterministic; a firing school carries a window, an abstaining one does not."""
    from interpreter.event_evidence import school_report, _SCHOOLS
    v = _chart(); v.gender = "female"
    prof = DOMAIN_PROFILES["marriage"]
    rows = candidate_map(v, prof, datetime(2012, 1, 1, tzinfo=UTC),
                         datetime(2020, 1, 1, tzinfo=UTC), step_days=45)
    rep = school_report(v, prof, rows)
    assert [r["school"] for r in rep] == list(_SCHOOLS)   # all 5, in order
    for r in rep:
        assert (r["window"] != "") == r["fires"]          # fires ⇔ has a window
        assert r["strength"] >= 0.0
    assert any(r["fires"] for r in rep)                   # something fires
    assert rep == school_report(v, prof, rows)            # deterministic


def test_task4_standing_nodes_bounded_and_domain_gated():
    """The 5 approved Parāśari/Jaimini nodes: bounded votes, correctly gated to
    their matter (Manglik/Karakāṃśa/husband-kāraka → marriage only; Indu → wealth
    only; female-husband-kāraka only for a ♀ chart)."""
    from interpreter.event_evidence import (WITNESSES, _w_manglik,
        _w_female_husband_karaka, _w_karakamsha_spouse, _w_indu_lagna,
        _w_bhava_chalit_shift)
    from advance_astrology import Planet
    v = _chart()
    names = [w.name for w in WITNESSES]
    for sub in ("Kuja dosha", "husband kāraka", "Karakāṃśa 7th-spouse",
                "Indu Lagna", "Bhāva-Chalit result-shift"):
        assert any(sub in n for n in names), sub
    mar, wealth, career = (DOMAIN_PROFILES["marriage"], DOMAIN_PROFILES["wealth"],
                           DOMAIN_PROFILES["career"])
    # Manglik: marriage-gated, non-positive, zero for career
    assert -1.0 <= _w_manglik(v, mar) <= 0.0
    assert _w_manglik(v, career) == 0.0
    # Karakāṃśa spouse: marriage-gated, bounded
    assert -0.5 <= _w_karakamsha_spouse(v, mar) <= 0.5
    assert _w_karakamsha_spouse(v, career) == 0.0
    # Indu Lagna: wealth-gated
    assert _w_indu_lagna(v, mar) == 0.0
    assert -0.4 <= _w_indu_lagna(v, wealth) <= 0.4
    # Bhāva-Chalit: bounded caution
    assert -0.6 <= _w_bhava_chalit_shift(v, mar) <= 0.0
    # female husband-kāraka: zero unless ♀
    v.gender = "male"
    assert _w_female_husband_karaka(v, mar) == 0.0
    v.gender = "female"
    assert -0.4 <= _w_female_husband_karaka(v, mar) <= 0.4


def test_coverage_matrix_in_sync_after_task4():
    from interpreter.coverage import audit
    a = audit()
    assert a["claims_without_witness"] == [], a["claims_without_witness"]
    assert a["witnesses_not_in_matrix"] == [], a["witnesses_not_in_matrix"]


def test_sade_sati_timing_node_wired():
    """Sade-Sati (Saturn 12/1/2 from natal Moon) is wired as a Parāśari-gochara
    timing node; computed per window as a bool."""
    from interpreter.event_evidence import WITNESSES, _school
    assert any("Sade-Sati" in w.name for w in WITNESSES)
    assert _school("Sade-Sati / Kaṇṭaka (Saturn-from-Moon)") == "parashari"
    v = _chart()
    rows = candidate_map(v, DOMAIN_PROFILES["marriage"],
                         datetime(2018, 1, 1, tzinfo=UTC),
                         datetime(2022, 1, 1, tzinfo=UTC), step_days=45)
    assert rows and all(isinstance(r.sade_sati, bool) for r in rows)


def test_day_convergence_multi_method_and_direction():
    """Multi-method DAY convergence: pure independent methods, bounded 3..5 count,
    signed direction label, gap-separated, deterministic, domain-general."""
    from interpreter.event_evidence import day_convergence
    v = _chart(); v.gender = "female"
    prof = DOMAIN_PROFILES["marriage"]
    s, e = datetime(2021, 1, 1, tzinfo=UTC), datetime(2024, 1, 1, tzinfo=UTC)
    res = day_convergence(v, prof, s, e)
    assert res
    for r in res:
        assert 3 <= r["methods"] <= 5 and r["active"]
        assert r["direction"] in ("union", "break", "troubled", "mixed")
        assert isinstance(r["score"], int)
    ds = sorted(datetime.strptime(x["date"], "%Y-%m-%d") for x in res)
    for a, b in zip(ds, ds[1:]):
        assert (b - a).days >= 10                     # gap-separated
    assert res == day_convergence(v, prof, s, e)      # deterministic
    # domain-general: runs for a non-marriage domain without error
    assert isinstance(day_convergence(v, DOMAIN_PROFILES["career"],
                                      s, e), list)


def test_day_convergence_direction_defers_to_window_signals():
    """When candidate/reversal windows are supplied, direction is the tested
    window signal (rule, not a native date): a day inside an elapsed LOSS/BREAK
    rupture window reads 'break'; a KP-negation-lean window reads 'troubled'
    (afflicted ≠ break); a KP-fulfil-lean window reads 'union'."""
    from interpreter.event_evidence import (day_convergence, candidate_map,
                                            reversal_map, _window_direction)
    from datetime import datetime as _dt
    v = _chart(); v.gender = "female"
    prof = DOMAIN_PROFILES["marriage"]
    s, e = datetime(2021, 1, 1, tzinfo=UTC), datetime(2024, 6, 30, tzinfo=UTC)
    rows = candidate_map(v, prof, s, e, step_days=30)
    rr = reversal_map(v, prof, s, e, step_days=30)
    res = day_convergence(v, prof, s, e, windows=rows, rwindows=rr, top=12)
    assert res
    # every 'break' label must be backed by a real elapsed LOSS/BREAK window
    for r in res:
        if r["direction"] == "break":
            dt = _dt.strptime(r["date"], "%Y-%m-%d").replace(tzinfo=UTC)
            assert any(x.kind == "LOSS/BREAK" and x.rupture_score >= 3
                       and abs((x.start - dt).days) <= 45 for x in rr)
    # _window_direction is a pure function of the window signals (rule-verifiable)
    brk = [x for x in rr if x.kind == "LOSS/BREAK" and x.rupture_score >= 3]
    if brk:
        lbl, _sc = _window_direction(brk[0].start, rows, rr)
        assert lbl in ("break", "troubled", "union")


def test_bhinnashtakavarga_delivery_node_registered_and_domain_scoped():
    """The Bhinnāṣṭakavarga DELIVERY node (previously computed-but-UNWIRED — the
    red 'Bhinnāṣṭakavarga of house/lord' coverage item) is now a registered,
    domain-general timing witness: a transit fructifies in proportion to the
    bindus the TRANSITING SIGNIFICATOR holds in its own BAV (BPHS Aṣṭakavarga
    gochara). MECHANICAL only — asserts it exists, computes a bounded graded
    value on every window, is a SOFT additive weight (never negative → never a
    veto), and belongs to the Parāśari corpus (not a phantom independent school).
    No date is asserted (that would be calibration)."""
    names = [w.name for w in WITNESSES if w.layer == "timing"]
    assert any("Bhinnāṣṭakavarga delivery" in n for n in names), \
        "Bhinnāṣṭakavarga delivery node not registered"
    node = next(w for w in WITNESSES
                if w.layer == "timing" and "Bhinnāṣṭakavarga delivery" in w.name)
    # it is a SOFT weight (< the hard 1.0 timekeepers) and reads a graded fraction,
    # so it can only UP-WEIGHT a window — it can never suppress an otherwise-strong
    # one (respects "never a veto").
    assert 0 < node.weight < 1.0
    # Aṣṭakavarga is the Parāśari corpus (SAME school as the generic Kakṣyā node),
    # so wiring it does NOT invent a new independent school / false convergence.
    assert _school(node.name) == "parashari"
    assert _paddhati(node.name) == "ashtakavarga"

    v = _chart()
    rows = candidate_map(v, DOMAIN_PROFILES["marriage"],
                         datetime(2023, 1, 1, tzinfo=UTC),
                         datetime(2025, 6, 1, tzinfo=UTC))
    assert rows
    for r in rows:                       # computed on every window, bounded [0,1]
        assert isinstance(r.karaka_kakshya, float)
        assert 0.0 <= r.karaka_kakshya <= 1.0
        assert node.vote(r) >= 0.0       # graded, never negative → never a veto
    # fires (graded > 0) somewhere in a multi-year band — not dead code
    assert any(r.karaka_kakshya > 0.0 for r in rows)
    # domain-general: the kāraka set differs by domain, so the delivery node must
    # also compute for a non-marriage matter without error
    crows = candidate_map(v, DOMAIN_PROFILES["career"],
                          datetime(2023, 1, 1, tzinfo=UTC),
                          datetime(2025, 6, 1, tzinfo=UTC))
    assert crows and all(0.0 <= r.karaka_kakshya <= 1.0 for r in crows)


def test_bnn_quality_standing_witnesses_registered_and_fire():
    """The three user-approved BNN marriage-QUALITY nodes (jīva 12th-from-kāraka;
    kāraka 12th-from-descriptor delay; kāraka conjunct separator) are registered
    domain-general STANDING witnesses. MECHANICAL — asserts registration, the
    dormancy invariants (deterministic), that each FIRES on a controlled synthetic
    placement (not dead code), that the sign is always in {0, -0.5, -0.6} (soft,
    quality-only, never positive/never a veto), and the Nāḍī-school mapping. No
    native date is asserted (that would be calibration)."""
    from interpreter.event_evidence import (
        _w_jiva_12th_from_karaka, _w_karaka_12th_from_descriptor,
        _w_karaka_conjunct_separator, Planet, nadi_timing_karaka, nadi_karaka)
    snames = [w.name for w in WITNESSES if w.layer == "standing"]
    for needle in ("jīva 12th-from-kāraka", "kāraka 12th-from-descriptor",
                   "kāraka conjunct separator"):
        assert any(needle in n for n in snames), f"BNN standing node missing: {needle}"
    # BNN principles are the Nāḍī corpus (standing → they don't enter the timing
    # school-convergence count, but the mapping must be coherent)
    assert _school("BNN: jīva 12th-from-kāraka (quality-drag)") == "nadi"

    v = _chart()
    marriage = DOMAIN_PROFILES["marriage"]
    # valid range on a real chart: soft, quality-only, never positive → never a veto
    for w in (_w_jiva_12th_from_karaka, _w_karaka_12th_from_descriptor,
              _w_karaka_conjunct_separator):
        val = w(v, marriage)
        assert val in (0.0, -0.5, -0.6)
    # dormancy invariants (deterministic, no chart needed to reason about):
    #  #1 is dormant when the kāraka IS Jupiter (children: natural_karaka=Jupiter)
    assert _w_jiva_12th_from_karaka(v, DOMAIN_PROFILES["children"]) == 0.0
    #  #2 is dormant when event-kāraka == descriptor (career: no distinct descriptor)
    assert _w_karaka_12th_from_descriptor(v, DOMAIN_PROFILES["career"]) == 0.0

    # FIRING on controlled synthetic placements (proves not dead code) ----------
    class _FakeV:
        def __init__(self, signs, gender=""):
            self.signs, self.gender = signs, gender

    ve = nadi_timing_karaka(v, marriage)          # Venus (event-kāraka, both sexes)
    # #1: Jupiter placed 12th-from-Venus → -0.6
    base = {p: 0 for p in Planet}
    base[Planet.VENUS] = 3
    base[Planet.JUPITER] = (3 + 11) % 12
    assert _w_jiva_12th_from_karaka(_FakeV(base), marriage) == -0.6
    # #2 (female): event Venus 12th-from-descriptor Mars → -0.5
    vf = _FakeV({p: 0 for p in Planet}, gender="female")
    assert nadi_karaka(vf, marriage) == Planet.MARS and ve == Planet.VENUS
    vf.signs[Planet.MARS] = 5
    vf.signs[Planet.VENUS] = (5 + 11) % 12
    assert _w_karaka_12th_from_descriptor(vf, marriage) == -0.5
    # #3: Venus in the same sign as Rāhu (separator company) → -0.6
    sep = {p: 0 for p in Planet}
    sep[Planet.RAHU] = 7
    sep[Planet.VENUS] = 7
    assert _w_karaka_conjunct_separator(_FakeV(sep), marriage) == -0.6


def test_nadi_pinpoint_anchors_the_spouse_karaka_for_female():
    """BNN pinpoint must anchor the SPOUSE/gender kāraka (Mars for a female =
    husband), not only the event-kāraka Venus — so the husband-kāraka's
    degree-return can stamp the day (R.G. Rao: the husband is read from Mars for a
    female). MECHANICAL — asserts the spouse-kāraka is distinct for a female, the
    same as the event-kāraka for a male (backward-compatible), and that the new
    'spouse-kāraka degree-return' refinement is reachable over a multi-year span.
    No native's date is asserted (blind-test integrity)."""
    from interpreter.event_evidence import (nadi_pinpoint, nadi_karaka,
                                            nadi_timing_karaka, DOMAIN_PROFILES, Planet)
    p = DOMAIN_PROFILES["marriage"]
    v = _chart()
    # male-class: spouse-kāraka == event-kāraka (both Venus) → anchor set unchanged
    v.gender = "male"
    assert nadi_karaka(v, p) == nadi_timing_karaka(v, p) == Planet.VENUS
    # female: husband-kāraka Mars distinct from the event-kāraka Venus
    v.gender = "female"
    assert nadi_karaka(v, p) == Planet.MARS and nadi_timing_karaka(v, p) == Planet.VENUS
    pins = nadi_pinpoint(v, p, datetime(2010, 1, 1, tzinfo=UTC),
                         datetime(2026, 1, 1, tzinfo=UTC), top=12)
    assert pins
    hits = [h for r in pins for h in r["hits"]]
    assert any("spouse-kāraka degree-return" in h for h in hits), \
        "husband-kāraka (Mars) anchor never fired — spouse-kāraka not wired into the funnel"


def test_role_significators_ranks_by_weighted_role_density():
    """The marriage-timer is found by ROLE-DENSITY, not by a hard-coded planet
    (docs/AI_TRIANGULATION_PROMPT §4C-bis). MECHANICAL — asserts the scorer is
    deterministic, weights the promise-giving roles above incidental ones, and
    that the top-ranked graha holds at least one HEAVY promise-role (owns the
    house / is its kāraka / cusp-sub-lord / Darakaraka). No native date asserted."""
    from interpreter.event_evidence import role_significators, DOMAIN_PROFILES
    v = _chart()
    v.gender = "male"
    p = DOMAIN_PROFILES["marriage"]
    rs = role_significators(v, p)
    assert rs and rs == role_significators(v, p)          # non-empty + deterministic
    # sorted descending by weighted score
    assert all(rs[i]["score"] >= rs[i + 1]["score"] for i in range(len(rs) - 1))
    HEAVY = ("7H-lord", "primary-cusp-sub-lord", "event-kāraka", "Darakaraka")
    top = rs[0]
    assert any(r.startswith(HEAVY) or "(primary)" in r for r in top["roles"]), \
        "top significator must hold a heavy promise-role, not only soft ones"
    # weighting really bites: a graha owning the house + being its kāraka must
    # out-score one that merely aspects it / sits in Lagna (soft roles only)
    soft = [x for x in rs if not any(r.startswith(HEAVY) or "(primary)" in r
                                     for r in x["roles"])]
    if soft:
        assert top["score"] > soft[0]["score"]
    # domain-general: runs for a non-marriage matter too
    assert role_significators(v, DOMAIN_PROFILES["career"])


def test_shukra_guru_refine_is_natal_anchored_not_chart_independent():
    """The Śukra≈Guru day-refine must be NATAL-ANCHORED: a transit-Venus≈transit-
    Jupiter contact is the same sky for every chart, so it may count only when
    the pair sits on THIS chart's natal Venus or natal Jupiter degree
    (degree-to-degree). MECHANICAL property test — for every pinpoint day that
    carries the hit, the anchor predicate must hold when recomputed from the
    ephemeris; and a second chart with different natal degrees must not simply
    inherit the same fire-days. No native outcome date is asserted."""
    from interpreter.event_evidence import (nadi_pinpoint, DOMAIN_PROFILES,
                                            Planet, _deg_close)
    p = DOMAIN_PROFILES["marriage"]
    span = (datetime(2023, 12, 1, tzinfo=UTC), datetime(2024, 3, 1, tzinfo=UTC))
    charts = [_chart(),
              VedicChart.create(when=datetime(1990, 10, 10, 12, 0,
                                              tzinfo=ZoneInfo("Asia/Kolkata")),
                                latitude=23.63, longitude=85.52, ayanamsa="lahiri")]
    fire_days = []
    for v in charts:
        v.gender = "male"
        tr = v.transits()
        nv = float(v.longitudes[Planet.VENUS])
        nj = float(v.longitudes[Planet.JUPITER])
        days = set()
        for r in nadi_pinpoint(v, p, *span, top=10):
            if not any("Śukra≈Guru" in h for h in r["hits"]):
                continue
            days.add(r["date"])
            d = datetime.strptime(r["date"], "%Y-%m-%d").replace(tzinfo=UTC)
            jup = float(tr.positions(d, [Planet.JUPITER])[Planet.JUPITER])
            # the anchor predicate: the pair sits on natal Venus or natal Jupiter
            assert _deg_close(jup, nv) or _deg_close(jup, nj), \
                f"chart-independent Śukra≈Guru fired on {r['date']}"
        fire_days.append(days)
    # the stamp is personal: two different charts must not share an identical
    # non-empty fire-set by construction (the old bug fired for everyone)
    assert not (fire_days[0] and fire_days[0] == fire_days[1]), \
        "Śukra≈Guru fired identically across two different charts"
