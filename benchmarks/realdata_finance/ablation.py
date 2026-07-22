#!/usr/bin/env python3
"""Ablation: frozen TCM vs each cure (and combined) with bootstrap CIs.

Implements improvement-option #5 (measurement rigor): every comparison reports
a 95% bootstrap CI and a paired bootstrap p-value against the frozen baseline,
on the held-out split, for both overall accuracy and flip-detection accuracy.
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

from tcm import BatchedReserveCellular  # noqa: E402

from cures import ALL_CURES, CuredCellular  # noqa: E402
from evaluate import CELL_PARAMS, ece  # noqa: E402
from stream import FinanceNewsStream  # noqa: E402

RNG = np.random.default_rng(20260722)


def run_vectors(stream: FinanceNewsStream, model, split: str) -> dict:
    """Causal full-stream replay; collect per-event vectors for `split`."""
    q: dict[int, list] = defaultdict(list)
    recs = []
    want = {id(e) for e in stream.events if e.split == split}
    for event in stream.events:
        for fb in q.pop(event.t, []):
            model.feedback(fb)
        p, tr = model.predict(event.key, event.reports, event.t)
        used = int(tr.get("used", len(event.reports)))
        q[event.t + 1].append(
            {
                "key": event.key,
                "reports": event.reports,
                "truth": event.truth,
                "pred": p,
                "trace": tr,
                "time": event.t + 1,
            }
        )
        if id(event) not in want:
            continue
        is_flip = event.prev_truth is not None and event.truth != event.prev_truth
        recs.append(
            {
                "truth": event.truth,
                "p": float(p),
                "correct": int(int(p >= 0.5) == event.truth),
                "flip": int(is_flip),
                "used": used,
            }
        )
    truth = np.array([r["truth"] for r in recs], float)
    p = np.array([r["p"] for r in recs], float)
    correct = np.array([r["correct"] for r in recs], float)
    flip = np.array([r["flip"] for r in recs], bool)
    return {
        "n": len(recs),
        "truth": truth,
        "p": p,
        "correct": correct,
        "flip": flip,
        "used": np.array([r["used"] for r in recs], float),
        "accuracy": float(correct.mean()),
        "flip_accuracy": float(correct[flip].mean()) if flip.any() else float("nan"),
        "nonflip_accuracy": float(correct[~flip].mean()) if (~flip).any() else float("nan"),
        "flip_n": int(flip.sum()),
        "brier": float(np.mean((p - truth) ** 2)),
        "ece": ece(p, truth),
        "pred_up_rate": float((p >= 0.5).mean()),
        "avg_activated": float(np.mean([r["used"] for r in recs])),
    }


def boot_ci(vec: np.ndarray, mask: np.ndarray | None = None, n_boot: int = 5000):
    v = vec if mask is None else vec[mask]
    if len(v) == 0:
        return (float("nan"), float("nan"), float("nan"))
    idx = RNG.integers(0, len(v), size=(n_boot, len(v)))
    means = v[idx].mean(axis=1)
    return (float(v.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


def paired_delta(base: np.ndarray, cure: np.ndarray, mask: np.ndarray | None = None, n_boot: int = 5000):
    """Paired bootstrap of (cure - base); returns mean delta, 95% CI, 2-sided p."""
    b = base if mask is None else base[mask]
    c = cure if mask is None else cure[mask]
    if len(b) == 0:
        return {"delta": float("nan"), "lo": float("nan"), "hi": float("nan"), "p": float("nan")}
    diff = c - b
    idx = RNG.integers(0, len(diff), size=(n_boot, len(diff)))
    boot = diff[idx].mean(axis=1)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    # two-sided p: 2 x tail mass on the side of 0
    frac_gt = float(np.mean(boot > 0))
    frac_lt = float(np.mean(boot < 0))
    p = 2.0 * min(frac_gt, frac_lt)
    p = min(1.0, max(0.0, p))
    return {"delta": float(diff.mean()), "lo": float(lo), "hi": float(hi), "p": float(p)}


def build(cures):
    return CuredCellular(cures=cures, **CELL_PARAMS)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, default=ROOT / "data")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "results")
    ap.add_argument("--n-boot", type=int, default=5000)
    ap.add_argument("--horizon", type=int, default=1)
    args = ap.parse_args()

    stream = FinanceNewsStream(args.data_dir, horizon=args.horizon)

    configs = {"baseline_frozen": None, "cured_null": []}
    for cure in ALL_CURES:
        configs[cure] = [cure]
    configs["calibrate_both"] = ["source_calib", "corr_downweight"]
    configs["all_combined"] = list(ALL_CURES)

    payload = {"protocol": "realdata_finance_ablation_v0", "stream": stream.summary(), "splits": {}}
    vectors = {}
    for split in ("contact", "holdout"):
        payload["splits"][split] = {}
        for name, cures in configs.items():
            model = BatchedReserveCellular(**CELL_PARAMS) if cures is None else build(cures)
            res = run_vectors(stream, model, split)
            vectors[(split, name)] = res
            payload["splits"][split][name] = {
                k: res[k]
                for k in (
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

    # Sanity: cured_null must reproduce the frozen baseline exactly (holdout).
    base_h = vectors[("holdout", "baseline_frozen")]
    null_h = vectors[("holdout", "cured_null")]
    reproduces = bool(
        base_h["n"] == null_h["n"]
        and np.allclose(base_h["p"], null_h["p"], atol=1e-9)
    )
    payload["null_reproduces_frozen"] = reproduces

    # Bootstrap CIs + paired tests vs frozen baseline on HOLDOUT.
    stats = {}
    base = vectors[("holdout", "baseline_frozen")]
    for name in configs:
        cur = vectors[("holdout", name)]
        acc_mean, acc_lo, acc_hi = boot_ci(cur["correct"], n_boot=args.n_boot)
        flip_mean, flip_lo, flip_hi = boot_ci(cur["correct"], cur["flip"], n_boot=args.n_boot)
        entry = {
            "accuracy": {"mean": acc_mean, "lo": acc_lo, "hi": acc_hi},
            "flip_accuracy": {"mean": flip_mean, "lo": flip_lo, "hi": flip_hi},
        }
        if name != "baseline_frozen":
            entry["vs_frozen_accuracy"] = paired_delta(base["correct"], cur["correct"], n_boot=args.n_boot)
            # flip subset: pair on the baseline flip mask (same events/order)
            entry["vs_frozen_flip"] = paired_delta(
                base["correct"], cur["correct"], base["flip"], n_boot=args.n_boot
            )
        stats[name] = entry
    payload["holdout_stats"] = stats

    payload["horizon"] = args.horizon
    args.out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "" if args.horizon == 1 else f"_h{args.horizon}"
    (args.out_dir / f"ablation{suffix}.json").write_text(json.dumps(payload, indent=2, allow_nan=True))

    # Console summary.
    print(f"null_reproduces_frozen = {reproduces}")
    for split in ("contact", "holdout"):
        print(f"\n=== {split.upper()} ===")
        print(f"{'config':18s} {'acc':>7s} {'flip':>7s} {'nonflip':>8s} {'act':>6s} {'pup':>6s} {'brier':>6s}")
        for name in configs:
            m = payload["splits"][split][name]
            print(
                f"{name:18s} {m['accuracy']:.4f} {m['flip_accuracy']:.4f} "
                f"{m['nonflip_accuracy']:.4f} {m['avg_activated']:6.2f} "
                f"{m['pred_up_rate']:.3f} {m['brier']:.3f}"
            )
    print("\n=== HOLDOUT paired vs frozen (Δ, 95% CI, p) ===")
    for name in configs:
        if name == "baseline_frozen":
            continue
        a = stats[name]["vs_frozen_accuracy"]
        f = stats[name]["vs_frozen_flip"]
        print(
            f"{name:18s} acc Δ={a['delta']:+.4f} [{a['lo']:+.4f},{a['hi']:+.4f}] p={a['p']:.3f} | "
            f"flip Δ={f['delta']:+.4f} [{f['lo']:+.4f},{f['hi']:+.4f}] p={f['p']:.3f}"
        )


if __name__ == "__main__":
    main()
