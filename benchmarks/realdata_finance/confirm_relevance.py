#!/usr/bin/env python3
"""One-shot fresh-company confirmation for the fixed sensory relevance gate."""

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
from relevance import RelevanceFinanceNewsStream  # noqa: E402
from stream import FinanceNewsStream  # noqa: E402
from tcm import SensoryGatedCellular  # noqa: E402


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
    ap.add_argument("--data-dir", type=Path, default=ROOT / "data_confirmation2")
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "relevance_confirmation.json")
    ap.add_argument("--n-boot", type=int, default=5000)
    args = ap.parse_args()

    ordinary = FinanceNewsStream(args.data_dir)
    relevance = RelevanceFinanceNewsStream(args.data_dir)
    baseline = run_vectors(
        ordinary,
        CuredCellular(cures=("source_calib", "corr_downweight"), **CELL_PARAMS),
        "holdout",
    )
    gated = run_vectors(
        relevance,
        SensoryGatedCellular(**CELL_PARAMS),
        "holdout",
    )
    if gated["n"] != baseline["n"] or not (gated["flip"] == baseline["flip"]).all():
        raise RuntimeError("relevance stream no longer aligns with baseline events")

    comparison = {
        "accuracy": paired_delta(baseline["correct"], gated["correct"], n_boot=args.n_boot),
        "flip_accuracy": paired_delta(
            baseline["correct"], gated["correct"], baseline["flip"], n_boot=args.n_boot
        ),
    }
    intervals = {
        "baseline_accuracy": dict(zip(("mean", "lo", "hi"), boot_ci(baseline["correct"], n_boot=args.n_boot))),
        "gated_accuracy": dict(zip(("mean", "lo", "hi"), boot_ci(gated["correct"], n_boot=args.n_boot))),
        "baseline_flip": dict(zip(("mean", "lo", "hi"), boot_ci(baseline["correct"], baseline["flip"], n_boot=args.n_boot))),
        "gated_flip": dict(zip(("mean", "lo", "hi"), boot_ci(gated["correct"], gated["flip"], n_boot=args.n_boot))),
    }
    passed = bool(
        comparison["flip_accuracy"]["delta"] >= 0.03
        and comparison["accuracy"]["delta"] >= -0.01
        and gated["pred_up_rate"] <= 0.65
    )
    payload = {
        "protocol": "relevance_confirmation_v1",
        "fixed_candidate": "source calibration + correlation discount + explicit title relevance + memory fallback",
        "stream": relevance.summary(),
        "warmup": "first 70% of dates; causal state only, not scored",
        "confirmation": {
            "calibrated_baseline": concise(baseline),
            "relevance_gated": concise(gated),
            "paired_vs_calibrated_baseline": comparison,
            "bootstrap_confidence_intervals": intervals,
            "passes_predeclared_gate": passed,
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, allow_nan=True))

    for name, result in (("calibrated baseline", baseline), ("relevance gated", gated)):
        print(
            f"{name:20s} acc={result['accuracy']:.4f} flip={result['flip_accuracy']:.4f} "
            f"up={result['pred_up_rate']:.3f} act={result['avg_activated']:.2f} "
            f"brier={result['brier']:.3f}"
        )
    for metric, result in comparison.items():
        print(
            f"{metric:14s} Δ={result['delta']:+.4f} "
            f"[{result['lo']:+.4f}, {result['hi']:+.4f}] p={result['p']:.3f}"
        )
    print(
        f"relevant_articles={relevance.summary()['relevant_article_fraction']:.3f} "
        f"events_with_no_relevant_reports={relevance.events_without_relevant_reports}"
    )
    print(f"passes_predeclared_gate={passed}")


if __name__ == "__main__":
    main()
