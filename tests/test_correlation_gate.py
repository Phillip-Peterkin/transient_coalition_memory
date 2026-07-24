"""Regression: null gate must not use coalition-discounted max |Δ|."""

from __future__ import annotations

from tcm import ActiveCoalitionCellular, AwareCoalitionCellular


CELL = dict(
    lr=0.22,
    fast_decay=0.90,
    contradiction_gain=0.85,
    uncertainty_cost=0.38,
    temp=0.95,
    anchor=0.58,
    min_k=1,
    max_k=8,
    header_cost=0.08,
    cert_delta=0.08,
    hazard_gain=3.0,
    min_margin=0.0,
    shadow_scale=0.75,
    reserve_claim_gain=1.2,
    reserve_source_gain=0.0,
    certify_slack=0.0,
    min_delta=0.15,
    force_all_positive_null=False,
)


def _train_good_sources(cell, sources, *, rounds: int = 30) -> None:
    key = ("item", 0)
    for step in range(rounds):
        truth = step % 2
        reports = [(source, 0, truth) for source in sources]
        _, trace = cell.predict(key, reports, t=step)
        cell.feedback(
            {
                "key": key,
                "truth": truth,
                "reports": reports,
                "trace": trace,
                "time": step,
            }
        )


def test_twelve_agreeing_trusted_sources_are_not_false_null():
    """DBSA-shaped batch: 12 unanimous good sources must not look empty.

    Old bug: correlation discount divided every |Δ| by 12, then compared the
    shrunken max to min_delta=0.15, so a room full of agreeing evidence was
    routed into the anti-prior null channel.
    """
    sources = [f"s{i}" for i in range(12)]
    cell = ActiveCoalitionCellular(**CELL)
    # Mild reliability: raw |Δ| clears min_delta, but raw/12 does not —
    # the exact trap the old gate fell into mid-stream.
    for source in sources:
        cell.src_vote_up[(source, 1)] = 8.0
        cell.src_vote_up[(source, 0)] = 2.0
        cell.src_vote_down[(source, 1)] = 2.0
        cell.src_vote_down[(source, 0)] = 8.0
    reports = [(source, 0, 1) for source in sources]
    raw = cell._max_raw_abs_delta(reports)
    scale = cell._correlation_scale(reports)
    assert raw >= cell.min_delta
    assert raw * scale < cell.min_delta  # would have failed the old gate
    _, trace = cell.predict(("item", 0), reports, t=100)
    assert trace["stop_reason"] != "null_diagnostic"
    assert trace["used"] > 0
    assert trace["max_delta"] >= cell.min_delta
    # Full-batch shrink would still look empty; active-set shrink should not.
    assert raw * scale < cell.min_delta


def test_copy_coalition_keeps_one_source_worth_after_early_certificate():
    """Recruit on raw Δ, then discount the active sum — not each row first."""
    sources = [f"s{i}" for i in range(12)]
    cell = ActiveCoalitionCellular(**CELL)
    for source in sources:
        cell.src_vote_up[(source, 1)] = 8.0
        cell.src_vote_up[(source, 0)] = 2.0
        cell.src_vote_down[(source, 1)] = 2.0
        cell.src_vote_down[(source, 0)] = 8.0
    reports = [(source, 0, 1) for source in sources]
    raw_one = cell._report_delta(sources[0], 1)
    _, trace = cell.predict(("item", 0), reports, t=100)
    assert trace["stop_reason"] == "free_energy_certified"
    # Should be near one source's evidence, not a small fraction of it.
    assert abs(trace["evidence_lo"]) >= 0.75 * abs(raw_one)
    assert abs(trace["evidence_lo"]) <= 1.25 * abs(raw_one)


def test_redundant_sources_are_not_double_recruited():
    cell = ActiveCoalitionCellular(
        use_source_redundancy=True,
        source_redundant_agree=0.90,
        source_redundant_min_pairs=5,
        **CELL,
    )
    key = ("item", 0)
    # Teach: leader+copy always right together; other always wrong.
    for step in range(16):
        truth = step % 2
        reports = [("leader", 0, truth), ("copy", 0, truth), ("other", 0, 1 - truth)]
        _, trace = cell.predict(key, reports, t=step)
        cell.feedback(
            {
                "key": key,
                "truth": truth,
                "reports": reports,
                "trace": trace,
                "time": step,
            }
        )
    reports = [("leader", 0, 1), ("copy", 0, 1), ("other", 0, 0)]
    _, trace = cell.predict(key, reports, t=20)
    assert trace["stop_reason"] != "null_diagnostic"
    active_sources = [row[0] for row in trace["active"]]
    assert "leader" in active_sources or "copy" in active_sources
    assert not ("leader" in active_sources and "copy" in active_sources)
    assert cell.source_redundant_skips >= 1


def test_aware_can_reach_agreement_evidence_on_large_unanimous_batch():
    sources = [f"s{i}" for i in range(12)]
    cell = AwareCoalitionCellular(**CELL)
    _train_good_sources(cell, sources)
    # Teach sheath that unanimous agreement has been diagnostic.
    key = ("item", 0)
    for step in range(24):
        reports = [(source, 0, 1) for source in sources]
        _, trace = cell.predict(key, reports, t=200 + step)
        cell.feedback(
            {
                "key": key,
                "truth": 1,
                "reports": reports,
                "trace": trace,
                "time": 200 + step,
            }
        )
    reports = [(source, 0, 1) for source in sources]
    _, trace = cell.predict(key, reports, t=300)
    assert trace["stop_reason"] != "null_diagnostic"
    assert cell.awareness_evidence_routes >= 1
