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


class WaveXVIIITrustCellular(SensoryGatedCellular):
    """Development-only per-item prediction-error-driven trust mechanism.

    A confident error does not directly flip a belief. It changes how the
    *next* decision treats its own memory versus relevant fresh evidence:
    recruit one report deeper, weaken the anchor, and protect counter-evidence.
    Correct confident predictions relax the same local state.
    """

    name = "wave_xviii_trust_cellular"

    def __init__(
        self,
        *,
        confidence_threshold: float = 0.20,
        mistrust_gain: float = 0.75,
        correct_relaxation: float = 0.40,
        trust_hazard_gain: float = 0.25,
        recruit_threshold: float = 0.50,
        anchor_floor: float = 0.35,
        fresh_evidence_floor: float = 0.75,
        **params,
    ):
        super().__init__(**params)
        self.confidence_threshold = confidence_threshold
        self.mistrust_gain = mistrust_gain
        self.correct_relaxation = correct_relaxation
        self.trust_hazard_gain = trust_hazard_gain
        self.recruit_threshold = recruit_threshold
        self.anchor_floor = anchor_floor
        self.fresh_evidence_floor = fresh_evidence_floor

        self.mistrust = defaultdict(float)
        self.trust_raises = 0
        self.trust_relaxations = 0
        self.floor_hits = 0
        self.extra_recruitments = 0

    def _signal_strength(self, probability: float) -> float:
        """Map prediction confidence to [0, 1] above the declared threshold."""
        confidence = 2.0 * abs(probability - 0.5)
        if confidence < self.confidence_threshold:
            return 0.0
        return (confidence - self.confidence_threshold) / max(
            EPS, 1.0 - self.confidence_threshold
        )

    def _anchor_scale(self, key) -> float:
        return 1.0 - self.mistrust[key] * (1.0 - self.anchor_floor)

    def _anchor_side(self, key):
        preference = (
            self.cf[(key, 1)]
            - self.cf[(key, 0)]
            + self.cs[(key, 1)]
            - self.cs[(key, 0)]
        )
        if abs(preference) <= EPS:
            return None
        return 1 if preference > 0 else 0

    def _rows(self, key, reports):
        # The zero-state path is exact SensoryGatedCellular behavior.
        if self.mistrust[key] <= 0:
            return super()._rows(key, reports)

        correlation_scale = self._correlation_scale(reports)
        anchor_scale = self._anchor_scale(key)
        old_side = self._anchor_side(key)
        fresh_floor = self.mistrust[key] * self.fresh_evidence_floor
        rows = []
        for source, context, vote in reports:
            sign = 1.0 if vote else -1.0
            claim_key = (key, vote)
            calibration = self._calibration_weight((source, context), vote)
            sensory = (
                self.direct + self.wsrc * self.src[(source, context)]
            ) * calibration * correlation_scale
            anchor = (
                self.wf * self.cf[claim_key] + self.ws * self.cs[claim_key]
            ) * calibration * correlation_scale * anchor_scale
            strength = sensory + anchor

            # Fresh relevant evidence that disagrees with the stale belief must
            # retain at least this fraction of its sensory strength. The floor
            # rises only after confident error and only for counter-evidence.
            if old_side is not None and vote != old_side:
                floor = fresh_floor * sensory
                if strength < floor:
                    strength = floor
                    self.floor_hits += 1

            signed_strength = sign * strength
            rows.append(
                (abs(signed_strength), signed_strength, source, context, vote, claim_key)
            )
        rows.sort(key=lambda row: row[0], reverse=True)
        self.preview_ops += self.header_cost * len(rows)
        return rows

    def _base_hazard(self, key, reports, t):
        ones = sum(vote for _, _, vote in reports)
        zeros = len(reports) - ones
        report_disagreement = min(ones, zeros) / (max(ones, zeros) + EPS)
        fast_preference = self.cf[(key, 1)] - self.cf[(key, 0)]
        slow_preference = self.cs[(key, 1)] - self.cs[(key, 0)]
        memory_conflict = float(fast_preference * slow_preference < 0)
        volatility = min(1.0, abs(fast_preference - slow_preference))
        age = max(0, t - self.last_fb[key])
        stale = min(1.0, age / 30.0)
        return min(
            1.0,
            0.45 * report_disagreement
            + 0.25 * memory_conflict
            + 0.20 * volatility
            + 0.10 * stale,
        )

    def _predict_with_trust(self, key, reports, t):
        """Compressed-reserve prediction with Wave XVIII's one-report cap."""
        rows = self._rows(key, reports)[: self.max_k]
        count = len(rows)
        suffix_pos = [0.0] * (count + 1)
        suffix_neg = [0.0] * (count + 1)
        for index in range(count - 1, -1, -1):
            strength = rows[index][1]
            suffix_pos[index] = suffix_pos[index + 1] + (
                abs(strength) if strength >= 0 else 0.0
            )
            suffix_neg[index] = suffix_neg[index + 1] + (
                abs(strength) if strength < 0 else 0.0
            )

        base_hazard = self._base_hazard(key, reports, t)
        mistrust = self.mistrust[key]
        hazard = min(1.0, base_hazard + self.trust_hazard_gain * mistrust)
        base_required = min(
            self.max_k,
            max(self.min_k, 1 + int(round(self.hazard_gain * base_hazard))),
        )
        extra_report = int(mistrust >= self.recruit_threshold)
        required = min(self.max_k, base_required + extra_report)
        self.extra_recruitments += extra_report

        stop_reason = "budget"
        certificate_shift = 1.0
        coalition = []
        evidence_sum = positive = negative = 0.0
        for index, row in enumerate(rows):
            coalition.append(row)
            strength = row[1]
            evidence_sum += strength
            if strength >= 0:
                positive += abs(strength)
            else:
                negative += abs(strength)
            self.activation_ops += 1.0
            self.ops += 2
            if len(coalition) < required:
                continue

            remaining_positive = suffix_pos[index + 1]
            remaining_negative = suffix_neg[index + 1]
            if remaining_positive + remaining_negative <= EPS:
                stop_reason = "exhausted"
                certificate_shift = 0.0
                break
            contradiction = min(positive, negative) / (max(positive, negative) + EPS)
            current = evidence_sum * (1.0 - self.cg * contradiction)
            full_positive = positive + remaining_positive
            full_negative = negative + remaining_negative
            full_sum = full_positive - full_negative
            full_contradiction = min(full_positive, full_negative) / (
                max(full_positive, full_negative) + EPS
            )
            full = full_sum * (1.0 - self.cg * full_contradiction)
            current_probability = _sigmoid(current / max(self.temp, EPS))
            full_probability = _sigmoid(full / max(self.temp, EPS))
            certificate_shift = abs(current_probability - full_probability)
            same_decision = (current >= 0) == (full >= 0)
            reserve_mass = remaining_positive + remaining_negative
            robust = abs(current) > self.certify_slack + reserve_mass * (
                1.0 - self.cg * min(1.0, contradiction + 0.25)
            )
            if (
                same_decision
                and robust
                and abs(current) >= self.min_margin
                and certificate_shift <= self.cert_delta
            ):
                stop_reason = "compressed_certified"
                break

        contradiction = min(positive, negative) / (max(positive, negative) + EPS)
        final = evidence_sum * (1.0 - self.cg * contradiction)
        probability = _sigmoid(final / max(self.temp, EPS))
        cutoff = len(coalition)
        shadow_zero = sum(abs(row[1]) for row in rows[cutoff:] if row[4] == 0)
        shadow_one = sum(abs(row[1]) for row in rows[cutoff:] if row[4] == 1)
        return probability, {
            "key": key,
            "p": probability,
            "active": [
                (source, context, vote, claim_key, abs(strength))
                for _, strength, source, context, vote, claim_key in coalition
            ],
            "used": cutoff,
            "contradiction": contradiction,
            "hazard": hazard,
            "base_hazard": base_hazard,
            "required": required,
            "extra_recruited": extra_report,
            "mistrust": mistrust,
            "anchor_scale": self._anchor_scale(key),
            "fresh_evidence_floor": mistrust * self.fresh_evidence_floor,
            "certificate_shift": certificate_shift,
            "stop_reason": stop_reason,
            "shadow_mass": (shadow_zero, shadow_one),
        }

    def predict(self, key, reports, t):
        mistrust = self.mistrust[key]
        if mistrust <= 0:
            probability, trace = super().predict(key, reports, t)
            trace.update(
                {
                    "mistrust": 0.0,
                    "anchor_scale": 1.0,
                    "fresh_evidence_floor": 0.0,
                    "base_hazard": trace.get("hazard", 0.0),
                    "extra_recruited": 0,
                }
            )
            return probability, trace

        if not reports:
            memory_log_odds = (
                self.wf * (self.cf[(key, 1)] - self.cf[(key, 0)])
                + self.ws * (self.cs[(key, 1)] - self.cs[(key, 0)])
            ) * self._anchor_scale(key)
            probability = _sigmoid(memory_log_odds / max(self.temp, EPS))
            self.infer_reads += 1.0
            return probability, {
                "key": key,
                "p": probability,
                "active": [],
                "used": 0,
                "contradiction": 0.0,
                "hazard": 0.0,
                "base_hazard": 0.0,
                "required": 0,
                "extra_recruited": 0,
                "mistrust": mistrust,
                "anchor_scale": self._anchor_scale(key),
                "fresh_evidence_floor": mistrust * self.fresh_evidence_floor,
                "certificate_shift": 0.0,
                "stop_reason": "no_relevant_report",
                "shadow_mass": (0.0, 0.0),
            }

        probability, trace = self._predict_with_trust(key, reports, t)
        self.infer_reads += self.header_cost * len(reports) + trace["used"]
        self._record_emissions(reports)
        return probability, trace

    def feedback(self, event):
        probability = float(event["trace"]["p"])
        truth = int(event["truth"])
        key = event["key"]
        signal = self._signal_strength(probability)
        correct = int(probability >= 0.5) == truth

        super().feedback(event)

        if signal <= 0:
            return
        if correct:
            self.mistrust[key] *= 1.0 - self.correct_relaxation * signal
            self.trust_relaxations += 1
        else:
            self.mistrust[key] += self.mistrust_gain * signal * (
                1.0 - self.mistrust[key]
            )
            self.trust_raises += 1

    def stats(self):
        stats = super().stats()
        stats.update(
            {
                "trust_raises": self.trust_raises,
                "trust_relaxations": self.trust_relaxations,
                "floor_hits": self.floor_hits,
                "extra_recruitments": self.extra_recruitments,
            }
        )
        return stats
