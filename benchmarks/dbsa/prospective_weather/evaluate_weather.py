#!/usr/bin/env python3
"""Sealed prospective-weather scoring (opens only when protocol conditions hold)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
DBSA = ROOT.parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(DBSA))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(ROOT))

from baselines import (  # noqa: E402
    AdaHedge,
    AgreementDiscountedBayes,
    FadingSourceBayes,
    FixedShareHedge,
    Majority,
    Persistence,
    PrecisionWhitenedDelayedResidual,
)
from evaluate import (  # noqa: E402
    ACI_PARAMS,
    AWARE_PARAMS,
    AWARE_POOL_RESTORE_PARAMS,
    AWARE_ROPL_PARAMS,
    AWARE_AROUSAL_PARAMS,
    BRIER_NONINFERIORITY_DELTA,
    CELL_PARAMS,
    _ece,
    _log_loss,
    _mean_metrics,
    _paired_bootstrap_delta,
)
from tcm import ActiveExperimentalCellular, AwareCoalitionCellular  # noqa: E402
from weather_stream import build_events, ledger_status  # noqa: E402

SCORING_PROTOCOL = ROOT / "SCORING_PROTOCOL.md"


def _git_sha(path: Path) -> str:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD:" + str(path.relative_to(REPO))],
                cwd=REPO,
                text=True,
            ).strip()
        )
    except Exception:
        return "unknown"


def _method_factories():
    return {
        "persistence": Persistence,
        "majority": Majority,
        "fixed_share_hedge": FixedShareHedge,
        "ada_hedge": AdaHedge,
        "fading_source_bayes": FadingSourceBayes,
        "agreement_discounted_bayes": AgreementDiscountedBayes,
        "pwdr": PrecisionWhitenedDelayedResidual,
        "active_experimental_aci": lambda: ActiveExperimentalCellular(
            **ACI_PARAMS, **CELL_PARAMS
        ),
        "aware_coalition": lambda: AwareCoalitionCellular(**AWARE_PARAMS, **CELL_PARAMS),
        "aware_pool_restore": lambda: AwareCoalitionCellular(
            **AWARE_POOL_RESTORE_PARAMS, **CELL_PARAMS
        ),
        "aware_ropl": lambda: AwareCoalitionCellular(
            **AWARE_ROPL_PARAMS, **CELL_PARAMS
        ),
        "aware_arousal": lambda: AwareCoalitionCellular(
            **AWARE_AROUSAL_PARAMS, **CELL_PARAMS
        ),
    }


def run_model(events, model) -> dict:
    queue: dict[int, list[dict]] = defaultdict(list)
    rows = []
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
                "post_shift": False,
            }
        )

    truth = np.asarray([row["truth"] for row in rows], dtype=float)
    probability = np.asarray([row["p"] for row in rows], dtype=float)
    correct = np.asarray([row["correct"] for row in rows], dtype=float)
    flip = np.asarray([row["flip"] for row in rows], dtype=bool)
    predicted_change = np.asarray([row["predicted_change"] for row in rows], dtype=bool)
    brier = (probability - truth) ** 2
    return {
        "n": len(rows),
        "brier": float(brier.mean()) if len(rows) else None,
        "log_loss": float(np.mean([_log_loss(row["p"], row["truth"]) for row in rows]))
        if rows
        else None,
        "ece": _ece(probability, truth) if len(rows) else None,
        "accuracy": float(correct.mean()) if len(rows) else None,
        "flip_n": int(flip.sum()),
        "flip_recall": float(predicted_change[flip].mean()) if flip.any() else None,
        "change_false_alarm": (
            float(predicted_change[~flip].mean()) if (~flip).any() else None
        ),
        "post_shift_n": 0,
        "post_shift_brier": None,
        "avg_reports_inspected": float(np.mean([row["n_reports"] for row in rows]))
        if rows
        else None,
        "avg_downstream_activated": float(np.mean([row["used"] for row in rows]))
        if rows
        else None,
        "wall_seconds": None,
        "cpu_seconds": None,
        "peak_tracemalloc_mb": None,
        "events_per_second": None,
        "model_stats": model.stats(),
    }


def open_conditions(status: dict) -> dict:
    synthetic = DBSA / "results" / "dbsa_v1_contract_200_push.json"
    if not synthetic.exists():
        synthetic = DBSA / "results" / "dbsa_v1_contract_200.json"
    checks = {
        "forecast_days_ge_60": bool(status["open_forecast_days_met"]),
        "labeled_decision_days_ge_45": bool(status["open_label_days_met"]),
        "scoring_protocol_present": SCORING_PROTOCOL.exists(),
        "synthetic_200_artifact_present": synthetic.exists(),
    }
    return {
        "checks": checks,
        "all_passed": all(checks.values()),
        "synthetic_artifact": str(synthetic.relative_to(DBSA)) if synthetic.exists() else None,
        "scoring_protocol_git_sha": _git_sha(SCORING_PROTOCOL),
        "status": status,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        type=Path,
        default=DBSA / "results" / "dbsa_weather_prospective_sealed.json",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Run even if open conditions fail (debug only; default refuses).",
    )
    args = parser.parse_args()

    status = ledger_status()
    gate = open_conditions(status)
    if not gate["all_passed"] and not args.force:
        print("REFUSING to score: open conditions not met")
        print(json.dumps(gate, indent=2))
        raise SystemExit(2)

    events = build_events()
    # Bootstrap CI needs multiple paired blocks: split by decision day.
    days = sorted({event.day for event in events})
    per_method_day: dict[str, list[dict]] = defaultdict(list)
    summaries = {}
    for name, factory in _method_factories().items():
        # One continuous causal stream (not refit per day).
        result = run_model(events, factory())
        summaries[name] = result
        # Day-block Brier for paired bootstrap vs Fixed-Share.
        by_day = defaultdict(list)
        # Recompute day blocks with a fresh model for fair block metrics.
        model = factory()
        queue: dict[int, list[dict]] = defaultdict(list)
        for event in events:
            for feedback in queue.pop(event.t, []):
                model.feedback(feedback)
            probability, trace = model.predict(event.key, event.reports, event.t)
            queue[event.due_t].append(
                {
                    "key": event.key,
                    "reports": event.reports,
                    "truth": event.truth,
                    "pred": float(probability),
                    "trace": trace,
                    "time": event.due_t,
                }
            )
            by_day[event.day].append((float(probability), event.truth))
        for day in days:
            pairs = by_day[day]
            if not pairs:
                continue
            brier = float(np.mean([(p - y) ** 2 for p, y in pairs]))
            per_method_day[name].append({"brier": brier, "day": day})

    # Align day rows
    aware_rows = per_method_day["aware_coalition"]
    fs_rows = per_method_day["fixed_share_hedge"]
    brier_delta = _paired_bootstrap_delta(aware_rows, fs_rows, "brier")
    payload = {
        "protocol": "dbsa_prospective_weather_sealed_v1",
        "scoring_protocol_git_sha": gate["scoring_protocol_git_sha"],
        "open_gate": gate,
        "n_events": len(events),
        "n_decision_days": len(days),
        "primary_metric": "prequential_brier",
        "brier_noninferiority_delta": BRIER_NONINFERIORITY_DELTA,
        "summary": summaries,
        "comparisons": {
            "aware_vs_fixed_share_brier": brier_delta,
            "brier_noninferior": (
                brier_delta["one_sided_97_5_upper"] is not None
                and brier_delta["one_sided_97_5_upper"] <= BRIER_NONINFERIORITY_DELTA
            ),
        },
        "honesty": {
            "collection_includes_archive_backfill": True,
            "spent_weather_beds_excluded": True,
            "no_retune_on_this_look": True,
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, default=float))
    print("n_events", len(events), "days", len(days))
    for name, values in summaries.items():
        print(
            f"{name:30} brier={values['brier']:.4f} acc={values['accuracy']:.3f} "
            f"flip={values['flip_recall']} used={values['avg_downstream_activated']:.2f}"
        )
    print(
        "noninferiority",
        payload["comparisons"]["brier_noninferior"],
        payload["comparisons"]["aware_vs_fixed_share_brier"],
    )
    print("wrote", args.out)


if __name__ == "__main__":
    main()
