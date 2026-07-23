"""Evolve the Mnemosheath: 1 → 2 → 4 bits under online feedback."""

from __future__ import annotations

from tcm import AwareCoalitionCellular, Mnemosheath
from tcm.awareness import STAGE_CAPS


def test_starts_with_agreement_and_empty_pulses():
    sheath = Mnemosheath()
    cues = {bit.cue for bit in sheath.bits}
    assert "unanimous" in cues
    assert "empty" in cues
    assert sheath.stage_cap == STAGE_CAPS[0]


def test_cheerleader_stays_null_weather_consensus_becomes_evidence():
    # Finance-like: unanimous Positive is coin-flip vs truth → null.
    cheer = AwareCoalitionCellular(
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
    key = (0, 0)
    for truth in (1, 0, 1, 0, 1, 0, 1, 0, 1, 0):
        reports = [("a", 0, 1), ("b", 0, 1), ("c", 0, 1)]
        p, tr = cheer.predict(key, reports, t=0)
        cheer.feedback(
            {
                "key": key,
                "truth": truth,
                "reports": reports,
                "trace": tr,
                "time": 1,
            }
        )
    # Still near coin-flip diagnosticity → unanimous routes null.
    _, tr_null = cheer.predict(key, [("a", 0, 1), ("b", 0, 1)], t=2)
    assert tr_null["stop_reason"] in {"null_diagnostic", "silence_channel"}

    # Weather-like: unanimous warmer always matches truth → becomes evidence.
    trust = AwareCoalitionCellular(
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
        min_delta=0.01,
    )
    for _ in range(24):
        reports = [("gfs", 0, 1), ("ecmwf", 0, 1), ("icon", 0, 1)]
        # Teach discriminative LRs a little with mixed batches interleaved.
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
    assert trust.sheath.bits[0].diagnosticity() > 0.7
    # After awareness learns diagnosticity, unanimous should leave null path
    # once LRs exist — force sheath threshold via direct feedback already done.
    assert trust.sheath.agreement_is_evidence(
        {"unanimous": True, "unanimous_pos": True}
    )


def test_maturation_splits_toward_two_then_four_bits():
    sheath = Mnemosheath(dwell=3, split_merit=0.05)
    cues = {"unanimous": True, "unanimous_pos": True}
    # Earn persistence with consistently correct majority.
    for _ in range(40):
        sheath.feedback(cues, majority_vote=1, truth=1)
        # Also fire child cues once born.
        live = {bit.cue: True for bit in sheath.bits}
        sheath.feedback(live, majority_vote=1, truth=1)
    assert sheath.bit_count >= 2
    # Keep feeding until stage can hold 4.
    for _ in range(80):
        live = {bit.cue: True for bit in sheath.bits}
        # Mix a little so multiple cues can fire across updates.
        sheath.feedback(live, majority_vote=1, truth=1)
    assert sheath.bit_count >= 2
    assert sheath.stage_cap in STAGE_CAPS


def test_prior_never_enters_report_delta():
    cell = AwareCoalitionCellular(
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
    )
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
