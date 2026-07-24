"""Mnemosheath selective awareness — basic invariants."""

from __future__ import annotations

from tcm import AwareCoalitionCellular, Mnemosheath


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
)


def test_starts_with_agreement_and_empty_pulses():
    sheath = Mnemosheath()
    cues = {bit.cue for bit in sheath.bits}
    assert cues == {"unanimous", "empty"}
    assert sheath.grown_count == 0
    assert all(bit.seed for bit in sheath.bits)


def test_cheerleader_stays_null_weather_consensus_becomes_evidence():
    cheer = AwareCoalitionCellular(**CELL)
    key = (0, 0)
    for truth in (1, 0, 1, 0, 1, 0, 1, 0, 1, 0):
        reports = [("a", 0, 1), ("b", 0, 1), ("c", 0, 1)]
        _, tr = cheer.predict(key, reports, t=0)
        cheer.feedback(
            {"key": key, "truth": truth, "reports": reports, "trace": tr, "time": 1}
        )
    _, tr_null = cheer.predict(key, [("a", 0, 1), ("b", 0, 1)], t=2)
    assert tr_null["stop_reason"] in {"null_diagnostic", "silence_channel"}

    trust = AwareCoalitionCellular(**{**CELL, "min_delta": 0.01})
    for _ in range(24):
        reports = [("gfs", 0, 1), ("ecmwf", 0, 1), ("icon", 0, 1)]
        trust.feedback(
            {
                "key": key,
                "truth": 1,
                "reports": reports,
                "trace": {
                    "p": 0.7,
                    "prior_p": 0.5,
                    "stop_reason": "budget",
                    "majority_vote": 1,
                    "awareness_cues": {"unanimous": True, "unanimous_pos": True},
                },
                "time": 1,
            }
        )
    assert trust.sheath.candidates["unanimous"].merit() > 0.2
    assert trust.sheath.agreement_is_evidence(
        {"unanimous": True, "unanimous_pos": True}
    )


def test_no_lineage_stamp_birth_without_candidate_merit():
    sheath = Mnemosheath(dwell=3, split_merit=0.05, n_min=40, hysteresis=5)
    # Only feed empty with coin-flip outcomes — should NOT sprout garbage.
    for step in range(80):
        cues = {"empty": True, "fresh_vacancy": True}
        sheath.prime_absence("k", cues, prev_truth=0, time_since_evidence=1)
        sheath.feedback(
            cues, majority_vote=None, truth=step % 2, key="k"
        )
    assert sheath.grown_cues() == set()
    assert sheath.admitted_cues() == {"unanimous", "empty"}


def test_prior_never_enters_report_delta():
    cell = AwareCoalitionCellular(**CELL)
    key = (1, 0)
    for _ in range(15):
        cell.feedback(
            {
                "key": key,
                "truth": 1,
                "reports": [("s", 0, 1)],
                "trace": {"p": 0.6, "prior_p": 0.5, "active": []},
                "time": 1,
            }
        )
    d0 = cell._report_delta("s", 1)
    cell.cf[(key, 1)] = 9.0
    cell.cf[(key, 0)] = -9.0
    assert abs(cell._report_delta("s", 1) - d0) < 1e-9


def test_agreement_evidence_sharpens_probability_toward_vote():
    """Christmas bow: sheath courage must enter p, not only the trace."""
    cell = AwareCoalitionCellular(**{**CELL, "min_delta": 0.01})
    key = ("wx", 0)
    reports = [("gfs", 0, 1), ("ecmwf", 0, 1), ("icon", 0, 1), ("gem", 0, 1)]
    for _ in range(30):
        _, tr = cell.predict(key, reports, t=0)
        cell.feedback(
            {
                "key": key,
                "truth": 1,
                "reports": reports,
                "trace": tr,
                "time": 1,
            }
        )
    assert cell.sheath.agreement_is_evidence({"unanimous": True, "unanimous_pos": True})
    p, tr = cell.predict(key, reports, t=100)
    assert tr["stop_reason"] != "null_diagnostic"
    assert tr["awareness"]["awareness_sharpness_applied"] is True
    assert tr["awareness"]["agreement_blend_weight"] > 0.0
    # Must be braver than the timid pre-awareness probability on clear yes-votes.
    assert p > tr["awareness"]["p_before_awareness"]
    assert p >= 0.70
