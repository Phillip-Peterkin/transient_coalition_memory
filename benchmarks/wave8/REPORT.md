# Wave VIII — Value-of-Information Gating

Scope remained fixed: only the stopping policy changed. The memory, feedback, causal trace, and benchmark world were unchanged.

| Method | Overall | Changed facts | Avg activated | P90 activated | Ops/correct |
|---|---:|---:|---:|---:|---:|
| provenance_graph | 0.9667 | 0.9466 | 12.00 | 12.0 | 24.8 |
| old_energetic | 0.9797 | 0.9425 | 1.21 | 1.0 | 51.5 |
| fixed_k8 | 0.9867 | 0.9640 | 8.00 | 8.0 | 64.9 |
| voi_cellular | 0.9823 | 0.9520 | 4.09 | 4.0 | 57.2 |

The repaired gate stops only when remaining evidence is unlikely to flip or materially change the prediction. It uses existing disagreement, fast/slow memory divergence, feedback age, and a pessimistic bound on the next evidence item.

Result: the new gate beats the provenance graph on overall and changed-fact accuracy while activating about one third of the available reports. Fixed-k=8 remains the quality ceiling, so the remaining problem is closing that final accuracy gap without returning to fixed recruitment.