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

`CleanEvidenceCellular` is the next experimental step: keep the sensory gate,
but remove two remaining impurities inside the decision path itself:

1. Memory may change a report's weight, never its direction.
2. Source trust is learned from delayed correctness, not emission rarity.
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


class CleanEvidenceCellular(SensoryGatedCellular):
    """Sensory TCM with sign-preserving memory and delayed source trust.

    Hard rules:

    - A report's vote direction is owned by the report. Memory may raise or
      lower its weight down to a tiny positive floor, but cannot flip it.
    - Source multipliers come from delayed correctness (Laplace-smoothed hit
      rate), not from how rarely a publisher emits a Positive/Negative label.
    """

    name = "clean_evidence_cellular"

    def __init__(
        self,
        *,
        trust_min: float = 0.25,
        trust_max: float = 2.5,
        trust_prior_hits: float = 1.0,
        trust_prior_tries: float = 2.0,
        preserve_sign: bool = True,
        use_delayed_trust: bool = True,
        **params,
    ):
        super().__init__(**params)
        self.trust_min = trust_min
        self.trust_max = trust_max
        self.trust_prior_hits = trust_prior_hits
        self.trust_prior_tries = trust_prior_tries
        self.preserve_sign = preserve_sign
        self.use_delayed_trust = use_delayed_trust
        self.src_hits = defaultdict(lambda: float(trust_prior_hits))
        self.src_tries = defaultdict(lambda: float(trust_prior_tries))
        self.sign_floors = 0
        self.trust_updates = 0

    def _delayed_trust_weight(self, source_key) -> float:
        hit_rate = self.src_hits[source_key] / max(EPS, self.src_tries[source_key])
        # Map [0, 1] reliability onto the same general scale as emission calib.
        return min(self.trust_max, max(self.trust_min, self.trust_min + (self.trust_max - self.trust_min) * hit_rate))

    def _source_weight(self, source_key, vote: int) -> float:
        if self.use_delayed_trust:
            return self._delayed_trust_weight(source_key)
        return self._calibration_weight(source_key, vote)

    def _rows(self, key, reports):
        correlation_scale = self._correlation_scale(reports)
        rows = []
        for source, context, vote in reports:
            sign = 1.0 if vote else -1.0
            claim_key = (key, vote)
            sensory = self.direct + self.wsrc * self.src[(source, context)]
            memory = self.wf * self.cf[claim_key] + self.ws * self.cs[claim_key]
            strength = sensory + memory
            if self.preserve_sign and strength <= 0:
                strength = EPS
                self.sign_floors += 1
            strength *= self._source_weight((source, context), vote) * correlation_scale
            signed_strength = sign * abs(strength) if self.preserve_sign else sign * strength
            rows.append(
                (abs(signed_strength), signed_strength, source, context, vote, claim_key)
            )
        rows.sort(key=lambda row: row[0], reverse=True)
        self.preview_ops += self.header_cost * len(rows)
        return rows

    def feedback(self, event):
        super().feedback(event)
        if not self.use_delayed_trust:
            return
        truth = int(event["truth"])
        for source, context, vote in event.get("reports", []):
            key = (source, context)
            self.src_tries[key] += 1.0
            if int(vote) == truth:
                self.src_hits[key] += 1.0
            self.trust_updates += 1

    def stats(self):
        stats = super().stats()
        stats.update(
            {
                "sign_floors": self.sign_floors,
                "trust_updates": self.trust_updates,
                "mean_source_trust": (
                    sum(
                        self.src_hits[key] / max(EPS, self.src_tries[key])
                        for key in self.src_tries
                    )
                    / max(1, len(self.src_tries))
                ),
            }
        )
        return stats


def _logit(probability: float) -> float:
    probability = min(1.0 - EPS, max(EPS, probability))
    return math.log(probability / (1.0 - probability))


