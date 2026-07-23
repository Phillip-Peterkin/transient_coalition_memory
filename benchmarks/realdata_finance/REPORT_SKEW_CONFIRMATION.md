# Skew-correction confirmation — FAIL

One-shot look at virgin `confirmation3`. No retuning afterward.

## Frozen candidate

`SessionRelevanceFinanceNewsStream` + `SkewCorrectedCellular(base_rate_scale=1.5)`

Protocol: `SKEW_CONFIRMATION_PROTOCOL.md`

## Held-out confirmation (last 30% of days)

| Model | Acc | Flip | Non-flip | Pred-up | Act | Flip n |
|---|---:|---:|---:|---:|---:|---:|
| Clean evidence baseline | 0.513 | 0.438 | 0.587 | 0.569 | 0.38 | 393 |
| Skew corrected (1.5) | 0.509 | **0.422** | 0.595 | 0.448 | 0.42 | 393 |

Paired vs clean:

- accuracy Δ −0.4 pts (p≈0.84)
- flip Δ **−1.5 pts** (p≈0.65)

## Gate

| Rule | Result |
|---|---|
| flip ≥ 45% | **FAIL** (42.2%) |
| accuracy drop ≤ 1 pt vs clean | pass (−0.4 pts) |
| pred-up ≤ 0.65 | pass (0.448) |

**passes_predeclared_gate = False**

## Plain English

The contact-tail 47% did not survive a fresh company universe. On new names,
skew correction did not help change detection and landed at 42% — under the
45% bar, and slightly below the clean session baseline on the same events.

This universe is now spent for confirmatory claims about this mechanism.
Development may continue elsewhere; this result stands as recorded.
