"""Deterministic delayed-feedback source-aggregation worlds for DBSA-v1."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

WORLD_NAMES = (
    "independent_stable",
    "correlated_stable",
    "abrupt_drift",
    "recurring_crossover",
    "adversarial_switch",
    "bursty_missing",
)
N_ITEMS = 24
N_SOURCES = 12
N_BLOCKS = 4
SOURCES_PER_BLOCK = N_SOURCES // N_BLOCKS
DELAY = 14


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


def _phase(world: str, t: int, rounds: int) -> int:
    if world in {"abrupt_drift", "adversarial_switch"}:
        return int(t >= rounds // 2)
    if world == "recurring_crossover":
        return (t // max(1, rounds // 4)) % 2
    return 0


def _source_accuracy(world: str, source: int, phase: int) -> float:
    block = source // SOURCES_PER_BLOCK
    if world in {"independent_stable", "correlated_stable", "bursty_missing"}:
        return 0.76
    if world == "abrupt_drift":
        is_good = (source < N_SOURCES // 2) if phase == 0 else (source >= N_SOURCES // 2)
        return 0.90 if is_good else 0.56
    if world == "recurring_crossover":
        return 0.89 if block % 2 == phase else 0.55
    if world == "adversarial_switch":
        if block == 0:
            return 0.87 if phase == 0 else 0.14
        return 0.76
    raise ValueError(f"unknown world: {world}")


def _copy_probability(world: str) -> float:
    return 0.92 if world == "correlated_stable" else 0.15


def _available(world: str, source: int, t: int, rng: np.random.Generator) -> bool:
    if world != "bursty_missing":
        return True
    # Each 100-event segment hides one source block 80% of the time.
    burst_block = (t // 100) % N_BLOCKS
    if source // SOURCES_PER_BLOCK == burst_block:
        return bool(rng.random() >= 0.80)
    return bool(rng.random() >= 0.04)


def _shift_age(world: str, t: int, rounds: int) -> int | None:
    if world in {"abrupt_drift", "adversarial_switch"}:
        switch_t = rounds // 2
        return t - switch_t if t >= switch_t else None
    if world == "recurring_crossover":
        block = max(1, rounds // 4)
        return t % block if t >= block else None
    return None


def generate(
    world: str,
    seed: int,
    *,
    rounds: int,
    delay: int = DELAY,
) -> list[Event]:
    """Create a hidden-state world, returning only ordinary report packets."""

    if world not in WORLD_NAMES:
        raise ValueError(f"unknown world: {world}")
    if rounds <= delay:
        raise ValueError("rounds must exceed feedback delay")

    rng = np.random.default_rng(seed)
    truth_state = rng.integers(0, 2, size=N_ITEMS, dtype=int)
    previous: dict[tuple[int, int], int] = {}
    events: list[Event] = []
    copy_probability = _copy_probability(world)

    for t in range(rounds):
        item = int(rng.integers(0, N_ITEMS))
        key = (item, 0)
        # Persistence belongs to the data-generating truth, not any method.
        if rng.random() < 0.23:
            truth_state[item] = 1 - truth_state[item]
        truth = int(truth_state[item])
        phase = _phase(world, t, rounds)

        block_votes: dict[int, int] = {}
        reports: list[tuple[int, int, int]] = []
        for source in range(N_SOURCES):
            if not _available(world, source, t, rng):
                continue
            block = source // SOURCES_PER_BLOCK
            accuracy = _source_accuracy(world, source, phase)
            if block not in block_votes:
                block_votes[block] = truth if rng.random() < accuracy else 1 - truth
            if rng.random() < copy_probability:
                vote = block_votes[block]
            else:
                vote = truth if rng.random() < accuracy else 1 - truth
            reports.append((source, 0, int(vote)))

        # Never hand an empty packet to a method; a source has to exist.
        if not reports:
            fallback = int(rng.integers(0, N_SOURCES))
            reports.append((fallback, 0, truth if rng.random() < 0.76 else 1 - truth))

        events.append(
            Event(
                t=t,
                key=key,
                reports=reports,
                truth=truth,
                prev_truth=previous.get(key),
                due_t=t + delay,
                world=world,
                shift_age=_shift_age(world, t, rounds),
            )
        )
        previous[key] = truth

    return events