class SkewCorrectedCellular(CleanEvidenceCellular):
    """Clean evidence plus publisher Positive base-rate correction.

    Relevant financial headlines are ~88% Positive while next-session direction
    is ~50%.  An all-Positive coalition therefore carries an emission base-rate
    that should not be read as strong up evidence.

    For cheerleader (all-Positive) coalitions this class subtracts

        scale * mean_i [logit(P_emit+(source_i)) - logit(market_rate)]

    from the decision logit.  Report signs stay preserved; mixed or negative
    coalitions are untouched.  `scale=1` is the theoretical full correction.
    """

    name = "skew_corrected_cellular"

    def __init__(
        self,
        *,
        base_rate_scale: float = 1.0,
        only_all_positive: bool = True,
        market_rate: float = 0.5,
        **params,
    ):
        super().__init__(**params)
        self.base_rate_scale = float(base_rate_scale)
        self.only_all_positive = bool(only_all_positive)
        self.market_rate = float(market_rate)
        self.skew_penalties = 0
        self.skew_penalty_sum = 0.0

    def _cheerleader_penalty(self, reports) -> float:
        if not reports:
            return 0.0
        if self.only_all_positive and not all(vote == 1 for _, _, vote in reports):
            return 0.0
        gaps = []
        for source, context, vote in reports:
            if vote != 1:
                continue
            positive = self.src_pos[(source, context)]
            negative = self.src_neg[(source, context)]
            emit_positive = positive / (positive + negative)
            gaps.append(max(0.0, _logit(emit_positive) - _logit(self.market_rate)))
        if not gaps:
            return 0.0
        return self.base_rate_scale * (sum(gaps) / len(gaps))

    def predict(self, key, reports, t):
        probability, trace = super().predict(key, reports, t)
        penalty = self._cheerleader_penalty(reports)
        if penalty <= 0:
            trace = dict(trace)
            trace.update({"skew_penalty": 0.0, "p_raw": probability})
            return probability, trace
        corrected = _sigmoid(_logit(probability) - penalty)
        self.skew_penalties += 1
        self.skew_penalty_sum += penalty
        trace = dict(trace)
        trace.update(
            {
                "p": corrected,
                "p_raw": probability,
                "skew_penalty": penalty,
            }
        )
        return corrected, trace

    def stats(self):
        stats = super().stats()
        stats.update(
            {
                "skew_penalties": self.skew_penalties,
                "mean_skew_penalty": (
                    self.skew_penalty_sum / max(1, self.skew_penalties)
                ),
            }
        )
        return stats


