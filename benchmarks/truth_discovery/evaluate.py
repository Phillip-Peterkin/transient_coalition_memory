#!/usr/bin/env python3
"""Run literature TD methods on Stock + Weather; score quality and efficiency."""

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
import pandas as pd

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(REPO / "src"))

from methods import METHODS  # noqa: E402

SLIM = ROOT / "data" / "slim"
OUT = ROOT / "results"

CONTINUOUS = {"change_pct", "last_price", "open_price", "prev_close", "temperature"}


def load_task(claims_path: Path, gold_path: Path, attributes: list[str] | None = None):
    claims = pd.read_parquet(claims_path)
    gold = pd.read_parquet(gold_path)
    if attributes:
        claims = claims[claims.attribute.isin(attributes)]
        gold = gold[gold.attribute.isin(attributes)]
    claim_rows = claims.to_dict("records")
    gold_map = {
        (r["day"], r["object"], r["attribute"]): r["value"]
        for r in gold.to_dict("records")
    }
    return claim_rows, gold_map, {
        "n_claims": int(len(claims)),
        "n_sources": int(claims.source.nunique()),
        "n_objects": int(claims.object.nunique()),
        "n_days": int(claims.day.nunique()),
        "attributes": sorted(claims.attribute.unique()),
        "n_gold": int(len(gold_map)),
    }


def score(truths: dict, gold_map: dict) -> dict:
    cont_err = []
    cat_ok = []
    matched = 0
    for key, truth in gold_map.items():
        if key not in truths:
            continue
        matched += 1
        pred = truths[key]
        attr = key[2]
        if attr in CONTINUOUS:
            cont_err.append(abs(float(pred) - float(truth)))
            # rounded match for discrete view
            if attr == "temperature":
                cat_ok.append(int(round(float(pred)) == round(float(truth))))
            else:
                cat_ok.append(int(round(float(pred), 2) == round(float(truth), 2)))
        else:
            cat_ok.append(int(str(pred) == str(truth)))
    out = {"matched_gold": matched, "coverage": matched / max(1, len(gold_map))}
    if cont_err:
        arr = np.asarray(cont_err, dtype=float)
        out["mae"] = float(arr.mean())
        out["rmse"] = float(np.sqrt(np.mean(arr**2)))
    if cat_ok:
        out["error_rate"] = float(1.0 - np.mean(cat_ok))
        out["accuracy"] = float(np.mean(cat_ok))
    return out


def timed_run(method_name: str, claims: list[dict]):
    cls = METHODS[method_name]
    model = cls() if isinstance(cls, type) else cls
    gc.collect()
    tracemalloc.start()
    gc.disable()
    cpu0 = time.process_time_ns()
    wall0 = time.perf_counter_ns()
    try:
        result = model.run(claims)
    finally:
        wall1 = time.perf_counter_ns()
        cpu1 = time.process_time_ns()
        gc.enable()
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    return result, {
        "wall_seconds": (wall1 - wall0) / 1e9,
        "cpu_seconds": (cpu1 - cpu0) / 1e9,
        "peak_tracemalloc_mb": peak / (1024 * 1024),
        "iterations": result.iterations,
        "ops": result.ops,
        "claims_per_sec": len(claims) / max(1e-9, (wall1 - wall0) / 1e9),
    }


def run_fusion_suite(name: str, claims, gold_map, meta, methods: list[str]) -> dict:
    holdout = {}
    for method in methods:
        result, efficiency = timed_run(method, claims)
        metrics = score(result.truths, gold_map)
        holdout[method] = {**metrics, **efficiency}
        print(
            f"  {name}/{method}: "
            + " ".join(
                f"{k}={metrics[k]:.4f}"
                for k in ("mae", "rmse", "error_rate", "accuracy")
                if k in metrics
            )
            + f" wall={efficiency['wall_seconds']:.3f}s"
            + f" cpu={efficiency['cpu_seconds']:.3f}s"
            + f" cps={efficiency['claims_per_sec']:.0f}"
        )
    return {"dataset": name, "meta": meta, "methods": holdout}


