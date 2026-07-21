# Wave XII — Calibration Probe

## Scope

Post-hoc calibration only. The cellular substrate, gate, learning rule, feedback batching, active recruitment, and operation accounting were frozen.

Calibration was fitted on four separate development worlds (15400–15403), then locked and evaluated on four untouched worlds (15500–15503).

## Locked test results

| Method | Accuracy | Changed-fact accuracy | Brier | ECE | NLL | False certainty |
|---|---:|---:|---:|---:|---:|---:|
| Provenance graph | 0.961223 | 0.932221 | 0.030112 | 0.019749 | 0.141263 | 0.018229 |
| Cellular, uncalibrated | 0.986272 | 0.963319 | 0.018285 | 0.056642 | 0.101418 | 0.007143 |
| Cellular + temperature | 0.986272 | 0.963319 | 0.015354 | 0.010933 | 0.070426 | 0.010603 |
| Cellular + Platt | 0.985950 | 0.963372 | 0.015364 | 0.010297 | 0.070389 | 0.010578 |
| Cellular + isotonic | 0.986260 | 0.963319 | 0.012732 | 0.001966 | 0.059250 | 0.006399 |

## Primary finding

Temperature scaling with T = 0.600483 reduced cellular ECE from 0.056642 to 0.010933 on untouched worlds, while preserving every binary decision. This beats the provenance graph's ECE of 0.019749 on the same worlds.

Because T is below 1, the raw cellular probabilities were systematically underconfident rather than overconfident. Sharpening the logits corrected the confidence mapping.

## Decision

Temperature scaling is the clean default calibration repair because it:

- preserves all classifications;
- preserves accuracy and changed-fact accuracy exactly;
- leaves active recruitment and operation counts unchanged;
- reduces ECE by 80.7%;
- reduces Brier by 16.0%;
- reduces NLL by 30.6%;
- beats the graph on calibration as well as accuracy, drift performance, Brier, and compute.

Isotonic regression produced the best probability metrics, but it slightly changed threshold decisions and is more flexible. It should remain a secondary benchmark rather than the default claim.

## Invariants

- Average activated reports: 4.0541
- Operations per correct: 9.6731
- Inference operations per correct: 5.0839
- Learning operations per correct: 4.5892
- Temperature-scaled classifications identical to uncalibrated classifications: yes
