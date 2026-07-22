# Publisher skew correction — cheerleader base-rate fix

Finance development only. Contact-tail selection; old holdout not used as a
design knob. Holdout numbers below are a post-design snapshot.

## Problem

After the dead-pixel cleanup, change detection reached ~41% — but prediction-up
sat at ~70%. The sensory path was honest: relevant headlines are ~88% Positive
while next-session direction is ~50%. Sign-preserving evidence cannot hide that
anymore.

Breakdown on the contact tail (clean evidence):

| Flip direction | Accuracy | Notes |
|---|---:|---|
| to-up | 60.8% | cheerleader news helps |
| to-down | 20.7% | same cheerleader news hurts |

## Rejected: last-truth mean-reversion

Predicting the opposite of the item's last observed truth on all-Positive days
jumps flip accuracy above 60% and looks like a win. It is not.

On consecutive news days that label equals the flip baseline, so the rule hacks
the flip metric and collapses non-flip accuracy (~59% → ~40%). Discarded.

## Mechanism kept

`SkewCorrectedCellular` keeps clean evidence (no sign-reversal, delayed source
trust) and, for **all-Positive coalitions only**, subtracts

```text
scale * mean_i [ logit(P_emit+(source_i)) - logit(0.5) ]
```

from the decision logit. Mixed / negative coalitions are untouched. Report
signs stay preserved.

Predeclared scale grid: `1.0`, `1.25`, `1.5` (theory starts at `1.0`).

## Contact-tail results

| Cell | Acc | Flip | Non-flip | Pred-up | Act |
|---|---:|---:|---:|---:|---:|
| clean baseline | 0.504 | 0.408 | 0.591 | 0.696 | 0.80 |
| skew scale 1.0 | 0.487 | 0.436 | 0.533 | 0.351 | 0.91 |
| skew scale 1.25 | 0.493 | 0.463 | 0.521 | 0.347 | 0.93 |
| **skew scale 1.5** | **0.495** | **0.472** | 0.516 | **0.358** | 0.93 |

Gate (flip ≥ 45%, pred-up ≤ 65%, accuracy drop < 1 pt): **passed by scale 1.5**
(smallest grid point that clears; scale 1.25 misses the accuracy floor by a
hair).

Paired vs clean on flips for scale 1.5: Δ **+6.4 pts** (p≈0.064).

## Plain English

We stopped treating “everyone said Positive” as strong up evidence. That is the
right sensory correction for a market that only goes up half the time.

Cost: prediction-up falls to ~36% — a mirror bias. The gate only forbade the
old up-spam failure (≥65%). Balancing toward ~50% without giving back the flip
gains is the next impurity.

## Holdout snapshot (post-design)

| Cell | Acc | Flip | Pred-up |
|---|---:|---:|---:|
| session clean | 0.517 | 0.421 | 0.692 |
| skew scale 1.0 | 0.490 | 0.450 | 0.370 |
| skew scale 1.5 | 0.494 | 0.477 | 0.368 |

Same shape. Not a virgin confirmation.

## Status

- **Baked as development model:** `tcm.SkewCorrectedCellular` with contact-
  selected `base_rate_scale=1.5`, on `SessionRelevanceFinanceNewsStream`.
- **Not a confirmed final win:** needs a fresh-company check; pred-up still
  off-center.
- **Still frozen:** Wave XI reference; archival sensory confirmation path.
