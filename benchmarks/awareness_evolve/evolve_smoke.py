#!/usr/bin/env python3
"""Grow a Mnemosheath from 1 bit toward higher stages on synthetic cues."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from tcm import Mnemosheath  # noqa: E402


def main() -> None:
    sheath = Mnemosheath(dwell=4, split_merit=0.05)
    history = []
    for step in range(200):
        # Alternate trustworthy unanimity with cheerleader noise episodes.
        if step % 17 < 12:
            cues = {
                "unanimous": True,
                "unanimous_pos": True,
                "high_agree": True,
                "wide_margin": True,
            }
            truth = 1
            majority = 1
        else:
            cues = {
                "unanimous": True,
                "unanimous_pos": True,
                "high_agree": True,
                "thin_margin": True,
            }
            truth = step % 2
            majority = 1
        live = {bit.cue: cues.get(bit.cue, False) for bit in sheath.bits}
        # Ensure parent cue still observed.
        live["unanimous"] = True
        sheath.feedback(live, majority_vote=majority, truth=truth)
        if step in {0, 9, 24, 49, 99, 199}:
            history.append({"step": step, **sheath.stats()})
    print(json.dumps({"final": sheath.stats(), "history": history}, indent=2))
    assert sheath.bit_count >= 2, sheath.stats()
    print("evolve_smoke: matured beyond 1 bit")


if __name__ == "__main__":
    main()
