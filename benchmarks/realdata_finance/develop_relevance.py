#!/usr/bin/env python3
"""Contact-only test of the explicit-company sensory relevance gate."""

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
from relevance import RelevanceFinanceNewsStream, RelevanceGatedCellular  # noqa: E402
from stream import FinanceNewsStream  # noqa: E402


def model():
    return CuredCellular(cures=("source_calib", "corr_downweight"), **CELL_PARAMS)


def concise(result: dict) -> dict:
    return {
        key: value
        for key, value in result.items()
        if key not in {"correct", "flip", "stats"}
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, default=ROOT / "data")
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "relevance_development.json")
    ap.add_argument("--n-boot", type=int, default=2000)
    args = ap.parse_args()

    ordinary = FinanceNewsStream(args.data_dir)
    days = contact_tail_days(ordinary)
    baseline = score_days(ordinary, model(), days)

    relevance_stream = RelevanceFinanceNewsStream(args.data_dir)
    relevant = score_days(
        relevance_stream,
        RelevanceGatedCellular(cures=("source_calib", "corr_downweight"), **CELL_PARAMS),
        days,
    )
    if relevant["n"] != baseline["n"] or not (relevant["flip"] == baseline["flip"]).all():
        raise RuntimeError("relevance stream no longer aligns with baseline events")

    comparison = {
        "accuracy": paired_delta(baseline["correct"], relevant["correct"], n_boot=args.n_boot),
        "flip_accuracy": paired_delta(
            baseline["correct"], relevant["correct"], baseline["flip"], n_boot=args.n_boot
        ),
    }
    passes_development_gate = bool(
        comparison["flip_accuracy"]["delta"] >= 0.03
        and comparison["accuracy"]["delta"] >= -0.01
        and relevant["pred_up_rate"] <= 0.65
    )
    payload = {
        "protocol": "contact_tail_relevance_development_v1",
        "n_scored_days": len(days),
        "calibrated_baseline": concise(baseline),
        "relevance_gated": concise(relevant),
        "stream": relevance_stream.summary(),
        "paired_vs_calibrated_baseline": comparison,
        "passes_development_gate": passes_development_gate,
        "rule": (
            "flip gain >= 0.03, accuracy drop < 0.01, prediction-up rate <= 0.65; "
            "a separate fresh universe is required for any claim."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, allow_nan=True))

    for name, result in (("calibrated baseline", baseline), ("relevance gated", relevant)):
        print(
            f"{name:20s} acc={result['accuracy']:.4f} flip={result['flip_accuracy']:.4f} "
            f"up={result['pred_up_rate']:.3f} act={result['avg_activated']:.2f}"
        )
    for metric, result in comparison.items():
        print(
            f"{metric:14s} Δ={result['delta']:+.4f} "
            f"[{result['lo']:+.4f}, {result['hi']:+.4f}] p={result['p']:.3f}"
        )
    print(
        f"relevant_articles={relevance_stream.summary()['relevant_article_fraction']:.3f} "
        f"events_with_no_relevant_reports={relevance_stream.events_without_relevant_reports}"
    )
    print(f"passes_development_gate={passes_development_gate}")


if __name__ == "__main__":
    main()
