#!/usr/bin/env python3
"""Run the preregistered DBSA-v1 causal delayed-feedback pilot."""

from __future__ import annotations

import argparse
import gc
import json
import sys
import time
import tracemalloc
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(REPO / "src"))

from baselines import (  # noqa: E402
    AgreementDiscountedBayes,
    FadingSourceBayes,
    FixedShareHedge,
    Majority,
    Persistence,
)
from simulator import WORLD_NAMES, Event, generate  # noqa: E402
from tcm import ActiveExperimentalCellular, AwareCoalitionCellular  # noqa: E402

CELL_PARAMS = {
    "lr": 0.22,
    "fast_decay": 0.90,
    "contradiction_gain": 0.85,
    "uncertainty_cost": 0.38,
    "temp": 0.95,
    "anchor": 0.58,
    "min_k": 1,
    "max_k": 8,
    "header_cost": 0.08,
    "cert_delta": 0.08,
    "hazard_gain": 3.0,
    "min_margin": 0.0,
    "shadow_scale": 0.75,
    "reserve_claim_gain": 1.2,
    "reserve_source_gain": 0.0,
    "certify_slack": 0.0,
}
ACI_PARAMS = {
    "min_delta": 0.15,
    "max_silence_hazard": 0.55,
    "null_rho_gain": 0.30,
    "null_pe_floor": 0.35,
    "null_pe_span": 0.50,
    "null_err_beta": 0.30,
    "force_all_positive_null": True,
    "fe_cert_slack": 0.0,
}
AWARE_PARAMS = {key: value for key, value in ACI_PARAMS.items() if key != "force_all_positive_null"}


def _method_factories():
    return {
        "persistence": Persistence,
        "majority": Majority,
        "fixed_share_hedge": FixedShareHedge,
        "fading_source_bayes": FadingSourceBayes,
        "agreement_discounted_bayes": AgreementDiscountedBayes,
        "active_experimental_aci": lambda: ActiveExperimentalCellular(
            **ACI_PARAMS, **CELL_PARAMS
        ),
        "aware_coalition": lambda: AwareCoalitionCellular(**AWARE_PARAMS, **CELL_PARAMS),
    }


def _log_loss(probability: float, truth: int) -> float:
    probability = min(1.0 - 1e-9, max(1e-9, probability))
    return -(truth * np.log(probability) + (1 - truth) * np.log(1.0 - probability))


def run_model(events: list[Event], model) -> dict:
    """Replay every event in causal order with labels released at ``due_t``."""

    queue: dict[int, list[dict]] = defaultdict(list)
    rows = []
    gc.collect()
    tracemalloc.start()
    gc.disable()
    cpu_start = time.process_time_ns()
    wall_start = time.perf_counter_ns()
    try:
        for event in events:
            for feedback in queue.pop(event.t, []):
                model.feedback(feedback)
            probability, trace = model.predict(event.key, event.reports, event.t)
            probability = float(probability)
            queue[event.due_t].append(
                {
                    "key": event.key,
                    "reports": event.reports,
                    "truth": event.truth,
                    "pred": probability,
                    "trace": trace,
                    "time": event.due_t,
                }
            )
            prediction = int(probability >= 0.5)
            is_flip = event.prev_truth is not None and event.truth != event.prev_truth
            predicted_change = (
                event.prev_truth is not None and prediction != event.prev_truth
            )
            rows.append(
                {
                    "truth": event.truth,
                    "p": probability,
                    "correct": int(prediction == event.truth),
                    "flip": bool(is_flip),
                    "predicted_change": bool(predicted_change),
                    "used": int(trace.get("used", len(event.reports))),
                    "n_reports": len(event.reports),
                    "post_shift": event.shift_age is not None and event.shift_age < 120,
                }
            )
    finally:
        wall_end = time.perf_counter_ns()
        cpu_end = time.process_time_ns()
        gc.enable()
        _, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()

    truth = np.asarray([row["truth"] for row in rows], dtype=float)
    probability = np.asarray([row["p"] for row in rows], dtype=float)
    correct = np.asarray([row["correct"] for row in rows], dtype=float)
    flip = np.asarray([row["flip"] for row in rows], dtype=bool)
    predicted_change = np.asarray([row["predicted_change"] for row in rows], dtype=bool)
    post_shift = np.asarray([row["post_shift"] for row in rows], dtype=bool)
    brier = (probability - truth) ** 2
    stats = model.stats()
    return {
        "n": len(rows),
        "brier": float(brier.mean()),
        "log_loss": float(np.mean([_log_loss(row["p"], row["truth"]) for row in rows])),
        "accuracy": float(correct.mean()),
        "flip_n": int(flip.sum()),
        "flip_recall": float(predicted_change[flip].mean()) if flip.any() else None,
        "change_false_alarm": (
            float(predicted_change[~flip].mean()) if (~flip).any() else None
        ),
        "post_shift_n": int(post_shift.sum()),
        "post_shift_brier": float(brier[post_shift].mean()) if post_shift.any() else None,
        "avg_reports_inspected": float(np.mean([row["n_reports"] for row in rows])),
        "avg_downstream_activated": float(np.mean([row["used"] for row in rows])),
        "wall_seconds": (wall_end - wall_start) / 1e9,
        "cpu_seconds": (cpu_end - cpu_start) / 1e9,
        "peak_tracemalloc_mb": peak_bytes / (1024 * 1024),
        "events_per_second": len(rows) / max(1e-9, (wall_end - wall_start) / 1e9),
        "model_stats": stats,
    }


