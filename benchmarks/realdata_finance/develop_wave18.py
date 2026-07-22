#!/usr/bin/env python3
"""Finance-only development ablation for Wave XVIII's trust loop."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(ROOT))

from ablation import paired_delta  # noqa: E402
from develop_transition import contact_tail_days  # noqa: E402
from evaluate import CELL_PARAMS  # noqa: E402
from relevance import RelevanceFinanceNewsStream  # noqa: E402
from tcm import SensoryGatedCellular, WaveXVIIITrustCellular  # noqa: E402


WAVE_XVIII_CANDIDATES = {
    "light": {
        "mistrust_gain": 0.50,
        "correct_relaxation": 0.30,
        "trust_hazard_gain": 0.15,
        "anchor_floor": 0.55,
        "fresh_evidence_floor": 0.50,
    },
    "balanced": {
        "mistrust_gain": 0.75,
        "correct_relaxation": 0.40,
        "trust_hazard_gain": 0.25,
        "anchor_floor": 0.35,
        "fresh_evidence_floor": 0.75,
    },
    "strong": {
        "mistrust_gain": 1.00,
        "correct_relaxation": 0.50,
        "trust_hazard_gain": 0.35,
        "anchor_floor": 0.15,
        "fresh_evidence_floor": 1.00,
    },
}
COMMON = {"confidence_threshold": 0.20, "recruit_threshold": 0.50}


def score_days(stream, model, days: set[str]) -> dict:
    queue: dict[int, list] = defaultdict(list)
    records = []
    mistrust = []
    anchor_scales = []
    floors = []
    extra = []

    for event in stream.events:
        for feedback in queue.pop(event.t, []):
            model.feedback(feedback)
        probability, trace = model.predict(event.key, event.reports, event.t)
        queue[event.t + 1].append(
            {
                "key": event.key,
                "reports": event.reports,
                "truth": event.truth,
                "pred": probability,
                "trace": trace,
                "time": event.t + 1,
            }
        )
        if event.day not in days:
            continue
        correct = int((probability >= 0.5) == event.truth)
        records.append(
            (
                correct,
                event.prev_truth is not None and event.truth != event.prev_truth,
                probability >= 0.5,
                trace["used"],
            )
        )
        mistrust.append(trace.get("mistrust", 0.0))
        anchor_scales.append(trace.get("anchor_scale", 1.0))
        floors.append(trace.get("fresh_evidence_floor", 0.0))
        extra.append(trace.get("extra_recruited", 0))

    data = np.asarray(records, float)
    correct = data[:, 0]
    flip = data[:, 1].astype(bool)
    return {
        "correct": correct,
        "flip": flip,
        "accuracy": float(correct.mean()),
        "flip_accuracy": float(correct[flip].mean()),
        "nonflip_accuracy": float(correct[~flip].mean()),
        "n": int(len(correct)),
        "flip_n": int(flip.sum()),
        "pred_up_rate": float(data[:, 2].mean()),
        "avg_activated": float(data[:, 3].mean()),
        "mean_mistrust": float(np.mean(mistrust)),
        "mean_anchor_scale": float(np.mean(anchor_scales)),
        "mean_fresh_floor": float(np.mean(floors)),
        "extra_recruitment_rate": float(np.mean(extra)),
        "stats": model.stats(),
    }


def public(result: dict) -> dict:
    return {key: value for key, value in result.items() if key not in {"correct", "flip"}}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, default=ROOT / "data")
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "wave18_development.json")
    ap.add_argument("--n-boot", type=int, default=2000)
    args = ap.parse_args()

    stream = RelevanceFinanceNewsStream(args.data_dir)
    days = contact_tail_days(stream)
    baseline = score_days(stream, SensoryGatedCellular(**CELL_PARAMS), days)
    all_results = {"sensory_baseline": public(baseline)}
    comparisons = {}

    for name, params in WAVE_XVIII_CANDIDATES.items():
        model = WaveXVIIITrustCellular(**COMMON, **params, **CELL_PARAMS)
        current = score_days(stream, model, days)
        all_results[name] = public(current)
        comparisons[name] = {
            "accuracy": paired_delta(
                baseline["correct"], current["correct"], n_boot=args.n_boot
            ),
            "flip_accuracy": paired_delta(
                baseline["correct"], current["correct"], baseline["flip"], n_boot=args.n_boot
            ),
        }

    eligible = [
        name
        for name, result in all_results.items()
        if name != "sensory_baseline"
        and result["flip_accuracy"] >= 0.45
        and result["accuracy"] >= baseline["accuracy"] - 0.01
        and result["pred_up_rate"] <= 0.65
        and result["avg_activated"] <= baseline["avg_activated"] + 0.25
    ]
    winner = max(eligible, key=lambda name: all_results[name]["flip_accuracy"]) if eligible else None
    payload = {
        "protocol": "wave_xviii_finance_development_v1",
        "scored_days": sorted(days),
        "results": all_results,
        "vs_sensory_baseline": comparisons,
        "selection_rule": (
            "flip >= 0.45; accuracy >= baseline - 0.01; prediction-up <= 0.65; "
            "activation <= baseline + 0.25. Weather is not read."
        ),
        "selected_for_weather": winner,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, allow_nan=True))

    print(f"finance development: {len(days)} days, {baseline['n']} events, {baseline['flip_n']} flips")
    print(
        f"{'candidate':17s} {'acc':>7s} {'flip':>7s} {'up':>6s} {'act':>6s} "
        f"{'trust':>7s} {'anchor':>7s} {'extra':>6s}"
    )
    for name, result in all_results.items():
        print(
            f"{name:17s} {result['accuracy']:.4f} {result['flip_accuracy']:.4f} "
            f"{result['pred_up_rate']:.3f} {result['avg_activated']:6.2f} "
            f"{result['mean_mistrust']:.3f} {result['mean_anchor_scale']:.3f} "
            f"{result['extra_recruitment_rate']:.3f}"
        )
    for name, comparison in comparisons.items():
        change = comparison["flip_accuracy"]
        print(
            f"{name} flip delta={change['delta']:+.4f} "
            f"[{change['lo']:+.4f}, {change['hi']:+.4f}] p={change['p']:.3f}"
        )
    print(f"selected_for_weather={winner}")


if __name__ == "__main__":
    main()
