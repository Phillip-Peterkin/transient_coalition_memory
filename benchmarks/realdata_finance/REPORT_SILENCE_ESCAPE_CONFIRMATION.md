# Silence-escape confirmation — PASS

One-shot look at virgin `confirmation4`. No retuning afterward.

## Frozen candidate

`SessionRelevanceFinanceNewsStream` +
`SilenceEscapeCellular(pe_floor=0.35, pe_span=0.50, rho_gain=0.30,
max_hazard=0.70, apply_to_all_positive=True)`

Protocol: `SILENCE_ESCAPE_CONFIRMATION_PROTOCOL.md`

## Held-out confirmation (last 30% of days)

| Model | Acc | Flip | Non-flip | Pred-up | Act | Flip n |
|---|---:|---:|---:|---:|---:|---:|
| Clean evidence baseline | 0.508 | 0.431 | 0.581 | 0.649 | 0.45 | 490 |
| **Silence escape** | **0.515** | **0.522** | **0.508** | **0.501** | 0.04 | 490 |

Paired vs clean:

- accuracy Δ **+0.7 pts** (p≈0.72)
- flip Δ **+9.2 pts** (p≈0.004)

## Gate

| Rule | Result |
|---|---|
| flip ≥ 45% | **PASS** (52.2%) |
| accuracy drop ≤ 1 pt vs clean | **PASS** (+0.7 pts) |
| pred-up ≤ 0.65 | **PASS** (0.501) |
| non-flip ≥ 50% | **PASS** (50.8%) |

**passes_predeclared_gate = True**

## Plain English

On a fresh company universe never used for design, releasing sticky memory
when sensation is null lifted change detection from 43% to **52%**, kept
overall accuracy, and centered prediction-up near 50%.

This is the first sealed real-data confirmation that clears the 45%
change-detection bar.
