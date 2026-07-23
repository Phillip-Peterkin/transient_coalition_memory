# Weather architecture confirmation — PASS

Protocol: `WEATHER_ARCHITECTURE_CONFIRMATION_PROTOCOL.md` (written before scoring)  
Universe: virgin `confirmation2` (12 cities disjoint from the first Weather bed)  
**Architecture under test:** `ActiveExperimentalCellular` (sealed ACI)  
**Not under test:** Wave XI (`BatchedReserveCellular`) — synthetic reference only

## Holdout scores

| method | acc | flip | nonflip | pred-up | act | flips |
|---|---:|---:|---:|---:|---:|---:|
| persistence | 0.494 | 0.000 | 1.000 | 0.511 | 0.00 | 1056 |
| majority | 0.811 | 0.820 | 0.801 | 0.505 | 6.00 | 1056 |
| silence escape (lineage) | 0.640 | 0.663 | 0.617 | 0.315 | 2.65 | 1056 |
| **active experimental ACI** | **0.723** | **0.733** | **0.712** | **0.397** | 3.12 | 1056 |

## Gate

| rule | result |
|---|---|
| flip ≥ 0.45 | **pass** (0.733) |
| flip ≥ silence lineage | **pass** (+0.070) |
| acc ≥ persistence − 0.01 | **pass** (+0.229) |
| pred-up ≤ 0.65 | **pass** (0.397) |
| nonflip ≥ 0.50 | **pass** (0.712) |

**`passes_predeclared_gate=True`**

## Reading

Testing the **real active architecture** (ACI) against its lineage — not Wave XI —
clears the predeclared Weather gate on a virgin city universe. ACI lifts
silence-escape flip by ~7 points while holding accuracy far above persistence.

Majority remains the trustworthy-source ceiling (flip 0.820); ACI does not
claim to beat the raw ensemble. Wave XI is out of the gate by design.

No retuning. confirmation2 is spent. Still a **new** clean Weather bed, not
recovery of the old sandbox Weather final.
