"""Active real-data experimental TCM mechanisms.

Active experimental model (finance-confirmed):
    `ActiveCoalitionCellular` — Active Coalition Inference (ACI).
    Pair with `SessionRelevanceFinanceNewsStream`. Sealed on virgin
    confirmation8; Wave XI reference stays frozen.

Context-awareness organ (experimental, maturing):
    `AwareCoalitionCellular` — ACI + Mnemosheath (1→2→4→12 bit distinctions).
    Learns whether agreement is evidence or cheerleader null. See
    `docs/MNEMOSHEATH.md`.

Historical / ancestor cells kept for regression and protocol archives:
    `SensoryGatedCellular`, `CleanEvidenceCellular`, `SilenceEscapeCellular`,
    and failed screens (`SkewCorrectedCellular`, `DiagnosticContrastCellular`,
    `WaveXVIIITrustCellular`).

ACI laws (one cell, not bolted modules):
1. Evidence is contrast (source LRs); prior never enters report strength.
2. Null sensation (empty / cheerleader Positive / near-zero Δ) is a first-class
   channel: PE+|ρ| anti-prior mix (Friston form of sealed silence escape).
3. Recruit by |Δ|; certify when unread discrimination mass cannot flip
   (free-energy stop). Prior and evidence meet once at the posterior.
4. Budgeted reading is TCM's novelty on top of predictive processing.

Upstream relevance still belongs to the ingestion stream
(`benchmarks/realdata_finance/relevance.py` / `session_stream.py`).
"""

from __future__ import annotations

import math
from collections import defaultdict

from .reference import BatchedReserveCellular

EPS = 1e-9


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(-40.0, min(40.0, value))))


