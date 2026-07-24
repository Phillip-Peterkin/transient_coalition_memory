"""Mnemosheath — maturing context-awareness organ for ACI.

Council synthesis (6 agents). Original TCM mechanism. Not a neural net,
not pymdp/ActInfToolbox, not transformers, not RAG.

Awareness = one bounded diagnosticity scalar grown from binary distinctions
that EARN persistence. Stages: 1 → 2 → 4 → 12 bits.

Coupling (single elegant join): modulates whether unanimous agreement is
treated as null (cheerleader) or as evidence (trustworthy consensus).
Prior still never enters report Δ — that law stays in ACI.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

EPS = 1e-9
STAGE_CAPS = (1, 2, 4, 12)


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(-40.0, min(40.0, value))))


# Cue catalogue — observables already native to ACI streams.
CUE_ORDER = (
    "unanimous",
    "unanimous_pos",
    "unanimous_neg",
    "high_agree",
    "low_delta",
    "high_pe",
    "mixed",
    "empty",
    "agree_with_prior_side",  # majority matches prior direction (stickiness cue)
    "against_prior_side",
    "wide_margin",  # |mean vote - 0.5| large
    "thin_margin",
)


@dataclass
class DistinctionBit:
    """One binary distinction the sheath can hold about the sensory field."""

    name: str
    cue: str
    hit: float = 1.0  # majority aligned with truth when this cue fired
    miss: float = 1.0
    persistence: int = 0
    age: int = 0

    def diagnosticity(self) -> float:
        return self.hit / max(EPS, self.hit + self.miss)

    def merit(self) -> float:
        # Distance from coin-flip: only earned distinctions pay rent.
        return abs(self.diagnosticity() - 0.5)

    def update(self, majority_correct: bool) -> None:
        self.age += 1
        if majority_correct:
            self.hit += 1.0
            self.persistence += 1
        else:
            self.miss += 1.0
            self.persistence = 0


@dataclass
class Mnemosheath:
    """Maturing sheath of context distinctions (the awareness organ)."""

    bits: list[DistinctionBit] = field(default_factory=list)
    stage_index: int = 0
    dwell: int = 8
    split_merit: float = 0.12
    evidence_threshold: float = 0.62
    context_log_odds: float = 0.0
    births: int = 0
    updates: int = 0

    def __post_init__(self) -> None:
        if not self.bits:
            # Stage 1 — Pulse Sense: same/changed via unanimous agreement cue.
            self.bits = [DistinctionBit(name="pulse.unanimous", cue="unanimous")]

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
    ) -> dict[str, bool]:
        votes = [int(vote) for _, _, vote in reports]
        n = len(votes)
        mean = (sum(votes) / n) if n else 0.5
        unanimous = n > 0 and len(set(votes)) == 1
        prior_side = 1 if prior_p >= 0.5 else 0
        majority = 1 if mean >= 0.5 else 0
        return {
            "empty": n == 0,
            "unanimous": unanimous,
            "unanimous_pos": n > 0 and all(v == 1 for v in votes),
            "unanimous_neg": n > 0 and all(v == 0 for v in votes),
            "high_agree": n > 0 and (mean >= 0.8 or mean <= 0.2),
            "low_delta": max_delta < min_delta,
            "high_pe": null_pe > 0.55,
            "mixed": n > 0 and len(set(votes)) > 1,
            "agree_with_prior_side": n > 0 and majority == prior_side,
            "against_prior_side": n > 0 and majority != prior_side,
            "wide_margin": n > 0 and abs(mean - 0.5) >= 0.35,
            "thin_margin": n > 0 and abs(mean - 0.5) < 0.20,
        }

    def fired_bits(self, cues: dict[str, bool]) -> list[DistinctionBit]:
        return [bit for bit in self.bits if cues.get(bit.cue, False)]

    def diagnosticity(self, cues: dict[str, bool]) -> float:
        fired = self.fired_bits(cues)
        if not fired:
            return 0.5
        weights = []
        values = []
        for bit in fired:
            weight = 1.0 + bit.persistence
            weights.append(weight)
            values.append(bit.diagnosticity())
        return float(sum(w * v for w, v in zip(weights, values)) / sum(weights))

    def agreement_is_evidence(self, cues: dict[str, bool]) -> bool:
        """High diagnosticity ⇒ unanimous/high-agree is evidence, not null."""
        return self.diagnosticity(cues) >= self.evidence_threshold

    def vote_context(self, cues: dict[str, bool]) -> float:
        """Second coalition: bits vote a bounded context log-odds."""
        fired = self.fired_bits(cues)
        if not fired:
            self.context_log_odds = 0.0
            return 0.0
        total = 0.0
        for bit in fired:
            # Sign: evidence-like (+), cheerleader-like (−)
            center = bit.diagnosticity() - 0.5
            total += center * (1.0 + 0.1 * bit.persistence)
        self.context_log_odds = max(-3.0, min(3.0, total))
        return self.context_log_odds

    def mix_null_hazard(self, base_hazard: float, max_hazard: float) -> float:
        """Single coupling: context shifts null hazard only."""
        gate = _sigmoid(self.context_log_odds)
        # High diagnostic context → lower null hazard (trust the world more).
        tuned = (1.0 - gate) * max_hazard + gate * (0.15 * max_hazard)
        return float(min(max_hazard, 0.5 * base_hazard + 0.5 * tuned))

    def _next_cue_for_split(self, parent: DistinctionBit) -> str | None:
        owned = {bit.cue for bit in self.bits}
        # Prefer refining the parent's family, then unused catalogue cues.
        family = {
            "unanimous": ("unanimous_pos", "unanimous_neg"),
            "unanimous_pos": ("wide_margin", "agree_with_prior_side"),
            "unanimous_neg": ("wide_margin", "against_prior_side"),
            "high_agree": ("wide_margin", "thin_margin"),
            "mixed": ("against_prior_side", "high_pe"),
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
        cap = self.stage_cap
        if len(self.bits) >= cap:
            # Advance stage when current cap is filled with mature bits.
            mature = sum(1 for bit in self.bits if bit.persistence >= self.dwell)
            if mature >= cap and self.stage_index + 1 < len(STAGE_CAPS):
                self.stage_index += 1
            return
        parent = max(self.bits, key=lambda bit: bit.persistence * (0.1 + bit.merit()))
        if parent.persistence < self.dwell or parent.merit() < self.split_merit:
            return
        child_cue = self._next_cue_for_split(parent)
        if child_cue is None:
            return
        child = DistinctionBit(
            name=f"s{self.stage_index}.{child_cue}",
            cue=child_cue,
            hit=1.0 + 0.25 * parent.hit,
            miss=1.0 + 0.25 * parent.miss,
        )
        self.bits.append(child)
        parent.persistence = 0  # must re-earn rent after mitosis
        self.births += 1

    def feedback(
        self,
        cues: dict[str, bool],
        *,
        majority_vote: int | None,
        truth: int,
    ) -> None:
        if majority_vote is None:
            return
        majority_correct = int(majority_vote) == int(truth)
        fired = self.fired_bits(cues)
        if not fired:
            return
        for bit in fired:
            bit.update(majority_correct)
        self.updates += 1
        self._maybe_birth()

    def stats(self) -> dict:
        return {
            "bits": self.bit_count,
            "stage_index": self.stage_index,
            "stage_cap": self.stage_cap,
            "births": self.births,
            "updates": self.updates,
            "context_log_odds": self.context_log_odds,
            "cues": [bit.cue for bit in self.bits],
            "diagnosticities": {
                bit.name: round(bit.diagnosticity(), 4) for bit in self.bits
            },
        }
