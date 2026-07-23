"""DBSA-v1 causal protocol checks against the contract simulator."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(REPO / "src"))

from baselines import AdaHedge, FadingSourceBayes, FixedShareHedge
from contract_simulator import WORLD_NAMES, generate
from evaluate import BRIER_NONINFERIORITY_DELTA, run_model


def test_all_preregistered_worlds_generate_delayed_named_reports():
    for world in WORLD_NAMES:
        events = generate(world, seed=7, rounds=80)
        assert len(events) == 80
        assert all(event.due_t == event.t + 14 for event in events)
        assert all(event.reports for event in events)
        assert all(len(report) == 3 for event in events for report in event.reports)


def test_feedback_is_not_available_before_its_declared_delay():
    events = generate("independent_stable", seed=11, rounds=15)[:14]
    model = FadingSourceBayes()
    result = run_model(events, model)
    assert result["model_stats"]["updates"] == 0
    assert result["n"] == 14


def test_fixed_share_updates_only_on_queue_release():
    events = generate("independent_stable", seed=11, rounds=15)[:14]
    model = FixedShareHedge()
    result = run_model(events, model)
    assert result["model_stats"]["updates"] == 0


def test_ada_hedge_updates_only_on_queue_release():
    events = generate("independent_stable", seed=11, rounds=15)[:14]
    model = AdaHedge()
    result = run_model(events, model)
    assert result["model_stats"]["updates"] == 0


def test_ada_hedge_learns_after_delay_release():
    events = generate("independent_stable", seed=11, rounds=40)
    model = AdaHedge()
    result = run_model(events, model)
    assert result["model_stats"]["updates"] > 0
    assert result["model_stats"]["ada_hedge_alpha"] >= 0.0


def test_noninferiority_delta_is_locked():
    assert BRIER_NONINFERIORITY_DELTA == 0.005


def test_same_packets_are_fully_inspected_by_causal_baseline():
    events = generate("correlated_stable", seed=13, rounds=60)
    result = run_model(events, FadingSourceBayes())
    mean_reports = sum(len(event.reports) for event in events) / len(events)
    assert result["avg_reports_inspected"] == mean_reports
    assert result["avg_downstream_activated"] == mean_reports