class SensoryGatedCellular(BatchedReserveCellular):
    """Historical first real-data front end (relevance confirmation).

    Superseded as the *active* experimental model by `ActiveCoalitionCellular`.
    Kept for archival protocols and regression against the relevance bake.

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


class ActiveCoalitionCellular(BatchedReserveCellular):
    """Active Coalition Inference — active real-data experimental TCM.

    Predictive coding under a read budget. Defaults are the sealed
    confirmation8 freeze (do not retune on spent universes).

    - Prior (fast/slow claim memory) never enters report strength.
    - Each report is a precision-weighted log-likelihood ratio
      Δ = log P(vote|up) − log P(vote|down), learned from delayed outcomes.
    - Silence is a first-class channel: null PE + stickiness mix toward
      anti-prior under empty / cheerleader / non-diagnostic batches.
    - Recruitment ranks by |Δ| (discriminative power), never by agreement
      with memory — prior-neutral sampling.
    - Prior and evidence meet once: posterior_lo = prior_lo + Σ Δ_active.
    - Free-energy certificate: stop when unread Σ|Δ| cannot flip the sign
      of the posterior (expected surprise reduction below read cost).

    Not a Wave XI replacement: frozen `BatchedReserveCellular` remains the
    synthetic reference. This cell is the active experimental real-data model.
    """

    name = "active_coalition_cellular"
    # Sealed finance confirmation (confirmation8); do not retune here.
    confirmed_universe = "confirmation8"
    confirmed_flip = 0.5256410256410257

    def __init__(
        self,
        *,
        laplace: float = 1.0,
        min_delta: float = 0.15,
        max_silence_hazard: float = 0.55,
        null_pe_floor: float = 0.35,
        null_pe_span: float = 0.50,
        null_err_beta: float = 0.30,
        null_rho_gain: float = 0.30,
        fe_cert_slack: float = 0.0,
        use_correlation_discount: bool = True,
        force_all_positive_null: bool = True,
        # Source-trust regime tracking (all default off = sealed confirmation8).
        # 1) Constant fade before each update (baseline repair).
        source_forget: float = 1.0,
        # 2) Fixed-Share-style never-zero floor: mix toward Laplace so a
        #    disgraced source can re-earn trust and a hero can be disowned.
        source_share: float = 0.0,
        # 3) Shift-triggered hard discount: per-source mini change-point
        #    (Mnemosheath idea pointed at sources). window 0 = disabled.
        source_shift_window: int = 0,
        source_shift_gap: float = 0.35,
        source_shift_discount: float = 0.15,
        source_shift_long_beta: float = 0.05,
        # 4) Observable copy-skipping: if two sources almost always agree,
        #    do not recruit both as independent evidence (default off).
        use_source_redundancy: bool = False,
        source_redundant_agree: float = 0.90,
        source_redundant_min_pairs: int = 8,
        **params,
    ):
        super().__init__(**params)
        self.laplace = float(laplace)
        self.min_delta = float(min_delta)
        self.max_silence_hazard = float(max_silence_hazard)
        self.null_pe_floor = float(null_pe_floor)
        self.null_pe_span = float(null_pe_span)
        self.null_err_beta = float(null_err_beta)
        self.null_rho_gain = float(null_rho_gain)
        self.fe_cert_slack = float(fe_cert_slack)
        self.use_correlation_discount = bool(use_correlation_discount)
        self.force_all_positive_null = bool(force_all_positive_null)
        self.source_forget = float(source_forget)
        self.source_share = float(source_share)
        self.source_shift_window = int(source_shift_window)
        self.source_shift_gap = float(source_shift_gap)
        self.source_shift_discount = float(source_shift_discount)
        self.source_shift_long_beta = float(source_shift_long_beta)
        self.use_source_redundancy = bool(use_source_redundancy)
        self.source_redundant_agree = float(source_redundant_agree)
        self.source_redundant_min_pairs = int(source_redundant_min_pairs)
        if not (0.0 < self.source_forget <= 1.0):
            raise ValueError("source_forget must be in (0, 1]")
        if not (0.0 <= self.source_share <= 1.0):
            raise ValueError("source_share must be in [0, 1]")
        if self.source_shift_window < 0:
            raise ValueError("source_shift_window must be >= 0")
        if not (0.0 < self.source_shift_discount <= 1.0):
            raise ValueError("source_shift_discount must be in (0, 1]")

        # Likelihood tables: counts of (source said vote | truth).
        self.src_vote_up = defaultdict(lambda: self.laplace)
        self.src_vote_down = defaultdict(lambda: self.laplace)
        # Global backoff (pooled over sources) for sparse publishers.
        self.global_vote_up = {0: self.laplace, 1: self.laplace}
        self.global_vote_down = {0: self.laplace, 1: self.laplace}

        # Per-source recent errors for shift detection.
        self.src_recent_err = defaultdict(list)
        self.src_long_err = defaultdict(lambda: 0.5)
        self.source_shift_events = 0

        # Observable pairwise agreement for copy-skipping.
        self.pair_agree = defaultdict(float)
        self.pair_both = defaultdict(float)
        self.source_redundant_skips = 0

        # Null-channel precision: PE EWMA under emptiness / non-diagnostic
        # clouds. High PE ⇒ continuation hypothesis failing ⇒ anti-prior mix.
        # Start at 0.5 (same cold start as sealed silence-escape PE).
        self.null_pe = defaultdict(lambda: 0.5)
        self.belief_hist = defaultdict(list)

        self.silence_events = 0
        self.null_diagnostic_events = 0
        self.fe_certificates = 0
        self.source_backoff = 8.0

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
        return effective_count / len(reports)

    @staticmethod
    def _pair_key(left, right):
        return (left, right) if left < right else (right, left)

    def _record_source_pairs(self, reports) -> None:
        if not self.use_source_redundancy or len(reports) < 2:
            return
        entries = [(source, int(vote)) for source, _, vote in reports]
        for index, (source_a, vote_a) in enumerate(entries):
            for source_b, vote_b in entries[index + 1 :]:
                key = self._pair_key(source_a, source_b)
                self.pair_both[key] += 1.0
                if vote_a == vote_b:
                    self.pair_agree[key] += 1.0

    def _is_redundant_source(self, source, active_sources) -> bool:
        if not self.use_source_redundancy or not active_sources:
            return False
        for other in active_sources:
            key = self._pair_key(source, other)
            both = self.pair_both[key]
            if both < self.source_redundant_min_pairs:
                continue
            if self.pair_agree[key] / both >= self.source_redundant_agree:
                return True
        return False

    def _diversify_rows(self, rows):
        """Drop historical near-copies so certificate unread mass is honest."""
        if not self.use_source_redundancy:
            return rows
        diverse = []
        active_sources = []
        for row in rows:
            source = row[2]
            if self._is_redundant_source(source, active_sources):
                self.source_redundant_skips += 1
                continue
            diverse.append(row)
            active_sources.append(source)
        return diverse

    def _prior_log_odds(self, key) -> float:
        return (
            self.wf * (self.cf[(key, 1)] - self.cf[(key, 0)])
            + self.ws * (self.cs[(key, 1)] - self.cs[(key, 0)])
        ) / max(self.temp, EPS)

    def _source_counts(self, source, vote: int) -> tuple[float, float, float, float]:
        # Touch both votes so Laplace prior is symmetric for new sources.
        up_v = self.src_vote_up[(source, vote)]
        up_o = self.src_vote_up[(source, 1 - vote)]
        down_v = self.src_vote_down[(source, vote)]
        down_o = self.src_vote_down[(source, 1 - vote)]
        return up_v, up_o, down_v, down_o

    def _report_delta(self, source, vote: int) -> float:
        """Evidence log-odds for *up* from observing this vote.

        Source LR backed off toward a global pooled LR so sparse publishers
        are not stuck at Δ≈0 forever.
        """
        vote = int(vote)
        up_v, up_o, down_v, down_o = self._source_counts(source, vote)
        p_v_up = up_v / max(EPS, up_v + up_o)
        p_v_down = down_v / max(EPS, down_v + down_o)
        source_delta = math.log(max(EPS, p_v_up)) - math.log(max(EPS, p_v_down))

        g_up_v = self.global_vote_up[vote]
        g_up_o = self.global_vote_up[1 - vote]
        g_down_v = self.global_vote_down[vote]
        g_down_o = self.global_vote_down[1 - vote]
        g_p_up = g_up_v / max(EPS, g_up_v + g_up_o)
        g_p_down = g_down_v / max(EPS, g_down_v + g_down_o)
        global_delta = math.log(max(EPS, g_p_up)) - math.log(max(EPS, g_p_down))

        n_source = up_v + up_o + down_v + down_o - 4.0 * self.laplace
        weight = max(0.0, n_source) / (max(0.0, n_source) + self.source_backoff)
        return weight * source_delta + (1.0 - weight) * global_delta

    def _max_raw_abs_delta(self, reports) -> float:
        """Largest per-source |Δ| before agreement/correlation discount.

        The null gate (`min_delta`) asks whether any single source is
        informative. That question must not be answered with a value that has
        already been divided by coalition size — otherwise large agreeing
        batches falsely look empty and fall into the anti-prior null channel.
        Correlation discount still applies when *summing* evidence below.
        """
        if not reports:
            return 0.0
        return max(
            abs(self._report_delta(source, int(vote))) for source, _, vote in reports
        )

    def _evidence_rows(self, reports):
        """Raw per-source rows for recruitment / certificate.

        Agreement discount must NOT shrink rows before the certificate stops —
        otherwise a large copy-coalition is certified after reading a few
        shrunken scraps and keeps only a fraction of one source's evidence.
        Discount is applied once to the active sum after recruitment.
        """
        rows = []
        for source, context, vote in reports:
            delta = self._report_delta(source, int(vote))
            rows.append((abs(delta), delta, source, context, int(vote)))
        rows.sort(key=lambda row: row[0], reverse=True)
        self.preview_ops += self.header_cost * len(rows)
        return rows

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

    def _track_belief(self, key) -> None:
        fast = self.cf[(key, 1)] - self.cf[(key, 0)]
        hist = self.belief_hist[key]
        hist.append(fast)
        if len(hist) > 8:
            del hist[0]

    def _null_hazard(self, key) -> float:
        pe = self.null_pe[key]
        hazard = max(0.0, (pe - self.null_pe_floor) / max(EPS, self.null_pe_span))
        if self.null_rho_gain:
            hazard += self.null_rho_gain * self._rho(key)
        return float(min(self.max_silence_hazard, hazard))

    def _silence_posterior(self, key, prior_p: float) -> tuple[float, float]:
        # Precision that the continuation hypothesis is failing under null
        # sensation — mix toward the rival (anti-prior). Friston form of the
        # sealed silence-escape law (PE + stickiness), inside the null organ.
        hazard = self._null_hazard(key)
        probability = (1.0 - hazard) * prior_p + hazard * (1.0 - prior_p)
        return probability, hazard

    def _is_null_batch(self, reports, max_delta: float) -> bool:
        if not reports:
            return True
        if self.force_all_positive_null and all(vote == 1 for _, _, vote in reports):
            return True
        return max_delta < self.min_delta

    def predict(self, key, reports, t):
        prior_lo = self._prior_log_odds(key)
        prior_p = _sigmoid(prior_lo)

        rows = self._evidence_rows(reports) if reports else []
        rows = self._diversify_rows(rows)[: self.max_k]
        # Gate on raw per-source strength.
        max_delta = self._max_raw_abs_delta(reports)
        batch_scale = (
            self._correlation_scale(reports) if self.use_correlation_discount else 1.0
        )
        max_delta_scaled = max_delta * batch_scale

        if self._is_null_batch(reports, max_delta):
            probability, hazard = self._silence_posterior(key, prior_p)
            if not reports:
                self.silence_events += 1
                stop_reason = "silence_channel"
                self.infer_reads += 1.0
            else:
                self.null_diagnostic_events += 1
                stop_reason = "null_diagnostic"
                self.infer_reads += self.header_cost * len(reports) + 1.0
            self._track_belief(key)
            return probability, {
                "key": key,
                "p": probability,
                "prior_p": prior_p,
                "prior_lo": prior_lo,
                "evidence_lo": 0.0,
                "active": [],
                "used": 0,
                "contradiction": 0.0,
                "hazard": hazard,
                "required": 0,
                "certificate_shift": 0.0,
                "stop_reason": stop_reason,
                "shadow_mass": (0.0, 0.0),
                "max_delta": max_delta,
                "max_delta_scaled": max_delta_scaled,
                "correlation_scale": batch_scale,
                "null_pe": self.null_pe[key],
            }

        # Certificate / recruitment in raw |Δ| space on diversified rows.
        count = len(rows)
        suffix_abs = [0.0] * (count + 1)
        for index in range(count - 1, -1, -1):
            suffix_abs[index] = suffix_abs[index + 1] + rows[index][0]

        active = []
        raw_evidence_lo = 0.0
        stop_reason = "budget"
        for index, row in enumerate(rows):
            abs_delta, delta, source, context, vote = row
            active.append(row)
            raw_evidence_lo += delta
            self.activation_ops += 1.0
            self.ops += 2
            posterior_lo = prior_lo + raw_evidence_lo
            unread = suffix_abs[index + 1]
            # Certificate: unread discrimination cannot flip the commitment.
            if len(active) >= self.min_k and abs(posterior_lo) > unread + self.fe_cert_slack:
                stop_reason = "free_energy_certified"
                self.fe_certificates += 1
                break

        # Shrink the *active* sum by effective coalition size among actives.
        # Using len(active) (not the full batch) keeps one source-worth of
        # evidence when copies are certified early.
        active_reports = [
            (source, context, vote) for _abs, _delta, source, context, vote in active
        ]
        active_scale = (
            self._correlation_scale(active_reports)
            if self.use_correlation_discount and active_reports
            else 1.0
        )
        evidence_lo = raw_evidence_lo * active_scale
        posterior_lo = prior_lo + evidence_lo
        probability = _sigmoid(posterior_lo)
        pos = sum(delta for _, delta, _, _, _ in active if delta >= 0)
        neg = sum(-delta for _, delta, _, _, _ in active if delta < 0)
        contradiction = min(pos, neg) / (max(pos, neg) + EPS)
        self.infer_reads += self.header_cost * len(reports) + len(active)
        self._track_belief(key)
        # Leftover diversified rows after early-stop (ESSC shadow input).
        unread_rows = rows[len(active) :]

        return probability, {
            "key": key,
            "p": probability,
            "prior_p": prior_p,
            "prior_lo": prior_lo,
            "evidence_lo": evidence_lo,
            "raw_evidence_lo": raw_evidence_lo,
            "active": [
                (source, context, vote, (key, vote), abs_delta)
                for abs_delta, delta, source, context, vote in active
            ],
            "used": len(active),
            "contradiction": contradiction,
            "hazard": 0.0,
            "required": self.min_k,
            "certificate_shift": suffix_abs[len(active)] if active else 0.0,
            "stop_reason": stop_reason,
            "shadow_mass": (0.0, 0.0),
            "max_delta": max_delta,
            "max_delta_scaled": max_delta * active_scale,
            "correlation_scale": active_scale,
            "unread_mass": suffix_abs[len(active)] if active else 0.0,
            "unread_rows": [
                (abs_delta, delta, source, context, vote)
                for abs_delta, delta, source, context, vote in unread_rows
            ],
        }

    def feedback(self, event):
        key = event["key"]
        truth = int(event["truth"])
        reports = event.get("reports", [])
        trace = event["trace"]
        null_channel = trace.get("stop_reason") in {
            "silence_channel",
            "null_diagnostic",
        }

        if null_channel or not reports:
            # Precision update on the null channel from posterior error
            # (same target as sealed silence-escape PE EWMA).
            probability = float(trace["p"])
            self.null_pe[key] = (
                (1.0 - self.null_err_beta) * self.null_pe[key]
                + self.null_err_beta * abs(truth - probability)
            )

        if reports:
            self._record_source_pairs(reports)
            self._update_source_likelihoods(reports, truth)

        # Prior update only — evidence tables above are the likelihood organ.
        probability = float(trace["p"])
        err = float(truth) - probability
        anchor_step = self.lr * self.anchor * (0.25 + abs(err))
        true_key = (key, truth)
        false_key = (key, 1 - truth)
        self.cf[true_key] = self.fd * self.cf[true_key] + anchor_step
        self.cf[false_key] = self.fd * self.cf[false_key] - anchor_step
        self.cs[true_key] = self.sd * self.cs[true_key] + 0.08 * anchor_step
        self.cs[false_key] = self.sd * self.cs[false_key] - 0.08 * anchor_step
        self.up += 4
        if hasattr(self, "learn_writes"):
            self.learn_writes += 4.0
        self.last_fb[key] = event.get("time", self.last_fb[key])

    def _scale_source_counts(self, source, factor: float) -> None:
        for vote_side in (0, 1):
            self.src_vote_up[(source, vote_side)] *= factor
            self.src_vote_down[(source, vote_side)] *= factor

    def _mix_source_toward_prior(self, source) -> None:
        """Never-zero floor: keep a small escape hatch in both directions."""
        share = self.source_share
        if share <= 0.0:
            return
        keep = 1.0 - share
        prior = self.laplace
        for vote_side in (0, 1):
            self.src_vote_up[(source, vote_side)] = (
                keep * self.src_vote_up[(source, vote_side)] + share * prior
            )
            self.src_vote_down[(source, vote_side)] = (
                keep * self.src_vote_down[(source, vote_side)] + share * prior
            )

    def _maybe_shift_reset(self, source, wrong: float) -> None:
        """Hard-discount history when recent errors look like a new persona."""
        window = self.source_shift_window
        if window <= 0:
            return
        recent = self.src_recent_err[source]
        recent.append(float(wrong))
        if len(recent) > window:
            del recent[0 : len(recent) - window]

        long_err = float(self.src_long_err[source])
        if len(recent) >= window:
            recent_err = sum(recent) / len(recent)
            # Compare against the long-run rate *before* folding in this point.
            if recent_err - long_err >= self.source_shift_gap:
                self._scale_source_counts(source, self.source_shift_discount)
                self.source_shift_events += 1
                # Restart the short window so one cluster does not re-fire.
                self.src_recent_err[source] = []
                long_err = recent_err

        beta = self.source_shift_long_beta
        self.src_long_err[source] = (1.0 - beta) * long_err + beta * float(wrong)

    def _update_source_likelihoods(self, reports, truth: int) -> None:
        """Regime-aware source trust: fade → shift reset → count → floor mix."""
        truth = int(truth)
        # Global table fades once per released packet (not once per source).
        if self.source_forget < 1.0:
            fade = self.source_forget
            for vote_side in (0, 1):
                self.global_vote_up[vote_side] *= fade
                self.global_vote_down[vote_side] *= fade

        faded = set()
        for source, _context, vote in reports:
            vote = int(vote)
            wrong = float(vote != truth)
            if source not in faded:
                if self.source_forget < 1.0:
                    self._scale_source_counts(source, self.source_forget)
                faded.add(source)
            self._maybe_shift_reset(source, wrong)

            if truth == 1:
                self.src_vote_up[(source, vote)] += 1.0
                self.global_vote_up[vote] += 1.0
            else:
                self.src_vote_down[(source, vote)] += 1.0
                self.global_vote_down[vote] += 1.0

            self._mix_source_toward_prior(source)

        if self.source_share > 0.0:
            keep = 1.0 - self.source_share
            prior = self.laplace
            for vote_side in (0, 1):
                self.global_vote_up[vote_side] = (
                    keep * self.global_vote_up[vote_side] + self.source_share * prior
                )
                self.global_vote_down[vote_side] = (
                    keep * self.global_vote_down[vote_side]
                    + self.source_share * prior
                )

    def stats(self):
        stats = super().stats()
        stats.update(
            {
                "silence_events": self.silence_events,
                "null_diagnostic_events": self.null_diagnostic_events,
                "fe_certificates": self.fe_certificates,
                "source_shift_events": self.source_shift_events,
                "source_redundant_skips": self.source_redundant_skips,
                "source_forget": self.source_forget,
                "source_share": self.source_share,
                "mean_null_pe": (
                    sum(self.null_pe.values()) / max(1, len(self.null_pe))
                ),
                "likelihood_sources": len(
                    {source for source, _vote in self.src_vote_up}
                    | {source for source, _vote in self.src_vote_down}
                ),
            }
        )
        return stats


class AwareCoalitionCellular(ActiveCoalitionCellular):
    """ACI + Mnemosheath — awareness that learns under emptiness.

    Keeps every ACI law. Agreement bits learn cheerleader vs consensus.
    Silence bits use a two-phase curriculum: prime on empty predict, complete
    when truth arrives (change vs stay). No separate tutor stack.

    Optional ESSC (ESS-Shadow Sheath Completion): after ACI early-stop, unread
    diversified mass re-enters ``p`` as an ESS-weighted shadow under a sheath
    credit gate — including against majority. Default **off** (sealed cells).
    Christmas-bow majority blend is disabled when ESSC is on (crush path).
    """

    name = "aware_coalition_cellular"

    def __init__(self, **params):
        params = dict(params)
        params["force_all_positive_null"] = False
        # ESSC knobs — opt-in; defaults preserve sealed Aware behavior.
        self.essc_enabled = bool(params.pop("essc_enabled", False))
        self.essc_disable_christmas_bow = bool(
            params.pop("essc_disable_christmas_bow", True)
        )
        self.essc_credit_init = float(params.pop("essc_credit_init", 0.20))
        self.essc_max_credit = float(params.pop("essc_max_credit", 0.50))
        self.essc_lo_cap = float(params.pop("essc_lo_cap", 1.25))
        self.essc_credit_lr = float(params.pop("essc_credit_lr", 0.08))
        self.essc_disagree_emphasis = float(
            params.pop("essc_disagree_emphasis", 2.5)
        )
        if not (0.0 <= self.essc_credit_init <= self.essc_max_credit):
            raise ValueError("essc_credit_init must be in [0, essc_max_credit]")
        if self.essc_max_credit <= 0.0:
            raise ValueError("essc_max_credit must be > 0")
        super().__init__(**params)
        from .awareness import Mnemosheath

        self.sheath = Mnemosheath()
        self.awareness_evidence_routes = 0
        self.awareness_null_routes = 0
        self.time_since_evidence = defaultdict(int)
        self.last_truth = {}
        self.last_was_flip = defaultdict(bool)
        self.essc_credit = float(self.essc_credit_init)
        self.essc_applications = 0
        self.essc_oppose_majority = 0
        self.essc_gate_updates = 0

    def _batch_cues(self, key, reports, max_delta: float, prior_p: float):
        return self.sheath.sense_cues(
            reports,
            max_delta=max_delta,
            min_delta=self.min_delta,
            null_pe=float(self.null_pe[key]),
            prior_p=prior_p,
            time_since_evidence=int(self.time_since_evidence[key]),
            prev_truth=self.last_truth.get(key),
            last_was_flip=bool(self.last_was_flip[key]),
        )

    def _is_null_batch(self, reports, max_delta: float) -> bool:
        if not reports:
            return True
        if max_delta < self.min_delta:
            return True
        votes = [int(vote) for _, _, vote in reports]
        unanimous = len(set(votes)) == 1
        if not unanimous:
            return False
        cues = getattr(self, "_pending_cues", None)
        if cues is None:
            cues = self.sheath.sense_cues(
                reports,
                max_delta=max_delta,
                min_delta=self.min_delta,
                null_pe=0.5,
                prior_p=0.5,
            )
        if self.sheath.agreement_is_evidence(cues):
            self.awareness_evidence_routes += 1
            return False
        self.awareness_null_routes += 1
        return True

    def _null_hazard(self, key) -> float:
        base = super()._null_hazard(key)
        return self.sheath.mix_null_hazard(base, self.max_silence_hazard)

    def _apply_awareness_sharpness(
        self, probability: float, reports, cues: dict, stop_reason: str
    ) -> tuple[float, dict]:
        """Put Mnemosheath's learned courage into the emitted probability.

        Bug/gap: ``vote_context`` was computed and traced but never entered
        ``p``. On clear diagnostic agreement that made Aware timid versus a
        simple vote — the weather near-miss. Null/silence paths stay untouched.
        """
        meta = {
            "awareness_sharpness_applied": False,
            "p_before_awareness": float(probability),
            "agreement_blend_weight": 0.0,
            "signed_context_lo": 0.0,
        }
        if (
            not reports
            or stop_reason in {"silence_channel", "null_diagnostic"}
            or cues is None
        ):
            return float(probability), meta

        votes = [int(vote) for _, _, vote in reports]
        if not votes or not self.sheath.agreement_is_evidence(cues):
            return float(probability), meta
        majority = 1 if sum(votes) >= (len(votes) / 2) else 0
        vote_mean = sum(votes) / len(votes)
        aci_side = 1 if float(probability) >= 0.5 else 0
        diagnosticity = float(self.sheath.diagnosticity(cues))
        # Only sharpen when the sheath trusts agreement AND ACI already
        # picked the crowd's side — bravery without flip-chasing.
        if aci_side != majority:
            meta.update(
                {
                    "awareness_sharpness_applied": False,
                    "diagnosticity": diagnosticity,
                    "sharpen_aligned_with_majority": False,
                }
            )
            return float(probability), meta
        # Mild courage: move partway toward the vote rate. Keep the step
        # bounded so regime flips (where agreement can be briefly wrong)
        # are not over-chased.
        blend = min(0.40, max(0.0, diagnosticity - 0.5))
        signed_context = float(self.sheath.context_log_odds) * (
            1.0 if majority == 1 else -1.0
        )
        # Cap context add so sheath confidence cannot dominate evidence.
        signed_context = max(-0.75, min(0.75, signed_context))
        base_lo = _logit(float(probability))
        sharpened = _sigmoid(base_lo + signed_context)
        sharpened = (1.0 - blend) * sharpened + blend * vote_mean
        meta.update(
            {
                "awareness_sharpness_applied": True,
                "agreement_blend_weight": blend,
                "signed_context_lo": signed_context,
                "diagnosticity": diagnosticity,
                "sharpen_aligned_with_majority": True,
            }
        )
        return float(min(1.0 - EPS, max(EPS, sharpened))), meta

    def _essc_block_collapse(self, unread_rows: list) -> list[list]:
        """Soft-collapse historical near-copies; independent unread stay separate."""
        blocks: list[list] = []
        for row in unread_rows:
            placed = False
            source = row[2]
            for block in blocks:
                members = [member[2] for member in block]
                if self._is_redundant_source(source, members):
                    block.append(row)
                    placed = True
                    break
            if not placed:
                blocks.append([row])
        return blocks

    def _essc_shadow_log_odds(self, unread_rows: list) -> tuple[float, float, int]:
        """ESS-weighted shadow log-odds from unread blocks (one ESS unit each)."""
        if not unread_rows:
            return 0.0, 0.0, 0
        blocks = self._essc_block_collapse(unread_rows)
        shadow_lo = 0.0
        total_ess = 0.0
        for block in blocks:
            # Collapsed block = one effective ballot (mean Δ, ESS = 1).
            mean_delta = sum(float(row[1]) for row in block) / len(block)
            ess = 1.0
            shadow_lo += mean_delta * ess
            total_ess += ess
        return float(shadow_lo), float(total_ess), len(blocks)

    def _apply_essc_shadow(
        self, probability: float, reports, cues: dict, trace: dict
    ) -> tuple[float, dict]:
        """Sheath-gated shadow completion into ``p`` (may oppose majority)."""
        meta = {
            "essc_applied": False,
            "p_before_essc": float(probability),
            "essc_shadow_lo": 0.0,
            "essc_ess": 0.0,
            "essc_unread_n": 0,
            "essc_blocks": 0,
            "essc_credit": float(self.essc_credit),
            "essc_gate": 0.0,
            "essc_opposes_majority": False,
            "essc_opposes_active": False,
            "christmas_bow_off": True,
        }
        stop_reason = trace.get("stop_reason", "")
        if (
            not self.essc_enabled
            or not reports
            or stop_reason in {"silence_channel", "null_diagnostic"}
        ):
            meta["christmas_bow_off"] = bool(
                self.essc_enabled and self.essc_disable_christmas_bow
            )
            return float(probability), meta

        # Use ACI leftover rows only — never re-diversify (would double-count
        # skips / preview ops) and never densify the active set.
        unread = list(trace.get("unread_rows") or [])
        shadow_lo, total_ess, n_blocks = self._essc_shadow_log_odds(unread)
        meta.update(
            {
                "essc_shadow_lo": float(shadow_lo),
                "essc_ess": float(total_ess),
                "essc_unread_n": len(unread),
                "essc_blocks": int(n_blocks),
            }
        )
        if abs(shadow_lo) <= EPS or total_ess <= EPS:
            return float(probability), meta

        diagnosticity = (
            float(self.sheath.diagnosticity(cues)) if cues is not None else 0.5
        )
        # Sheath scales the learned credit; never blends toward majority vote.
        gate = float(self.essc_credit) * (0.5 + 0.5 * diagnosticity)
        gate = max(0.0, min(self.essc_max_credit, gate))
        signed = max(-self.essc_lo_cap, min(self.essc_lo_cap, gate * shadow_lo))
        completed = _sigmoid(_logit(float(probability)) + signed)

        active_side = 1 if float(probability) >= 0.5 else 0
        shadow_side = 1 if shadow_lo > 0.0 else 0
        votes = [int(vote) for _, _, vote in reports]
        majority = 1 if sum(votes) >= (len(votes) / 2) else 0
        opposes_majority = shadow_side != majority
        opposes_active = shadow_side != active_side
        if opposes_majority:
            self.essc_oppose_majority += 1
        self.essc_applications += 1
        meta.update(
            {
                "essc_applied": True,
                "essc_gate": float(gate),
                "essc_signed_lo": float(signed),
                "essc_opposes_majority": bool(opposes_majority),
                "essc_opposes_active": bool(opposes_active),
                "essc_shadow_side": int(shadow_side),
                "essc_active_side": int(active_side),
                "diagnosticity": diagnosticity,
            }
        )
        # Selective stop held: do not inflate ``used`` — unread is shadow only.
        return float(min(1.0 - EPS, max(EPS, completed))), meta

    def _essc_update_credit(self, trace: dict, truth: int) -> None:
        """Delay-corrected merit on the credit gate; emphasize disagreement."""
        essc = (trace.get("awareness") or {}).get("essc") or {}
        if not essc.get("essc_applied"):
            return
        p_before = float(essc.get("p_before_essc", trace.get("p", 0.5)))
        p_after = float(trace.get("p", p_before))
        err_before = (p_before - truth) ** 2
        err_after = (p_after - truth) ** 2
        disagree = bool(
            essc.get("essc_opposes_majority") or essc.get("essc_opposes_active")
        )
        lr = self.essc_credit_lr * (
            self.essc_disagree_emphasis if disagree else 0.25
        )
        if err_after + 1e-12 < err_before:
            self.essc_credit += lr * (self.essc_max_credit - self.essc_credit)
        else:
            self.essc_credit -= lr * self.essc_credit
        self.essc_credit = float(
            max(0.0, min(self.essc_max_credit, self.essc_credit))
        )
        self.essc_gate_updates += 1

    def predict(self, key, reports, t):
        prior_lo = self._prior_log_odds(key)
        prior_p = _sigmoid(prior_lo)
        # Cues / low_delta must see raw per-source strength, not the
        # coalition-discounted mass used when summing agreeing votes.
        max_delta = self._max_raw_abs_delta(reports)
        cues = self._batch_cues(key, reports, max_delta, prior_p)
        self._pending_cues = cues
        # Phase 1: emptiness is a sensory event — stash lesson before truth.
        self.sheath.prime_absence(
            key,
            cues,
            prev_truth=self.last_truth.get(key),
            time_since_evidence=int(self.time_since_evidence[key]),
        )
        self.sheath.vote_context(cues)
        if reports:
            self.time_since_evidence[key] = 0
        else:
            self.time_since_evidence[key] = int(self.time_since_evidence[key]) + 1
        probability, trace = super().predict(key, reports, t)
        bow_blocked = self.essc_enabled and self.essc_disable_christmas_bow
        if bow_blocked:
            sharp_meta = {
                "awareness_sharpness_applied": False,
                "p_before_awareness": float(probability),
                "agreement_blend_weight": 0.0,
                "signed_context_lo": 0.0,
                "christmas_bow_off": True,
            }
        else:
            probability, sharp_meta = self._apply_awareness_sharpness(
                probability, reports, cues, trace.get("stop_reason", "")
            )
        essc_meta = {
            "essc_applied": False,
            "essc_enabled": bool(self.essc_enabled),
            "christmas_bow_off": bool(bow_blocked),
        }
        if self.essc_enabled:
            probability, essc_meta = self._apply_essc_shadow(
                probability, reports, cues, trace
            )
        trace = dict(trace)
        # Real shadow mass for traces (was a (0,0) stub on the crush path).
        shadow_lo = float(essc_meta.get("essc_shadow_lo", 0.0))
        if shadow_lo > 0.0:
            trace["shadow_mass"] = (0.0, abs(shadow_lo))
        elif shadow_lo < 0.0:
            trace["shadow_mass"] = (abs(shadow_lo), 0.0)
        trace["p"] = probability
        trace["awareness"] = {
            "cues": {name: bool(flag) for name, flag in cues.items() if flag},
            "diagnosticity": self.sheath.diagnosticity(cues),
            "absence_change_rate": self.sheath.absence_change_rate(cues),
            "context_log_odds": self.sheath.context_log_odds,
            "bits": self.sheath.bit_count,
            "stage_cap": self.sheath.stage_cap,
            "empty_lessons": self.sheath.empty_lessons,
            **sharp_meta,
            "essc": essc_meta,
        }
        trace["awareness_cues"] = cues
        if reports:
            votes = [int(vote) for _, _, vote in reports]
            trace["majority_vote"] = (
                int(sum(votes) >= (len(votes) / 2)) if votes else None
            )
        else:
            trace["majority_vote"] = None
        return probability, trace

    def feedback(self, event):
        key = event["key"]
        truth = int(event["truth"])
        trace = event["trace"]
        cues = trace.get("awareness_cues")
        if cues is not None:
            self.sheath.feedback(
                cues,
                majority_vote=trace.get("majority_vote"),
                truth=truth,
                key=key,
            )
        if self.essc_enabled:
            self._essc_update_credit(trace, truth)
        prev = self.last_truth.get(key)
        self.last_was_flip[key] = prev is not None and int(prev) != truth
        self.last_truth[key] = truth
        super().feedback(event)

    def stats(self):
        stats = super().stats()
        stats.update(
            {
                "awareness": self.sheath.stats(),
                "awareness_evidence_routes": self.awareness_evidence_routes,
                "awareness_null_routes": self.awareness_null_routes,
                "essc_enabled": self.essc_enabled,
                "essc_credit": self.essc_credit,
                "essc_applications": self.essc_applications,
                "essc_oppose_majority": self.essc_oppose_majority,
                "essc_gate_updates": self.essc_gate_updates,
            }
        )
        return stats

