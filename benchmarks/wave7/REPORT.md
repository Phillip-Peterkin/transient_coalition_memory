# Wave VII — Energetic Gating Blended with Cellular Credit Assignment

## Architecture
The model combines only mechanisms that survived prior ablations:

- fast claim-specific memory for rapid reversal learning,
- slow claim memory for stability,
- source reliability as a weak prior,
- temporary eligibility traces for delayed credit,
- no permanent path-memory channel,
- energetic confidence stopping,
- contradiction-dependent recruitment thresholds.

Energetic gating controls how much evidence is recruited. Eligibility traces control where feedback is assigned. They are intentionally separated.

## Fresh holdout results
Four untouched worlds, seeds 11700–11703.

| Method | Overall accuracy | Changed-fact accuracy | Brier | Avg. activated reports | Ops/correct |
|---|---:|---:|---:|---:|---:|
| Dynamic Bayes | 97.01% | 93.93% | 0.0248 | 12.0 | 12.4 |
| EWMA evidence | 96.25% | 94.29% | 0.0277 | 12.0 | 12.5 |
| Provenance graph | 97.02% | 95.15% | 0.0234 | 12.0 | 24.7 |
| Energetic cellular | 97.93% | 94.02% | 0.0505 | 1.2 | 51.5 |

## Fixed-k cellular ablation

| Recruitment | Overall accuracy | Changed-fact accuracy | Avg. activated | Ops/correct |
|---|---:|---:|---:|---:|
| k=1 | 97.35% | 94.17% | 1.0 | 51.4 |
| k=2 | 97.67% | 94.88% | 2.0 | 53.2 |
| k=4 | 98.01% | 95.00% | 4.0 | 57.1 |
| k=8 | 98.65% | 96.15% | 8.0 | 64.9 |

## Interpretation
The blend worked in one important sense: the energetic model used only 1.2 of 12 reports on average while achieving the highest overall accuracy among the traditional baselines. However, the current stopping rule is too eager. It stops near one report and leaves changed-world performance below the provenance graph.

The strongest result is the fixed-k curve. Cellular learning itself now surpasses the provenance graph when allowed four to eight contributors. This means the remaining weakness is not the memory or credit system. It is the gate.

The next repair should make gating difficulty-sensitive rather than margin-only. It should estimate expected value of the next contributor and continue whenever contradiction, source disagreement, or recent claim volatility predicts that another report may change the answer. Easy cases should stop at one or two reports; changed or unstable cases should recruit four to eight.
