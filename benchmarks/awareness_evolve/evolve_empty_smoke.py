#!/usr/bin/env python3
"""Grow silence bits under emptiness alone (no majority teacher)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from tcm import Mnemosheath  # noqa: E402


def main() -> None:
    sheath = Mnemosheath(dwell=4, split_merit=0.05)
    key = "solo"
    history = []
    for step in range(120):
        cues = {
            "empty": True,
            "long_vacancy": step % 5 >= 3,
            "fresh_vacancy": step % 5 < 2,
            "empty_after_flip": step % 4 == 0,
            "empty_after_stay": step % 4 != 0,
            "high_pe": step % 6 == 0,
        }
        prev = 0 if step % 3 else 1
        sheath.prime_absence(key, cues, prev_truth=prev, time_since_evidence=step % 7)
        truth = 1 - prev if step % 3 == 0 else prev  # occasional change
        sheath.feedback(cues, majority_vote=None, truth=truth, key=key)
        if step in {0, 19, 39, 79, 119}:
            history.append({"step": step, **sheath.stats()})
    assert sheath.empty_lessons >= 100
    assert sheath.bit_count >= 3
    print(json.dumps({"final": sheath.stats(), "history": history}, indent=2))
    print("evolve_empty_smoke: silence curriculum matured")


if __name__ == "__main__":
    main()
