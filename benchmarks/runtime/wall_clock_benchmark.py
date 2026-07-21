"""Reproducible wall-clock benchmark for the frozen Wave XI comparison."""
from __future__ import annotations

import argparse
import csv
import gc
import json
import os
import platform
import random
import statistics
import sys
import time
import tracemalloc
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "benchmarks" / "wave11"))
from wave11_benchmark import BatchedReserveCellular, FairProvGraph, run  # noqa: E402

CELLULAR = {
    "lr": .22, "fast_decay": .90, "contradiction_gain": .85,
    "uncertainty_cost": .38, "temp": .95, "anchor": .58,
    "min_k": 1, "max_k": 8, "header_cost": .08, "cert_delta": .08,
    "hazard_gain": 3.0, "min_margin": 0.0, "shadow_scale": .75,
    "reserve_claim_gain": 1.2, "reserve_source_gain": 0.0,
    "certify_slack": 0.0,
}
GRAPH = {"lr": .12, "decay": .98, "claim": .5}
METHODS = {
    "fair_provenance_graph": (FairProvGraph, GRAPH),
    "batched_reserve_cellular": (BatchedReserveCellular, CELLULAR),
}

def percentile(values: list[float], q: float) -> float:
    return float(np.percentile(np.asarray(values, dtype=float), q))

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", nargs="+", type=int, default=[15300, 15301, 15302, 15303])
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--warmup", type=int, default=1)
    ap.add_argument("--out", default=str(ROOT / "benchmarks" / "runtime" / "results"))
    args = ap.parse_args()
    if args.repeats < 1 or args.warmup < 0:
        ap.error("repeats must be >= 1 and warmup must be >= 0")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    for _ in range(args.warmup):
        for name, (cls, params) in METHODS.items():
            run(args.seeds[0], cls, params)

    jobs = [(r, seed, name) for r in range(args.repeats) for seed in args.seeds for name in METHODS]
    random.Random(20260721).shuffle(jobs)
    rows = []
    for repeat, seed, name in jobs:
        cls, params = METHODS[name]
        gc.collect()
        tracemalloc.start()
        gc.disable()
        cpu0 = time.process_time_ns()
        wall0 = time.perf_counter_ns()
        try:
            metrics = run(seed, cls, params)
        finally:
            wall1 = time.perf_counter_ns()
            cpu1 = time.process_time_ns()
            gc.enable()
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
        rows.append({
            "repeat": repeat,
            "seed": seed,
            "method": name,
            "wall_seconds": (wall1 - wall0) / 1e9,
            "cpu_seconds": (cpu1 - cpu0) / 1e9,
            "peak_python_bytes": peak,
            "accuracy": metrics["accuracy"],
            "changed_fact_accuracy": metrics["changed_fact_accuracy"],
            "avg_activated": metrics["avg_activated"],
            "ops_per_correct": metrics["ops_per_correct"],
        })
        print(name, seed, f"{rows[-1]['wall_seconds']:.4f}s", flush=True)

    with (out / "runtime_results.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)

    summary = {}
    for name in METHODS:
        subset = [r for r in rows if r["method"] == name]
        walls = [r["wall_seconds"] for r in subset]
        cpus = [r["cpu_seconds"] for r in subset]
        peaks = [r["peak_python_bytes"] for r in subset]
        summary[name] = {
            "n": len(subset),
            "wall_mean_seconds": statistics.mean(walls),
            "wall_median_seconds": statistics.median(walls),
            "wall_sd_seconds": statistics.stdev(walls) if len(walls) > 1 else 0.0,
            "wall_p95_seconds": percentile(walls, 95),
            "cpu_mean_seconds": statistics.mean(cpus),
            "peak_python_bytes_median": statistics.median(peaks),
            "accuracy_mean": statistics.mean(r["accuracy"] for r in subset),
            "changed_fact_accuracy_mean": statistics.mean(r["changed_fact_accuracy"] for r in subset),
        }
    payload = {
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "processor": platform.processor(),
            "numpy": np.__version__,
            "logical_cpus": os.cpu_count(),
        },
        "design": {"seeds": args.seeds, "repeats": args.repeats, "warmup": args.warmup,
                   "randomized_order_seed": 20260721},
        "summary": summary,
        "runs": rows,
    }
    (out / "runtime_results.json").write_text(json.dumps(payload, indent=2))

    lines = ["# Wave XI Wall-Clock Benchmark", "", "Machine-dependent measurements; compare only runs made under the same documented environment.", "",
             "| Method | n | Mean wall (s) | Median wall (s) | p95 wall (s) | Mean CPU (s) | Median peak Python memory (MiB) |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for name, s in summary.items():
        lines.append(f"| {name} | {s['n']} | {s['wall_mean_seconds']:.6f} | {s['wall_median_seconds']:.6f} | {s['wall_p95_seconds']:.6f} | {s['cpu_mean_seconds']:.6f} | {s['peak_python_bytes_median']/1048576:.3f} |")
    lines += ["", "Run with:", "", "```bash", "python benchmarks/runtime/wall_clock_benchmark.py", "```", ""]
    (out / "WALL_CLOCK_REPORT.md").write_text("\n".join(lines))

if __name__ == "__main__":
    main()
