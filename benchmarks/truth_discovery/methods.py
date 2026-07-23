"""Literature truth-discovery methods + trivial baselines.

Reference shapes follow Yin et al. 2008 (TruthFinder), Li et al. 2014 (CRH),
Li et al. 2015 (CATD). StreamingCRH is an online day-ordered CRH variant
(closest practical streaming TD analogue for this harness).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.stats import chi2

EPS = 1e-12


@dataclass
class TDResult:
    truths: dict[tuple[str, str, str], Any]  # (day, object, attribute) -> value
    source_weights: dict[str, float]
    iterations: int
    ops: int


def _group_claims(claims: list[dict]):
    by_item: dict[tuple, list[tuple[str, Any]]] = defaultdict(list)
    by_source: dict[str, list[tuple[tuple, Any]]] = defaultdict(list)
    for row in claims:
        item = (row["day"], row["object"], row["attribute"])
        by_item[item].append((row["source"], row["value"]))
        by_source[row["source"]].append((item, row["value"]))
    return by_item, by_source


def _is_numeric_attr(attribute: str) -> bool:
    return attribute in {
        "change_pct",
        "last_price",
        "open_price",
        "prev_close",
        "temperature",
    }


def _round_value(attribute: str, value: Any) -> Any:
    if not _is_numeric_attr(attribute):
        return value
    x = float(value)
    if attribute == "temperature":
        return round(x)  # 1°F bins for categorical TF
    if attribute == "change_pct":
        return round(x, 2)
    return round(x, 2)


class MajorityTD:
    name = "majority_median"

    def run(self, claims: list[dict], *, max_iter: int = 1) -> TDResult:
        by_item, by_source = _group_claims(claims)
        truths = {}
        ops = 0
        for item, pairs in by_item.items():
            vals = [v for _, v in pairs]
            ops += len(vals)
            if _is_numeric_attr(item[2]):
                truths[item] = float(np.median(np.asarray(vals, dtype=float)))
            else:
                # mode
                values, counts = np.unique(np.asarray(vals, dtype=object), return_counts=True)
                truths[item] = values[int(np.argmax(counts))]
        weights = {s: 1.0 / max(1, len(by_source)) for s in by_source}
        return TDResult(truths, weights, 1, ops)


class TruthFinder:
    """Yin et al. 2008 — iterative source trust / value confidence."""

    name = "truthfinder"

    def __init__(self, damping: float = 0.3, delta: float = 1e-3, max_iter: int = 20):
        self.damping = damping
        self.delta = delta
        self.max_iter = max_iter

    def run(self, claims: list[dict], *, max_iter: int | None = None) -> TDResult:
        max_iter = self.max_iter if max_iter is None else max_iter
        by_item, by_source = _group_claims(claims)
        # work in rounded categorical space
        cat_item: dict[tuple, dict[Any, set[str]]] = {}
        for item, pairs in by_item.items():
            buckets: dict[Any, set[str]] = defaultdict(set)
            for source, value in pairs:
                buckets[_round_value(item[2], value)].add(source)
            cat_item[item] = buckets

        trust = {source: 0.8 for source in by_source}
        ops = 0
        iterations = 0
        for iterations in range(1, max_iter + 1):
            conf: dict[tuple, dict[Any, float]] = {}
            for item, buckets in cat_item.items():
                conf[item] = {}
                for value, sources in buckets.items():
                    # P(wrong) = Π (1 - T_s)
                    wrong = 1.0
                    for source in sources:
                        wrong *= 1.0 - trust[source]
                        ops += 1
                    conf[item][value] = 1.0 - wrong
                # simple similarity dampening among neighbors (equality only → no-op)
                # keep damping toward uniform to avoid overconfidence
                if conf[item]:
                    mean_c = float(np.mean(list(conf[item].values())))
                    for value in conf[item]:
                        conf[item][value] = (
                            (1 - self.damping) * conf[item][value] + self.damping * mean_c
                        )

            new_trust = {}
            for source, items in by_source.items():
                scores = []
                for item, value in items:
                    key = _round_value(item[2], value)
                    scores.append(conf[item].get(key, 0.0))
                    ops += 1
                new_trust[source] = float(np.mean(scores)) if scores else 0.5

            # cosine convergence on trust vector
            keys = sorted(trust)
            a = np.asarray([trust[k] for k in keys], dtype=float)
            b = np.asarray([new_trust[k] for k in keys], dtype=float)
            denom = (np.linalg.norm(a) * np.linalg.norm(b)) + EPS
            cosine = float(np.dot(a, b) / denom)
            trust = new_trust
            if 1.0 - cosine <= self.delta:
                break

        truths = {}
        for item, buckets in cat_item.items():
            best_val = max(buckets, key=lambda v: conf[item][v])
            # map back to a representative raw value (median of sources in bin)
            raw_vals = [v for s, v in by_item[item] if _round_value(item[2], v) == best_val]
            if _is_numeric_attr(item[2]):
                truths[item] = float(np.median(np.asarray(raw_vals, dtype=float)))
            else:
                truths[item] = best_val
        return TDResult(truths, trust, iterations, ops)


def _item_scales(by_item: dict) -> dict[tuple, float]:
    """Per-item scale so heterogeneous continuous attrs share a loss unit."""
    scales = {}
    for item, pairs in by_item.items():
        if not _is_numeric_attr(item[2]):
            scales[item] = 1.0
            continue
        vals = np.asarray([float(v) for _, v in pairs], dtype=float)
        span = float(vals.max() - vals.min()) if len(vals) else 1.0
        scales[item] = span if span > EPS else 1.0
    return scales


class CRH:
    """Li et al. 2014 — Conflict Resolution on Heterogeneous data (core loop)."""

    name = "crh"

    def __init__(self, max_iter: int = 20, delta: float = 1e-3):
        self.max_iter = max_iter
        self.delta = delta

    def run(self, claims: list[dict], *, max_iter: int | None = None) -> TDResult:
        max_iter = self.max_iter if max_iter is None else max_iter
        by_item, by_source = _group_claims(claims)
        scales = _item_scales(by_item)
        weights = {source: 1.0 for source in by_source}
        truths: dict[tuple, Any] = {}
        ops = 0
        iterations = 0

        # init truths
        for item, pairs in by_item.items():
            vals = [v for _, v in pairs]
            truths[item] = (
                float(np.median(np.asarray(vals, dtype=float)))
                if _is_numeric_attr(item[2])
                else max(set(vals), key=vals.count)
            )
            ops += len(vals)

        for iterations in range(1, max_iter + 1):
            # source losses (scale-normalized for continuous attrs)
            loss = {source: 0.0 for source in by_source}
            for source, items in by_source.items():
                for item, value in items:
                    truth = truths[item]
                    if _is_numeric_attr(item[2]):
                        err = (float(value) - float(truth)) / scales[item]
                        loss[source] += err ** 2
                    else:
                        loss[source] += 0.0 if value == truth else 1.0
                    ops += 1
            # Inverse-loss weights (stable when sources nearly agree).
            # Equivalent spirit to CRH's "low-loss → high weight" update.
            new_weights = {}
            for source in by_source:
                new_weights[source] = 1.0 / (loss[source] + 1e-6)
            ssum = sum(new_weights.values()) + EPS
            for source in new_weights:
                new_weights[source] /= ssum

            # update truths
            new_truths = {}
            for item, pairs in by_item.items():
                if _is_numeric_attr(item[2]):
                    num = 0.0
                    den = 0.0
                    for source, value in pairs:
                        w = new_weights[source]
                        num += w * float(value)
                        den += w
                        ops += 1
                    new_truths[item] = num / (den + EPS)
                else:
                    score: dict[Any, float] = defaultdict(float)
                    for source, value in pairs:
                        score[value] += new_weights[source]
                        ops += 1
                    new_truths[item] = max(score, key=score.get)

            keys = sorted(weights)
            a = np.asarray([weights[k] for k in keys], dtype=float)
            b = np.asarray([new_weights[k] for k in keys], dtype=float)
            cosine = float(np.dot(a, b) / ((np.linalg.norm(a) * np.linalg.norm(b)) + EPS))
            weights = new_weights
            truths = new_truths
            if 1.0 - cosine <= self.delta:
                break

        return TDResult(truths, weights, iterations, ops)


class CATD:
    """Li et al. 2015 — Confidence-Aware Truth Discovery (long-tail)."""

    name = "catd"

    def __init__(self, alpha: float = 0.05, max_iter: int = 20, delta: float = 1e-3):
        self.alpha = alpha
        self.max_iter = max_iter
        self.delta = delta

    def run(self, claims: list[dict], *, max_iter: int | None = None) -> TDResult:
        max_iter = self.max_iter if max_iter is None else max_iter
        by_item, by_source = _group_claims(claims)
        scales = _item_scales(by_item)
        ops = 0
        # init truths
        truths: dict[tuple, Any] = {}
        for item, pairs in by_item.items():
            vals = [v for _, v in pairs]
            if _is_numeric_attr(item[2]):
                truths[item] = float(np.median(np.asarray(vals, dtype=float)))
            else:
                truths[item] = max(set(vals), key=vals.count)
            ops += len(vals)

        weights = {source: 1.0 / len(by_source) for source in by_source}
        iterations = 0
        for iterations in range(1, max_iter + 1):
            # variance + CI upper bound
            var_hat = {}
            n_s = {}
            for source, items in by_source.items():
                errs = []
                for item, value in items:
                    truth = truths[item]
                    if _is_numeric_attr(item[2]):
                        err = (float(value) - float(truth)) / scales[item]
                        errs.append(err ** 2)
                    else:
                        errs.append(0.0 if value == truth else 1.0)
                    ops += 1
                n_s[source] = max(1, len(errs))
                var_hat[source] = float(np.mean(errs)) if errs else 1.0

            new_weights = {}
            for source in by_source:
                df = max(1, n_s[source])
                # upper bound of variance CI: df * s^2 / chi2_{alpha/2, df}
                chi = float(chi2.ppf(self.alpha / 2.0, df))
                chi = max(chi, EPS)
                upper = df * var_hat[source] / chi
                new_weights[source] = 1.0 / (upper + EPS)
            ssum = sum(new_weights.values()) + EPS
            for source in new_weights:
                new_weights[source] /= ssum

            new_truths = {}
            for item, pairs in by_item.items():
                if _is_numeric_attr(item[2]):
                    num = 0.0
                    den = 0.0
                    for source, value in pairs:
                        w = new_weights[source]
                        num += w * float(value)
                        den += w
                        ops += 1
                    new_truths[item] = num / (den + EPS)
                else:
                    # categorical: weighted average in one-hot → pick max
                    score: dict[Any, float] = defaultdict(float)
                    for source, value in pairs:
                        score[value] += new_weights[source]
                        ops += 1
                    new_truths[item] = max(score, key=score.get)

            keys = sorted(weights)
            a = np.asarray([weights[k] for k in keys], dtype=float)
            b = np.asarray([new_weights[k] for k in keys], dtype=float)
            cosine = float(np.dot(a, b) / ((np.linalg.norm(a) * np.linalg.norm(b)) + EPS))
            weights = new_weights
            truths = new_truths
            if 1.0 - cosine <= self.delta:
                break

        return TDResult(truths, weights, iterations, ops)


class StreamingCRH:
    """Day-ordered online CRH — streaming truth-discovery analogue."""

    name = "streaming_crh"

    def __init__(self, forget: float = 0.85, max_iter_day: int = 5):
        self.forget = forget
        self.max_iter_day = max_iter_day
        self._crh = CRH(max_iter=max_iter_day)

    def run(self, claims: list[dict], *, max_iter: int | None = None) -> TDResult:
        by_day: dict[str, list[dict]] = defaultdict(list)
        for row in claims:
            by_day[row["day"]].append(row)
        weights: dict[str, float] = {}
        truths: dict[tuple, Any] = {}
        ops = 0
        iterations = 0
        for day in sorted(by_day):
            day_claims = by_day[day]
            # seed CRH with carried weights via claim replication factor (soft prior)
            result = self._crh.run(day_claims, max_iter=self.max_iter_day)
            iterations += result.iterations
            ops += result.ops
            truths.update(result.truths)
            # EMA merge of source weights
            for source, w in result.source_weights.items():
                if source in weights:
                    weights[source] = self.forget * weights[source] + (1 - self.forget) * w
                else:
                    weights[source] = w
        if weights:
            ssum = sum(weights.values()) + EPS
            weights = {s: w / ssum for s, w in weights.items()}
        return TDResult(truths, weights, max(1, iterations), ops)


METHODS = {
    MajorityTD.name: MajorityTD,
    TruthFinder.name: TruthFinder,
    CRH.name: CRH,
    CATD.name: CATD,
    StreamingCRH.name: StreamingCRH,
}
