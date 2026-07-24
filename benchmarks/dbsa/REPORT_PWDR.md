# PWDR first look — does not crush majority

Room consensus object implemented, bug-checked, tested, then scored.
**Bar held:** crush full-source majority on raw prequential Brier.

## Locked knobs (before scoring)

| Knob | Value |
|---|---|
| `PWDR_RIDGE` | 0.05 |
| `PWDR_COV_FORGET` | 0.99 |
| `PWDR_RESIDUAL_LR` | 0.05 |
| `PWDR_RESIDUAL_L2` | 0.01 |
| `PWDR_RESIDUAL_CLIP` | 0.35 |
| `PWDR_MIN_UPDATES` | 20 |

Code: `baselines.PrecisionWhitenedDelayedResidual` (`name="pwdr"`).

## Gross bugs found in review (fixed before re-score)

1. **`vote − truth` cannot make negative cross-terms** on binary labels → switched to signed-correctness residuals \(s_i\in\{+1,-1\}\).
2. **Sigmoid-of-whitened-logits did not reduce to majority when \(\Lambda\propto I\)** → switched to precision-weighted vote \(m=(\mathbf{1}^\top\Lambda v)/(\mathbf{1}^\top\Lambda\mathbf{1})\).

Unit tests: `tests/test_pwdr.py` (8 passed), plus existing `tests/test_dbsa.py`.

## Prospective weather (Christmas ledger, new method row)

| Method | Brier | Acc | Used |
|---|---:|---:|---:|
| **Majority** | **0.1624** | 0.756 | 5.95 |
| Aware | 0.1724 | 0.758 | 3.56 |
| Fixed-Share | 0.1781 | 0.744 | 5.95 |
| **PWDR** | **0.2149** | 0.698 | 5.95 |

Diagnostic (not a gate, not a retune):
- Whitened base alone \(m\): Brier **0.1661** (near majority)
- Full \(m+r\): Brier **0.2149** (residual head hurts under locked knobs)

### Falsifiable slice prediction — FAIL

| Slice | PWDR | Majority |
|---|---:|---:|
| High \(\lambda_1\) (top quartile, n=180) | 0.2030 | **0.1751** |
| Low \(\lambda_1\) (bottom quartile, n=180) | 0.2343 | **0.1549** |

Against-majority emissions (n=40): PWDR acc 0.425 vs majority-side acc 0.550.

**Verdict:** PWDR does **not** crush majority. Consensus object is instantiated; first look rejects it as a win under these knobs. No silent retune.

## Synthetic 24-seed × 400 rounds (mean Brier)

| World | Majority | PWDR | Δ (PWDR − Maj) |
|---|---:|---:|---:|
| independent_stable | 0.0756 | 0.1014 | +0.0258 |
| correlated_stable | 0.0998 | 0.1357 | +0.0358 |
| abrupt_drift | 0.0882 | 0.1793 | +0.0911 |
| recurring_crossover | 0.0956 | 0.1600 | +0.0644 |
| adversarial_switch | 0.0614 | 0.1060 | +0.0446 |
| bursty_missing | 0.0801 | 0.1191 | +0.0390 |

Majority ahead on every world. Object not yet the crusher.

## Artifact

`results/dbsa_pwdr_first_look.json`

## Honesty

- Metrics not softened.
- Christmas bow path not used.
- Weather bed is the prospective ledger; PWDR is a new row, not a retune of Aware.
- Next move (if any) must change the object or declare new knobs **before** a fresh bed — not chase this look.
