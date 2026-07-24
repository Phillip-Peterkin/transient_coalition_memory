#!/usr/bin/env python3
"""One-shot Weather confirmation for sealed Active Coalition Inference.

Protocol: WEATHER_ACI_CONFIRMATION_PROTOCOL.md
One look. No retuning.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
FINANCE = REPO / "benchmarks" / "realdata_finance"
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(FINANCE))
sys.path.insert(0, str(ROOT))  # weather stream must win over finance stream.py

from ablation import paired_delta  # noqa: E402
from evaluate import CELL_PARAMS  # noqa: E402
from weather_stream import CleanWeatherStream  # noqa: E402
from tcm import (  # noqa: E402
    ActiveCoalitionCellular,
    BatchedReserveCellular,
    SilenceEscapeCellular,
)

SILENCE_FROZEN = {
    "pe_floor": 0.35,
    "pe_span": 0.50,
    "rho_gain": 0.30,
    "max_hazard": 0.70,
    "apply_to_all_positive": True,
}

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

FLIP_MIN = 0.45
FLIP_LIFT_VS_WAVEXI = 0.05
ACC_VS_PERSIST = -0.01
PRED_UP_MAX = 0.65
NONFLIP_MIN = 0.50


def _feedback_due(stream: CleanWeatherStream) -> dict[int, int]:
    """Map event.t -> earliest t' where day >= label_day+1 (= decision_day+2)."""
    days = sorted({event.day for event in stream.events})
    day_index = {day: index for index, day in enumerate(days)}
    first_t_for_day = {}
    for event in stream.events:
        first_t_for_day.setdefault(event.day, event.t)
    due = {}
    for event in stream.events:
        idx = day_index[event.day]
        target_idx = idx + 2  # D+2 after decision day D
        if target_idx >= len(days):
            continue
        due[event.t] = first_t_for_day[days[target_idx]]
    return due


def run_cellular(stream: CleanWeatherStream, model, split: str = "holdout") -> dict:
    due_map = _feedback_due(stream)
    queue: dict[int, list] = defaultdict(list)
    rows = []
    for event in stream.events:
        for feedback in queue.pop(event.t, []):
            model.feedback(feedback)
        probability, trace = model.predict(event.key, event.reports, event.t)
        due = due_map.get(event.t)
        if due is not None:
            queue[due].append(
                {
                    "key": event.key,
                    "reports": event.reports,
                    "truth": event.truth,
                    "pred": probability,
                    "trace": trace,
                    "time": due,
                }
            )
        if event.split != split:
            continue
        flip = event.prev_truth is not None and event.truth != event.prev_truth
        rows.append(
            {
                "p": float(probability),
                "y": int(event.truth),
                "correct": int((probability >= 0.5) == event.truth),
                "flip": int(flip),
                "used": float(trace.get("used", len(event.reports))),
            }
        )
    return _summarize(rows)


def run_persistence(stream: CleanWeatherStream, split: str = "holdout") -> dict:
    rows = []
    for event in stream.events:
        if event.split != split:
            continue
        if event.prev_truth is None:
            probability = 0.5
        else:
            probability = float(event.prev_truth)
        flip = event.prev_truth is not None and event.truth != event.prev_truth
        rows.append(
            {
                "p": probability,
                "y": int(event.truth),
                "correct": int((probability >= 0.5) == event.truth),
                "flip": int(flip),
                "used": 0.0,
            }
        )
    return _summarize(rows)


def run_majority(stream: CleanWeatherStream, split: str = "holdout") -> dict:
    rows = []
    for event in stream.events:
        if event.split != split:
            continue
        votes = [vote for _, _, vote in event.reports]
        probability = float(np.mean(votes)) if votes else 0.5
        flip = event.prev_truth is not None and event.truth != event.prev_truth
        rows.append(
            {
                "p": probability,
                "y": int(event.truth),
                "correct": int((probability >= 0.5) == event.truth),
                "flip": int(flip),
                "used": float(len(votes)),
            }
        )
    return _summarize(rows)


