"""30-cue needle: only 2 signals matter; sheath must not sprout garbage."""

from __future__ import annotations

import numpy as np

from tcm import Mnemosheath


def test_thirty_cue_needle_admits_exactly_two_signal_bits():
    rng = np.random.default_rng(7)
    signals = ("sig_a", "sig_b")
    noises = tuple(f"noise_{index:02d}" for index in range(28))
    pool = signals + noises

    sheath = Mnemosheath(
        seed_cues=(),  # pure competition — no free pulses
        candidate_cues=pool,
        grow_caps=(0, 1, 2),  # allow exactly two grown bits
        n_min=50,
        merit_hi=0.18,
        lead_hi=0.08,
        noise_floor=0.05,
        hysteresis=6,
    )

    # Delayed feedback loop: observe cues, then label arrives.
    for step in range(700):
        label = int(rng.integers(0, 2))  # 1 => majority_correct
        cues = {
            # sig_a predicts correctness; sig_b predicts incorrectness (both high merit).
            "sig_a": bool(rng.random() < (0.88 if label == 1 else 0.12)),
            "sig_b": bool(rng.random() < (0.88 if label == 0 else 0.12)),
        }
        for name in noises:
            cues[name] = bool(rng.random() < 0.40)  # independent of label
        # Agreement path: majority_vote==truth iff label==1
        sheath.feedback(cues, majority_vote=label, truth=1, key=step)

    grown = sheath.grown_cues()
    admitted = sheath.admitted_cues()
    assert grown == set(signals), {
        "grown": sorted(grown),
        "stats": sheath.stats(),
    }
    assert admitted == set(signals)
    assert not any(name.startswith("noise_") for name in admitted)
    assert sheath.births == 2
    # Top unadmitted merits should be noise and below winners.
    tops = sheath.stats()["top_candidates"]
    noise_merits = [
        row["merit"] for row in tops if row["cue"].startswith("noise_")
    ]
    signal_merits = [
        sheath.candidates[name].merit() for name in signals
    ]
    assert min(signal_merits) > max(noise_merits + [0.0])


def test_needle_with_seeds_does_not_duplicate_seed_signal():
    rng = np.random.default_rng(11)
    pool = ("unanimous", "sig_only") + tuple(f"noise_{i:02d}" for i in range(28))
    sheath = Mnemosheath(
        seed_cues=("unanimous",),
        candidate_cues=pool,
        grow_caps=(0, 1),  # one grown slot — seed already carries the other signal
        n_min=50,
        merit_hi=0.18,
        lead_hi=0.08,
        noise_floor=0.05,
        hysteresis=6,
    )
    for step in range(500):
        label = int(rng.integers(0, 2))
        cues = {
            "unanimous": bool(rng.random() < (0.85 if label == 1 else 0.15)),
            "sig_only": bool(rng.random() < (0.85 if label == 0 else 0.15)),
        }
        for index in range(28):
            cues[f"noise_{index:02d}"] = bool(rng.random() < 0.4)
        sheath.feedback(cues, majority_vote=label, truth=1, key=step)

    grown = sheath.grown_cues()
    assert grown == {"sig_only"}, grown
    assert "unanimous" in sheath.admitted_cues()
    assert sheath.bits[0].seed is True
    assert sum(1 for bit in sheath.bits if bit.cue == "unanimous") == 1


def test_silence_needle_two_vacancy_signals():
    rng = np.random.default_rng(3)
    signals = ("vac_change", "vac_stay")
    noises = tuple(f"silence_noise_{i:02d}" for i in range(28))
    pool = signals + noises
    sheath = Mnemosheath(
        seed_cues=(),
        candidate_cues=pool,
        grow_caps=(0, 1, 2),
        n_min=50,
        merit_hi=0.18,
        lead_hi=0.08,
        noise_floor=0.05,
        hysteresis=6,
    )
    for step in range(650):
        changed = int(rng.integers(0, 2))
        cues = {
            "empty": True,  # opens absence path
            "vac_change": bool(rng.random() < (0.87 if changed else 0.13)),
            "vac_stay": bool(rng.random() < (0.87 if not changed else 0.13)),
        }
        for name in noises:
            cues[name] = bool(rng.random() < 0.4)
        prev = 0
        truth = 1 if changed else 0
        sheath.prime_absence("k", cues, prev_truth=prev, time_since_evidence=2)
        sheath.feedback(cues, majority_vote=None, truth=truth, key="k")

    assert sheath.grown_cues() == set(signals), sheath.stats()
    assert not any("noise" in cue for cue in sheath.grown_cues())
