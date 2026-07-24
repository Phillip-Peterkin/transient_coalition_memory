"""Causal delayed-label source-aggregation baselines for DBSA-v1."""

from __future__ import annotations

import math
from collections import defaultdict

import numpy as np

EPS = 1e-9

# Locked PWDR knobs (CONSENSUS_MISSING_OBJECT.md) — declared before scoring.
PWDR_RIDGE = 0.05
PWDR_COV_FORGET = 0.99
PWDR_RESIDUAL_LR = 0.05
PWDR_RESIDUAL_L2 = 0.01
PWDR_RESIDUAL_CLIP = 0.35
PWDR_MIN_UPDATES = 20


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
    """Sleeping-expert Fixed-Share Hedge.

    Textbook Fixed Share assumes immediate losses. Under DBSA delays this row
    updates **only when the shared evaluator queue releases the label**
    (`due_t`). It never sees same-step oracle losses.
    """

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


class AdaHedge(_Baseline):
    """Sleeping-expert AdaHedge with adaptive learning rate.

    Textbook AdaHedge assumes immediate losses. Under DBSA delays this row
    updates **only when the shared evaluator queue releases the label**
    (`due_t`). It never sees same-step oracle losses.

    Mixability-gap adaptation follows the standard cumulative-gap schedule:
    ``η = sqrt((ln K) / α)`` with ``α`` the cumulative mixability gap over
    awake experts on each released packet.
    """

    name = "ada_hedge"

    def __init__(self) -> None:
        super().__init__()
        self.cumulative_loss: dict[int, float] = {}
        self.alpha = 0.0
        self.last_eta = 0.0

    def _ensure(self, source: int) -> None:
        if source not in self.cumulative_loss:
            self.cumulative_loss[source] = 0.0

    def _eta(self, awake_count: int) -> float:
        if awake_count <= 1:
            return 0.0
        if self.alpha <= EPS:
            return math.sqrt(math.log(awake_count) / EPS)
        return math.sqrt(math.log(awake_count) / self.alpha)

    def _posterior(self, sources: list[int]) -> dict[int, float]:
        eta = self._eta(len(sources))
        self.last_eta = eta
        if eta <= EPS or len(sources) == 1:
            mass = 1.0 / len(sources)
            return {source: mass for source in sources}
        # Stable softmax: shift by min cumulative loss to avoid underflow.
        min_loss = min(self.cumulative_loss[source] for source in sources)
        unnormalized = {
            source: math.exp(-eta * (self.cumulative_loss[source] - min_loss))
            for source in sources
        }
        total = sum(unnormalized.values())
        if total <= EPS:
            winners = [
                source
                for source in sources
                if self.cumulative_loss[source] <= min_loss + EPS
            ]
            mass = 1.0 / len(winners)
            return {source: (mass if source in winners else 0.0) for source in sources}
        return {source: weight / total for source, weight in unnormalized.items()}

    def predict(self, key, reports, t):
        del key, t
        sources = []
        votes = {}
        for source, _, vote in reports:
            source = int(source)
            self._ensure(source)
            sources.append(source)
            votes[source] = int(vote)
        posterior = self._posterior(sources)
        probability = sum(posterior[source] * votes[source] for source in sources)
        return self._trace(probability, reports)

    def feedback(self, event) -> None:
        truth = int(event["truth"])
        sources = []
        losses = {}
        for source, _, vote in event["reports"]:
            source = int(source)
            self._ensure(source)
            sources.append(source)
            losses[source] = float(int(vote) != truth)
        if not sources:
            return
        posterior = self._posterior(sources)
        eta = self.last_eta
        expected_loss = sum(posterior[source] * losses[source] for source in sources)
        if eta <= EPS:
            mix_loss = expected_loss
        else:
            # Stable mix loss: -η^{-1} log ∑ p_i e^{-η ℓ_i}
            min_awake_loss = min(losses[source] for source in sources)
            mix_mass = sum(
                posterior[source] * math.exp(-eta * (losses[source] - min_awake_loss))
                for source in sources
            )
            mix_loss = min_awake_loss - math.log(max(EPS, mix_mass)) / eta
        self.alpha += max(0.0, expected_loss - mix_loss)
        for source in sources:
            self.cumulative_loss[source] += losses[source]
        self.updates += len(sources)

    def stats(self) -> dict:
        return {
            **super().stats(),
            "memory_states": len(self.cumulative_loss),
            "ada_hedge_alpha": self.alpha,
            "ada_hedge_eta": self.last_eta,
        }


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


