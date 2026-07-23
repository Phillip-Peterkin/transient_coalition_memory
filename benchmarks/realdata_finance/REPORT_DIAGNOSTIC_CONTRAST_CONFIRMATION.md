# Diagnostic-contrast confirmation — FAIL

Protocol: `DIAGNOSTIC_CONTRAST_CONFIRMATION_PROTOCOL.md`  
Universe: `confirmation5` (virgin; one look; no retune)

## Held-out scores

| cell | acc | flip | nonflip | pred-up | act | flips |
|---|---:|---:|---:|---:|---:|---:|
| clean | 0.521 | 0.463 | 0.574 | 0.684 | 0.58 | 268 |
| silence escape | 0.466 | 0.463 | 0.470 | 0.541 | 0.07 | 268 |
| **diagnostic contrast** | **0.473** | **0.478** | **0.470** | **0.530** | **0.05** | 268 |

Paired vs clean: acc Δ=-0.048 (p≈0.11); flip Δ=+0.015 (p≈0.67)  
Paired vs silence: acc Δ=+0.007 (p≈0.45); flip Δ=+0.015 (p≈0.15)

## Gate

| rule | result |
|---|---|
| flip ≥ 0.45 | pass (0.478) |
| acc drop vs clean ≤ 0.01 | **fail** (−0.048) |
| pred-up ≤ 0.65 | pass (0.530) |
| nonflip ≥ 0.50 | **fail** (0.470) |

**`passes_predeclared_gate=False`**

## Reading

Contact suggested a modest lift over silence. Sealed confirmation5 did not
reproduce a win: flip is only a small non-significant bump over silence, and
the same nonflip/accuracy tax that silence pays on this world keeps the gate
closed. DCAI slot laws did not blow the numbers out.

No retuning on confirmation5. Universe is spent.