class SilenceEscapeCellular(CleanEvidenceCellular):
    """Release sticky memory when sensation is absent or cheerleader-null.

    Autopsy of real flip misses: under sensory silence, memory is
    *anti*-correlated with the next move.  The attractor seals the old regime
    exactly when the world is changing.

    Mechanism (HRF / fitted-dynamics aligned):

    - Treat no relevant reports, and optionally all-Positive cheerleader
      coalitions, as null sensation.
    - Estimate a local escape hazard from precision-weighted prediction-error
      EWMA and optional belief AR(1) criticality (|rho|).
    - Mix memory toward the anti-memory hypothesis with that hazard.
    - When real mixed/negative reports arrive, fall through to clean evidence
      (sign-preserving, delayed trust). Never uses the previous label.
    """

    name = "silence_escape_cellular"

    def __init__(
        self,
        *,
        pe_floor: float = 0.35,
        pe_span: float = 0.50,
        rho_gain: float = 0.30,
        max_hazard: float = 0.70,
        apply_to_all_positive: bool = True,
        err_beta: float = 0.30,
        **params,
    ):
        super().__init__(**params)
        self.pe_floor = float(pe_floor)
        self.pe_span = float(pe_span)
        self.rho_gain = float(rho_gain)
        self.max_hazard = float(max_hazard)
        self.apply_to_all_positive = bool(apply_to_all_positive)
        self.err_beta = float(err_beta)
        self.err_ewma = defaultdict(lambda: 0.5)
        self.belief_hist = defaultdict(list)
        self.escape_events = 0

    def _is_null_sensation(self, reports) -> bool:
        if not reports:
            return True
        if self.apply_to_all_positive and all(vote == 1 for _, _, vote in reports):
            return True
        return False

    def _rho(self, key) -> float:
        hist = self.belief_hist[key]
        if len(hist) < 4:
            return 0.0
        x = hist[-4:-1]
        y = hist[-3:]
        mx = sum(x) / len(x)
        my = sum(y) / len(y)
        num = sum((a - mx) * (b - my) for a, b in zip(x, y))
        den = sum((a - mx) ** 2 for a in x)
        if den <= EPS:
            return 0.0
        return float(min(1.0, abs(num / den)))

    def _escape_hazard(self, key) -> float:
        pe = self.err_ewma[key]
        hazard = max(0.0, (pe - self.pe_floor) / max(EPS, self.pe_span))
        if self.rho_gain:
            hazard += self.rho_gain * self._rho(key)
        return float(min(self.max_hazard, hazard))

    def _memory_probability(self, key) -> float:
        memory_log_odds = (
            self.wf * (self.cf[(key, 1)] - self.cf[(key, 0)])
            + self.ws * (self.cs[(key, 1)] - self.cs[(key, 0)])
        )
        return _sigmoid(memory_log_odds / max(self.temp, EPS))

    def _track_belief(self, key) -> None:
        fast = self.cf[(key, 1)] - self.cf[(key, 0)]
        hist = self.belief_hist[key]
        hist.append(fast)
        if len(hist) > 8:
            del hist[0]

    def predict(self, key, reports, t):
        if not self._is_null_sensation(reports):
            probability, trace = super().predict(key, reports, t)
            self._track_belief(key)
            return probability, trace

        memory_p = self._memory_probability(key)
        hazard = self._escape_hazard(key)
        probability = (1.0 - hazard) * memory_p + hazard * (1.0 - memory_p)
        self.infer_reads += 1.0
        if hazard > 0:
            self.escape_events += 1
        self._track_belief(key)
        return probability, {
            "key": key,
            "p": probability,
            "active": [],
            "used": 0,
            "contradiction": 0.0,
            "hazard": hazard,
            "required": 0,
            "certificate_shift": 0.0,
            "stop_reason": "silence_escape",
            "shadow_mass": (0.0, 0.0),
            "memory_p": memory_p,
            "escape_hazard": hazard,
            "err_ewma": self.err_ewma[key],
            "rho": self._rho(key),
        }

    def feedback(self, event):
        key = event["key"]
        probability = float(event["trace"]["p"])
        truth = int(event["truth"])
        self.err_ewma[key] = (
            (1.0 - self.err_beta) * self.err_ewma[key]
            + self.err_beta * abs(truth - probability)
        )
        super().feedback(event)

    def stats(self):
        stats = super().stats()
        stats["escape_events"] = self.escape_events
        return stats


