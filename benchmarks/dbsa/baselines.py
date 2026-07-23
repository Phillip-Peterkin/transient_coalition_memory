"""Causal delayed-label source-aggregation baselines for DBSA-v1."""

from __future__ import annotations

import math
from collections import defaultdict

EPS = 1e-9


def _clip_probability(value: float) -> float:
    return min(1.0 - EPS, max(EPS, float(value)))


def _sigmoid(log_odds: float) -> float:
    log_odds = max(-35.0, min(35.0, log_odds))
    return 1.0 / (1.0 + math.exp(-log_odds))


class _Baseline:
    """Shared accounting: all baselines inspect and score every report."""

    name = "baseline"

    def __init__(self) -> None:
        self.inspected = 0
        self.scored = 0
        self.updates = 0

    def _trace(self, probability: float, reports) -> tuple[float, dict]:
        self.inspected += len(reports)
        self.scored += len(reports)
        return _clip_probability(probability), {"used": len(reports)}

    def stats(self) -> dict:
        return {
            "reports_inspected": self.inspected,
            "reports_scored": self.scored,
            "updates": self.updates,
            "memory_states": 0,
        }


class Persistence(_Baseline):
    """Causal per-item last-truth predictor."""

    name = "persistence"

    def __init__(self) -> None:
        super().__init__()
        self.last_truth: dict[tuple, int] = {}

    def predict(self, key, reports, t):
        return self._trace(0.5 if key not in self.last_truth else self.last_truth[key], reports)

    def feedback(self, event) -> None:
        self.last_truth[event["key"]] = int(event["truth"])
        self.updates += 1

    def stats(self) -> dict:
        return {**super().stats(), "memory_states": len(self.last_truth)}


class Majority(_Baseline):
    """Equal-weight vote aggregation with no source-learning."""

    name = "majority"

    def predict(self, key, reports, t):
        probability = sum(int(vote) for _, _, vote in reports) / max(1, len(reports))
        return self._trace(probability, reports)

    def feedback(self, event) -> None:
        self.updates += 1


class FixedShareHedge(_Baseline):
    """Sleeping-expert Fixed-Share Hedge updated only at delayed label arrival."""

    name = "fixed_share_hedge"

    def __init__(self, *, eta: float = 0.90, share: float = 0.03) -> None:
        super().__init__()
        self.eta = float(eta)
        self.share = float(share)
        self.weights: dict[int, float] = {}

    def _ensure(self, source: int) -> None:
        if source not in self.weights:
            self.weights[source] = 1.0

    def predict(self, key, reports, t):
        for source, _, _ in reports:
            self._ensure(int(source))
        denom = sum(self.weights[int(source)] for source, _, _ in reports)
        probability = (
            sum(self.weights[int(source)] * int(vote) for source, _, vote in reports)
            / max(EPS, denom)
        )
        return self._trace(probability, reports)

    def feedback(self, event) -> None:
        truth = int(event["truth"])
        for source, _, vote in event["reports"]:
            source = int(source)
            self._ensure(source)
            loss = float(int(vote) != truth)
            self.weights[source] *= math.exp(-self.eta * loss)
        total = sum(self.weights.values())
        count = max(1, len(self.weights))
        for source, weight in tuple(self.weights.items()):
            normalized = weight / max(EPS, total)
            self.weights[source] = (1.0 - self.share) * normalized + self.share / count
        self.updates += len(event["reports"])

    def stats(self) -> dict:
        return {**super().stats(), "memory_states": len(self.weights)}


class FadingSourceBayes(_Baseline):
    """Past-only Beta reliability filter; optional agreement dependence shrink."""

    name = "fading_source_bayes"

    def __init__(self, *, discount_agreement: bool = False, forget: float = 0.985) -> None:
        super().__init__()
        self.discount_agreement = bool(discount_agreement)
        self.forget = float(forget)
        self.correct = defaultdict(lambda: 1.0)
        self.wrong = defaultdict(lambda: 1.0)

    def predict(self, key, reports, t):
        del key, t
        deltas = []
        for source, _, vote in reports:
            source = int(source)
            reliability = self.correct[source] / (self.correct[source] + self.wrong[source])
            reliability = min(0.995, max(0.005, reliability))
            signed = 1.0 if int(vote) else -1.0
            deltas.append(signed * math.log(reliability / (1.0 - reliability)))

        scale = 1.0
        if self.discount_agreement and len(reports) > 1:
            votes = [int(vote) for _, _, vote in reports]
            agreeing_pairs = sum(
                votes[left] == votes[right]
                for left in range(len(votes))
                for right in range(left + 1, len(votes))
            )
            pair_count = len(votes) * (len(votes) - 1) / 2
            agreement = agreeing_pairs / pair_count
            effective_count = 1.0 + (len(votes) - 1) * (1.0 - agreement)
            scale = effective_count / len(votes)

        return self._trace(_sigmoid(scale * sum(deltas)), reports)

    def feedback(self, event) -> None:
        truth = int(event["truth"])
        for source, _, vote in event["reports"]:
            source = int(source)
            self.correct[source] *= self.forget
            self.wrong[source] *= self.forget
            if int(vote) == truth:
                self.correct[source] += 1.0
            else:
                self.wrong[source] += 1.0
        self.updates += len(event["reports"])

    def stats(self) -> dict:
        return {**super().stats(), "memory_states": 2 * len(self.correct)}


class AgreementDiscountedBayes(FadingSourceBayes):
    """Causal source Bayes with an observable agreement-only shrinkage."""

    name = "agreement_discounted_bayes"

    def __init__(self) -> None:
        super().__init__(discount_agreement=True)
