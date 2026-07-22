#!/usr/bin/env python3
"""One-shot fresh-company confirmation for Active Coalition Inference.

Protocol: ACTIVE_COALITION_CONFIRMATION_PROTOCOL.md
Universe: confirmation8 (virgin). One look. No retuning.
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
from tcm import (  # noqa: E402
    ActiveCoalitionCellular,
    CleanEvidenceCellular,
    SilenceEscapeCellular,
)

SILENCE_FROZEN = {
    "pe_floor": 0.35,
    "pe_span": 0.50,
    "rho_gain": 0.30,
    "max_hazard": 0.70,
    "apply_to_all_positive": True,
}

FROZEN = {
    "min_delta": 0.15,
    "max_silence_hazard": 0.55,
    "null_rho_gain": 0.30,
    "null_pe_floor": 0.35,
    "null_pe_span": 0.50,
    "null_err_beta": 0.30,
    "force_all_positive_null": True,
    "fe_cert_slack": 0.0,
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
    ap.add_argument("--data-dir", type=Path, default=ROOT / "data_confirmation8")
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "results" / "active_coalition_confirmation.json",
    )
    ap.add_argument("--n-boot", type=int, default=5000)
    args = ap.parse_args()

    stream = SessionRelevanceFinanceNewsStream(args.data_dir)
    clean = run_vectors(stream, CleanEvidenceCellular(**CELL_PARAMS), "holdout")
    silence = run_vectors(
        stream,
        SilenceEscapeCellular(**SILENCE_FROZEN, **CELL_PARAMS),
        "holdout",
    )
    candidate = run_vectors(
        stream,
        ActiveCoalitionCellular(**FROZEN, **CELL_PARAMS),
        "holdout",
    )
    if candidate["n"] != clean["n"] or not (candidate["flip"] == clean["flip"]).all():
        raise RuntimeError("ACI candidate no longer aligns with clean baseline")

    comparison = {
        "vs_clean_accuracy": paired_delta(
            clean["correct"], candidate["correct"], n_boot=args.n_boot
        ),
        "vs_clean_flip": paired_delta(
            clean["correct"],
            candidate["correct"],
            clean["flip"],
            n_boot=args.n_boot,
        ),
        "vs_silence_accuracy": paired_delta(
            silence["correct"], candidate["correct"], n_boot=args.n_boot
        ),
        "vs_silence_flip": paired_delta(
            silence["correct"],
            candidate["correct"],
            silence["flip"],
            n_boot=args.n_boot,
        ),
    }
    intervals = {
        "clean_flip": dict(
            zip(
                ("mean", "lo", "hi"),
                boot_ci(clean["correct"], clean["flip"], n_boot=args.n_boot),
            )
        ),
        "silence_flip": dict(
            zip(
                ("mean", "lo", "hi"),
                boot_ci(silence["correct"], silence["flip"], n_boot=args.n_boot),
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
        and comparison["vs_clean_accuracy"]["delta"] >= -0.01
        and candidate["pred_up_rate"] <= 0.65
        and candidate["nonflip_accuracy"] >= 0.50
    )
    payload = {
        "protocol": "active_coalition_confirmation_v1",
        "fixed_candidate": f"SessionRelevanceFinanceNewsStream + ActiveCoalitionCellular({FROZEN})",
        "baselines": {
            "clean": "CleanEvidenceCellular",
            "silence_escape": f"SilenceEscapeCellular({SILENCE_FROZEN})",
        },
        "universe": "confirmation8_universe",
        "stream": stream.summary(),
        "warmup": "first 70% of dates; causal state only, not scored",
        "confirmation": {
            "clean_baseline": concise(clean),
            "silence_escape": concise(silence),
            "active_coalition": concise(candidate),
            "paired": comparison,
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

    for name, result in (
        ("clean", clean),
        ("silence", silence),
        ("aci", candidate),
    ):
        print(
            f"{name:10s} acc={result['accuracy']:.4f} flip={result['flip_accuracy']:.4f} "
            f"non={result['nonflip_accuracy']:.4f} up={result['pred_up_rate']:.3f} "
            f"act={result['avg_activated']:.2f} flips={result['flip_n']}"
        )
    for metric, result in comparison.items():
        print(
            f"{metric:22s} Δ={result['delta']:+.4f} "
            f"[{result['lo']:+.4f}, {result['hi']:+.4f}] p={result['p']:.3f}"
        )
    print(f"passes_predeclared_gate={passed}")


if __name__ == "__main__":
    main()
