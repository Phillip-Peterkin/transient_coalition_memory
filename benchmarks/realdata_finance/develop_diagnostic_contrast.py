#!/usr/bin/env python3
"""Contact-tail screen for diagnostic-contrast (DCAI laws inside TCM).

One mechanism. Development lens only. No fresh-universe look here.

Bakes into SilenceEscapeCellular:
  - confirmed cheerleader-null kept
  - slot preserve-cloud null (memory-paraphrase is not sensation)
  - typed paraphrase demotion on slot-edit paths
  - PE+|rho| sum escape (survival noisy-OR over those scalars is off)
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
from tcm import (  # noqa: E402
    CleanEvidenceCellular,
    DiagnosticContrastCellular,
    SilenceEscapeCellular,
)

SILENCE_FROZEN = {
    "pe_floor": 0.35,
    "pe_span": 0.50,
    "rho_gain": 0.30,
    "max_hazard": 0.70,
    "apply_to_all_positive": True,
}

# Predeclared before inspecting scores.
GRID = (
    {"slot_preserve_scale": 0.35, "use_slot_null": True, "use_survival_hazard": False},
    {"slot_preserve_scale": 0.50, "use_slot_null": True, "use_survival_hazard": False},
    {"slot_preserve_scale": 0.65, "use_slot_null": True, "use_survival_hazard": False},
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
        default=ROOT / "results" / "diagnostic_contrast_development.json",
    )
    parser.add_argument("--n-boot", type=int, default=2000)
    args = parser.parse_args()

    stream = SessionRelevanceFinanceNewsStream(args.data_dir)
    days = contact_tail_days(stream)
    clean = score_days(stream, CleanEvidenceCellular(**CELL_PARAMS), days)
    silence = score_days(
        stream,
        SilenceEscapeCellular(**SILENCE_FROZEN, **CELL_PARAMS),
        days,
    )

    cells = {"clean_baseline": clean, "silence_escape": silence}
    comparisons = {}
    for params in GRID:
        name = f"dcai_slot{params['slot_preserve_scale']:g}"
        result = score_days(
            stream,
            DiagnosticContrastCellular(**SILENCE_FROZEN, **params, **CELL_PARAMS),
            days,
        )
        cells[name] = result
        comparisons[name] = {
            "vs_clean_accuracy": paired_delta(
                clean["correct"], result["correct"], n_boot=args.n_boot
            ),
            "vs_clean_flip": paired_delta(
                clean["correct"],
                result["correct"],
                clean["flip"],
                n_boot=args.n_boot,
            ),
            "vs_silence_flip": paired_delta(
                silence["correct"],
                result["correct"],
                silence["flip"],
                n_boot=args.n_boot,
            ),
        }

    winners = [
        name
        for name, result in cells.items()
        if name.startswith("dcai_") and passes_gate(result, clean)
    ]
    winner = None
    if winners:
        winner = max(
            winners,
            key=lambda name: (
                cells[name]["flip_accuracy"] - silence["flip_accuracy"],
                cells[name]["flip_accuracy"],
                cells[name]["nonflip_accuracy"],
                cells[name]["accuracy"],
            ),
        )

    payload = {
        "protocol": "finance_diagnostic_contrast_development_v1",
        "mechanism": (
            "DCAI laws inside SilenceEscapeCellular: cheerleader-null kept, "
            "slot preserve-cloud null, paraphrase demotion on edits; sum escape."
        ),
        "grid": list(GRID),
        "silence_frozen": SILENCE_FROZEN,
        "selection": (
            "Among gate passers vs clean (flip>=0.45, acc drop<0.01, up<=0.65, "
            "nonflip>=0.50) pick max (flip-silence, flip, nonflip, acc)."
        ),
        "cells": {name: concise(result) for name, result in cells.items()},
        "paired": comparisons,
        "winners": winners,
        "selected_winner": winner,
        "passes_development_gate": winner is not None,
        "note": (
            "Contact-tail only. Fresh confirmation requires confirmation5 and a "
            "frozen one-shot protocol — not this script."
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
