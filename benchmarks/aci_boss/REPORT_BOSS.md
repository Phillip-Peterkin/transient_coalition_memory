# ACI synthetic adversarial boss — FAIL

Protocol: `BOSS_PROTOCOL.md` (written before scoring)  
Worlds: Wave XI `World` seeds (adversarial source reversals / stale persistence)  
Candidate: sealed confirmation8 `ActiveCoalitionCellular` (no retune)

## Fresh holdout (`15300`–`15303`)

| method | acc | changed-fact | avg act | ops/correct |
|---|---:|---:|---:|---:|
| fair provenance graph | 0.9678 | 0.9521 | 12.00 | 21.00 |
| Wave XI (`BatchedReserveCellular`) | **0.9860** | **0.9660** | 4.05 | 9.69 |
| **ACI (sealed)** | 0.9599 | 0.9290 | 3.90 | 7.44 |

## Gate

| rule | result |
|---|---|
| ACI acc ≥ Wave XI − 0.015 | **FAIL** (−0.026) |
| ACI changed ≥ Wave XI − 0.025 | **FAIL** (−0.037) |
| ACI acc ≥ graph | **FAIL** (−0.008) |
| ACI changed ≥ graph | **FAIL** (−0.023) |

**`passes_predeclared_gate=False`**

Regression seeds (`15200`–`15201`) show the same pattern (ACI 0.963 / 0.942 vs Wave XI 0.988 / 0.967).

## Reading

Finance-sealed ACI is **not** Wave XI–compatible on the adversarial synthetic
suite. It stays cheaper on ops but loses quality to both the frozen reference
and the fair graph under the predeclared slacks.

This blocks any foundation-replacement claim. confirmation8 remains a sealed
finance win; the active experimental bake stands for that regime only.

Weather (trustworthy-source final boss) was **not** run — harness absent;
inventing one post-development is forbidden.

No retuning on these seeds.
