"""Mnemosheath — maturing context-awareness + learning under emptiness.

Council #1 built agreement diagnosticity. Council #2 (empty-world) adds a
two-phase silence curriculum inside the SAME organ (no separate tutor class —
anti-theft Agent 5 rejected VacancyTutor as a parallel stack).

Phase 1 (predict, no truth): when empty/low_delta fires, record a pending
lesson {cues, prev_truth, time_since_evidence}. Emptiness is a sensory channel.

Phase 2 (feedback): when majority_vote is None, teach silence-family bits
whether emptiness preceded CHANGE vs STAY. That is the lesson labels allow.

Still not a neural net / pymdp / RAG. Prior never enters report Δ.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

EPS = 1e-9
STAGE_CAPS = (1, 2, 4, 12)

# Silence-family cues — meanings of absence (Tacitheca curriculum).
SILENCE_CUES = frozenset(
    {
        "empty",
        "low_delta",
        "high_pe",
        "long_vacancy",  # time_since_evidence high
        "fresh_vacancy",
        "empty_after_flip",  # previous outcome was a change
        "empty_after_stay",
    }
)

CUE_ORDER = (
    "unanimous",
    "unanimous_pos",
    "unanimous_neg",
    "high_agree",
    "low_delta",
    "high_pe",
    "mixed",
    "empty",
    "agree_with_prior_side",
    "against_prior_side",
    "wide_margin",
    "thin_margin",
    "long_vacancy",
    "fresh_vacancy",
    "empty_after_flip",
    "empty_after_stay",
)


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(-40.0, min(40.0, value))))


@dataclass
class DistinctionBit:
    """One binary distinction the sheath can hold about the sensory field."""

    name: str
    cue: str
    hit: float = 1.0
    miss: float = 1.0
    persistence: int = 0
    age: int = 0
    # Empty curriculum: did this silence cue precede change?
    change: float = 1.0
    stay: float = 1.0
    primed: int = 0  # phase-1 sightings before truth

    def diagnosticity(self) -> float:
        return self.hit / max(EPS, self.hit + self.miss)

    def change_rate(self) -> float:
        return self.change / max(EPS, self.change + self.stay)

    def merit(self) -> float:
        if self.cue in SILENCE_CUES:
            return abs(self.change_rate() - 0.5)
        return abs(self.diagnosticity() - 0.5)

    def update(self, majority_correct: bool) -> None:
        self.age += 1
        if majority_correct:
            self.hit += 1.0
            self.persistence += 1
        else:
            self.miss += 1.0
            self.persistence = 0

    def update_absence(self, preceded_change: bool) -> None:
        """Phase-2 empty lesson: emptiness preceded change vs stay."""
        self.age += 1
        if preceded_change:
            self.change += 1.0
        else:
            self.stay += 1.0
        # Vacancy lessons always earn dwell toward mitosis; merit carries meaning.
        self.persistence += 1


@dataclass
class Mnemosheath:
    """Maturing sheath: agreement bits + silence bits (one organ)."""

    bits: list[DistinctionBit] = field(default_factory=list)
    stage_index: int = 0
    dwell: int = 8
    split_merit: float = 0.12
    evidence_threshold: float = 0.62
    context_log_odds: float = 0.0
    births: int = 0
    updates: int = 0
    empty_lessons: int = 0
    empty_primes: int = 0
    pending: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.bits:
            # Twin pulse at birth: agreement sense + emptiness sense.
            self.bits = [
                DistinctionBit(name="pulse.unanimous", cue="unanimous"),
                DistinctionBit(name="pulse.empty", cue="empty"),
            ]
            # Stage cap still 1 for mitosis pressure on the dominant lineage;
            # both seed bits exist so emptiness is never "learned from nothing."
            self.stage_index = 0

    @property
    def bit_count(self) -> int:
        return len(self.bits)

    @property
    def stage_cap(self) -> int:
        return STAGE_CAPS[min(self.stage_index, len(STAGE_CAPS) - 1)]

    def sense_cues(
        self,
        reports: list,
        max_delta: float,
        min_delta: float,
        null_pe: float,
        prior_p: float,
        *,
        time_since_evidence: int = 0,
        prev_truth: int | None = None,
        last_was_flip: bool = False,
    ) -> dict[str, bool]:
        votes = [int(vote) for _, _, vote in reports]
        n = len(votes)
        mean = (sum(votes) / n) if n else 0.5
        unanimous = n > 0 and len(set(votes)) == 1
        prior_side = 1 if prior_p >= 0.5 else 0
        majority = 1 if mean >= 0.5 else 0
        empty = n == 0
        return {
            "empty": empty,
            "unanimous": unanimous,
            "unanimous_pos": n > 0 and all(v == 1 for v in votes),
            "unanimous_neg": n > 0 and all(v == 0 for v in votes),
            "high_agree": n > 0 and (mean >= 0.8 or mean <= 0.2),
            "low_delta": (not empty) and max_delta < min_delta,
            "high_pe": null_pe > 0.55,
            "mixed": n > 0 and len(set(votes)) > 1,
            "agree_with_prior_side": n > 0 and majority == prior_side,
            "against_prior_side": n > 0 and majority != prior_side,
            "wide_margin": n > 0 and abs(mean - 0.5) >= 0.35,
            "thin_margin": n > 0 and abs(mean - 0.5) < 0.20,
            "long_vacancy": empty and time_since_evidence >= 3,
            "fresh_vacancy": empty and time_since_evidence <= 1,
            "empty_after_flip": empty and last_was_flip,
            "empty_after_stay": empty and (prev_truth is not None) and (not last_was_flip),
        }

    def fired_bits(self, cues: dict[str, bool]) -> list[DistinctionBit]:
        return [bit for bit in self.bits if cues.get(bit.cue, False)]

    def diagnosticity(self, cues: dict[str, bool]) -> float:
        fired = [bit for bit in self.fired_bits(cues) if bit.cue not in SILENCE_CUES]
        if not fired:
            return 0.5
        weights = [1.0 + bit.persistence for bit in fired]
        values = [bit.diagnosticity() for bit in fired]
        return float(sum(w * v for w, v in zip(weights, values)) / sum(weights))

    def absence_change_rate(self, cues: dict[str, bool]) -> float:
        fired = [bit for bit in self.fired_bits(cues) if bit.cue in SILENCE_CUES]
        if not fired:
            return 0.5
        weights = [1.0 + bit.persistence for bit in fired]
        values = [bit.change_rate() for bit in fired]
        return float(sum(w * v for w, v in zip(weights, values)) / sum(weights))

    def agreement_is_evidence(self, cues: dict[str, bool]) -> bool:
        return self.diagnosticity(cues) >= self.evidence_threshold

    def vote_context(self, cues: dict[str, bool]) -> float:
        total = 0.0
        for bit in self.fired_bits(cues):
            if bit.cue in SILENCE_CUES:
                # High change-rate under silence → raise urgency (negative trust)
                center = 0.5 - bit.change_rate()
            else:
                center = bit.diagnosticity() - 0.5
            total += center * (1.0 + 0.1 * bit.persistence)
        self.context_log_odds = max(-3.0, min(3.0, total))
        return self.context_log_odds

    def mix_null_hazard(self, base_hazard: float, max_hazard: float) -> float:
        gate = _sigmoid(self.context_log_odds)
        tuned = (1.0 - gate) * max_hazard + gate * (0.15 * max_hazard)
        return float(min(max_hazard, 0.5 * base_hazard + 0.5 * tuned))

    def prime_absence(
        self,
        key,
        cues: dict[str, bool],
        *,
        prev_truth: int | None,
        time_since_evidence: int,
    ) -> None:
        """Phase 1: learn that emptiness happened — before truth exists."""
        if not (cues.get("empty") or cues.get("low_delta")):
            return
        for bit in self.fired_bits(cues):
            if bit.cue in SILENCE_CUES:
                bit.primed += 1
        self.pending[key] = {
            "cues": dict(cues),
            "prev_truth": prev_truth,
            "time_since_evidence": int(time_since_evidence),
        }
        self.empty_primes += 1

    def _next_cue_for_split(self, parent: DistinctionBit) -> str | None:
        owned = {bit.cue for bit in self.bits}
        family = {
            "unanimous": ("unanimous_pos", "unanimous_neg"),
            "unanimous_pos": ("wide_margin", "agree_with_prior_side"),
            "unanimous_neg": ("wide_margin", "against_prior_side"),
            "high_agree": ("wide_margin", "thin_margin"),
            "mixed": ("against_prior_side", "high_pe"),
            "empty": ("long_vacancy", "fresh_vacancy"),
            "long_vacancy": ("empty_after_flip", "empty_after_stay"),
            "fresh_vacancy": ("high_pe", "low_delta"),
            "low_delta": ("high_pe", "empty"),
        }
        for cue in family.get(parent.cue, ()):
            if cue not in owned:
                return cue
        for cue in CUE_ORDER:
            if cue not in owned:
                return cue
        return None

    def _maybe_birth(self) -> None:
        # Twin seeds (unanimous+empty) need stage 0→1 before further mitosis.
        if self.stage_index == 0 and len(self.bits) >= 2:
            mature = sum(
                1
                for bit in self.bits
                if bit.persistence >= self.dwell or bit.primed >= self.dwell
            )
            if mature >= 1:
                self.stage_index = 1
        cap = self.stage_cap
        if len(self.bits) >= cap:
            mature = sum(1 for bit in self.bits if bit.persistence >= self.dwell)
            if mature >= 1 and self.stage_index + 1 < len(STAGE_CAPS):
                self.stage_index += 1
                cap = self.stage_cap
            if len(self.bits) >= cap:
                return
        parent = max(
            self.bits,
            key=lambda bit: bit.persistence * (0.1 + bit.merit()) + 0.05 * bit.primed,
        )
        # Silence lineage may split from persistence alone once stage ≥ 1;
        # agreement lineage still needs merit distance from coin-flip.
        ready = parent.persistence >= self.dwell
        if parent.cue in SILENCE_CUES:
            ready = ready and (parent.merit() >= self.split_merit or parent.primed >= self.dwell)
        else:
            ready = ready and parent.merit() >= self.split_merit
        if not ready:
            return
        child_cue = self._next_cue_for_split(parent)
        if child_cue is None:
            return
        child = DistinctionBit(
            name=f"s{self.stage_index}.{child_cue}",
            cue=child_cue,
            hit=1.0 + 0.25 * parent.hit,
            miss=1.0 + 0.25 * parent.miss,
            change=1.0 + 0.25 * parent.change,
            stay=1.0 + 0.25 * parent.stay,
        )
        self.bits.append(child)
        parent.persistence = 0
        self.births += 1

    def feedback(
        self,
        cues: dict[str, bool],
        *,
        majority_vote: int | None,
        truth: int,
        key=None,
    ) -> None:
        # --- Phase 2 empty curriculum (no majority teacher) ---
        if majority_vote is None:
            lesson = self.pending.pop(key, None) if key is not None else None
            if lesson is None:
                # Still allow cue-tagged empty feedback if caller stashed cues.
                lesson_cues = cues
                prev = None
            else:
                lesson_cues = lesson["cues"]
                prev = lesson.get("prev_truth")
            if not (lesson_cues.get("empty") or lesson_cues.get("low_delta")):
                return
            preceded_change = prev is not None and int(truth) != int(prev)
            fired = [
                bit
                for bit in self.fired_bits(lesson_cues)
                if bit.cue in SILENCE_CUES
            ]
            if not fired:
                # Ensure empty pulse still learns.
                fired = [bit for bit in self.bits if bit.cue == "empty"]
            for bit in fired:
                bit.update_absence(preceded_change)
            self.updates += 1
            self.empty_lessons += 1
            self._maybe_birth()
            return

        # --- Agreement curriculum (existing) ---
        majority_correct = int(majority_vote) == int(truth)
        fired = [bit for bit in self.fired_bits(cues) if bit.cue not in SILENCE_CUES]
        if not fired:
            return
        for bit in fired:
            bit.update(majority_correct)
        self.updates += 1
        self.pending.pop(key, None) if key is not None else None
        self._maybe_birth()

    def stats(self) -> dict:
        return {
            "bits": self.bit_count,
            "stage_index": self.stage_index,
            "stage_cap": self.stage_cap,
            "births": self.births,
            "updates": self.updates,
            "empty_primes": self.empty_primes,
            "empty_lessons": self.empty_lessons,
            "pending": len(self.pending),
            "context_log_odds": self.context_log_odds,
            "cues": [bit.cue for bit in self.bits],
            "diagnosticities": {
                bit.name: round(bit.diagnosticity(), 4) for bit in self.bits
            },
            "change_rates": {
                bit.name: round(bit.change_rate(), 4)
                for bit in self.bits
                if bit.cue in SILENCE_CUES
            },
        }
