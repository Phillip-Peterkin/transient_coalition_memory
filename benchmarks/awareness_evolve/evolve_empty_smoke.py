#!/usr/bin/env python3
"""Empty curriculum smoke: only predictive vacancy cues may grow."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from tcm import Mnemosheath  # noqa: E402


def main() -> None:
    rng = np.random.default_rng(0)
    pool = ("empty", "vac_change", "vac_stay") + tuple(
        f"silence_noise_{i:02d}" for i in range(10)
    )
    sheath = Mnemosheath(
        seed_cues=("empty",),
        candidate_cues=pool,
        grow_caps=(0, 1, 2),
        n_min=40,
        merit_hi=0.18,
        lead_hi=0.08,
        hysteresis=5,
    )
    for step in range(500):
        changed = int(rng.integers(0, 2))
        cues = {
            "empty": True,
            "vac_change": bool(rng.random() < (0.88 if changed else 0.12)),
            "vac_stay": bool(rng.random() < (0.88 if not changed else 0.12)),
        }
        for index in range(10):
            cues[f"silence_noise_{index:02d}"] = bool(rng.random() < 0.4)
        sheath.prime_absence("solo", cues, prev_truth=0, time_since_evidence=2)
        sheath.feedback(
            cues, majority_vote=None, truth=(1 if changed else 0), key="solo"
        )
    grown = sheath.grown_cues()
    assert grown == {"vac_change", "vac_stay"}, grown
    assert not any("noise" in cue for cue in grown)
    print(json.dumps(sheath.stats(), indent=2))
    print("evolve_empty_smoke: selective silence growth OK")


if __name__ == "__main__":
    main()