def _mean_metrics(rows: list[dict]) -> dict:
    out = {}
    for key in (
        "brier",
        "log_loss",
        "accuracy",
        "flip_recall",
        "change_false_alarm",
        "post_shift_brier",
        "avg_reports_inspected",
        "avg_downstream_activated",
        "wall_seconds",
        "cpu_seconds",
        "peak_tracemalloc_mb",
        "events_per_second",
    ):
        values = [row[key] for row in rows if row[key] is not None]
        out[key] = float(np.mean(values)) if values else None
    out["n"] = int(sum(row["n"] for row in rows))
    out["flip_n"] = int(sum(row["flip_n"] for row in rows))
    out["post_shift_n"] = int(sum(row["post_shift_n"] for row in rows))
    return out


def _paired_bootstrap_delta(
    aware_rows: list[dict],
    baseline_rows: list[dict],
    metric: str,
    *,
    draws: int = 2000,
) -> dict:
    if any(
        aware[metric] is None or baseline[metric] is None
        for aware, baseline in zip(aware_rows, baseline_rows)
    ):
        return {"aware_minus_fixed_share": None, "lo": None, "hi": None}
    differences = np.asarray(
        [aware[metric] - baseline[metric] for aware, baseline in zip(aware_rows, baseline_rows)],
        dtype=float,
    )
    rng = np.random.default_rng(20260723)
    sample_indexes = rng.integers(0, len(differences), size=(draws, len(differences)))
    means = differences[sample_indexes].mean(axis=1)
    return {
        "aware_minus_fixed_share": float(differences.mean()),
        "lo": float(np.quantile(means, 0.025)),
        "hi": float(np.quantile(means, 0.975)),
    }


def evaluate_world(world: str, seeds: range, rounds: int) -> dict:
    per_method: dict[str, list[dict]] = defaultdict(list)
    for seed in seeds:
        events = generate(world, seed, rounds=rounds)
        for name, factory in _method_factories().items():
            per_method[name].append(run_model(events, factory()))

    summary = {name: _mean_metrics(rows) for name, rows in per_method.items()}
    comparisons = {
        "aware_vs_fixed_share_brier": _paired_bootstrap_delta(
            per_method["aware_coalition"], per_method["fixed_share_hedge"], "brier"
        ),
        "aware_vs_fixed_share_post_shift_brier": _paired_bootstrap_delta(
            per_method["aware_coalition"],
            per_method["fixed_share_hedge"],
            "post_shift_brier",
        ),
    }
    return {
        "world": world,
        "seeds": list(seeds),
        "rounds_per_seed": rounds,
        "summary": summary,
        "comparisons": comparisons,
    }


def pilot_gate(worlds: dict[str, dict]) -> dict:
    brier_checks = {}
    for name, payload in worlds.items():
        aware = payload["summary"]["aware_coalition"]["brier"]
        hedge = payload["summary"]["fixed_share_hedge"]["brier"]
        brier_checks[name] = aware <= hedge + 0.002

    recovery_worlds = ("abrupt_drift", "adversarial_switch")
    recovery_checks = {
        name: worlds[name]["summary"]["aware_coalition"]["post_shift_brier"]
        < worlds[name]["summary"]["fixed_share_hedge"]["post_shift_brier"]
        for name in recovery_worlds
        if name in worlds
    }
    return {
        "brier_noninferior_to_fixed_share_by_0.002": brier_checks,
        "better_post_shift_brier_than_fixed_share": recovery_checks,
        "pilot_passes": all(brier_checks.values()) and all(recovery_checks.values()),
    }


def _print_world(payload: dict) -> None:
    print(f"\n{payload['world']} ({len(payload['seeds'])} seeds × {payload['rounds_per_seed']} events)")
    print("  method                         brier   logloss  acc    flip-r  false-a  act   eps")
    for name, values in payload["summary"].items():
        flip_recall = values["flip_recall"]
        false_alarm = values["change_false_alarm"]
        print(
            f"  {name:30} {values['brier']:.4f}  {values['log_loss']:.4f}  "
            f"{values['accuracy']:.3f}  "
            f"{flip_recall:.3f}  {false_alarm:.3f}  "
            f"{values['avg_downstream_activated']:.2f}  "
            f"{values['events_per_second']:.0f}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=24)
    parser.add_argument("--rounds", type=int, default=800)
    parser.add_argument("--worlds", nargs="+", choices=WORLD_NAMES, default=list(WORLD_NAMES))
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "results" / "dbsa_v1_pilot.json",
    )
    args = parser.parse_args()
    if args.seeds < 2:
        parser.error("--seeds must be at least 2")
    if args.rounds <= 14:
        parser.error("--rounds must exceed the fixed feedback delay (14)")

    worlds = {
        world: evaluate_world(world, range(args.seeds), args.rounds) for world in args.worlds
    }
    result = {
        "protocol": "dbsa_v1",
        "task": "causal delayed-feedback source aggregation under drift and dependence",
        "fixed_feedback_delay_events": 14,
        "worlds": worlds,
        "pilot_gate": pilot_gate(worlds),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, default=float))
    for payload in worlds.values():
        _print_world(payload)
    print("\nPILOT GATE", result["pilot_gate"]["pilot_passes"])
    print("wrote", args.out)


if __name__ == "__main__":
    main()
