#!/usr/bin/env python3
"""Virgin Weather confirmation of AwareCoalitionCellular (Mnemosheath).

Protocol: WEATHER_AWARE_CONFIRMATION_PROTOCOL.md
Subject: AwareCoalitionCellular — packaged ACI + awareness organ.
One look on confirmation3. No retuning.
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
sys.path.insert(0, str(ROOT))

from ablation import paired_delta  # noqa: E402
from evaluate import CELL_PARAMS  # noqa: E402
from weather_stream import CleanWeatherStream  # noqa: E402
from tcm import (  # noqa: E402
    ActiveExperimentalCellular,
    AwareCoalitionCellular,
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

# Same ACI freeze; Aware class forces force_all_positive_null=False.
AWARE_FROZEN = {
    "min_delta": 0.15,
    "max_silence_hazard": 0.55,
    "null_rho_gain": 0.30,
    "null_pe_floor": 0.35,
    "null_pe_span": 0.50,
    "null_err_beta": 0.30,
    "fe_cert_slack": 0.0,
}

FLIP_MIN = 0.45
ACC_VS_PERSIST = -0.01
PRED_UP_MAX = 0.65
NONFLIP_MIN = 0.50


def _feedback_due(stream: CleanWeatherStream) -> dict[int, int]:
    days = sorted({event.day for event in stream.events})
    day_index = {day: index for index, day in enumerate(days)}
    first_t_for_day = {}
    for event in stream.events:
        first_t_for_day.setdefault(event.day, event.t)
    due = {}
    for event in stream.events:
        idx = day_index[event.day]
        target_idx = idx + 2
        if target_idx >= len(days):
            continue
        due[event.t] = first_t_for_day[days[target_idx]]
    return due


def run_cellular(stream: CleanWeatherStream, model, split: str = "holdout") -> dict:
    due_map = _feedback_due(stream)
    queue: dict[int, list] = defaultdict(list)
    rows = []
    awareness_bits = []
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
        awareness = trace.get("awareness") or {}
        if "bits" in awareness:
            awareness_bits.append(int(awareness["bits"]))
        rows.append(
            {
                "p": float(probability),
                "y": int(event.truth),
                "correct": int((probability >= 0.5) == event.truth),
                "flip": int(flip),
                "used": float(trace.get("used", len(event.reports))),
            }
        )
    summary = _summarize(rows)
    if awareness_bits:
        summary["awareness_bits_mean"] = float(np.mean(awareness_bits))
        summary["awareness_bits_max"] = int(max(awareness_bits))
    if hasattr(model, "awareness_evidence_routes"):
        summary["awareness_evidence_routes"] = int(model.awareness_evidence_routes)
        summary["awareness_null_routes"] = int(model.awareness_null_routes)
    if hasattr(model, "sheath"):
        summary["grown_cues"] = sorted(model.sheath.grown_cues())
        summary["sheath_stats"] = model.sheath.stats()
    return summary


def run_persistence(stream: CleanWeatherStream, split: str = "holdout") -> dict:
    rows = []
    for event in stream.events:
        if event.split != split:
            continue
        probability = 0.5 if event.prev_truth is None else float(event.prev_truth)
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
    keys = (
        "n",
        "accuracy",
        "flip_accuracy",
        "nonflip_accuracy",
        "flip_n",
        "brier",
        "pred_up_rate",
        "avg_activated",
        "awareness_bits_mean",
        "awareness_bits_max",
        "awareness_evidence_routes",
        "awareness_null_routes",
        "grown_cues",
    )
    return {key: result[key] for key in keys if key in result}


def gate(aware: dict, aci: dict, silence: dict, persist: dict) -> dict:
    checks = {
        "flip_ge_0.45": aware["flip_accuracy"] >= FLIP_MIN,
        "flip_ge_sealed_aci": aware["flip_accuracy"] >= aci["flip_accuracy"],
        "flip_ge_silence_lineage": aware["flip_accuracy"] >= silence["flip_accuracy"],
        "acc_vs_persistence": aware["accuracy"] >= persist["accuracy"] + ACC_VS_PERSIST,
        "pred_up_le_0.65": aware["pred_up_rate"] <= PRED_UP_MAX,
        "nonflip_ge_0.50": aware["nonflip_accuracy"] >= NONFLIP_MIN,
    }
    return {"checks": checks, "passes": all(checks.values())}


def _assert_disjoint(stream: CleanWeatherStream) -> None:
    contact_meta = json.loads((ROOT / "data" / "download_meta.json").read_text())
    conf2_meta = json.loads(
        (ROOT / "data_confirmation2" / "download_meta.json").read_text()
    )
    contact_cities = {city["symbol"] for city in contact_meta["cities"]}
    conf2_cities = {city["symbol"] for city in conf2_meta["cities"]}
    conf3_cities = set(stream.city_symbols)
    overlap_contact = contact_cities & conf3_cities
    overlap_conf2 = conf2_cities & conf3_cities
    if overlap_contact:
        raise RuntimeError(f"confirmation3 overlaps contact bed: {overlap_contact}")
    if overlap_conf2:
        raise RuntimeError(f"confirmation3 overlaps confirmation2: {overlap_conf2}")


def main() -> None:
    data = ROOT / "data_confirmation3"
    if not data.exists():
        raise SystemExit(
            "missing data_confirmation3/; run download_confirmation3.py first"
        )
    stream = CleanWeatherStream(data)
    _assert_disjoint(stream)

    persistence = run_persistence(stream)
    majority = run_majority(stream)
    silence = run_cellular(
        stream, SilenceEscapeCellular(**SILENCE_FROZEN, **CELL_PARAMS)
    )
    aci = run_cellular(
        stream, ActiveExperimentalCellular(**ACI_FROZEN, **CELL_PARAMS)
    )
    aware = run_cellular(
        stream, AwareCoalitionCellular(**AWARE_FROZEN, **CELL_PARAMS)
    )
    decision = gate(aware, aci, silence, persistence)

    payload = {
        "protocol": "weather_aware_confirmation_v1",
        "architecture_under_test": "AwareCoalitionCellular (ACI + Mnemosheath)",
        "not_under_test": "BatchedReserveCellular (Wave XI synthetic reference)",
        "candidate": f"CleanWeatherStream + AwareCoalitionCellular({AWARE_FROZEN})",
        "parent_architecture": f"ActiveExperimentalCellular({ACI_FROZEN})",
        "universe": "confirmation3",
        "stream": stream.summary(),
        "warmup": "first 70% of days; causal state only, not scored",
        "feedback_delay": "first event on decision_day+2",
        "holdout": {
            "persistence": concise(persistence),
            "majority": concise(majority),
            "silence_escape": concise(silence),
            "active_experimental_aci": concise(aci),
            "aware_coalition": concise(aware),
        },
        "paired": {
            "vs_aci_accuracy": paired_delta(
                aci["correct"], aware["correct"], n_boot=5000
            ),
            "vs_aci_flip": paired_delta(
                aci["correct"], aware["correct"], aci["flip"], n_boot=5000
            ),
            "vs_silence_accuracy": paired_delta(
                silence["correct"], aware["correct"], n_boot=5000
            ),
            "vs_silence_flip": paired_delta(
                silence["correct"], aware["correct"], silence["flip"], n_boot=5000
            ),
            "vs_persistence_accuracy": paired_delta(
                persistence["correct"], aware["correct"], n_boot=5000
            ),
            "vs_majority_accuracy": paired_delta(
                majority["correct"], aware["correct"], n_boot=5000
            ),
        },
        "gate": decision,
        "passes_predeclared_gate": decision["passes"],
    }
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    path = out / "weather_aware_confirmation.json"
    path.write_text(json.dumps(payload, indent=2, default=float))

    print("WEATHER AWARE CONFIRMATION (ACI + Mnemosheath)")
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
    if "grown_cues" in aware:
        print(f"  aware grown_cues={aware.get('grown_cues')}")
        print(
            f"  aware routes evidence={aware.get('awareness_evidence_routes')} "
            f"null={aware.get('awareness_null_routes')} "
            f"bits_max={aware.get('awareness_bits_max')}"
        )
    print("GATE")
    for name, ok in decision["checks"].items():
        print(f"  {name}: {'PASS' if ok else 'FAIL'}")
    print("wrote", path)


if __name__ == "__main__":
    main()
