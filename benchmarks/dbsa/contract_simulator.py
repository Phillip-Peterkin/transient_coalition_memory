"""Declarative delayed-feedback source-aggregation simulator for DBSA-v1."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

CONTRACT_PATH = Path(__file__).resolve().parent / "contract" / "v1_worlds.json"

WORLD_NAMES = (
    "independent_stable",
    "correlated_stable",
    "abrupt_drift",
    "recurring_crossover",
    "adversarial_switch",
    "bursty_missing",
)


@dataclass(frozen=True)
class Event:
    """One causal decision packet; truth is released only at ``due_t``."""

    t: int
    key: tuple[int, int]
    reports: list[tuple[int, int, int]]
    truth: int
    prev_truth: int | None
    due_t: int
    world: str
    shift_age: int | None


def _seed_from(world: dict[str, Any], seed: int) -> int:
    salt = world["seed_salt"]
    payload = f"{seed}:{salt}".encode()
    return int.from_bytes(payload, "little") % (2**32)


def load_contract(path: Path | str | None = None) -> dict[str, Any]:
    contract_path = Path(path) if path is not None else CONTRACT_PATH
    with contract_path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_worlds(path: Path | str | None = None) -> dict[str, dict[str, Any]]:
    contract = load_contract(path)
    worlds = {world["name"]: world for world in contract["worlds"]}
    missing = [name for name in WORLD_NAMES if name not in worlds]
    if missing:
        raise ValueError(f"contract missing worlds: {missing}")
    return worlds


def _schedule_segments(schedule: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(schedule, key=lambda segment: segment["start_event"])


def _active_segment(schedule: list[dict[str, Any]], t: int) -> dict[str, Any]:
    segments = _schedule_segments(schedule)
    active = segments[0]
    for segment in segments:
        if t < segment["start_event"]:
            break
        if segment["end_event"] is None or t <= segment["end_event"]:
            active = segment
        elif t >= segment["start_event"]:
            active = segment
    return active


def _source_accuracies(segment: dict[str, Any]) -> dict[int, float]:
    return {int(source): float(probability) for source, probability in segment["source_accuracies"].items()}


def _shift_boundaries(schedule: list[dict[str, Any]]) -> list[int]:
    segments = _schedule_segments(schedule)
    boundaries: list[int] = []
    previous: dict[int, float] | None = None
    for segment in segments:
        accuracies = _source_accuracies(segment)
        if previous is not None and accuracies != previous:
            boundaries.append(int(segment["start_event"]))
        previous = accuracies
    return boundaries


def _shift_age(schedule: list[dict[str, Any]], t: int) -> int | None:
    boundaries = _shift_boundaries(schedule)
    applicable = [boundary for boundary in boundaries if boundary <= t]
    if not applicable:
        return None
    return t - max(applicable)


def _sample_delay(delay_spec: dict[str, Any], rng: np.random.Generator) -> int:
    delay_type = delay_spec["type"]
    if delay_type == "fixed":
        return int(delay_spec["events"])
    if delay_type == "geometric":
        mean = float(delay_spec["mean"])
        minimum = int(delay_spec["min"])
        maximum = int(delay_spec["max"])
        sampled = int(rng.geometric(1.0 / mean))
        return max(minimum, min(maximum, sampled))
    raise ValueError(f"unknown feedback_delay type: {delay_type}")


def _availability_probability(world: dict[str, Any], source: int, t: int) -> float:
    availability = world["availability"]
    probability = float(availability["default_p"])
    for burst in availability.get("bursts", []):
        if int(burst["start_event"]) <= t <= int(burst["end_event"]):
            if source in burst["source_ids"]:
                probability = float(burst["p"])
    return probability


def _incoming_copy_edges(world: dict[str, Any]) -> dict[int, list[tuple[int, float]]]:
    incoming: dict[int, list[tuple[int, float]]] = {source: [] for source in range(world["n_sources"])}
    for edge in world["copy_graph"]:
        incoming[int(edge["to"])].append((int(edge["from"]), float(edge["p"])))
    return incoming


def _fresh_vote(truth: int, accuracy: float, rng: np.random.Generator) -> int:
    return int(truth if rng.random() < accuracy else 1 - truth)


def _source_vote(
    source: int,
    truth: int,
    accuracy: float,
    incoming: dict[int, list[tuple[int, float]]],
    votes: dict[int, int],
    rng: np.random.Generator,
) -> int:
    for parent, probability in incoming[source]:
        if parent in votes and rng.random() < probability:
            return votes[parent]
    return _fresh_vote(truth, accuracy, rng)


def generate(
    world_name: str,
    seed: int,
    *,
    rounds: int,
    contract_path: Path | str | None = None,
) -> list[Event]:
    """Generate events by interpreting a declarative world contract."""

    worlds = load_worlds(contract_path)
    if world_name not in worlds:
        raise ValueError(f"unknown world: {world_name}")

    world = worlds[world_name]
    delay_spec = world["feedback_delay"]
    minimum_delay = (
        int(delay_spec["events"])
        if delay_spec["type"] == "fixed"
        else int(delay_spec["min"])
    )
    if rounds <= minimum_delay:
        raise ValueError("rounds must exceed feedback delay")

    rng = np.random.default_rng(_seed_from(world, seed))
    n_items = int(world["n_items"])
    n_sources = int(world["n_sources"])
    truth_flip_rate = float(world["truth_flip_rate"])
    schedule = world["accuracy_schedule"]
    incoming = _incoming_copy_edges(world)

    truth_state = rng.integers(0, 2, size=n_items, dtype=int)
    previous: dict[tuple[int, int], int] = {}
    events: list[Event] = []

    for t in range(rounds):
        item = int(rng.integers(0, n_items))
        key = (item, 0)
        if rng.random() < truth_flip_rate:
            truth_state[item] = 1 - truth_state[item]
        truth = int(truth_state[item])

        segment = _active_segment(schedule, t)
        accuracies = _source_accuracies(segment)

        votes: dict[int, int] = {}
        reports: list[tuple[int, int, int]] = []
        for source in range(n_sources):
            if rng.random() >= _availability_probability(world, source, t):
                continue
            vote = _source_vote(source, truth, accuracies[source], incoming, votes, rng)
            votes[source] = vote
            reports.append((source, 0, vote))

        if not reports:
            fallback = int(rng.integers(0, n_sources))
            fallback_accuracy = accuracies.get(fallback, 0.76)
            reports.append((fallback, 0, _fresh_vote(truth, fallback_accuracy, rng)))

        due_t = t + _sample_delay(delay_spec, rng)
        events.append(
            Event(
                t=t,
                key=key,
                reports=reports,
                truth=truth,
                prev_truth=previous.get(key),
                due_t=due_t,
                world=world_name,
                shift_age=_shift_age(schedule, t),
            )
        )
        previous[key] = truth

    return events
