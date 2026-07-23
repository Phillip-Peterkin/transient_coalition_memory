"""Learning under emptiness — two-phase silence curriculum."""

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


def test_sheath_seeds_empty_pulse_not_only_agreement():
    sheath = Mnemosheath()
    cues = {bit.cue for bit in sheath.bits}
    assert "empty" in cues
    assert "unanimous" in cues


def test_empty_predict_primes_and_feedback_teaches_without_majority():
    cell = AwareCoalitionCellular(**CELL)
    key = (0, 0)
    cell.last_truth[key] = 0
    p, tr = cell.predict(key, [], t=0)
    assert tr["stop_reason"] == "silence_channel"
    assert tr["majority_vote"] is None
    assert cell.sheath.empty_primes >= 1
    assert key in cell.sheath.pending

    cell.feedback(
        {
            "key": key,
            "truth": 1,
            "reports": [],
            "trace": tr,
            "time": 1,
        }
    )
    assert cell.sheath.empty_lessons >= 1
    empty_bit = next(bit for bit in cell.sheath.bits if bit.cue == "empty")
    assert empty_bit.change > empty_bit.stay


def test_empty_stay_lowers_change_rate():
    cell = AwareCoalitionCellular(**CELL)
    key = (2, 0)
    cell.last_truth[key] = 1
    for _ in range(12):
        _, tr = cell.predict(key, [], t=0)
        cell.feedback(
            {
                "key": key,
                "truth": 1,
                "reports": [],
                "trace": tr,
                "time": 1,
            }
        )
    empty_bit = next(bit for bit in cell.sheath.bits if bit.cue == "empty")
    assert empty_bit.change_rate() < 0.45


def test_selective_silence_growth_only_when_vacancy_predicts():
    """Predictive vacancy cue admits; coin-flip companion does not."""
    sheath = Mnemosheath(
        seed_cues=("empty",),
        candidate_cues=("empty", "vac_signal", "vac_noise"),
        grow_caps=(0, 1),
        n_min=40,
        merit_hi=0.18,
        lead_hi=0.08,
        noise_floor=0.05,
        hysteresis=5,
    )
    for step in range(400):
        changed = step % 2  # balanced but vac_signal tracks it with noise
        # Make vac_signal strongly predictive of change.
        import random

        random.seed(step + 99)
        cues = {
            "empty": True,
            "vac_signal": random.random() < (0.9 if changed else 0.1),
            "vac_noise": random.random() < 0.5,
        }
        sheath.prime_absence("k", cues, prev_truth=0, time_since_evidence=2)
        sheath.feedback(
            cues, majority_vote=None, truth=(1 if changed else 0), key="k"
        )
    assert sheath.grown_cues() == {"vac_signal"}, sheath.stats()
    assert "vac_noise" not in sheath.grown_cues()


def test_prior_still_out_of_report_delta_with_empty_curriculum():
    cell = AwareCoalitionCellular(**CELL)
    key = (9, 0)
    for _ in range(10):
        cell.feedback(
            {
                "key": key,
                "truth": 1,
                "reports": [("s", 0, 1)],
                "trace": {
                    "p": 0.6,
                    "prior_p": 0.5,
                    "majority_vote": 1,
                    "awareness_cues": {"unanimous": True, "unanimous_pos": True},
                },
                "time": 1,
            }
        )
    d0 = cell._report_delta("s", 1)
    cell.cf[(key, 1)] = 8.0
    cell.cf[(key, 0)] = -8.0
    assert abs(cell._report_delta("s", 1) - d0) < 1e-9
