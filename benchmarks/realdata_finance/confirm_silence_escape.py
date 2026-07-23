#!/usr/bin/env python3
"""One-shot fresh-company confirmation for frozen silence escape.

Protocol: SILENCE_ESCAPE_CONFIRMATION_PROTOCOL.md
Universe: confirmation4 (virgin). One look. No retuning.
"""

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
from evaluate import CELL_PARAMS  # noqa: E402
from session_stream import SessionRelevanceFinanceNewsStream  # noqa: E402
from tcm import CleanEvidenceCellular, SilenceEscapeCellular  # noqa: E402

FROZEN = {
    "pe_floor": 0.35,
    "pe_span": 0.50,
    "rho_gain": 0.30,
    "max_hazard": 0.70,
    "apply_to_all_positive": True,
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
    ap.add_argument("--data-dir", type=Path, default=ROOT / "data_confirmation4")
    ap.add_argument(
        "--out", type=Path, default=ROOT / "results" / "silence_escape_confirmation.json"
    )
    ap.add_argument("--n-boot", type=int, default=5000)
    args = ap.parse_args()

    stream = SessionRelevanceFinanceNewsStream(args.data_dir)
    baseline = run_vectors(stream, CleanEvidenceCellular(**CELL_PARAMS), "holdout")
    candidate = run_vectors(
        stream,
        SilenceEscapeCellular(**FROZEN, **CELL_PARAMS),
        "holdout",
    )
    if candidate["n"] != baseline["n"] or not (candidate["flip"] == baseline["flip"]).all():
        raise RuntimeError("silence-escape candidate no longer aligns with clean baseline")

    comparison = {
        "accuracy": paired_delta(
            baseline["correct"], candidate["correct"], n_boot=args.n_boot
        ),
        "flip_accuracy": paired_delta(
            baseline["correct"],
            candidate["correct"],
            baseline["flip"],
            n_boot=args.n_boot,
        ),
    }
    intervals = {
        "baseline_accuracy": dict(
            zip(("mean", "lo", "hi"), boot_ci(baseline["correct"], n_boot=args.n_boot))
        ),
        "candidate_accuracy": dict(
            zip(("mean", "lo", "hi"), boot_ci(candidate["correct"], n_boot=args.n_boot))
        ),
        "baseline_flip": dict(
            zip(
                ("mean", "lo", "hi"),
                boot_ci(baseline["correct"], baseline["flip"], n_boot=args.n_boot),
            )
        ),
        "candidate_flip": dict(
            zip(
                ("mean", "lo", "hi"),
                boot_ci(candidate["correct"], candidate["flip"], n_boot=args.n_boot),
            )
        ),
    }
    passed = bool(
        candidate["flip_accuracy"] >= 0.45
        and comparison["accuracy"]["delta"] >= -0.01
        and candidate["pred_up_rate"] <= 0.65
        and candidate["nonflip_accuracy"] >= 0.50
    )
    payload = {
        "protocol": "silence_escape_confirmation_v1",
        "fixed_candidate": f"SessionRelevanceFinanceNewsStream + SilenceEscapeCellular({FROZEN})",
        "baseline": "same stream + CleanEvidenceCellular",
        "universe": "confirmation4_universe",
        "stream": stream.summary(),
        "warmup": "first 70% of dates; causal state only, not scored",
        "confirmation": {
            "clean_baseline": concise(baseline),
            "silence_escape": concise(candidate),
            "paired_vs_clean_baseline": comparison,
            "bootstrap_confidence_intervals": intervals,
            "passes_predeclared_gate": passed,
            "gate": {
                "flip_accuracy_min": 0.45,
                "accuracy_max_drop_vs_clean": 0.01,
                "pred_up_rate_max": 0.65,
                "nonflip_accuracy_min": 0.50,
            },
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, allow_nan=True))

    for name, result in (("clean baseline", baseline), ("silence escape", candidate)):
        print(
            f"{name:16s} acc={result['accuracy']:.4f} flip={result['flip_accuracy']:.4f} "
            f"non={result['nonflip_accuracy']:.4f} up={result['pred_up_rate']:.3f} "
            f"act={result['avg_activated']:.2f} flips={result['flip_n']}"
        )
    for metric, result in comparison.items():
        print(
            f"{metric:14s} Δ={result['delta']:+.4f} "
            f"[{result['lo']:+.4f}, {result['hi']:+.4f}] p={result['p']:.3f}"
        )
    print(f"passes_predeclared_gate={passed}")


if __name__ == "__main__":
    main()
