#!/usr/bin/env python3
"""Contact-tail push against publisher Positive skew.

Builds on the cleaned session stream + sign-preserving evidence path.
Rejects last-truth mean-reversion (it hacks the flip metric).  Tests a
predeclared publisher base-rate correction on all-Positive coalitions.
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

from ablation import paired_delta  # noqa: E402
from develop_transition import contact_tail_days, score_days  # noqa: E402
from evaluate import CELL_PARAMS  # noqa: E402
from session_stream import SessionRelevanceFinanceNewsStream  # noqa: E402
from tcm import CleanEvidenceCellular, SkewCorrectedCellular  # noqa: E402

# Predeclared before inspecting contact-tail scores.
SCALE_GRID = (1.0, 1.25, 1.5)


def concise(result: dict) -> dict:
    return {
        key: value
        for key, value in result.items()
        if key not in {"correct", "flip", "stats"}
    }


def passes_gate(result: dict, baseline: dict) -> bool:
    return bool(
        result["flip_accuracy"] >= 0.45
        and result["pred_up_rate"] <= 0.65
        and result["accuracy"] >= baseline["accuracy"] - 0.01
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument(
        "--out", type=Path, default=ROOT / "results" / "skew_development.json"
    )
    parser.add_argument("--n-boot", type=int, default=2000)
    args = parser.parse_args()

    stream = SessionRelevanceFinanceNewsStream(args.data_dir)
    days = contact_tail_days(stream)
    baseline = score_days(stream, CleanEvidenceCellular(**CELL_PARAMS), days)

    cells = {"clean_baseline": baseline}
    comparisons = {}
    for scale in SCALE_GRID:
        name = f"skew_scale_{scale:g}"
        result = score_days(
            stream,
            SkewCorrectedCellular(base_rate_scale=scale, **CELL_PARAMS),
            days,
        )
        cells[name] = result
        comparisons[name] = {
            "accuracy": paired_delta(
                baseline["correct"], result["correct"], n_boot=args.n_boot
            ),
            "flip_accuracy": paired_delta(
                baseline["correct"],
                result["correct"],
                baseline["flip"],
                n_boot=args.n_boot,
            ),
        }

    winners = [
        name
        for name, result in cells.items()
        if name != "clean_baseline" and passes_gate(result, baseline)
    ]
    # Prefer the smallest theoretical scale that clears the gate.
    winner = None
    for scale in SCALE_GRID:
        name = f"skew_scale_{scale:g}"
        if name in winners:
            winner = name
            break

    payload = {
        "protocol": "finance_skew_correction_development_v1",
        "rejected": (
            "last_truth mean-reversion on cheerleader coalitions: it predicts "
            "the opposite of the previous label and hacks flip accuracy while "
            "destroying non-flip accuracy."
        ),
        "mechanism": (
            "For all-Positive coalitions, subtract "
            "scale * mean[logit(P_emit+) - logit(0.5)] from the decision logit. "
            "Report signs remain preserved."
        ),
        "scale_grid": list(SCALE_GRID),
        "stream": stream.summary(),
        "cells": {name: concise(result) for name, result in cells.items()},
        "paired_vs_clean": comparisons,
        "gate": {
            "flip_accuracy_min": 0.45,
            "pred_up_rate_max": 0.65,
            "accuracy_max_drop": 0.01,
        },
        "winners": winners,
        "selected_winner": winner,
        "passes_development_gate": winner is not None,
        "note": (
            "Contact-tail only. A winner still needs a fresh-company confirmation. "
            "Prediction-up may land well below 50% after full cheerleader correction; "
            "that mirror bias is reported, not hidden."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, allow_nan=True))

    for name, result in cells.items():
        print(
            f"{name:20s} acc={result['accuracy']:.4f} flip={result['flip_accuracy']:.4f} "
            f"non={result['nonflip_accuracy']:.4f} up={result['pred_up_rate']:.3f} "
            f"act={result['avg_activated']:.2f}"
        )
    for name, comps in comparisons.items():
        for metric, result in comps.items():
            print(
                f"{name}/{metric}: Δ={result['delta']:+.4f} "
                f"[{result['lo']:+.4f}, {result['hi']:+.4f}] p={result['p']:.3f}"
            )
    print(f"selected_winner={winner}")
    print(f"passes_development_gate={winner is not None}")


if __name__ == "__main__":
    main()
