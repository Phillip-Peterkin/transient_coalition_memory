# Pool-Restore Gate — first look on real weather

Implements the organ from [`WHY_MAJORITY_WINS.md`](WHY_MAJORITY_WINS.md):

> Emit equal-weight full-roster majority unless a *delayed* rolling
> \(\mathrm{Cov}/\mathrm{Var}\) rebate on \((p_{\mathrm{internal}}-p_{\mathrm{maj}},\,y-p_{\mathrm{maj}})\)
> clears **½** — then allow Aware+ESSC leave.

**Bar held:** crush Majority **0.162412**.  
**Verdict:** gap closed (≈ match). **Does not crush.**

Artifact: `results/dbsa_pool_restore_first_look.json`

---

## Locked knobs (before scoring)

| Knob | Value |
|---|---|
| `pool_restore_enabled` | True |
| `rebate_threshold` | **0.5** |
| `rebate_window` | 120 |
| `rebate_min_updates` | 40 |
| ESSC stack | same as `ESSC_PARAMS` (bow off) |

Code: `AwareCoalitionCellular` + `evaluate.AWARE_POOL_RESTORE_PARAMS`  
Method row: `aware_pool_restore`  
Defaults **off** for sealed non-DBSA cells.

---

## Gross-bug checks

- Rebate uses **delayed** labels only (queue-release)
- Cov/Var tracks **p_internal** (leave attempt), not the maj overwrite
- Christmas bow off under PRG
- Cold start / rebate ≤½ → emit majority (including null batches with reports)
- When emitting maj, `used` = full roster (honest)
- Unit tests: `tests/test_pool_restore.py` (6 passed)

---

## Prospective weather (708 events, 59 days)

### Method table

| Method | Brier | Acc | Used |
|---|---:|---:|---:|
| **Majority** | **0.162412** | 0.756 | 5.946 |
| **Aware+Pool-Restore** | **0.162697** | **0.767** | **5.397** |
| Aware+ESSC (no restore) | 0.172849 | 0.761 | 3.538 |
| Aware Christmas | 0.172395 | — | ~3.56 |
| Fixed-Share | 0.178110 | 0.744 | 5.946 |
| Fading Bayes | 0.191295 | 0.766 | 5.946 |
| PWDR | 0.214939 | 0.698 | 5.946 |

| Gap | Value |
|---|---:|
| Pool-Restore − Majority | **+0.000285** |
| ESSC − Majority (prior) | +0.010437 |
| Tax that ESSC paid | +0.010429 |

**The +0.01 variance tax is gone.** Remaining delta is noise-scale (~3×10⁻⁴), not a crush.

### Gate behavior on weather

| Quantity | Value |
|---|---:|
| Emit majority | **540 / 708 (76.3%)** |
| Leave allowed | **168 / 708 (23.7%)** |
| Final rebate est | 0.392 (< 0.5 — gate mostly closed) |
| Internal counterfactual Brier (always leave) | 0.171104 |
| Leave-slice PRG Brier | 0.162082 |
| Leave-slice Majority Brier | 0.160880 |
| Days exact tie vs maj | **76.3%** |
| Days PRG better | 13.6% |
| Days PRG worse | 10.2% |

Leave slice still slightly behind majority — rebate estimate is delayed/noisy, so some leaves are false opens. Net still ≈ maj.

---

## Synthetic 24-seed × 400 rounds (mean Brier)

| World | Majority | Aware+ESSC | **Pool-Restore** | Δ PRG−Maj |
|---|---:|---:|---:|---:|
| independent_stable | 0.0756 | 0.0760 | **0.0716** | **−0.0040** |
| correlated_stable | 0.0998 | 0.1200 | **0.1008** | +0.0010 |
| abrupt_drift | 0.0882 | 0.0363 | **0.0384** | **−0.0498** |
| recurring_crossover | 0.0956 | 0.0524 | **0.0549** | **−0.0408** |
| adversarial_switch | 0.0614 | 0.0489 | **0.0474** | **−0.0140** |
| bursty_missing | 0.0801 | 0.0771 | **0.0744** | **−0.0057** |

PRG keeps ESSC’s drift/crossover crush while **not** eating the correlated_stable tax (+0.001 vs ESSC’s +0.020).

---

## Interpretation

| Question | Answer |
|---|---|
| Did restoring the pooling organ close the weather gap? | **Yes** — +0.0104 → +0.0003 |
| Did we crush majority on weather? | **No** |
| Is the diagnosis operationally confirmed? | **Yes** — maj geometry was the lunch |
| What’s left for crush? | A *better* emit-time leave cue than delayed Cov/Var (still 0.39 < 0.5 on weather; false opens on 24% hurt slightly) |

---

## Honesty

- Not confirmation3; prospective weather bed
- Knobs locked before scoring; no silent retune
- Match ≠ crush; bar remains Majority **0.162412**
- Closest result to date — because it *is* mostly majority, with a gated leave that barely pays on this bed
