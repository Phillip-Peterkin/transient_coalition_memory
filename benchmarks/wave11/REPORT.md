# Wave XI — Exact Coalition Batching

## Scope

Wave XI changed only the delayed-feedback implementation. The Wave X decision policy, compressed reserve, gating rule, memory structure, and parameters were locked.

The original implementation repeatedly updated the same claim state once per contributing report. Wave XI derives the exact closed-form result of those sequential decay-and-update recurrences, then applies one physical write per answer coalition. This preserves the original mathematics while eliminating redundant writes.

Operation accounting was also made symmetric. Both the cellular system and provenance graph are charged for scalar evidence reads during inference and scalar state writes during learning.

## Results

### Regression worlds (Wave X holdout seeds)

| Method | Overall accuracy | Changed-fact accuracy | Avg activated | Ops / correct |
|---|---:|---:|---:|---:|
| Provenance graph | 97.10% | 94.82% | 12.00 | 20.99 |
| Exact-batched cellular | **98.80%** | **96.70%** | **4.06** | **9.71** |

The cellular system exactly reproduced the Wave X accuracy ceiling, confirming that batching did not alter the learned trajectory.

### Fresh untouched worlds

| Method | Overall accuracy | Changed-fact accuracy | Avg activated | Ops / correct |
|---|---:|---:|---:|---:|
| Provenance graph | 96.78% | 95.21% | 12.00 | 21.00 |
| Exact-batched cellular | **98.60%** | **96.60%** | **4.05** | **9.69** |

## Victory condition

On fresh worlds, the cellular architecture simultaneously achieved:

- higher overall accuracy,
- higher changed-world accuracy,
- one-third of the active reports,
- and 53.9% fewer total counted operations per correct answer.

The key implementation principle is:

> Many report-level eligibility events can belong to the same answer coalition. Their sequential learning recurrence can be solved exactly and committed once.

This is not approximate vectorization. It is mathematically equivalent to the original ordered decay-and-update sequence for the claim states.

## Remaining caveat

This remains a synthetic benchmark. The result establishes a strong internal architectural victory, not yet external superiority on real-world datasets. The next scientifically valid step is replication across larger worlds, broader source counts, independent implementations, and real temporal-provenance datasets.
