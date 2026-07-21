# Wave IX — Certified Energetic Gating with Shadow Eligibility

## Scope
This wave changed only the gating/credit bridge. The cellular memory, fast/slow claim states, source prior, temporary eligibility traces, delayed feedback, and benchmark world remained fixed.

## Missing link
Early stopping reduced inference cost, but it also starved unrecruited evidence of learning. Fixed-k=8 learned from eight reports every time; the adaptive gate learned only from activated reports.

The repair has two parts:

1. **Decision certificate** — stop only when the current decision is stable under the strongest available completion of the unrecruited coalition.
2. **Shadow eligibility** — unrecruited reports remain dormant during inference but retain lightweight temporary eligibility for a smaller delayed update.

No truth signal is used by the gate. Preview route headers are explicitly counted.

## Fresh holdout result

| Method | Overall accuracy | Changed-fact accuracy | Avg activated | P90 activated | Ops/correct |
|---|---:|---:|---:|---:|---:|
| Provenance graph | 96.82% | 95.69% | 12.00 | 12 | 24.8 |
| Fixed-k=8 cellular | 98.70% | 96.77% | 8.00 | 8 | 64.8 |
| Certified cellular | 98.57% | 96.42% | 5.94 | 6 | 39.0 |
| **Shadow-certified cellular** | **98.69%** | **96.77%** | **5.83** | **6** | 44.5 |

## Interpretation
Shadow-certified cellular matched fixed-k=8 on changed-world accuracy while activating 27.1% fewer reports. It also essentially matched overall accuracy and remained above the provenance graph on both accuracy measures.

This demonstrates that sparse inference and broad learning do not need to be the same operation. The system can reason with a compact coalition while delayed feedback trains a wider dormant reserve through temporary eligibility.

## What remains
This is the strongest result so far, but it is not yet the field-changing result. Average activation remains 5.83 rather than the desired 3–4, and counted operations remain higher than the provenance graph because route preview and distributed updates are still expensive.

The next narrow objective is to compress the reserve certificate and shadow trace so the same result survives with approximately four active reports and lower total operations.
