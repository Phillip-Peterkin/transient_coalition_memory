# ESSC first look — does not crush majority on weather

Start from Aware. PWDR rejected. Christmas bow off the crush path.
**Bar held:** crush full-source majority on raw prequential Brier.

## Locked knobs (before scoring)

| Knob | Value |
|---|---|
| `essc_enabled` | True |
| `essc_disable_christmas_bow` | True |
| `essc_credit_init` | 0.20 |
| `essc_max_credit` | 0.50 |
| `essc_lo_cap` | 1.25 |
| `essc_credit_lr` | 0.08 |
| `essc_disagree_emphasis` | 2.5 |

Code: `AwareCoalitionCellular` ESSC path (`evaluate.ESSC_PARAMS` / `AWARE_PARAMS`).
Defaults remain **off** for sealed non-DBSA cells.

## Gross bugs caught in review (fixed before score)

1. Unread must be **ACI leftover diversified rows** — not a second diversify pass (double-count skips / wrong set).
2. Source IDs are **strings** — do not `int()` them in block collapse.

Unit tests: `benchmarks/dbsa/tests/test_essc.py` (+ mnemosheath / correlation regressions).

## Prospective weather

| Method | Brier | Acc | Used |
|---|---:|---:|---:|
| **Majority** | **0.1624** | 0.756 | 5.95 |
| Aware+ESSC | 0.1728 | 0.761 | **3.54** |
| Aware Christmas (prior look) | 0.1724 | 0.758 | 3.56 |
| Fixed-Share | 0.1781 | 0.744 | 5.95 |
| PWDR (rejected) | 0.2149 | 0.698 | 5.95 |

ESSC applied on 632/708 events; opposed majority on 104.
Mean used **3.54** — selective stop held.

### Falsifiable oppose-slice — FAIL on weather

| Slice | Aware+ESSC | Majority |
|---|---:|---:|
| Shadow opposes majority (n=104) | 0.2612 | **0.2438** |
| Shadow agrees (applied, n≈528) | 0.1444 | **0.1340** |

**Verdict (weather):** does **not** crush majority. Gap ≈ Christmas Aware; not a PWDR-scale regression. No silent retune.

## Synthetic 24-seed × 400 rounds (mean Brier)

| World | Majority | Aware+ESSC | Δ |
|---|---:|---:|---:|
| independent_stable | 0.0756 | 0.0760 | +0.0004 |
| correlated_stable | 0.0998 | 0.1200 | +0.0201 |
| abrupt_drift | 0.0882 | **0.0363** | **−0.0519** |
| recurring_crossover | 0.0956 | **0.0524** | **−0.0433** |
| adversarial_switch | 0.0614 | **0.0489** | **−0.0125** |
| bursty_missing | 0.0801 | **0.0771** | **−0.0031** |

On synthetic drift / crossover / adversarial worlds, ESSC **beats** majority.
Weather still does not. Bar unmet on the held real lane.

## Artifact

`results/dbsa_essc_first_look.json`

## Honesty

- Crush majority remains the destination; weather FAIL stands.
- Selective activation retained; no Christmas blend; no PWDR residual.
- Synthetic wins are not a weather substitute.
