#!/usr/bin/env python3
"""One-shot ACI synthetic adversarial boss test (protocol-first)."""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
sys.path.insert(0, str(REPO / "src"))
for wave in ("wave4", "wave7", "wave9", "wave10", "wave11"):
    sys.path.insert(0, str(REPO / "benchmarks" / wave))

from wave4_benchmark import World, ece  # noqa: E402
from tcm import (  # noqa: E402
    ActiveCoalitionCellular,
    BatchedReserveCellular,
    FairProvGraph,
)

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
GRAPH_PARAMS = {"lr": 0.12, "decay": 0.98, "claim": 0.5}

# Sealed confirmation8 freeze — do not alter after protocol is written.
ACI_FROZEN = {
    "min_delta": 0.15,
    "max_silence_hazard": 0.55,
    "null_rho_gain": 0.30,
    "null_pe_floor": 0.35,
    "null_pe_span": 0.50,
    "null_err_beta": 0.30,
    "force_all_positive_null": True,
    "fe_cert_slack": 0.0,
}

REGRESSION_SEEDS = [15200, 15201]
FRESH_SEEDS = [15300, 15301, 15302, 15303]

ACC_SLACK = 0.015
CHANGED_SLACK = 0.025


def run(seed: int, cls, params: dict) -> dict:
    world = World(seed)
    model = cls(**params)
    queue: dict[int, list] = defaultdict(list)
    probs, labels, changed, false_cert, used = [], [], [], [], []
    for t in range(world.T):
        for event in queue.pop(t, []):
            model.feedback(event)
        for item in range(world.I):
            context = int(world.context[t, item])
            key = (item, context)
            reports = world.reports(t, item)
            probability, trace = model.predict(key, reports, t)
            truth = int(world.truth[t, item])
            probs.append(probability)
            labels.append(truth)
            old = int(world.truth[world.change_t - 1, item])
            changed.append(t >= world.change_t and truth != old)
            false_cert.append(
                (probability > 0.9 and truth == 0)
                or (probability < 0.1 and truth == 1)
            )
            used.append(trace.get("used", len(reports)))
            if world.feedback_mask[t, item]:
                due = t + int(world.delays[t, item])
                if due < world.T:
                    queue[due].append(
                        {
                            "key": key,
                            "reports": reports,
                            "truth": truth,
                            "pred": probability,
                            "trace": trace,
                            "time": due,
                        }
                    )
    probs_a = np.asarray(probs)
    labels_a = np.asarray(labels)
    changed_a = np.asarray(changed)
    correct = (probs_a >= 0.5).astype(int) == labels_a
    stats = model.stats()
    active_ops = float(stats.get("active_ops", 0.0))
    if "active_ops" not in stats:
        active_ops = float(
            stats.get("inference_ops", getattr(model, "infer_reads", 0.0))
            + stats.get("learning_ops", getattr(model, "learn_writes", 0.0))
        )
    return {
        "accuracy": float(correct.mean()),
        "changed_fact_accuracy": float(correct[changed_a].mean()),
        "brier": float(np.mean((probs_a - labels_a) ** 2)),
        "ece": ece(probs_a, labels_a),
        "false_certainty": float(np.mean(false_cert)),
        "avg_activated": float(np.mean(used)),
        "ops_per_correct": float(active_ops / max(1, int(correct.sum()))),
        "silence_events": int(stats.get("silence_events", 0)),
        "null_diagnostic_events": int(stats.get("null_diagnostic_events", 0)),
        "fe_certificates": int(stats.get("fe_certificates", 0)),
    }


def aggregate(cls, params: dict, seeds: list[int]) -> dict:
    runs = [run(seed, cls, params) for seed in seeds]
    keys = [key for key, value in runs[0].items() if isinstance(value, (int, float))]
    return {
        "mean": {key: float(np.mean([row[key] for row in runs])) for key in keys},
        "sd": {
            key: float(np.std([row[key] for row in runs], ddof=1)) for key in keys
        },
        "runs": runs,
        "params": params,
        "seeds": seeds,
    }


