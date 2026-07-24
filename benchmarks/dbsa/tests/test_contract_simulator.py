"""Smoke tests for the declarative DBSA contract simulator."""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from contract_simulator import WORLD_NAMES, generate, load_worlds


def test_all_six_worlds_load_from_contract():
    worlds = load_worlds()
    assert set(worlds) == set(WORLD_NAMES)
    for name, world in worlds.items():
        assert world["name"] == name
        assert world["n_items"] == 24
        assert world["n_sources"] == 12
        assert len(world["source_blocks"]) == 4
        assert all(len(block) == 3 for block in world["source_blocks"])
        assert world["feedback_delay"]["type"] == "fixed"
        assert world["feedback_delay"]["events"] == 14


def test_due_t_respects_declared_fixed_delay():
    worlds = load_worlds()
    for world_name in WORLD_NAMES:
        events = generate(world_name, seed=3, rounds=40)
        declared = worlds[world_name]["feedback_delay"]["events"]
        assert all(event.due_t == event.t + declared for event in events)


def test_copy_graph_increases_within_block_agreement():
    def block_agreement(events, block):
        agree = total = 0
        for event in events:
            block_reports = [vote for source, _, vote in event.reports if source in block]
            if len(block_reports) < 2:
                continue
            leader_vote = next(vote for source, _, vote in event.reports if source == block[0])
            for vote in block_reports[1:]:
                total += 1
                agree += int(vote == leader_vote)
        return agree / total if total else 0.0

    worlds = load_worlds()
    block = worlds["independent_stable"]["source_blocks"][0]
    independent = generate("independent_stable", seed=17, rounds=500)
    correlated = generate("correlated_stable", seed=17, rounds=500)

    independent_agreement = block_agreement(independent, block)
    correlated_agreement = block_agreement(correlated, block)
    assert correlated_agreement > independent_agreement + 0.25


def test_availability_bursts_reduce_exposed_sources():
    worlds = load_worlds()
    world = worlds["bursty_missing"]
    events = generate("bursty_missing", seed=29, rounds=800)

    burst = world["availability"]["bursts"][0]
    start = int(burst["start_event"])
    end = int(burst["end_event"])
    burst_sources = set(burst["source_ids"])

    burst_presence = []
    outside_presence = []
    for event in events:
        present = {source for source, _, _ in event.reports}
        rate = len(present & burst_sources) / len(burst_sources)
        if start <= event.t <= end:
            burst_presence.append(rate)
        elif event.t >= 120:
            outside_presence.append(rate)

    assert burst_presence
    assert outside_presence
    assert sum(burst_presence) / len(burst_presence) < 0.35
    assert sum(outside_presence) / len(outside_presence) > 0.85


def test_shift_age_tracks_accuracy_schedule_boundaries():
    events = generate("abrupt_drift", seed=5, rounds=450)
    pre_switch = [event for event in events if event.t < 400]
    post_switch = [event for event in events if event.t >= 400]

    assert all(event.shift_age is None for event in pre_switch)
    assert all(event.shift_age == event.t - 400 for event in post_switch)


def test_no_tcm_imports_in_contract_simulator_module():
    contract_path = ROOT / "contract_simulator.py"
    source = contract_path.read_text(encoding="utf-8")
    assert "tcm" not in source
    assert "import tcm" not in source
