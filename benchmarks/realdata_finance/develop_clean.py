#!/usr/bin/env python3
"""Mid-test the dead-pixel fixes and report new data markers.

Order of contact (finance development only):

1. Rebuild the stream with session cutoffs + adjacent-session flips.
2. Enforce no sign-reversal by memory.
3. Replace emission-rarity source weights with delayed correctness trust.

Each step is scored on the contact tail so the old holdout is not used as a
design knob. Markers are measured on the full stream construction.
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

from ablation import paired_delta  # noqa: E402
from develop_transition import contact_tail_days, score_days  # noqa: E402
from evaluate import CELL_PARAMS  # noqa: E402
from relevance import RelevanceFinanceNewsStream  # noqa: E402
from session_stream import SessionRelevanceFinanceNewsStream  # noqa: E402
from tcm import CleanEvidenceCellular, SensoryGatedCellular  # noqa: E402


def sign_reversal_rate(stream, model_factory) -> dict:
    model = model_factory()
    queue: dict[int, list] = defaultdict(list)
    reversed_n = 0
    total = 0
    floor_n = 0
    for event in stream.events:
        for feedback in queue.pop(event.t, []):
            model.feedback(feedback)
        if event.reports:
            rows = model._rows(event.key, event.reports)
            for _, signed, _, _, vote, _ in rows:
                total += 1
                raw = 1.0 if vote else -1.0
                if signed != 0 and np.sign(signed) != np.sign(raw):
                    reversed_n += 1
            floor_n += int(getattr(model, "sign_floors", 0))
            # Reset per-event floor counter pollution by reading delta via stats later.
        probability, trace = model.predict(event.key, event.reports, event.t)
        queue[event.t + 1].append(
            {
                "key": event.key,
                "reports": event.reports,
                "truth": event.truth,
                "pred": probability,
                "trace": trace,
                "time": event.t + 1,
            }
        )
    stats = model.stats()
    return {
        "report_rows": total,
        "sign_reversals": reversed_n,
        "sign_reversal_rate": reversed_n / max(1, total),
        "sign_floors": int(stats.get("sign_floors", floor_n)),
        "mean_source_trust": float(stats.get("mean_source_trust", float("nan"))),
        "trust_updates": int(stats.get("trust_updates", 0)),
    }


def flip_confidence_markers(stream, model_factory, days: set[str]) -> dict:
    model = model_factory()
    queue: dict[int, list] = defaultdict(list)
    flip_conf_correct = []
    flip_conf_wrong = []
    for event in stream.events:
        for feedback in queue.pop(event.t, []):
            model.feedback(feedback)
        probability, trace = model.predict(event.key, event.reports, event.t)
        queue[event.t + 1].append(
            {
                "key": event.key,
                "reports": event.reports,
                "truth": event.truth,
                "pred": probability,
                "trace": trace,
                "time": event.t + 1,
            }
        )
        if event.day not in days:
            continue
        is_flip = event.prev_truth is not None and event.truth != event.prev_truth
        if not is_flip:
            continue
        conf = abs(float(probability) - 0.5)
        if int(probability >= 0.5) == event.truth:
            flip_conf_correct.append(conf)
        else:
            flip_conf_wrong.append(conf)
    return {
        "flip_confidence_when_correct": float(np.mean(flip_conf_correct))
        if flip_conf_correct
        else float("nan"),
        "flip_confidence_when_wrong": float(np.mean(flip_conf_wrong))
        if flip_conf_wrong
        else float("nan"),
        "flip_correct_n": len(flip_conf_correct),
        "flip_wrong_n": len(flip_conf_wrong),
    }


def concise(result: dict) -> dict:
    return {
        key: value
        for key, value in result.items()
        if key not in {"correct", "flip", "stats"}
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument(
        "--out", type=Path, default=ROOT / "results" / "clean_development.json"
    )
    parser.add_argument("--n-boot", type=int, default=2000)
    args = parser.parse_args()

    old_stream = RelevanceFinanceNewsStream(args.data_dir)
    new_stream = SessionRelevanceFinanceNewsStream(args.data_dir)
    days = contact_tail_days(new_stream)

    cells = {
        "A_old_stream_sensory": (
            old_stream,
            lambda: SensoryGatedCellular(**CELL_PARAMS),
        ),
        "B_session_stream_sensory": (
            new_stream,
            lambda: SensoryGatedCellular(**CELL_PARAMS),
        ),
        "C_session_no_sign_reversal": (
            new_stream,
            lambda: CleanEvidenceCellular(
                preserve_sign=True,
                use_delayed_trust=False,
                **CELL_PARAMS,
            ),
        ),
        "D_session_clean_evidence": (
            new_stream,
            lambda: CleanEvidenceCellular(
                preserve_sign=True,
                use_delayed_trust=True,
                **CELL_PARAMS,
            ),
        ),
    }

    scored = {}
    markers = {}
    for name, (stream, factory) in cells.items():
        score_days_set = (
            contact_tail_days(stream) if stream is old_stream else days
        )
        scored[name] = score_days(stream, factory(), score_days_set)
        markers[name] = {
            **sign_reversal_rate(stream, factory),
            **flip_confidence_markers(stream, factory, score_days_set),
        }

    baseline = scored["B_session_stream_sensory"]
    comparisons = {}
    for name in (
        "C_session_no_sign_reversal",
        "D_session_clean_evidence",
    ):
        comparisons[name] = {
            "accuracy": paired_delta(
                baseline["correct"], scored[name]["correct"], n_boot=args.n_boot
            ),
            "flip_accuracy": paired_delta(
                baseline["correct"],
                scored[name]["correct"],
                baseline["flip"],
                n_boot=args.n_boot,
            ),
        }

    payload = {
        "protocol": "finance_clean_evidence_development_v1",
        "note": (
            "Contact-tail scores only. Old holdout is not used for design. "
            "Cell A uses the legacy calendar stream; B–D use session cutoffs."
        ),
        "legacy_stream_markers": {
            "n_events": old_stream.summary()["n_events"],
            "duplicate_symbol_session_events": int(
                len([(e.symbol, e.day) for e in old_stream.events])
                - len({(e.symbol, e.day) for e in old_stream.events})
            ),
            "events_without_relevant_reports": old_stream.events_without_relevant_reports,
            "relevant_article_fraction": old_stream.relevant_articles
            / max(1, old_stream.total_articles),
        },
        "session_stream": new_stream.summary(),
        "cells": {name: concise(result) for name, result in scored.items()},
        "markers": markers,
        "paired_vs_session_sensory": comparisons,
        "passes_internal_marker_gates": {
            "no_duplicate_sessions": new_stream.purity_markers()[
                "duplicate_symbol_session_events"
            ]
            == 0,
            "flips_are_adjacent_sessions": new_stream.purity_markers()[
                "flip_events_adjacent_session"
            ]
            == new_stream.purity_markers()["flip_events"],
            "clean_model_zero_sign_reversal": markers["D_session_clean_evidence"][
                "sign_reversal_rate"
            ]
            == 0.0,
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, allow_nan=True))

    print("SESSION STREAM", json.dumps(new_stream.summary(), indent=2))
    for name, result in scored.items():
        mark = markers[name]
        print(
            f"{name:32s} acc={result['accuracy']:.4f} flip={result['flip_accuracy']:.4f} "
            f"up={result['pred_up_rate']:.3f} act={result['avg_activated']:.2f} "
            f"sign_rev={mark['sign_reversal_rate']:.3f} "
            f"flip_conf_wrong={mark['flip_confidence_when_wrong']:.3f}"
        )
    for name, comps in comparisons.items():
        for metric, result in comps.items():
            print(
                f"{name}/{metric}: Δ={result['delta']:+.4f} "
                f"[{result['lo']:+.4f}, {result['hi']:+.4f}] p={result['p']:.3f}"
            )
    print(
        "marker_gates",
        json.dumps(payload["passes_internal_marker_gates"], indent=2),
    )


if __name__ == "__main__":
    main()
