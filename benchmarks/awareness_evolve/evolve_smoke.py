#!/usr/bin/env python3
"""Agreement curriculum smoke: 2 signals amid noise."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from tcm import Mnemosheath  # noqa: E402


def main() -> None:
    rng = np.random.default_rng(1)
    pool = ("sig_a", "sig_b") + tuple(f"noise_{i:02d}" for i in range(28))
    sheath = Mnemosheath(
        seed_cues=(),
        candidate_cues=pool,
        grow_caps=(0, 1, 2),
        n_min=50,
        merit_hi=0.18,
        lead_hi=0.08,
        hysteresis=6,
    )
    for step in range(700):
        label = int(rng.integers(0, 2))
        cues = {
            "sig_a": bool(rng.random() < (0.88 if label == 1 else 0.12)),
            "sig_b": bool(rng.random() < (0.88 if label == 0 else 0.12)),
        }
        for index in range(28):
            cues[f"noise_{index:02d}"] = bool(rng.random() < 0.4)
        sheath.feedback(cues, majority_vote=label, truth=1, key=step)
    assert sheath.grown_cues() == {"sig_a", "sig_b"}, sheath.grown_cues()
    print(json.dumps(sheath.stats(), indent=2))
    print("evolve_smoke: needle-selective maturation OK")


if __name__ == "__main__":
    main()
