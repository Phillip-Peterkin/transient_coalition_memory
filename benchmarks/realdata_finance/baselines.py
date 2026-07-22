"""Lightweight baselines that speak the same report API as TCM."""

from __future__ import annotations

from collections import defaultdict, deque

import numpy as np

EPS = 1e-9


def sigmoid(x: float) -> float:
    x = max(-40.0, min(40.0, x))
    return 1.0 / (1.0 + np.exp(-x))


def logit(p: float) -> float:
    p = min(1 - EPS, max(EPS, p))
    return float(np.log(p / (1 - p)))


class PersistenceOracle:
    """Uses the stream's same-day direction; no learning from reports."""

    name = "persistence_oracle"

    def __init__(self, stream):
        self.stream = stream
        self.ops = 0.0

    def predict(self, key, reports, t, event=None):
        self.ops += 1.0
        if event is None:
            return 0.5, {"used": 0}
        p = self.stream.persistence_prediction(event)
        if p is None:
            return 0.5, {"used": 0}
        return float(p), {"used": 0}

    def feedback(self, event):
        return

    def stats(self):
        return {"memory_states": 0, "updates": 0, "active_ops": self.ops}


class MemorylessMajority:
    name = "memoryless_majority"

    def __init__(self):
        self.ops = 0.0

    def predict(self, key, reports, t, event=None):
        if not reports:
            return 0.5, {"used": 0}
        vals = [y for _, _, y in reports]
        self.ops += len(vals)
        return float(np.mean(vals)), {"used": len(vals)}

    def feedback(self, event):
        return

    def stats(self):
        return {"memory_states": 0, "updates": 0, "active_ops": self.ops}


class DynamicBayes:
    name = "dynamic_bayes"

    def __init__(self, forget: float = 0.985, alpha: float = 2.0):
        self.f = forget
        self.a = defaultdict(lambda: alpha)
        self.b = defaultdict(lambda: alpha)
        self.ops = 0.0
        self.up = 0

    def predict(self, key, reports, t, event=None):
        z = 0.0
        for s, c, y in reports:
            r = self.a[(s, c)] / (self.a[(s, c)] + self.b[(s, c)])
            z += (1 if y else -1) * logit(max(0.501, r))
            self.ops += 1
        return sigmoid(z), {"used": len(reports), "contributors": reports}

    def feedback(self, e):
        touched = {(s, c) for s, c, _ in e["reports"]}
        for k in touched:
            self.a[k] = 2 + (self.a[k] - 2) * self.f
            self.b[k] = 2 + (self.b[k] - 2) * self.f
        for s, c, y in e["reports"]:
            if y == e["truth"]:
                self.a[(s, c)] += 1
            else:
                self.b[(s, c)] += 1
            self.up += 1

    def stats(self):
        return {
            "memory_states": 2 * len(self.a),
            "updates": self.up,
            "active_ops": self.ops,
        }


class RecentMajority:
    """Short history of report means per key (memoryless-with-lag baseline)."""

    name = "recent_majority"

    def __init__(self, window: int = 3):
        self.hist = defaultdict(lambda: deque(maxlen=window))
        self.ops = 0.0

    def predict(self, key, reports, t, event=None):
        vals = [y for _, _, y in reports]
        if vals:
            self.hist[key].append(sum(vals) / len(vals))
            self.ops += len(vals)
        if not self.hist[key]:
            return 0.5, {"used": len(vals)}
        return float(np.mean(self.hist[key])), {"used": len(vals)}

    def feedback(self, event):
        return

    def stats(self):
        return {
            "memory_states": sum(len(v) for v in self.hist.values()),
            "updates": 0,
            "active_ops": self.ops,
        }
