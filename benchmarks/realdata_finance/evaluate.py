#!/usr/bin/env python3
"""Run locked TCM + baselines on the finance/news real-data stream."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(ROOT))

from tcm import BatchedReserveCellular, FairProvGraph  # noqa: E402

from baselines import DynamicBayes, MemorylessMajority, PersistenceOracle, RecentMajority  # noqa: E402
from stream import FinanceNewsStream  # noqa: E402

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


def ece(p: np.ndarray, y: np.ndarray, bins: int = 10) -> float:
    p = np.asarray(p, float)
    y = np.asarray(y, float)
    edges = np.linspace(0, 1, bins + 1)
    total = 0.0
    n = len(p)
    if n == 0:
        return float("nan")
    for i in range(bins):
        m = (p >= edges[i]) & (p < edges[i + 1] if i < bins - 1 else p <= edges[i + 1])
        if not np.any(m):
            continue
        total += abs(p[m].mean() - y[m].mean()) * (m.sum() / n)
    return float(total)


def _predict(model, key, reports, t, event):
    if isinstance(model, PersistenceOracle):
        return model.predict(key, reports, t, event=event)
    return model.predict(key, reports, t)


def run_model(stream: FinanceNewsStream, model, split_filter: str | None = None) -> dict:
    q: dict[int, list] = defaultdict(list)
    rows = []
    events = [
        e
        for e in stream.events
        if split_filter is None or e.split == split_filter
    ]
    # Feedback queue is global in time; when evaluating a split alone we still
    # only score events in that split, but we replay the full stream so memory
    # state is causal. Callers wanting pure holdout-from-scratch should pass
    # a stream already filtered — default is full causal replay with split tags.
    score_ids = {id(e) for e in events} if split_filter else None

    for event in stream.events:
        for fb in q.pop(event.t, []):
            model.feedback(fb)
        p, tr = _predict(model, event.key, event.reports, event.t, event)
        used = int(tr.get("used", len(event.reports)))
        due = event.t + 1
        q[due].append(
            {
                "key": event.key,
                "reports": event.reports,
                "truth": event.truth,
                "pred": p,
                "trace": tr,
                "time": due,
            }
        )
        if score_ids is not None and id(event) not in score_ids:
            continue
        is_flip = event.prev_truth is not None and event.truth != event.prev_truth
        rows.append(
            {
                "day": event.day,
                "symbol": event.symbol,
                "split": event.split,
                "truth": event.truth,
                "prev_truth": event.prev_truth,
                "p": float(p),
                "hat": int(p >= 0.5),
                "correct": int(int(p >= 0.5) == event.truth),
                "flip": int(is_flip),
                "used": used,
                "n_reports": len(event.reports),
                "n_sites": event.n_sites,
                "agreement": stream.source_agreement(event.reports),
            }
        )

    if not rows:
        return {"n": 0}

    P = np.asarray([r["p"] for r in rows], float)
    Y = np.asarray([r["truth"] for r in rows], float)
    correct = np.asarray([r["correct"] for r in rows], float)
    flip_m = np.asarray([r["flip"] for r in rows], bool)
    st = model.stats()
    out = {
        "n": int(len(rows)),
        "accuracy": float(correct.mean()),
        "brier": float(np.mean((P - Y) ** 2)),
        "ece": ece(P, Y),
        "truth_up_rate": float(Y.mean()),
        "pred_up_rate": float((P >= 0.5).mean()),
        "flip_n": int(flip_m.sum()),
        "flip_accuracy": float(correct[flip_m].mean()) if flip_m.any() else float("nan"),
        "nonflip_accuracy": float(correct[~flip_m].mean()) if (~flip_m).any() else float("nan"),
        "avg_activated": float(np.mean([r["used"] for r in rows])),
        "avg_reports": float(np.mean([r["n_reports"] for r in rows])),
        "avg_sites": float(np.mean([r["n_sites"] for r in rows])),
        "mean_source_agreement": float(np.nanmean([r["agreement"] for r in rows])),
        "active_ops": float(st.get("active_ops", 0.0)),
        "ops_per_correct": float(st.get("active_ops", 0.0) / max(1.0, correct.sum())),
        "memory_states": int(st.get("memory_states", 0)),
    }
    return out


def evaluate_all(stream: FinanceNewsStream) -> dict:
    methods = {
        "persistence_oracle": PersistenceOracle(stream),
        "memoryless_majority": MemorylessMajority(),
        "recent_majority": RecentMajority(window=3),
        "dynamic_bayes": DynamicBayes(),
        "fair_provenance_graph": FairProvGraph(**GRAPH_PARAMS),
        "batched_reserve_cellular": BatchedReserveCellular(**CELL_PARAMS),
    }
    payload = {
        "protocol": "realdata_finance_v0",
        "stream": stream.summary(),
        "params": {"cellular": CELL_PARAMS, "graph": GRAPH_PARAMS},
        "splits": {},
    }
    for split in ("all", "contact", "holdout"):
        split_filter = None if split == "all" else split
        payload["splits"][split] = {}
        for name, factory in methods.items():
            # Fresh model per split evaluation, but causal replay uses full stream
            # with scoring restricted to the split (except persistence/majority which
            # are nearly memoryless).
            if name == "persistence_oracle":
                model = PersistenceOracle(stream)
            elif name == "memoryless_majority":
                model = MemorylessMajority()
            elif name == "recent_majority":
                model = RecentMajority(window=3)
            elif name == "dynamic_bayes":
                model = DynamicBayes()
            elif name == "fair_provenance_graph":
                model = FairProvGraph(**GRAPH_PARAMS)
            else:
                model = BatchedReserveCellular(**CELL_PARAMS)
            payload["splits"][split][name] = run_model(stream, model, split_filter=split_filter)
    return payload


def write_summary_csv(payload: dict, path: Path) -> None:
    fields = [
        "split",
        "method",
        "n",
        "accuracy",
        "flip_accuracy",
        "nonflip_accuracy",
        "flip_n",
        "brier",
        "ece",
        "pred_up_rate",
        "avg_activated",
        "avg_reports",
        "mean_source_agreement",
        "ops_per_correct",
    ]
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for split, methods in payload["splits"].items():
            for method, m in methods.items():
                w.writerow(
                    {
                        "split": split,
                        "method": method,
                        **{k: m.get(k, "") for k in fields[2:]},
                    }
                )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, default=ROOT / "data")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "results")
    args = ap.parse_args()
    stream = FinanceNewsStream(args.data_dir)
    payload = evaluate_all(stream)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "results.json").write_text(json.dumps(payload, indent=2, allow_nan=True))
    write_summary_csv(payload, args.out_dir / "summary.csv")

    print("STREAM", json.dumps(payload["stream"], indent=2))
    for split in ("contact", "holdout", "all"):
        print(f"\n=== {split.upper()} ===")
        for method, m in payload["splits"][split].items():
            print(
                f"{method:26s} acc={m['accuracy']:.4f} flip={m['flip_accuracy']:.4f} "
                f"persist_gap_vs_oracle=({m['accuracy'] - payload['splits'][split]['persistence_oracle']['accuracy']:+.4f}) "
                f"act={m['avg_activated']:.2f} n={m['n']} flips={m['flip_n']}"
            )


if __name__ == "__main__":
    main()
