#!/usr/bin/env python3
"""Small, contact-only design tests for the transition-investigation circuit.

The old holdout has already informed previous work, so this script never scores
it.  It replays the full stream causally but scores only the final 30% of the
already-contacted days.  That gives us a small development signal for choosing
whether the circuit deserves a truly fresh ticker-universe confirmation.
"""

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
from cures import CuredCellular  # noqa: E402
from evaluate import CELL_PARAMS  # noqa: E402
from stream import FinanceNewsStream  # noqa: E402
from transition import TransitionInvestigator  # noqa: E402


def contact_tail_days(stream: FinanceNewsStream, fraction: float = 0.30) -> set[str]:
    days = sorted({event.day for event in stream.events if event.split == "contact"})
    return set(days[int((1.0 - fraction) * len(days)) :])


def score_days(stream: FinanceNewsStream, model, days: set[str]) -> dict:
    """Replay causally; score only events belonging to selected days."""
    feedback_queue: dict[int, list] = defaultdict(list)
    correct = []
    flips = []
    activated = []
    prediction_up = []

    for event in stream.events:
        for feedback in feedback_queue.pop(event.t, []):
            model.feedback(feedback)
        p, trace = model.predict(event.key, event.reports, event.t)
        feedback_queue[event.t + 1].append(
            {
                "key": event.key,
                "reports": event.reports,
                "truth": event.truth,
                "pred": p,
                "trace": trace,
                "time": event.t + 1,
            }
        )
        if event.day not in days:
            continue
        hit = int((p >= 0.5) == event.truth)
        correct.append(hit)
        flips.append(event.prev_truth is not None and event.truth != event.prev_truth)
        activated.append(trace["used"])
        prediction_up.append(p >= 0.5)

    correct = np.asarray(correct, float)
    flips = np.asarray(flips, bool)
    return {
        "correct": correct,
        "flip": flips,
        "accuracy": float(correct.mean()),
        "flip_accuracy": float(correct[flips].mean()),
        "nonflip_accuracy": float(correct[~flips].mean()),
        "avg_activated": float(np.mean(activated)),
        "pred_up_rate": float(np.mean(prediction_up)),
        "n": int(len(correct)),
        "flip_n": int(flips.sum()),
        "stats": model.stats(),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, default=ROOT / "data")
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "transition_development.json")
    ap.add_argument("--n-boot", type=int, default=2000)
    args = ap.parse_args()

    stream = FinanceNewsStream(args.data_dir)
    days = contact_tail_days(stream)

    # Small, predeclared mechanism sweep.  Each candidate varies the four
    # meaningful biological controls: how confident/wrong a prediction must be
    # to count, how much error it takes to ignite, how long investigation stays
    # open, and how strongly it protects counter-evidence.  No old holdout
    # scores are read or used here.
    candidates = {
        "calibrated_baseline": None,
        "brief_cautious": {
            "error_decay": 0.30,
            "ignite_threshold": 0.35,
            "confidence_floor": 0.10,
            "investigate_decay": 0.50,
            "anchor_floor": 0.50,
            "counterevidence_floor": 0.50,
        },
        "brief_strong": {
            "error_decay": 0.30,
            "ignite_threshold": 0.35,
            "confidence_floor": 0.10,
            "investigate_decay": 0.50,
            "anchor_floor": 0.20,
            "counterevidence_floor": 0.75,
        },
        "medium_cautious": {
            "error_decay": 0.45,
            "ignite_threshold": 0.50,
            "confidence_floor": 0.15,
            "investigate_decay": 0.72,
            "anchor_floor": 0.50,
            "counterevidence_floor": 0.50,
        },
        "medium_strong": {
            "error_decay": 0.45,
            "ignite_threshold": 0.50,
            "confidence_floor": 0.15,
            "investigate_decay": 0.72,
            "anchor_floor": 0.20,
            "counterevidence_floor": 0.75,
        },
        "long_cautious": {
            "error_decay": 0.60,
            "ignite_threshold": 0.75,
            "confidence_floor": 0.20,
            "investigate_decay": 0.88,
            "anchor_floor": 0.50,
            "counterevidence_floor": 0.50,
        },
        "long_strong": {
            "error_decay": 0.60,
            "ignite_threshold": 0.75,
            "confidence_floor": 0.20,
            "investigate_decay": 0.88,
            "anchor_floor": 0.20,
            "counterevidence_floor": 0.75,
        },
    }

    results = {}
    vectors = {}
    for name, params in candidates.items():
        if params is None:
            model = CuredCellular(cures=("source_calib", "corr_downweight"), **CELL_PARAMS)
        else:
            model = TransitionInvestigator(**params, **CELL_PARAMS)
        result = score_days(stream, model, days)
        vectors[name] = result
        results[name] = {
            key: value
            for key, value in result.items()
            if key not in {"correct", "flip", "stats"}
        }
        results[name]["stats"] = result["stats"]

    baseline = vectors["calibrated_baseline"]
    comparisons = {}
    for name in candidates:
        if name == "calibrated_baseline":
            continue
        current = vectors[name]
        comparisons[name] = {
            "accuracy": paired_delta(
                baseline["correct"], current["correct"], n_boot=args.n_boot
            ),
            "flip_accuracy": paired_delta(
                baseline["correct"], current["correct"], baseline["flip"], n_boot=args.n_boot
            ),
        }

    # Selection gate: enough evidence to be worth the fresh test, but no
    # declaration of success until the untouched universe is run.
    eligible = [
        name
        for name, comparison in comparisons.items()
        if comparison["flip_accuracy"]["delta"] >= 0.03
        and comparison["accuracy"]["delta"] >= -0.01
        and results[name]["pred_up_rate"] <= 0.65
    ]
    winner = max(eligible, key=lambda name: comparisons[name]["flip_accuracy"]["delta"]) if eligible else None

    payload = {
        "protocol": "contact_tail_development_only_v1",
        "scored_days": sorted(days),
        "n_scored_days": len(days),
        "results": results,
        "vs_calibrated_baseline": comparisons,
        "selection_rule": (
            "flip gain >= 0.03, accuracy drop < 0.01, prediction-up rate <= 0.65; "
            "winner is highest flip gain.  Fresh universe is required for any claim."
        ),
        "selected_for_fresh_confirmation": winner,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, allow_nan=True))

    print(f"contact-tail days={len(days)} events={baseline['n']} flips={baseline['flip_n']}")
    print(f"{'candidate':18s} {'acc':>7s} {'flip':>7s} {'act':>6s} {'up':>6s} {'flip Δ':>9s}")
    for name in candidates:
        result = results[name]
        delta = 0.0 if name == "calibrated_baseline" else comparisons[name]["flip_accuracy"]["delta"]
        print(
            f"{name:18s} {result['accuracy']:.4f} {result['flip_accuracy']:.4f} "
            f"{result['avg_activated']:6.2f} {result['pred_up_rate']:.3f} {delta:+.4f}"
        )
    print(f"selected_for_fresh_confirmation={winner}")


if __name__ == "__main__":
    main()
