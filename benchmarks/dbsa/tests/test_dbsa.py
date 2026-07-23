"""DBSA-v1 causal protocol checks."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parents[2] / "src"))

from baselines import FadingSourceBayes
from evaluate import run_model
from simulator import DELAY, WORLD_NAMES, generate


def test_all_preregistered_worlds_generate_delayed_named_reports():
    for world in WORLD_NAMES:
        events = generate(world, seed=7, rounds=80)
        assert len(events) == 80
        assert all(event.due_t == event.t + DELAY for event in events)
        assert all(event.reports for event in events)
        assert all(len(report) == 3 for event in events for report in event.reports)


def test_feedback_is_not_available_before_its_declared_delay():
    events = generate("independent_stable", seed=11, rounds=DELAY + 1)[:DELAY]
    model = FadingSourceBayes()
    result = run_model(events, model)
    assert result["model_stats"]["updates"] == 0
    assert result["n"] == DELAY


def test_same_packets_are_fully_inspected_by_causal_baseline():
    events = generate("correlated_stable", seed=13, rounds=60)
    result = run_model(events, FadingSourceBayes())
    mean_reports = sum(len(event.reports) for event in events) / len(events)
    assert result["avg_reports_inspected"] == mean_reports
    assert result["avg_downstream_activated"] == mean_reports
