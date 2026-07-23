# Diagnostic-contrast v2 confirmation — FAIL

Protocol: `DIAGNOSTIC_CONTRAST_V2_CONFIRMATION_PROTOCOL.md`  
Universe: `confirmation7` (virgin; one look; no retune)

`confirmation6` was invalid/spent (delisted-ticker download + accidental peek).

## Held-out scores

| cell | acc | flip | nonflip | pred-up | act | flips |
|---|---:|---:|---:|---:|---:|---:|
| clean | 0.501 | 0.451 | 0.546 | 0.605 | 0.44 | 226 |
| silence escape | 0.522 | 0.504 | 0.538 | 0.451 | 0.11 | 226 |
| **diagnostic contrast v2** | **0.491** | **0.500** | **0.482** | **0.528** | 0.23 | 226 |

Paired vs clean: acc Δ=-0.010 (p≈0.69); flip Δ=+0.049 (p≈0.22)  
Paired vs silence: acc Δ=-0.031 (p≈0.09); flip Δ=-0.004 (p≈0.80)

## Gate

| rule | result |
|---|---|
| flip ≥ 0.45 | pass (0.500) |
| acc drop vs clean ≤ 0.01 | **fail** (−0.0104) |
| pred-up ≤ 0.65 | pass (0.528) |
| nonflip ≥ 0.50 | **fail** (0.482) |

**`passes_predeclared_gate=False`**

## Reading

Contact had a real-looking lift (flip ~53% vs silence ~49%). Sealed
confirmation7 did not hold it: v2 matches silence on flip and pays a nonflip
tax. The deeper bake was architecturally more faithful; it did not become a
confirmed finance win.

No retuning on confirmation7. Universe is spent.
