#!/usr/bin/env python3
"""Contact-tail screen for silence / cheerleader attractor escape.

One mechanism. Development lens only. No fresh-universe look here.

Insight (from burned confirmation autopsy, not used for tuning): under sensory
silence, memory is anti-correlated with the next move. Escape hazard is driven
by prediction-error EWMA and belief criticality — never by the previous label.
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
from tcm import CleanEvidenceCellular, SilenceEscapeCellular  # noqa: E402

# Predeclared before inspecting this script's scores.
GRID = (
    {"pe_floor": 0.35, "pe_span": 0.35, "rho_gain": 0.30, "max_hazard": 0.70},
    {"pe_floor": 0.35, "pe_span": 0.50, "rho_gain": 0.30, "max_hazard": 0.70},
    {"pe_floor": 0.40, "pe_span": 0.35, "rho_gain": 0.30, "max_hazard": 0.70},
)


def concise(result: dict) -> dict:
    return {
        key: value
        for key, value in result.items()
        if key not in {"correct", "flip", "stats"}
    }


def passes_gate(result: dict, baseline: dict) -> bool:
    return bool(
        result["flip_accuracy"] >= 0.45
        and result["accuracy"] >= baseline["accuracy"] - 0.01
        and result["pred_up_rate"] <= 0.65
        and result["nonflip_accuracy"] >= 0.50
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "results" / "silence_escape_development.json",
    )
    parser.add_argument("--n-boot", type=int, default=2000)
    args = parser.parse_args()

    stream = SessionRelevanceFinanceNewsStream(args.data_dir)
    days = contact_tail_days(stream)
    baseline = score_days(stream, CleanEvidenceCellular(**CELL_PARAMS), days)

    cells = {"clean_baseline": baseline}
    comparisons = {}
    for params in GRID:
        name = (
            f"escape_floor{params['pe_floor']:g}"
            f"_span{params['pe_span']:g}"
            f"_rho{params['rho_gain']:g}"
            f"_maxh{params['max_hazard']:g}"
        )
        result = score_days(
            stream,
            SilenceEscapeCellular(
                apply_to_all_positive=True,
                **params,
                **CELL_PARAMS,
            ),
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
    # Prefer higher flip, then higher non-flip, among gate passers.
    winner = None
    if winners:
        winner = max(
            winners,
            key=lambda name: (
                cells[name]["flip_accuracy"],
                cells[name]["nonflip_accuracy"],
                cells[name]["accuracy"],
            ),
        )

    payload = {
        "protocol": "finance_silence_escape_development_v1",
        "mechanism": (
            "Null sensation (empty or all-Positive) + PE/rho escape hazard "
            "mixes memory toward anti-memory. Mixed/negative reports keep "
            "clean evidence."
        ),
        "grid": list(GRID),
        "selection": (
            "apply_to_all_positive=True fixed; among gate passers "
            "(flip>=0.45, acc drop<0.01, up<=0.65, nonflip>=0.50) pick max "
            "flip then nonflip."
        ),
        "cells": {name: concise(result) for name, result in cells.items()},
        "paired_vs_clean": comparisons,
        "winners": winners,
        "selected_winner": winner,
        "passes_development_gate": winner is not None,
        "note": (
            "Contact-tail only. Fresh confirmation requires a new virgin "
            "universe and a frozen one-shot protocol — not this script."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, allow_nan=True))

    for name, result in cells.items():
        print(
            f"{name:40s} acc={result['accuracy']:.4f} flip={result['flip_accuracy']:.4f} "
            f"non={result['nonflip_accuracy']:.4f} up={result['pred_up_rate']:.3f}"
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