def gate(fresh: dict) -> dict:
    aci = fresh["active_coalition"]["mean"]
    wave = fresh["batched_reserve_cellular"]["mean"]
    graph = fresh["fair_provenance_graph"]["mean"]
    checks = {
        "acc_vs_wavexi": aci["accuracy"] >= wave["accuracy"] - ACC_SLACK,
        "changed_vs_wavexi": (
            aci["changed_fact_accuracy"]
            >= wave["changed_fact_accuracy"] - CHANGED_SLACK
        ),
        "acc_vs_graph": aci["accuracy"] >= graph["accuracy"],
        "changed_vs_graph": (
            aci["changed_fact_accuracy"] >= graph["changed_fact_accuracy"]
        ),
    }
    return {
        "checks": checks,
        "passes": all(checks.values()),
        "deltas": {
            "acc_minus_wavexi": aci["accuracy"] - wave["accuracy"],
            "changed_minus_wavexi": (
                aci["changed_fact_accuracy"] - wave["changed_fact_accuracy"]
            ),
            "acc_minus_graph": aci["accuracy"] - graph["accuracy"],
            "changed_minus_graph": (
                aci["changed_fact_accuracy"] - graph["changed_fact_accuracy"]
            ),
        },
    }


def main() -> None:
    methods = {
        "fair_provenance_graph": (FairProvGraph, GRAPH_PARAMS),
        "batched_reserve_cellular": (BatchedReserveCellular, CELL_PARAMS),
        "active_coalition": (
            ActiveCoalitionCellular,
            {**CELL_PARAMS, **ACI_FROZEN},
        ),
    }
    results = {
        name: {
            "regression": aggregate(cls, params, REGRESSION_SEEDS),
            "fresh": aggregate(cls, params, FRESH_SEEDS),
        }
        for name, (cls, params) in methods.items()
    }
    fresh_means = {name: block["fresh"] for name, block in results.items()}
    decision = gate(fresh_means)
    payload = {
        "protocol": "aci_synthetic_adversarial_boss_v1",
        "candidate": f"ActiveCoalitionCellular({ACI_FROZEN})",
        "regression_seeds": REGRESSION_SEEDS,
        "fresh_holdout_seeds": FRESH_SEEDS,
        "gate_slacks": {"accuracy": ACC_SLACK, "changed_fact": CHANGED_SLACK},
        "results": results,
        "gate": decision,
    }
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    (out / "boss_results.json").write_text(json.dumps(payload, indent=2))
    fields = [
        "split",
        "method",
        "accuracy",
        "changed_fact_accuracy",
        "brier",
        "ece",
        "false_certainty",
        "avg_activated",
        "ops_per_correct",
        "null_diagnostic_events",
        "fe_certificates",
    ]
    with (out / "boss_summary.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for name, block in results.items():
            for split in ("regression", "fresh"):
                mean = block[split]["mean"]
                writer.writerow(
                    {
                        "split": split,
                        "method": name,
                        **{key: mean.get(key, "") for key in fields[2:]},
                    }
                )
    print("ACI SYNTHETIC ADVERSARIAL BOSS")
    print(f"passes_predeclared_gate={decision['passes']}")
    for split in ("regression", "fresh"):
        print(f"\n{split.upper()}")
        for name, block in results.items():
            mean = block[split]["mean"]
            print(
                f"  {name}: acc={mean['accuracy']:.4f} "
                f"changed={mean['changed_fact_accuracy']:.4f} "
                f"act={mean['avg_activated']:.2f} "
                f"ops/c={mean['ops_per_correct']:.2f}"
            )
    print("\nGATE CHECKS")
    for name, ok in decision["checks"].items():
        print(f"  {name}: {'PASS' if ok else 'FAIL'}")
    print("DELTAS", {k: round(v, 4) for k, v in decision["deltas"].items()})


if __name__ == "__main__":
    main()