def run_binary_stock(methods_cellular: bool = True) -> dict:
    """Binary last>prev_close track (Change% gold is degenerate ~100% up)."""
    claims_df = pd.read_parquet(SLIM / "stock_claims.parquet")
    gold_df = pd.read_parquet(SLIM / "stock_gold.parquet")
    last_c = claims_df[claims_df.attribute == "last_price"][
        ["day", "object", "source", "value"]
    ].rename(columns={"value": "last"})
    prev_c = claims_df[claims_df.attribute == "prev_close"][
        ["day", "object", "source", "value"]
    ].rename(columns={"value": "prev"})
    votes = last_c.merge(prev_c, on=["day", "object", "source"])
    votes["up"] = (votes["last"] > votes["prev"]).astype(int)

    last_g = gold_df[gold_df.attribute == "last_price"][
        ["day", "object", "value"]
    ].rename(columns={"value": "last"})
    prev_g = gold_df[gold_df.attribute == "prev_close"][
        ["day", "object", "value"]
    ].rename(columns={"value": "prev"})
    gold = last_g.merge(prev_g, on=["day", "object"])
    gold_sign = {
        (r.day, r.object): int(float(r.last) > float(r.prev)) for r in gold.itertuples()
    }

    by_item = defaultdict(list)
    source_ids = {}
    for r in votes.itertuples():
        key = (r.day, r.object)
        if key not in gold_sign:
            continue
        if r.source not in source_ids:
            source_ids[r.source] = len(source_ids)
        by_item[key].append((source_ids[r.source], 0, int(r.up)))

    days = sorted({day for day, _ in by_item})
    # Fusion-style on binary as categorical 0/1 for TD methods
    bin_claims = []
    gold_map = {}
    for (day, obj), reports in by_item.items():
        gold_map[(day, obj, "up")] = gold_sign[(day, obj)]
        for source, _, vote in reports:
            # reverse map source id for TD string keys
            src_name = next(s for s, i in source_ids.items() if i == source)
            bin_claims.append(
                {
                    "day": day,
                    "object": obj,
                    "source": src_name,
                    "attribute": "up",
                    "value": int(vote),
                }
            )

    up_rate = float(np.mean(list(gold_sign.values()))) if gold_sign else float("nan")
    block = run_fusion_suite(
        "stock_binary_last_gt_prev",
        bin_claims,
        gold_map,
        {
            "n_claims": len(bin_claims),
            "n_sources": len(source_ids),
            "n_objects": len({o for _, o in by_item}),
            "n_days": len(days),
            "attributes": ["up"],
            "n_gold": len(gold_map),
            "gold_up_rate": up_rate,
            "label": "last_price > prev_close (nasdaq gold)",
        },
        list(METHODS),
    )

    if not methods_cellular:
        return block

    # Cellular streaming path
    from tcm import (
        ActiveExperimentalCellular,
        AwareCoalitionCellular,
        BatchedReserveCellular,
    )

    sys.path.insert(0, str(REPO / "benchmarks" / "realdata_finance"))
    from evaluate import CELL_PARAMS as FIN_PARAMS

    ACI = {
        "min_delta": 0.15,
        "max_silence_hazard": 0.55,
        "null_rho_gain": 0.30,
        "null_pe_floor": 0.35,
        "null_pe_span": 0.50,
        "null_err_beta": 0.30,
        "force_all_positive_null": True,
        "fe_cert_slack": 0.0,
    }
    AWARE = {k: v for k, v in ACI.items() if k != "force_all_positive_null"}

    def run_cell(model):
        # chronological events
        events = []
        prev = {}
        for day in days:
            for (d, obj), reports in by_item.items():
                if d != day:
                    continue
                key = (obj,)
                truth = gold_sign[(d, obj)]
                events.append(
                    {
                        "day": d,
                        "key": key,
                        "reports": reports,
                        "truth": truth,
                        "prev": prev.get(key),
                        "t": len(events),
                    }
                )
                prev[key] = truth
        # feedback next day: due at first event of next day index
        day_index = {day: i for i, day in enumerate(days)}
        first_t = {}
        for e in events:
            first_t.setdefault(e["day"], e["t"])
        due = {}
        for e in events:
            idx = day_index[e["day"]]
            if idx + 1 >= len(days):
                continue
            due[e["t"]] = first_t[days[idx + 1]]

        queue = defaultdict(list)
        rows = []
        gc.collect()
        tracemalloc.start()
        gc.disable()
        cpu0 = time.process_time_ns()
        wall0 = time.perf_counter_ns()
        try:
            for e in events:
                for fb in queue.pop(e["t"], []):
                    model.feedback(fb)
                p, trace = model.predict(e["key"], e["reports"], e["t"])
                if e["t"] in due:
                    queue[due[e["t"]]].append(
                        {
                            "key": e["key"],
                            "reports": e["reports"],
                            "truth": e["truth"],
                            "pred": p,
                            "trace": trace,
                            "time": due[e["t"]],
                        }
                    )
                flip = e["prev"] is not None and e["prev"] != e["truth"]
                rows.append(
                    {
                        "correct": int((p >= 0.5) == e["truth"]),
                        "flip": int(flip),
                        "p": float(p),
                        "used": float(trace.get("used", len(e["reports"]))),
                    }
                )
        finally:
            wall1 = time.perf_counter_ns()
            cpu1 = time.process_time_ns()
            gc.enable()
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

        correct = np.asarray([r["correct"] for r in rows], float)
        flip = np.asarray([r["flip"] for r in rows], bool)
        return {
            "n": len(rows),
            "accuracy": float(correct.mean()),
            "flip_n": int(flip.sum()),
            "flip_accuracy": float(correct[flip].mean()) if flip.any() else None,
            "nonflip_accuracy": float(correct[~flip].mean()) if (~flip).any() else None,
            "pred_up_rate": float(np.mean([r["p"] >= 0.5 for r in rows])),
            "avg_activated": float(np.mean([r["used"] for r in rows])),
            "wall_seconds": (wall1 - wall0) / 1e9,
            "cpu_seconds": (cpu1 - cpu0) / 1e9,
            "peak_tracemalloc_mb": peak / (1024 * 1024),
            "events_per_sec": len(rows) / max(1e-9, (wall1 - wall0) / 1e9),
        }

    cellular = {
        "aware_coalition": run_cell(AwareCoalitionCellular(**AWARE, **FIN_PARAMS)),
        "active_experimental_aci": run_cell(
            ActiveExperimentalCellular(**ACI, **FIN_PARAMS)
        ),
        "wave_xi": run_cell(BatchedReserveCellular(**FIN_PARAMS)),
    }
    for name, metrics in cellular.items():
        flip_s = (
            f"{metrics['flip_accuracy']:.3f}"
            if metrics["flip_accuracy"] is not None
            else "n/a"
        )
        print(
            f"  stock_binary_cellular/{name}: acc={metrics['accuracy']:.3f} "
            f"flip={flip_s} (n={metrics['flip_n']}) "
            f"act={metrics['avg_activated']:.2f} "
            f"wall={metrics['wall_seconds']:.3f}s "
            f"eps={metrics['events_per_sec']:.0f}"
        )
    block["cellular"] = cellular
    return block


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--skip-cellular",
        action="store_true",
        help="skip Aware/ACI/Wave XI binary track",
    )
    args = ap.parse_args()
    if not (SLIM / "stock_claims.parquet").exists():
        raise SystemExit("missing slim tables; run prepare_slim.py")

    methods = list(METHODS)
    results = {
        "protocol": "truth_discovery_literature_v1",
        "datasets": {},
    }

    print("STOCK attribute fusion (NASDAQ-100 gold) — per attribute")
    for attr in ("change_pct", "last_price", "open_price"):
        stock_claims, stock_gold, stock_meta = load_task(
            SLIM / "stock_claims.parquet",
            SLIM / "stock_gold.parquet",
            attributes=[attr],
        )
        results["datasets"][f"stock_{attr}"] = run_fusion_suite(
            f"stock_{attr}", stock_claims, stock_gold, stock_meta, methods
        )

    print("WEATHER temperature fusion (weather_gov gold)")
    w_claims, w_gold, w_meta = load_task(
        SLIM / "weather_temperature_claims.parquet",
        SLIM / "weather_temperature_gold.parquet",
    )
    results["datasets"]["weather_temperature"] = run_fusion_suite(
        "weather_temperature", w_claims, w_gold, w_meta, methods
    )

    print("WEATHER conditions fusion (weather_gov gold)")
    c_claims, c_gold, c_meta = load_task(
        SLIM / "weather_conditions_claims.parquet",
        SLIM / "weather_conditions_gold.parquet",
    )
    results["datasets"]["weather_conditions"] = run_fusion_suite(
        "weather_conditions", c_claims, c_gold, c_meta, methods
    )

    print("STOCK binary last>prev streaming track")
    results["datasets"]["stock_binary"] = run_binary_stock(
        methods_cellular=not args.skip_cellular
    )

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "truth_discovery_benchmark.json"
    path.write_text(json.dumps(results, indent=2, default=float))
    print("wrote", path)


if __name__ == "__main__":
    main()
