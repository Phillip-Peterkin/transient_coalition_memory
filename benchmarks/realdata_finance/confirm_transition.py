#!/usr/bin/env python3
"""One-shot untouched-company confirmation for the fixed transition circuit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(ROOT))

from ablation import boot_ci, paired_delta, run_vectors  # noqa: E402
from cures import CuredCellular  # noqa: E402
from evaluate import CELL_PARAMS  # noqa: E402
from stream import FinanceNewsStream  # noqa: E402
from transition import TransitionInvestigator  # noqa: E402

FIXED_TRANSITION_PARAMS = {
    "error_decay": 0.60,
    "ignite_threshold": 0.75,
    "confidence_floor": 0.20,
    "investigate_decay": 0.88,
    "anchor_floor": 0.20,
    "counterevidence_floor": 0.75,
}


def concise(result: dict) -> dict:
    return {
        key: result[key]
        for key in (
            "n",
            "accuracy",
            "flip_accuracy",
            "nonflip_accuracy",
            "flip_n",
            "brier",
            "ece",
            "pred_up_rate",
            "avg_activated",
        )
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, default=ROOT / "data_confirmation")
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "transition_confirmation.json")
    ap.add_argument("--n-boot", type=int, default=5000)
    args = ap.parse_args()

    stream = FinanceNewsStream(args.data_dir)
    baseline = run_vectors(
        stream,
        CuredCellular(cures=("source_calib", "corr_downweight"), **CELL_PARAMS),
        "holdout",
    )
    candidate = run_vectors(
        stream,
        TransitionInvestigator(**FIXED_TRANSITION_PARAMS, **CELL_PARAMS),
        "holdout",
    )

    comparison = {
        "accuracy": paired_delta(
            baseline["correct"], candidate["correct"], n_boot=args.n_boot
        ),
        "flip_accuracy": paired_delta(
            baseline["correct"], candidate["correct"], baseline["flip"], n_boot=args.n_boot
        ),
    }
    confidence = {
        "baseline_accuracy": dict(zip(("mean", "lo", "hi"), boot_ci(baseline["correct"], n_boot=args.n_boot))),
        "candidate_accuracy": dict(zip(("mean", "lo", "hi"), boot_ci(candidate["correct"], n_boot=args.n_boot))),
        "baseline_flip": dict(zip(("mean", "lo", "hi"), boot_ci(baseline["correct"], baseline["flip"], n_boot=args.n_boot))),
        "candidate_flip": dict(zip(("mean", "lo", "hi"), boot_ci(candidate["correct"], candidate["flip"], n_boot=args.n_boot))),
    }
    passed = bool(
        comparison["flip_accuracy"]["delta"] >= 0.03
        and comparison["accuracy"]["delta"] >= -0.01
        and candidate["pred_up_rate"] <= 0.65
    )

    payload = {
        "protocol": "transition_confirmation_v1",
        "fixed_transition_params": FIXED_TRANSITION_PARAMS,
        "stream": stream.summary(),
        "warmup": "first 70% of days; causal state only, not scored",
        "confirmation": {
            "calibrated_baseline": concise(baseline),
            "transition_investigator": concise(candidate),
            "paired_vs_calibrated_baseline": comparison,
            "bootstrap_confidence_intervals": confidence,
            "passes_predeclared_gate": passed,
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, allow_nan=True))

    for name, result in (("calibrated baseline", baseline), ("transition investigator", candidate)):
        print(
            f"{name:24s} acc={result['accuracy']:.4f} flip={result['flip_accuracy']:.4f} "
            f"up={result['pred_up_rate']:.3f} act={result['avg_activated']:.2f} "
            f"brier={result['brier']:.3f}"
        )
    for metric, result in comparison.items():
        print(
            f"{metric:14s} Δ={result['delta']:+.4f} "
            f"[{result['lo']:+.4f}, {result['hi']:+.4f}] p={result['p']:.3f}"
        )
    print(f"passes_predeclared_gate={passed}")


if __name__ == "__main__":
    main()
