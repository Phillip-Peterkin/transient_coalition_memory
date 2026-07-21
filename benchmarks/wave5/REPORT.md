# Wave V — Temporary Causal Address Repair

## Objective
Repair the failed causal mechanism from Wave IV without converting the cellular system into a permanent graph. Each prediction now saves temporary distributed cell addresses for the exact contributors active at prediction time. Delayed feedback applies directional credit only to those saved addresses.

## What changed
- Claim and path memory are stored across fixed hashed cell fields rather than explicit claim/path records.
- Each prediction emits a temporary causal address containing the exact distributed cells used.
- Feedback uses saved prediction confidence and contributor direction to reward evidence that pushed toward truth and punish evidence that pushed away from truth.
- Temporary addresses disappear after feedback; learning remains in the distributed fields.
- Sparse adaptive recruitment remains active.

## Final comparison
Eight untouched test worlds were used for the full system and provenance graph.

| Method | Overall accuracy | Changed-fact accuracy | Brier | ECE | False certainty | Operations/correct |
|---|---:|---:|---:|---:|---:|---:|
| Provenance graph | 97.23% | 95.23% | 0.0200 | 0.0086 | 0.84% | 24.7 |
| Cellular addressed | 97.63% | 93.57% | 0.0457 | 0.1496 | 0.07% | 410.9 |

## Causal ablation
A four-world ablation removed exact path updates while preserving distributed claim and source learning.

| Variant | Overall accuracy | Changed-fact accuracy | Brier | False certainty |
|---|---:|---:|---:|---:|
| Full temporary addressing | approximately 97.6% | approximately 93.6% | 0.0457 | 0.07% |
| No exact path update | 95.78% | 89.00% | 0.0421 | 2.98% |

The ablation is not perfectly paired because the full result uses eight worlds and the quick ablation uses four, but the effect is large enough to justify a fully paired follow-up.

## Interpretation
The repair succeeded in one important sense: causal path addressing now carries measurable information. In Wave IV, removing path trust changed essentially nothing. In Wave V, removing exact path updates reduced changed-fact accuracy by roughly 4.6 percentage points and sharply increased false certainty.

The system still failed the superiority objective. The provenance graph remained about 1.7 percentage points better on changed facts, was much better calibrated, and required roughly one-sixteenth as many counted operations per correct answer.

The cellular system's overall accuracy remained slightly higher and its false-certainty rate was lower, but its probabilities were underconfident and poorly calibrated. The computational cost comes largely from repeatedly reading and writing multiple hashed cells for every claim and path.

## What this means
The missing causal mechanism has been repaired enough to matter. The next bottleneck is no longer credit assignment alone. It is efficient addressing and calibration.

The next design should:
1. Cache coalition addresses permanently at the microscopic substrate level rather than recomputing hashes per prediction.
2. Use event-driven sparse cell updates instead of reading dozens of cells for every source report.
3. Learn a local calibration gate so distributed evidence magnitude maps to realistic probability.
4. Run a paired ablation on identical worlds for full and no-path variants.
5. Compare under strict equal-memory and equal-operation budgets in addition to unconstrained performance.

## Honest conclusion
Wave V repaired the causal trace mechanism, but did not produce a superior system. It converted a nonfunctional path component into a useful one and exposed the next engineering target: preserve exact distributed credit while reducing its cost by at least an order of magnitude.
