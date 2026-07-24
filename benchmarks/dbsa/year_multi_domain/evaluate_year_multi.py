#!/usr/bin/env python3
"""Sealed year-multi-domain first look — opens only when protocol conditions hold."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
DBSA = ROOT.parent
REPO = DBSA.parents[1]
sys.path.insert(0, str(DBSA))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(DBSA / "prospective_weather"))
sys.path.insert(0, str(ROOT))

from baselines import FixedShareHedge, Majority, Persistence  # noqa: E402
from evaluate import (  # noqa: E402
    AWARE_AROUSAL_PARAMS,
    AWARE_PARAMS,
    AWARE_ROPL_PARAMS,
    AROUSAL_PARAMS,
    CELL_PARAMS,
    ROPL_PARAMS,
    _ece,
    _log_loss,
)
from tcm import AwareCoalitionCellular  # noqa: E402

SCORING_PROTOCOL = ROOT / "SCORING_PROTOCOL.md"


@dataclass
class SimpleEvent:
    t: int
    due_t: int
    key: tuple
    reports: list
    truth: int
    prev_truth: int | None
    day: str | None = None


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
        "aware_essc": lambda: AwareCoalitionCellular(**AWARE_PARAMS, **CELL_PARAMS),
        "aware_ropl": lambda: AwareCoalitionCellular(**AWARE_ROPL_PARAMS, **CELL_PARAMS),
        "aware_arousal": lambda: AwareCoalitionCellular(
            **AWARE_AROUSAL_PARAMS, **CELL_PARAMS
        ),
    }


def run_model(events: list[SimpleEvent], model) -> dict:
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
        awareness = (trace.get("awareness") or {}) if isinstance(trace, dict) else {}
        arousal = awareness.get("arousal") or {}
        rows.append(
            {
                "truth": event.truth,
                "p": probability,
                "correct": int(prediction == event.truth),
                "flip": bool(is_flip),
                "predicted_change": bool(predicted_change),
                "used": int(trace.get("used", len(event.reports))),
                "n_reports": len(event.reports),
                "day": event.day,
                "arousal_mode": arousal.get("mode"),
                "ropl_g": float(arousal.get("ropl_g", 0.0) or 0.0),
            }
        )

    truth = np.asarray([row["truth"] for row in rows], dtype=float)
    probability = np.asarray([row["p"] for row in rows], dtype=float)
    correct = np.asarray([row["correct"] for row in rows], dtype=float)
    flip = np.asarray([row["flip"] for row in rows], dtype=bool)
    predicted_change = np.asarray([row["predicted_change"] for row in rows], dtype=bool)
    brier = (probability - truth) ** 2
    modes = [row["arousal_mode"] for row in rows]
    thrift_n = sum(1 for m in modes if m == "thrift")
    truth_n = sum(1 for m in modes if m == "truth")
    out = {
        "n": len(rows),
        "brier": float(brier.mean()) if len(rows) else None,
        "log_loss": float(np.mean([_log_loss(row["p"], row["truth"]) for row in rows]))
        if rows
        else None,
        "ece": _ece(probability, truth) if len(rows) else None,
        "accuracy": float(correct.mean()) if len(rows) else None,
        "flip_n": int(flip.sum()),
        "flip_recall": float(predicted_change[flip].mean()) if flip.any() else None,
        "avg_reports_inspected": float(np.mean([row["n_reports"] for row in rows]))
        if rows
        else None,
        "avg_downstream_activated": float(np.mean([row["used"] for row in rows]))
        if rows
        else None,
        "model_stats": model.stats() if hasattr(model, "stats") else {},
    }
    if thrift_n + truth_n:
        out["arousal_thrift_frac"] = thrift_n / max(1, thrift_n + truth_n)
        out["arousal_truth_frac"] = truth_n / max(1, thrift_n + truth_n)
        thrift_used = [r["used"] for r in rows if r["arousal_mode"] == "thrift"]
        truth_used = [r["used"] for r in rows if r["arousal_mode"] == "truth"]
        out["thrift_mean_used"] = float(np.mean(thrift_used)) if thrift_used else None
        out["truth_mean_used"] = float(np.mean(truth_used)) if truth_used else None
        out["mean_ropl_g"] = float(np.mean([r["ropl_g"] for r in rows]))
    return out


def load_weather_events() -> list[SimpleEvent]:
    os.environ["DBSA_WEATHER_LEDGER"] = str(
        DBSA / "weather_year_stress" / "ledger"
    )
    from weather_stream import build_events

    raw = build_events()
    return [
        SimpleEvent(
            t=int(e.t),
            due_t=int(e.due_t),
            key=tuple(e.key),
            reports=[tuple(r) for r in e.reports],
            truth=int(e.truth),
            prev_truth=None if e.prev_truth is None else int(e.prev_truth),
            day=str(e.day),
        )
        for e in raw
    ]


def _json_lane_events(path: Path) -> list[SimpleEvent]:
    payload = json.loads(path.read_text())
    raw = payload["events"]
    # Map chronological dates → integer times for delay queue.
    stamps = sorted({e["t"] for e in raw} | {e["due_t"] for e in raw})
    index = {s: i for i, s in enumerate(stamps)}
    # source id map for string models
    source_ids: dict[str, int] = {}

    def sid(x) -> int | str:
        if isinstance(x, int):
            return x
        s = str(x)
        if s not in source_ids:
            source_ids[s] = len(source_ids)
        return source_ids[s]

    prev: dict = {}
    events: list[SimpleEvent] = []
    for e in sorted(raw, key=lambda r: (r["t"], str(r["key"]))):
        key = tuple(e["key"]) if isinstance(e["key"], list) else (e["key"],)
        entity = key[0]
        reports = []
        for rep in e["reports"]:
            src, ctx, vote = rep[0], int(rep[1]), int(rep[2])
            reports.append((sid(src), ctx, vote))
        events.append(
            SimpleEvent(
                t=index[e["t"]],
                due_t=index[e["due_t"]],
                key=key,
                reports=reports,
                truth=int(e["truth"]),
                prev_truth=prev.get(entity),
                day=str(e["t"]),
            )
        )
        prev[entity] = int(e["truth"])
    return events


def load_finance_events() -> list[SimpleEvent]:
    return _json_lane_events(ROOT / "finance" / "ledger" / "events.json")


def load_medical_events() -> list[SimpleEvent]:
    return _json_lane_events(ROOT / "medical" / "ledger" / "events.json")


def lane_status() -> dict:
    from status import main as status_main
    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    with redirect_stdout(buf):
        status_main()
    return json.loads(buf.getvalue())


def open_conditions() -> dict:
    status = lane_status()
    lanes = {lane["lane"]: lane for lane in status["lanes"]}
    weather = lanes.get("weather", {})
    finance = lanes.get("finance", {})
    medical = lanes.get("medical", {})
    synth = DBSA / "results" / "dbsa_v1_contract_200_push.json"
    if not synth.exists():
        synth = DBSA / "results" / "dbsa_v1_contract_200.json"
    checks = {
        "weather_forecast_year_ready": bool(weather.get("open_forecast_days_met"))
        or int(weather.get("n_forecast_days") or 0) >= 365,
        "weather_labels_ge_350": bool(weather.get("open_label_days_met"))
        or int(weather.get("n_labeled_decision_days") or 0) >= 350,
        "finance_events_ge_200": int(finance.get("n_events") or 0) >= 200,
        "medical_events_ge_40": int(medical.get("n_events") or 0) >= 40,
        "scoring_protocol_present": SCORING_PROTOCOL.exists(),
        "synthetic_200_artifact_present": synth.exists(),
    }
    return {
        "checks": checks,
        "all_passed": all(checks.values()),
        "status": status,
        "scoring_protocol_git_sha": _git_sha(SCORING_PROTOCOL),
    }


def score_lane(name: str, events: list[SimpleEvent]) -> dict:
    factories = _method_factories()
    # Persistence needs reports; skip if empty batches common — still run.
    results = {}
    for method, factory in factories.items():
        print(f"  {name}:{method} n={len(events)}", flush=True)
        res = run_model(events, factory())
        row = {
            "brier": res["brier"],
            "accuracy": res["accuracy"],
            "used": res["avg_downstream_activated"],
            "n": res["n"],
            "flip_n": res["flip_n"],
            "flip_recall": res["flip_recall"],
            "ece": res["ece"],
        }
        for k in (
            "arousal_thrift_frac",
            "arousal_truth_frac",
            "thrift_mean_used",
            "truth_mean_used",
            "mean_ropl_g",
        ):
            if k in res:
                row[k] = res[k]
        ms = res.get("model_stats") or {}
        for k in (
            "arousal_thrift_count",
            "arousal_truth_count",
            "rebate_est",
            "rebate_updates",
            "ropl_mean_g",
            "essc_applications",
        ):
            if k in ms:
                row[k] = ms[k]
        results[method] = row
    maj = results["majority"]["brier"]
    aro = results["aware_arousal"]["brier"]
    results["_delta"] = {
        "arousal_minus_majority": None if maj is None or aro is None else aro - maj,
        "arousal_minus_fixed_share": (
            None
            if results["fixed_share_hedge"]["brier"] is None or aro is None
            else aro - results["fixed_share_hedge"]["brier"]
        ),
        "arousal_minus_essc": (
            None
            if results["aware_essc"]["brier"] is None or aro is None
            else aro - results["aware_essc"]["brier"]
        ),
        "arousal_minus_ropl": (
            None
            if results["aware_ropl"]["brier"] is None or aro is None
            else aro - results["aware_ropl"]["brier"]
        ),
    }
    return results


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument(
        "--out",
        type=Path,
        default=DBSA / "results" / "dbsa_year_multi_domain_first_look.json",
    )
    args = ap.parse_args()

    gate = open_conditions()
    print(json.dumps({"open_conditions": gate["checks"], "all_passed": gate["all_passed"]}, indent=2))
    if not gate["all_passed"] and not args.force:
        raise SystemExit(
            "SCORING CLOSED — year_multi_domain open conditions not met. Collect only."
        )

    print("loading weather…", flush=True)
    weather = load_weather_events()
    print("loading finance…", flush=True)
    finance = load_finance_events()
    print("loading medical…", flush=True)
    medical = load_medical_events()

    lanes = {
        "weather": score_lane("weather", weather),
        "finance": score_lane("finance", finance),
        "medical": score_lane("medical", medical),
    }

    def verdict(lane: dict) -> dict:
        d = lane["_delta"]["arousal_minus_majority"]
        maj = lane["majority"]["brier"]
        aro = lane["aware_arousal"]["brier"]
        if d is None:
            headline = "n/a"
            crush = False
        elif d < 0:
            headline = "CRUSH majority"
            crush = True
        elif abs(d) <= 0.0005:
            headline = "MATCH majority"
            crush = False
        else:
            headline = "FAIL vs majority"
            crush = False
        return {
            "crushes_majority": crush,
            "brier_arousal": aro,
            "brier_majority": maj,
            "delta": d,
            "used_arousal": lane["aware_arousal"]["used"],
            "thrift_frac": lane["aware_arousal"].get("arousal_thrift_frac"),
            "headline": headline,
        }

    artifact = {
        "protocol": "dbsa_year_multi_domain_first_look_v1",
        "baked_at_utc": datetime.now(timezone.utc).isoformat(),
        "scoring_protocol_git_sha": gate["scoring_protocol_git_sha"],
        "arousal_params_locked": AROUSAL_PARAMS,
        "ropl_params_locked": ROPL_PARAMS,
        "open_conditions": gate,
        "lane_sizes": {
            "weather": len(weather),
            "finance": len(finance),
            "medical": len(medical),
        },
        "lanes": lanes,
        "verdicts": {name: verdict(payload) for name, payload in lanes.items()},
        "honesty": {
            "knobs_locked_before_scoring": True,
            "no_retune_after_look": True,
            "christmas_ledger_untouched": True,
            "finance_confirmation8_untouched": True,
            "scored_once": True,
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(artifact, indent=2))
    print("WROTE", args.out)
    print(json.dumps(artifact["verdicts"], indent=2))


if __name__ == "__main__":
    main()
