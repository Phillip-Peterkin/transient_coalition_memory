#!/usr/bin/env python3
"""Contact-only test: does causal headline novelty help calibrated TCM?"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(ROOT))

from ablation import paired_delta  # noqa: E402
from cures import CuredCellular  # noqa: E402
from develop_transition import contact_tail_days, score_days  # noqa: E402
from evaluate import CELL_PARAMS  # noqa: E402
from semantic import SemanticFinanceNewsStream  # noqa: E402
from stream import FinanceNewsStream  # noqa: E402


def model():
    return CuredCellular(cures=("source_calib", "corr_downweight"), **CELL_PARAMS)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, default=ROOT / "data")
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "semantic_development.json")
    ap.add_argument("--n-boot", type=int, default=2000)
    args = ap.parse_args()

    ordinary = FinanceNewsStream(args.data_dir)
    scored_days = contact_tail_days(ordinary)
    baseline = score_days(ordinary, model(), scored_days)

    # A small, transparent sweep over the only two semantic knobs.  The
    # headline comparison is causal; this old contact period is design-only.
    variants = {
        "novelty_055_history_6": {"novelty_threshold": 0.55, "history_size": 6},
        "novelty_070_history_6": {"novelty_threshold": 0.70, "history_size": 6},
        "novelty_085_history_6": {"novelty_threshold": 0.85, "history_size": 6},
        "novelty_055_history_12": {"novelty_threshold": 0.55, "history_size": 12},
        "novelty_070_history_12": {"novelty_threshold": 0.70, "history_size": 12},
        "novelty_085_history_12": {"novelty_threshold": 0.85, "history_size": 12},
    }

    results = {"calibrated_baseline": {key: value for key, value in baseline.items() if key not in {"correct", "flip", "stats"}}}
    comparisons = {}
    semantic_summaries = {}
    for name, params in variants.items():
        stream = SemanticFinanceNewsStream(args.data_dir, **params)
        current = score_days(stream, model(), scored_days)
        if current["n"] != baseline["n"] or not (current["flip"] == baseline["flip"]).all():
            raise RuntimeError("semantic stream no longer aligns with baseline events")
        results[name] = {key: value for key, value in current.items() if key not in {"correct", "flip", "stats"}}
        comparisons[name] = {
            "accuracy": paired_delta(baseline["correct"], current["correct"], n_boot=args.n_boot),
            "flip_accuracy": paired_delta(
                baseline["correct"], current["correct"], baseline["flip"], n_boot=args.n_boot
            ),
        }
        semantic_summaries[name] = stream.summary()

    eligible = [
        name
        for name, change in comparisons.items()
        if change["flip_accuracy"]["delta"] >= 0.03
        and change["accuracy"]["delta"] >= -0.01
        and results[name]["pred_up_rate"] <= 0.65
    ]
    winner = max(eligible, key=lambda name: comparisons[name]["flip_accuracy"]["delta"]) if eligible else None

    payload = {
        "protocol": "contact_tail_semantic_development_v1",
        "n_scored_days": len(scored_days),
        "results": results,
        "vs_calibrated_baseline": comparisons,
        "semantic_streams": semantic_summaries,
        "selection_rule": (
            "flip gain >= 0.03, accuracy drop < 0.01, prediction-up rate <= 0.65; "
            "confirmation requires a fresh ticker universe."
        ),
        "selected_for_fresh_confirmation": winner,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, allow_nan=True))

    print(f"contact-tail days={len(scored_days)} events={baseline['n']} flips={baseline['flip_n']}")
    print(f"{'candidate':25s} {'acc':>7s} {'flip':>7s} {'act':>6s} {'up':>6s} {'flip Δ':>9s} {'novel':>7s}")
    for name in ("calibrated_baseline", *variants):
        result = results[name]
        if name == "calibrated_baseline":
            delta = 0.0
            novel = 0.0
        else:
            delta = comparisons[name]["flip_accuracy"]["delta"]
            novel = semantic_summaries[name]["novel_report_fraction"]
        print(
            f"{name:25s} {result['accuracy']:.4f} {result['flip_accuracy']:.4f} "
            f"{result['avg_activated']:6.2f} {result['pred_up_rate']:.3f} {delta:+.4f} {novel:.3f}"
        )
    print(f"selected_for_fresh_confirmation={winner}")


if __name__ == "__main__":
    main()
