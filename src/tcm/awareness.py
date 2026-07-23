"""Mnemosheath — selective context awareness (cleanup rewrite).

Bits are PROPOSED from a candidate cue pool and ADMITTED only when their own
delayed predictive merit beats noise with hysteresis. No lineage stamp-book.
No parent-stat inheritance. No CUE_ORDER as learning policy.

Council #2 empty curriculum kept: prime on absence, complete on change/stay.
Prior never enters report Δ.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

EPS = 1e-9

# Default production cue catalogue (display / sensing). Admission is merit-gated.
DEFAULT_CANDIDATE_CUES: tuple[str, ...] = (
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

SILENCE_CUES = frozenset(
    {
        "empty",
        "low_delta",
        "high_pe",
        "long_vacancy",
        "fresh_vacancy",
        "empty_after_flip",
        "empty_after_stay",
    }
)

# Grown-bit caps by stage (seeds sit outside this budget).
GROW_CAPS = (0, 1, 2, 4, 10)  # stage 0: seeds only; then +1,+2,+4,+10 grown


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(-40.0, min(40.0, value))))


def _is_silence(cue: str) -> bool:
    return cue in SILENCE_CUES or cue.startswith("silence_") or cue.startswith("vac_")


@dataclass
class CandidateCue:
    """Unadmitted (or admitted) cue with its OWN delayed statistics."""

    cue: str
    hit: float = 1.0
    miss: float = 1.0
    change: float = 1.0
    stay: float = 1.0
    samples: int = 0
    streak: int = 0
    admitted: bool = False

    def rate(self) -> float:
        if _is_silence(self.cue):
            return self.change / max(EPS, self.change + self.stay)
        return self.hit / max(EPS, self.hit + self.miss)

    def merit(self) -> float:
        return abs(self.rate() - 0.5)

    def update_agreement(self, majority_correct: bool) -> None:
        self.samples += 1
        if majority_correct:
            self.hit += 1.0
        else:
            self.miss += 1.0

    def update_absence(self, preceded_change: bool) -> None:
        self.samples += 1
        if preceded_change:
            self.change += 1.0
        else:
            self.stay += 1.0


@dataclass
class DistinctionBit:
    """Admitted distinction — lives in the sheath vote."""

    name: str
    cue: str
    hit: float = 1.0
    miss: float = 1.0
    change: float = 1.0
    stay: float = 1.0
    persistence: int = 0
    age: int = 0
    primed: int = 0
    seed: bool = False

    def diagnosticity(self) -> float:
        return self.hit / max(EPS, self.hit + self.miss)

    def change_rate(self) -> float:
        return self.change / max(EPS, self.change + self.stay)

    def merit(self) -> float:
        if _is_silence(self.cue):
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
        self.age += 1
        if preceded_change:
            self.change += 1.0
        else:
            self.stay += 1.0
        self.persistence += 1


@dataclass
class Mnemosheath:
    """Selective sheath: candidates compete; only winners become bits."""

    bits: list[DistinctionBit] = field(default_factory=list)
    candidates: dict[str, CandidateCue] = field(default_factory=dict)
    seed_cues: tuple[str, ...] = ("unanimous", "empty")
    candidate_cues: tuple[str, ...] | None = None
    stage_index: int = 0
    grow_caps: tuple[int, ...] = GROW_CAPS
    # Admission hyperparameters (needle-hardened defaults).
    n_min: int = 50
    merit_hi: float = 0.18
    lead_hi: float = 0.08
    noise_floor: float = 0.05  # rivals below this are treated as this high
    hysteresis: int = 6
    evidence_threshold: float = 0.62
    context_log_odds: float = 0.0
    births: int = 0
    updates: int = 0
    empty_lessons: int = 0
    empty_primes: int = 0
    pending: dict = field(default_factory=dict)
    # Backward-compat aliases used by older tests/smoke.
    dwell: int = 8
    split_merit: float = 0.12

    def __post_init__(self) -> None:
        pool = tuple(self.candidate_cues) if self.candidate_cues is not None else DEFAULT_CANDIDATE_CUES
        # Ensure seeds are in the pool for sensing continuity.
        for cue in self.seed_cues:
            if cue not in pool:
                pool = pool + (cue,)
        self.candidate_cues = pool
        if not self.candidates:
            self.candidates = {
                cue: CandidateCue(cue=cue, admitted=(cue in self.seed_cues))
                for cue in pool
            }
        if not self.bits:
            self.bits = [
                DistinctionBit(name=f"seed.{cue}", cue=cue, seed=True)
                for cue in self.seed_cues
            ]
            for cue in self.seed_cues:
                self.candidates[cue].admitted = True

    @property
    def bit_count(self) -> int:
        return len(self.bits)

    @property
    def grown_count(self) -> int:
        return sum(1 for bit in self.bits if not bit.seed)

    @property
    def stage_cap(self) -> int:
        """Total bits = seeds + grown-cap at this stage."""
        grown_cap = self.grow_caps[min(self.stage_index, len(self.grow_caps) - 1)]
        return len(self.seed_cues) + grown_cap

    @property
    def grow_cap(self) -> int:
        return self.grow_caps[min(self.stage_index, len(self.grow_caps) - 1)]

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
        extra_cues: dict[str, bool] | None = None,
    ) -> dict[str, bool]:
        votes = [int(vote) for _, _, vote in reports]
        n = len(votes)
        mean = (sum(votes) / n) if n else 0.5
        unanimous = n > 0 and len(set(votes)) == 1
        prior_side = 1 if prior_p >= 0.5 else 0
        majority = 1 if mean >= 0.5 else 0
        empty = n == 0
        cues = {
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
            "empty_after_stay": empty
            and (prev_truth is not None)
            and (not last_was_flip),
        }
        if extra_cues:
            cues.update({key: bool(value) for key, value in extra_cues.items()})
        return cues

    def fired_bits(self, cues: dict[str, bool]) -> list[DistinctionBit]:
        return [bit for bit in self.bits if cues.get(bit.cue, False)]

    def diagnosticity(self, cues: dict[str, bool]) -> float:
        fired = [bit for bit in self.fired_bits(cues) if not _is_silence(bit.cue)]
        if not fired:
            return 0.5
        weights = [1.0 + bit.persistence for bit in fired]
        values = [bit.diagnosticity() for bit in fired]
        return float(sum(w * v for w, v in zip(weights, values)) / sum(weights))

    def absence_change_rate(self, cues: dict[str, bool]) -> float:
        fired = [bit for bit in self.fired_bits(cues) if _is_silence(bit.cue)]
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
            if _is_silence(bit.cue):
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
        if not (cues.get("empty") or cues.get("low_delta")):
            return
        for bit in self.fired_bits(cues):
            if _is_silence(bit.cue):
                bit.primed += 1
        self.pending[key] = {
            "cues": dict(cues),
            "prev_truth": prev_truth,
            "time_since_evidence": int(time_since_evidence),
        }
        self.empty_primes += 1

    def _ensure_candidate(self, cue: str) -> CandidateCue:
        if cue not in self.candidates:
            self.candidates[cue] = CandidateCue(cue=cue)
        return self.candidates[cue]

    def _update_candidates_agreement(
        self, cues: dict[str, bool], majority_correct: bool
    ) -> None:
        for cue, fired in cues.items():
            if not fired or _is_silence(cue):
                continue
            self._ensure_candidate(cue).update_agreement(majority_correct)

    def _update_candidates_absence(
        self, cues: dict[str, bool], preceded_change: bool
    ) -> None:
        for cue, fired in cues.items():
            if not fired or not _is_silence(cue):
                continue
            self._ensure_candidate(cue).update_absence(preceded_change)

    def _advance_stage_if_needed(self) -> None:
        while (
            self.grown_count >= self.grow_cap
            and self.stage_index + 1 < len(self.grow_caps)
        ):
            self.stage_index += 1

    def maybe_admit(self) -> str | None:
        """Admit at most one candidate that beats noise with hysteresis."""
        self._advance_stage_if_needed()
        if self.grown_count >= self.grow_cap:
            return None
        pool = [
            cand
            for cand in self.candidates.values()
            if (not cand.admitted)
            and cand.samples >= self.n_min
            and cand.cue in (self.candidate_cues or ())
        ]
        if not pool:
            return None
        best = max(pool, key=lambda cand: (cand.merit(), cand.samples))
        # Lead is vs sub-threshold rivals only — two opposite high-merit signals
        # must not veto each other (sig_a vs sig_b).
        noise_rivals = [
            cand.merit()
            for cand in pool
            if cand.cue != best.cue and cand.merit() < self.merit_hi
        ]
        noise = max(noise_rivals) if noise_rivals else 0.0
        noise = max(noise, self.noise_floor)
        lead = best.merit() - noise
        # Reject "best of garbage": absolute merit and lead over noise floor.
        if best.merit() >= self.merit_hi and lead >= self.lead_hi:
            best.streak += 1
        else:
            best.streak = 0
            return None
        if best.streak < self.hysteresis:
            return None
        # Seed cue already present — mark admitted, do not duplicate.
        if best.cue in self.seed_cues:
            best.admitted = True
            best.streak = 0
            for cand in pool:
                if cand.cue != best.cue:
                    cand.streak = 0
            return best.cue
        # Neutral newborn — no parent-stat inheritance.
        child = DistinctionBit(
            name=f"grown.{best.cue}",
            cue=best.cue,
            seed=False,
        )
        self.bits.append(child)
        best.admitted = True
        best.streak = 0
        for cand in pool:
            if cand.cue != best.cue:
                cand.streak = 0
        self.births += 1
        self._advance_stage_if_needed()
        return best.cue

    def feedback(
        self,
        cues: dict[str, bool],
        *,
        majority_vote: int | None,
        truth: int,
        key=None,
    ) -> None:
        if majority_vote is None:
            lesson = self.pending.pop(key, None) if key is not None else None
            if lesson is None:
                lesson_cues = cues
                prev = None
            else:
                lesson_cues = lesson["cues"]
                prev = lesson.get("prev_truth")
            if not (lesson_cues.get("empty") or lesson_cues.get("low_delta")):
                # Still allow pure silence-family external cues in tests.
                if not any(
                    lesson_cues.get(cue) for cue in lesson_cues if _is_silence(cue)
                ):
                    return
            preceded_change = prev is not None and int(truth) != int(prev)
            self._update_candidates_absence(lesson_cues, preceded_change)
            fired = [
                bit for bit in self.fired_bits(lesson_cues) if _is_silence(bit.cue)
            ]
            if not fired:
                fired = [bit for bit in self.bits if bit.cue == "empty"]
            for bit in fired:
                bit.update_absence(preceded_change)
            self.updates += 1
            self.empty_lessons += 1
            self.maybe_admit()
            return

        majority_correct = int(majority_vote) == int(truth)
        self._update_candidates_agreement(cues, majority_correct)
        fired = [bit for bit in self.fired_bits(cues) if not _is_silence(bit.cue)]
        for bit in fired:
            bit.update(majority_correct)
        self.updates += 1
        if key is not None:
            self.pending.pop(key, None)
        self.maybe_admit()

    def admitted_cues(self) -> set[str]:
        return {bit.cue for bit in self.bits}

    def grown_cues(self) -> set[str]:
        return {bit.cue for bit in self.bits if not bit.seed}

    def stats(self) -> dict:
        return {
            "bits": self.bit_count,
            "grown": self.grown_count,
            "stage_index": self.stage_index,
            "stage_cap": self.stage_cap,
            "grow_cap": self.grow_cap,
            "births": self.births,
            "updates": self.updates,
            "empty_primes": self.empty_primes,
            "empty_lessons": self.empty_lessons,
            "pending": len(self.pending),
            "context_log_odds": self.context_log_odds,
            "cues": [bit.cue for bit in self.bits],
            "grown_cues": sorted(self.grown_cues()),
            "diagnosticities": {
                bit.name: round(bit.diagnosticity(), 4) for bit in self.bits
            },
            "change_rates": {
                bit.name: round(bit.change_rate(), 4)
                for bit in self.bits
                if _is_silence(bit.cue)
            },
            "top_candidates": sorted(
                (
                    {
                        "cue": cand.cue,
                        "merit": round(cand.merit(), 4),
                        "samples": cand.samples,
                        "streak": cand.streak,
                        "admitted": cand.admitted,
                    }
                    for cand in self.candidates.values()
                ),
                key=lambda row: (-row["merit"], -row["samples"], row["cue"]),
            )[:8],
        }
