"""Active real-data experimental TCM mechanisms.

`SensoryGatedCellular` preserves the frozen Wave XI memory / reserve /
certification mechanism.  It adds the one real-data cure that survived a
predeclared fresh-company confirmation:

1. Source base-rate calibration: a message that a source says almost every day
   is weak; a rare message from that source is more informative.
2. Correlation discounting: several same-direction reports within an event do
   not count as independent evidence.
3. Sensory-silence memory fallback: when an upstream relevance gate finds no
   report actually about the current item, retain memory rather than treating
   a 50/50 tie as an implicit positive vote.

The upstream relevance gate belongs to the ingestion stream because it needs
article titles and item names.  See `benchmarks/realdata_finance/relevance.py`.
"""

from __future__ import annotations

import math
from collections import defaultdict

from .reference import BatchedReserveCellular

EPS = 1e-9


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(-40.0, min(40.0, value))))


class SensoryGatedCellular(BatchedReserveCellular):
    """Wave XI TCM with the confirmed real-data sensory evidence front end.

    The model expects report tuples `(source_id, context_id, vote)`.  `context`
    may remain `0`; source base-rate calibration is learned separately for each
    `(source, context)` population.
    """

    name = "sensory_gated_cellular"

    def __init__(self, *, cal_min: float = 0.3, cal_max: float = 3.0, **params):
        super().__init__(**params)
        self.cal_min = cal_min
        self.cal_max = cal_max
        # Laplace-smoothed source emission populations.  These are about what a
        # source says, not whether its prediction was correct.
        self.src_pos = defaultdict(lambda: 1.0)
        self.src_neg = defaultdict(lambda: 1.0)

    def _calibration_weight(self, source_key, vote: int) -> float:
        pos, neg = self.src_pos[source_key], self.src_neg[source_key]
        emission_probability = (pos if vote == 1 else neg) / (pos + neg)
        self_information_bits = -math.log(max(EPS, emission_probability)) / math.log(2.0)
        return min(self.cal_max, max(self.cal_min, self_information_bits))

    @staticmethod
    def _correlation_scale(reports) -> float:
        if len(reports) < 2:
            return 1.0
        votes = [vote for _, _, vote in reports]
        agreeing_pairs = sum(
            votes[i] == votes[j]
            for i in range(len(votes))
            for j in range(i + 1, len(votes))
        )
        total_pairs = len(votes) * (len(votes) - 1) / 2
        agreement = agreeing_pairs / total_pairs if total_pairs else 0.0
        effective_count = 1.0 + (len(votes) - 1) * (1.0 - agreement)
        return effective_count / len(votes)

    def _rows(self, key, reports):
        """Use calibrated, correlation-discounted evidence in frozen TCM."""
        correlation_scale = self._correlation_scale(reports)
        rows = []
        for source, context, vote in reports:
            sign = 1.0 if vote else -1.0
            claim_key = (key, vote)
            strength = (
                self.direct
                + self.wf * self.cf[claim_key]
                + self.ws * self.cs[claim_key]
                + self.wsrc * self.src[(source, context)]
            )
            strength *= self._calibration_weight((source, context), vote) * correlation_scale
            signed_strength = sign * strength
            rows.append((abs(signed_strength), signed_strength, source, context, vote, claim_key))
        rows.sort(key=lambda row: row[0], reverse=True)
        self.preview_ops += self.header_cost * len(rows)
        return rows

    def _record_emissions(self, reports) -> None:
        for source, context, vote in reports:
            if vote:
                self.src_pos[(source, context)] += 1.0
            else:
                self.src_neg[(source, context)] += 1.0

    def predict(self, key, reports, t):
        if reports:
            probability, trace = super().predict(key, reports, t)
            self._record_emissions(reports)
            return probability, trace

        # There is no sensory evidence after relevance filtering.  Preserve the
        # living fast/slow belief instead of converting an empty input into an
        # arbitrary "up" classification through a 0.5 threshold tie.
        memory_log_odds = (
            self.wf * (self.cf[(key, 1)] - self.cf[(key, 0)])
            + self.ws * (self.cs[(key, 1)] - self.cs[(key, 0)])
        )
        probability = _sigmoid(memory_log_odds / max(self.temp, EPS))
        self.infer_reads += 1.0
        return probability, {
            "key": key,
            "p": probability,
            "active": [],
            "used": 0,
            "contradiction": 0.0,
            "hazard": 0.0,
            "required": 0,
            "certificate_shift": 0.0,
            "stop_reason": "no_relevant_report",
            "shadow_mass": (0.0, 0.0),
        }