class DiagnosticContrastCellular(SilenceEscapeCellular):
    """Proper DCAI-law bake into the silence-escape cell (v2).

    Not wrappers. Three internal laws:

    1. Slot continuity — empty is sensory absence; preserve-cloud (every
       report paraphrases memory's direction slot) means belief continues.
       Cheerleader all-Positive is *not* blanket-null: against down-memory
       it is a real direction edit. Publisher skew is solved inside that
       edit path by emission base-rate contrast, not by overriding slots.

    2. Local survival — per-report slot-edit hazards pool by noisy-OR into
       recruitment depth (one hard edit can force a deeper look). This is
       not noisy-OR over global PE/|ρ| scalars.

    3. Certificate contrast — certify only when the claim side beats the
       nearest false alternative (opposing mass + remaining reserve) by a
       margin. Final probability is the contrast between side masses.

    Escape policy: PE+|ρ| anti-memory mix applies to true absence only.
    Preserve-cloud keeps memory (slot continuity), and does not escape.
    """

    name = "diagnostic_contrast_cellular"

    def __init__(
        self,
        *,
        cheerleader_contrast_scale: float = 1.0,
        contrast_margin: float = 0.08,
        survival_gain: float = 1.0,
        survival_tau: float = 1.0,
        preserve_recruit_scale: float = 0.0,
        market_rate: float = 0.5,
        apply_to_all_positive: bool = False,
        **params,
    ):
        # Slot law owns null; silence-escape cheerleader blanket stays off.
        params["apply_to_all_positive"] = bool(apply_to_all_positive)
        super().__init__(**params)
        self.cheerleader_contrast_scale = float(cheerleader_contrast_scale)
        self.contrast_margin = float(contrast_margin)
        self.survival_gain = float(survival_gain)
        self.survival_tau = float(survival_tau)
        self.preserve_recruit_scale = float(preserve_recruit_scale)
        self.market_rate = float(market_rate)
        self.operator_counts = defaultdict(int)
        self.slot_demotions = 0
        self.cheerleader_penalties = 0
        self.contrast_rejects = 0

    def _memory_side(self, key):
        preference = (
            self.wf * (self.cf[(key, 1)] - self.cf[(key, 0)])
            + self.ws * (self.cs[(key, 1)] - self.cs[(key, 0)])
        )
        if abs(preference) <= EPS:
            return None
        return 1 if preference > 0 else 0

    @staticmethod
    def _noisy_or(hazards) -> float:
        survival = 1.0
        for hazard in hazards:
            clamped = min(1.0, max(0.0, float(hazard)))
            survival *= 1.0 - clamped
        return 1.0 - survival

    def _emission_positive_gap(self, source, context) -> float:
        positive = self.src_pos[(source, context)]
        negative = self.src_neg[(source, context)]
        emit_positive = positive / (positive + negative)
        return max(0.0, _logit(emit_positive) - _logit(self.market_rate))

    def _operator_state(self, key, reports) -> dict:
        if not reports:
            return {
                "operators": ("absence",),
                "null": True,
                "cheerleader_edit": False,
                "edit_votes": (),
                "preserve_votes": (),
            }

        memory_side = self._memory_side(key)
        votes = [vote for _, _, vote in reports]
        all_positive = all(vote == 1 for vote in votes)
        mixed = len(set(votes)) > 1

        if memory_side is None:
            operators = []
            if mixed:
                operators.append("fusion_conflict")
            elif all_positive:
                operators.append("cheerleader_edit")
            else:
                operators.append("uncommitted_cloud")
            return {
                "operators": tuple(operators),
                "null": False,
                "cheerleader_edit": all_positive,
                "edit_votes": tuple(votes),
                "preserve_votes": (),
            }

        edit_votes = tuple(vote for vote in votes if vote != memory_side)
        preserve_votes = tuple(vote for vote in votes if vote == memory_side)
        if not edit_votes:
            # Calibrated fire: all-Positive paraphrase of up-memory is
            # emission-null (publisher cheerleading), not diagnostic
            # confirmation. Other preserve-clouds continue belief.
            cheerleader_preserve = all(vote == 1 for vote in votes)
            return {
                "operators": (
                    ("cheerleader_preserve",) if cheerleader_preserve else ("preserve_cloud",)
                ),
                "null": True,
                "cheerleader_edit": False,
                "edit_votes": (),
                "preserve_votes": preserve_votes,
            }

        operators = ["direction_swap"]
        cheerleader_edit = all_positive and memory_side == 0
        if cheerleader_edit:
            operators.append("cheerleader_edit")
        if preserve_votes and edit_votes:
            operators.append("fusion_conflict")
        return {
            "operators": tuple(operators),
            "null": False,
            "cheerleader_edit": cheerleader_edit,
            "edit_votes": edit_votes,
            "preserve_votes": preserve_votes,
        }

    def _rows(self, key, reports, *, cheerleader_edit: bool = False):
        correlation_scale = self._correlation_scale(reports)
        memory_side = self._memory_side(key)
        rows = []
        for source, context, vote in reports:
            sign = 1.0 if vote else -1.0
            claim_key = (key, vote)
            sensory = self.direct + self.wsrc * self.src[(source, context)]
            memory = self.wf * self.cf[claim_key] + self.ws * self.cs[claim_key]
            strength = sensory + memory
            if self.preserve_sign and strength <= 0:
                strength = EPS
                self.sign_floors += 1
            strength *= self._source_weight((source, context), vote) * correlation_scale

            # Structural shield: memory-paraphrase reports do not recruit as
            # sealing evidence.
            if memory_side is not None and vote == memory_side:
                strength *= self.preserve_recruit_scale
                self.slot_demotions += 1

            # Skew solved inside cheerleader edits (not by null override).
            if cheerleader_edit and vote == 1:
                gap = self._emission_positive_gap(source, context)
                strength = max(EPS, strength - self.cheerleader_contrast_scale * gap)
                self.cheerleader_penalties += 1

            signed_strength = sign * abs(strength) if self.preserve_sign else sign * strength
            rows.append(
                (abs(signed_strength), signed_strength, source, context, vote, claim_key)
            )
        rows.sort(key=lambda row: row[0], reverse=True)
        self.preview_ops += self.header_cost * len(rows)
        return rows

    def _local_edit_survival(self, key, rows) -> float:
        memory_side = self._memory_side(key)
        if memory_side is None:
            hazards = [
                min(1.0, abs(strength) / (abs(strength) + self.survival_tau))
                for _, strength, _, _, _, _ in rows
                if abs(strength) > EPS
            ]
        else:
            hazards = [
                min(1.0, abs(strength) / (abs(strength) + self.survival_tau))
                for _, strength, _, _, vote, _ in rows
                if vote != memory_side and abs(strength) > EPS
            ]
        if not hazards:
            return 0.0
        return self._noisy_or(hazards)

    def _base_hazard(self, key, reports, t) -> float:
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

    def _predict_contrast(self, key, reports, t, state) -> tuple:
        rows = self._rows(
            key, reports, cheerleader_edit=state["cheerleader_edit"]
        )[: self.max_k]
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
        edit_survival = self._local_edit_survival(key, rows)
        hazard = min(
            1.0,
            base_hazard + self.survival_gain * edit_survival * (1.0 - base_hazard),
        )
        required = min(
            self.max_k,
            max(self.min_k, 1 + int(round(self.hazard_gain * hazard))),
        )

        stop_reason = "budget"
        certificate_shift = 1.0
        contrast_margin_seen = 0.0
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
            reserve_mass = remaining_positive + remaining_negative
            if reserve_mass <= EPS and index + 1 >= count:
                stop_reason = "exhausted"
                certificate_shift = 0.0
                break

            # Nearest false alternative: opposing side plus all unused reserve.
            claim_is_up = evidence_sum >= 0
            claim_mass = positive if claim_is_up else negative
            false_mass = (negative if claim_is_up else positive) + reserve_mass
            contrast = claim_mass - false_mass
            contrast_margin_seen = contrast
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
            if contrast < self.contrast_margin:
                self.contrast_rejects += 1
                continue
            if (
                same_decision
                and contrast >= self.contrast_margin
                and abs(current) >= self.min_margin
                and certificate_shift <= self.cert_delta
            ):
                stop_reason = "contrast_certified"
                break

        contradiction = min(positive, negative) / (max(positive, negative) + EPS)
        # Decision from side-mass contrast, not sealed anchor sum alone.
        final_contrast = positive - negative
        probability = _sigmoid(final_contrast / max(self.temp, EPS))
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
            "edit_survival": edit_survival,
            "required": required,
            "certificate_shift": certificate_shift,
            "contrast_margin_seen": contrast_margin_seen,
            "stop_reason": stop_reason,
            "shadow_mass": (shadow_zero, shadow_one),
            "operators": state["operators"],
            "cheerleader_edit": state["cheerleader_edit"],
        }

    def predict(self, key, reports, t):
        state = self._operator_state(key, reports)
        for operator in state["operators"]:
            self.operator_counts[operator] += 1

        if state["null"]:
            memory_p = self._memory_probability(key)
            self.infer_reads += 1.0
            operators = state["operators"]
            # Absence or calibrated cheerleader-preserve: PE+|ρ| escape.
            # Ordinary preserve-cloud: continue memory (slot continuity).
            if operators in (("absence",), ("cheerleader_preserve",)):
                hazard = SilenceEscapeCellular._escape_hazard(self, key)
                probability = (1.0 - hazard) * memory_p + hazard * (1.0 - memory_p)
                if hazard > 0:
                    self.escape_events += 1
                stop_reason = (
                    "absence_escape"
                    if operators == ("absence",)
                    else "cheerleader_preserve_escape"
                )
            else:
                hazard = 0.0
                probability = memory_p
                stop_reason = "slot_preserve_continue"
            self._track_belief(key)
            return probability, {
                "key": key,
                "p": probability,
                "active": [],
                "used": 0,
                "contradiction": 0.0,
                "hazard": hazard,
                "required": 0,
                "certificate_shift": 0.0,
                "stop_reason": stop_reason,
                "shadow_mass": (0.0, 0.0),
                "memory_p": memory_p,
                "escape_hazard": hazard,
                "err_ewma": self.err_ewma[key],
                "rho": self._rho(key),
                "operators": state["operators"],
            }

        probability, trace = self._predict_contrast(key, reports, t, state)
        self.infer_reads += self.header_cost * len(reports) + trace["used"]
        self._record_emissions(reports)
        self._track_belief(key)
        return probability, trace

    def stats(self):
        stats = super().stats()
        stats.update(
            {
                "slot_demotions": self.slot_demotions,
                "cheerleader_penalties": self.cheerleader_penalties,
                "contrast_rejects": self.contrast_rejects,
                "operator_counts": dict(self.operator_counts),
            }
        )
        return stats


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
        fresh_floor_surprise_only: bool = False,
        require_counterevidence: bool = False,
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
        self.fresh_floor_surprise_only = fresh_floor_surprise_only
        self.require_counterevidence = require_counterevidence

        self.mistrust = defaultdict(float)
        self.trust_raises = 0
        self.trust_relaxations = 0
        self.counterevidence_raises = 0
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
                surprise_factor = 1.0
                if self.fresh_floor_surprise_only:
                    # A routine message from a source that says it almost
                    # every day is not "fresh" in the brain-like sense. Only
                    # a source-surprising message earns the elevated floor.
                    surprise_factor = max(
                        0.0,
                        (calibration - 1.0) / max(EPS, self.cal_max - 1.0),
                    )
                floor = fresh_floor * surprise_factor * sensory
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
        extra_report = int(
            self.trust_hazard_gain > 0 and mistrust >= self.recruit_threshold
        )
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
        predicted = int(probability >= 0.5)
        correct = predicted == truth
        has_ignored_counterevidence = any(
            vote != predicted for _, _, vote in event["reports"]
        )

        super().feedback(event)

        if signal <= 0:
            return
        if correct:
            self.mistrust[key] *= 1.0 - self.correct_relaxation * signal
            self.trust_relaxations += 1
        elif not self.require_counterevidence or has_ignored_counterevidence:
            self.mistrust[key] += self.mistrust_gain * signal * (
                1.0 - self.mistrust[key]
            )
            self.trust_raises += 1
            self.counterevidence_raises += int(has_ignored_counterevidence)

    def stats(self):
        stats = super().stats()
        stats.update(
            {
                "trust_raises": self.trust_raises,
                "trust_relaxations": self.trust_relaxations,
                "counterevidence_raises": self.counterevidence_raises,
                "floor_hits": self.floor_hits,
                "extra_recruitments": self.extra_recruitments,
            }
        )
        return stats
