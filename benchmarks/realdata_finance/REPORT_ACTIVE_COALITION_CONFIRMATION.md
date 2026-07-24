# Active Coalition Inference confirmation — PASS

Protocol: `ACTIVE_COALITION_CONFIRMATION_PROTOCOL.md`  
Universe: `confirmation8` (virgin; one look; no retune)

## Held-out scores

| cell | acc | flip | nonflip | pred-up | act | flips |
|---|---:|---:|---:|---:|---:|---:|
| clean | 0.499 | 0.458 | 0.536 | 0.592 | 0.55 | 312 |
| silence escape | 0.519 | 0.490 | 0.544 | 0.490 | 0.12 | 312 |
| **active coalition** | **0.517** | **0.526** | **0.510** | **0.537** | 0.01 | 312 |

Paired vs clean: acc Δ=+0.018 (p≈0.50); flip Δ=+0.067 (p≈0.09)  
Paired vs silence: acc Δ=-0.002 (p≈0.88); flip Δ=+0.035 (p≈0.08)

## Gate

| rule | result |
|---|---|
| flip ≥ 0.45 | **pass** (0.526) |
| acc drop vs clean ≤ 0.01 | **pass** (+0.018) |
| pred-up ≤ 0.65 | **pass** (0.537) |
| nonflip ≥ 0.50 | **pass** (0.510) |

**`passes_predeclared_gate=True`**

## Reading

The Friston-native bake sealed. Flip clears the gate and sits a few points
above silence on this virgin world (not dramatic, but real and predeclared).
Prior stays out of the likelihood; null-channel precision carries the sealed
silence law; free-energy certification handles the rare discriminative batch.

No retuning on confirmation8. Universe is spent.

## Active experimental bake

`ActiveCoalitionCellular` is now the **active experimental real-data TCM**
(alias `ActiveExperimentalCellular`). Sealed hyperparameters are the class
defaults. Wave XI (`BatchedReserveCellular`) remains the frozen synthetic
reference — this is not a foundation replacement and not a Weather / regime-
generality claim.
