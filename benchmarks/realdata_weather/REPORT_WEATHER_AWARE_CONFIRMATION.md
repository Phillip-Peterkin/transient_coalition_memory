# Weather Aware confirmation — PASS

Protocol: `WEATHER_AWARE_CONFIRMATION_PROTOCOL.md`  
Universe: virgin `confirmation3` (12 cities disjoint from contact + confirmation2)  
Subject: `AwareCoalitionCellular` (ACI + Mnemosheath)  
One look. No retuning.

## Held-out scores

| method | acc | flip | nonflip | pred-up | act | flips |
|---|---:|---:|---:|---:|---:|---:|
| persistence | 0.474 | 0.000 | 1.000 | 0.499 | 0.00 | 1099 |
| majority | 0.837 | 0.855 | 0.816 | 0.518 | 6.00 | 1099 |
| silence escape | 0.654 | 0.691 | 0.614 | 0.320 | 2.65 | 1099 |
| sealed ACI | 0.760 | 0.771 | 0.748 | 0.404 | 3.07 | 1099 |
| **Aware (ACI+Mnemosheath)** | **0.847** | **0.868** | **0.823** | **0.492** | 3.68 | 1099 |

Paired vs sealed ACI: acc Δ≈+0.087 (p≈0); flip Δ≈+0.097 (p≈0).

## Gate

| rule | result |
|---|---|
| flip ≥ 0.45 | **pass** (0.868) |
| flip ≥ sealed ACI | **pass** (+0.097) |
| flip ≥ silence lineage | **pass** (+0.177) |
| acc ≥ persistence − 0.01 | **pass** (0.847) |
| pred-up ≤ 0.65 | **pass** (0.492) |
| nonflip ≥ 0.50 | **pass** (0.823) |

**`passes_predeclared_gate=True`**

## Reading

On this virgin trustworthy-source world, Mnemosheath learned unanimous model
agreement is diagnostic (evidence routes 3235 / null routes 0) and replaced the
regime-blind `force_all_positive_null` stamp. Flip and accuracy clear sealed
ACI and silence; Aware also sits near the memoryless-majority ceiling without
activating every vote (act 3.68 vs majority 6.0).

Grown cues on this run (selective admission): `against_prior_side`,
`agree_with_prior_side`, `high_agree`, `mixed`, `unanimous_neg`,
`unanimous_pos`, `wide_margin` (plus seed pulses).

No retuning. confirmation3 is spent. Still a **new** clean Weather bed, not
recovery of the old sandbox Weather final.