class PrecisionWhitenedDelayedResidual(_Baseline):
    """PWDR — Precision-Whitened Delayed Residual (room consensus object).

    1. Estimate source covariance ``C`` from **delayed error** co-occurrence
       (vote − truth), never from forecast agreement.
    2. Base belief ``m`` from precision-whitened logits ``Λ ≈ C⁻¹`` — raw
       majority is not the attractor.
    3. Online residual ``r`` predicts delayed ``(y − m)`` from whitened
       disagreement features; emit ``Π(m + r)``.

    Forbidden by construction: Christmas-bow blend toward unwhitened majority.
    Knobs are module-level constants locked before scoring.
    """

    name = "pwdr"

    def __init__(
        self,
        *,
        ridge: float = PWDR_RIDGE,
        cov_forget: float = PWDR_COV_FORGET,
        residual_lr: float = PWDR_RESIDUAL_LR,
        residual_l2: float = PWDR_RESIDUAL_L2,
        residual_clip: float = PWDR_RESIDUAL_CLIP,
        min_updates: int = PWDR_MIN_UPDATES,
    ) -> None:
        super().__init__()
        self.ridge = float(ridge)
        self.cov_forget = float(cov_forget)
        self.residual_lr = float(residual_lr)
        self.residual_l2 = float(residual_l2)
        self.residual_clip = float(residual_clip)
        self.min_updates = int(min_updates)
        self._index: dict[int, int] = {}
        self._S = np.zeros((0, 0), dtype=float)
        self._cov_updates = 0
        # Features: bias, disagree_rate, whitened_std, neff_ratio, m_minus_majority
        self._residual_w = np.zeros(5, dtype=float)
        self._last_lambda1_frac = 0.0
        self._last_neff = 0.0

    def _ensure(self, sources: list[int]) -> None:
        for source in sources:
            if source in self._index:
                continue
            new_i = len(self._index)
            self._index[source] = new_i
            n = new_i + 1
            grown = np.zeros((n, n), dtype=float)
            if self._S.size:
                grown[:-1, :-1] = self._S
            self._S = grown

    def _precision_submatrix(self, idxs: list[int]) -> np.ndarray:
        """Regularized precision on the awake source set."""
        k = len(idxs)
        if k == 0:
            return np.zeros((0, 0), dtype=float)
        if self._cov_updates < self.min_updates or self._S.shape[0] == 0:
            return np.eye(k, dtype=float)
        sub = self._S[np.ix_(idxs, idxs)] / max(1, self._cov_updates)
        # Stabilize: ridge on the empirical second-moment matrix.
        cov = sub + self.ridge * np.eye(k, dtype=float)
        try:
            return np.linalg.inv(cov)
        except np.linalg.LinAlgError:
            return np.eye(k, dtype=float)

    @staticmethod
    def _lambda1_frac(cov: np.ndarray) -> float:
        if cov.size == 0:
            return 0.0
        try:
            eigenvalues = np.linalg.eigvalsh(cov)
        except np.linalg.LinAlgError:
            return 0.0
        total = float(np.sum(np.maximum(eigenvalues, 0.0)))
        if total <= EPS:
            return 0.0
        return float(max(eigenvalues) / total)

    def _whitened_base(
        self, reports
    ) -> tuple[float, float, float, float, np.ndarray, np.ndarray]:
        sources = [int(source) for source, _, _ in reports]
        votes = np.asarray([int(vote) for _, _, vote in reports], dtype=float)
        self._ensure(sources)
        idxs = [self._index[source] for source in sources]
        lam = self._precision_submatrix(idxs)
        ell = 2.0 * votes - 1.0
        ones = np.ones(len(votes), dtype=float)
        neff = float(ones @ lam @ ones)
        # Whitened pool: precision-weighted logit mass.
        logit_mass = float(ones @ (lam @ ell))
        # Scale so identity-Λ cold start stays O(1) in logit space.
        scale = 1.0 / max(1.0, math.sqrt(max(neff, 1.0)))
        m = _sigmoid(scale * logit_mass)
        majority = float(votes.mean()) if len(votes) else 0.5
        if self._cov_updates >= self.min_updates and len(idxs) >= 2:
            cov = self._S[np.ix_(idxs, idxs)] / max(1, self._cov_updates)
            cov = cov + self.ridge * np.eye(len(idxs), dtype=float)
            lambda1_frac = self._lambda1_frac(cov)
        else:
            lambda1_frac = 0.0
        whitened = lam @ ell
        return m, majority, neff, lambda1_frac, whitened, votes

    def _features(
        self, m: float, majority: float, neff: float, whitened: np.ndarray, votes: np.ndarray
    ) -> np.ndarray:
        k = max(1, len(votes))
        hard = 1.0 if m >= 0.5 else 0.0
        disagree = float(np.mean(votes != hard)) if len(votes) else 0.0
        whitened_std = float(np.std(whitened)) if len(whitened) > 1 else 0.0
        neff_ratio = float(neff / k)
        return np.asarray(
            [1.0, disagree, whitened_std, neff_ratio, m - majority], dtype=float
        )

    def predict(self, key, reports, t):
        del key, t
        if not reports:
            probability, trace = self._trace(0.5, reports)
            trace.update(
                {
                    "pwdr_m": 0.5,
                    "pwdr_r": 0.0,
                    "pwdr_phi": [1.0, 0.0, 0.0, 0.0, 0.0],
                    "pwdr_neff": 0.0,
                    "pwdr_lambda1_frac": 0.0,
                    "pwdr_majority": 0.5,
                    "christmas_bow_forbidden": True,
                }
            )
            return probability, trace

        m, majority, neff, lambda1_frac, whitened, votes = self._whitened_base(reports)
        phi = self._features(m, majority, neff, whitened, votes)
        r = float(self._residual_w @ phi)
        r = max(-self.residual_clip, min(self.residual_clip, r))
        # Emit Π(m + r). Never blend toward unwhitened majority.
        probability = _clip_probability(m + r)
        self._last_neff = neff
        self._last_lambda1_frac = lambda1_frac
        probability, trace = self._trace(probability, reports)
        trace.update(
            {
                "pwdr_m": float(m),
                "pwdr_r": float(r),
                "pwdr_phi": [float(x) for x in phi],
                "pwdr_neff": float(neff),
                "pwdr_lambda1_frac": float(lambda1_frac),
                "pwdr_majority": float(majority),
                "christmas_bow_forbidden": True,
            }
        )
        return probability, trace

    def feedback(self, event) -> None:
        truth = int(event["truth"])
        reports = event["reports"]
        if not reports:
            return
        sources = [int(source) for source, _, _ in reports]
        self._ensure(sources)
        idxs = [self._index[source] for source in sources]
        # Signed correctness ∈ {+1, −1}. Clones that err together get positive
        # co-occurrence; anti-correlated specialists go negative.
        # (vote−truth cannot express negative cross-terms on binary labels.)
        # Opinion agreement never enters C — only delayed label residuals.
        errors = np.asarray(
            [1.0 if int(vote) == truth else -1.0 for _, _, vote in reports],
            dtype=float,
        )
        self._S *= self.cov_forget
        self._S[np.ix_(idxs, idxs)] += np.outer(errors, errors)
        self._cov_updates += 1

        trace = event.get("trace") or {}
        phi = np.asarray(trace.get("pwdr_phi"), dtype=float)
        m = trace.get("pwdr_m")
        if phi.shape == self._residual_w.shape and m is not None:
            target = float(truth) - float(m)  # delayed residual of whitened base
            pred_r = float(self._residual_w @ phi)
            grad = (pred_r - target) * phi + self.residual_l2 * self._residual_w
            self._residual_w -= self.residual_lr * grad
        self.updates += len(reports)

    def stats(self) -> dict:
        return {
            **super().stats(),
            "memory_states": len(self._index),
            "pwdr_cov_updates": self._cov_updates,
            "pwdr_last_neff": self._last_neff,
            "pwdr_last_lambda1_frac": self._last_lambda1_frac,
            "pwdr_residual_w": [float(x) for x in self._residual_w],
            "pwdr_ridge": self.ridge,
            "pwdr_min_updates": self.min_updates,
        }