def _summarize(rows: list[dict]) -> dict:
    if not rows:
        raise RuntimeError("no scored rows")
    correct = np.asarray([row["correct"] for row in rows], dtype=float)
    flip = np.asarray([row["flip"] for row in rows], dtype=bool)
    probs = np.asarray([row["p"] for row in rows], dtype=float)
    truths = np.asarray([row["y"] for row in rows], dtype=float)
    used = np.asarray([row["used"] for row in rows], dtype=float)
    nonflip = ~flip
    return {
        "n": int(len(rows)),
        "accuracy": float(correct.mean()),
        "flip_accuracy": float(correct[flip].mean()) if flip.any() else float("nan"),
        "nonflip_accuracy": (
            float(correct[nonflip].mean()) if nonflip.any() else float("nan")
        ),
        "flip_n": int(flip.sum()),
        "brier": float(np.mean((probs - truths) ** 2)),
        "pred_up_rate": float((probs >= 0.5).mean()),
        "avg_activated": float(used.mean()),
        "correct": correct,
        "flip": flip,
        "p": probs,
    }


def concise(result: dict) -> dict:
    return {
        key: result[key]
        for key in (
            "n",
            "accuracy",
            "flip_accuracy",
            "nonflip_accuracy",
            "flip_n",
            "brier",
            "pred_up_rate",
            "avg_activated",
        )
    }


def gate(aci: dict, wave: dict, persist: dict) -> dict:
    checks = {
        "flip_ge_0.45": aci["flip_accuracy"] >= FLIP_MIN,
        "flip_lift_vs_wavexi": (
            aci["flip_accuracy"] >= wave["flip_accuracy"] + FLIP_LIFT_VS_WAVEXI
        ),
        "acc_vs_persistence": aci["accuracy"] >= persist["accuracy"] + ACC_VS_PERSIST,
        "pred_up_le_0.65": aci["pred_up_rate"] <= PRED_UP_MAX,
        "nonflip_ge_0.50": aci["nonflip_accuracy"] >= NONFLIP_MIN,
    }
    return {"checks": checks, "passes": all(checks.values())}


def main() -> None:
    stream = CleanWeatherStream(ROOT / "data")
    persistence = run_persistence(stream)
    majority = run_majority(stream)
    wave = run_cellular(stream, BatchedReserveCellular(**CELL_PARAMS))
    silence = run_cellular(
        stream, SilenceEscapeCellular(**SILENCE_FROZEN, **CELL_PARAMS)
    )
    aci = run_cellular(stream, ActiveCoalitionCellular(**ACI_FROZEN, **CELL_PARAMS))

    decision = gate(aci, wave, persistence)
    payload = {
        "protocol": "weather_aci_confirmation_v1",
        "candidate": f"CleanWeatherStream + ActiveCoalitionCellular({ACI_FROZEN})",
        "stream": stream.summary(),
        "warmup": "first 70% of days; causal state only, not scored",
        "feedback_delay": "first event on decision_day+2 (label uses obs day+1)",
        "holdout": {
            "persistence": concise(persistence),
            "majority": concise(majority),
            "wave_xi": concise(wave),
            "silence_escape": concise(silence),
            "active_coalition": concise(aci),
        },
        "paired": {
            "vs_wave_xi_accuracy": paired_delta(
                wave["correct"], aci["correct"], n_boot=5000
            ),
            "vs_wave_xi_flip": paired_delta(
                wave["correct"], aci["correct"], wave["flip"], n_boot=5000
            ),
            "vs_persistence_accuracy": paired_delta(
                persistence["correct"], aci["correct"], n_boot=5000
            ),
            "vs_majority_accuracy": paired_delta(
                majority["correct"], aci["correct"], n_boot=5000
            ),
        },
        "gate": decision,
        "passes_predeclared_gate": decision["passes"],
    }
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    path = out / "weather_aci_confirmation.json"
    path.write_text(json.dumps(payload, indent=2, default=float))

    print("WEATHER ACI CONFIRMATION")
    print(f"passes_predeclared_gate={decision['passes']}")
    for name, block in payload["holdout"].items():
        print(
            f"  {name}: acc={block['accuracy']:.3f} "
            f"flip={block['flip_accuracy']:.3f} "
            f"nonflip={block['nonflip_accuracy']:.3f} "
            f"pred_up={block['pred_up_rate']:.3f} "
            f"act={block['avg_activated']:.2f} "
            f"flips={block['flip_n']}"
        )
    print("GATE")
    for name, ok in decision["checks"].items():
        print(f"  {name}: {'PASS' if ok else 'FAIL'}")
    print("wrote", path)


if __name__ == "__main__":
    main()
