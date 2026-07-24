# Baked diagnosis — prospective weather (real data)

Frozen after whiteboard autopsy validation. **No retune.**
Artifact: `results/dbsa_weather_baked_diagnosis.json`

**Bed:** `prospective_weather/` (not confirmation3)  
**Events:** 708 · **Decision days:** 59 · **Sources:** 6 NWP `previous_day1`  
**Roster:** ATL PHL MSP MUC LIS HEL TPE KUL LIM NBO PER DXB  
**Span:** 2026-05-25 → 2026-07-23 (archive backfill disclosed)

---

## Method table (raw prequential Brier)

| Method | Brier | Acc | Used |
|---|---:|---:|---:|
| **Majority** | **0.162412** | 0.756 | 5.95 |
| Aware Christmas (bow on, ESSC off) | 0.172395 | — | ~3.56 |
| **Aware+ESSC** (DBSA default) | **0.172849** | 0.761 | **3.538** |
| Fixed-Share | 0.178110 | 0.744 | 5.95 |
| Agree-discount Bayes | 0.183342 | 0.766 | 5.95 |
| Fading Bayes | 0.191295 | 0.766 | 5.95 |
| PWDR | 0.214939 | 0.698 | 5.95 |
| ACI | 0.214657 | 0.675 | 2.99 |
| Persistence | 0.526836 | 0.476 | 5.95 |

Diagnostic (not a gate row): PWDR whitened base alone **0.166096**.

**Gap Aware+ESSC − Majority = +0.010437**

---

## Spectrum (real vote correlation)

| Quantity | Value |
|---|---:|
| Sources | 6 |
| λ₁ / Tr(C) | **0.550169** |
| Mean pairwise ρ | **0.454949** |
| ESS (equal-weight) | **1.832** |
| Majority wrong rate | **0.244350** |

Spike-dominated. Weather is λ₁-heavy.

---

## Variance tax (Aware+ESSC vs Majority)

\[
\Delta\mathrm{BS}\;\approx\;\mathrm{Var}(p-p_{\mathrm{maj}})-2\,\mathrm{Cov}\bigl(p-p_{\mathrm{maj}},\,y-p_{\mathrm{maj}}\bigr)
\]

| Quantity | Value |
|---|---:|
| Var(δp) | 0.028238 |
| Cov(δp, y−p_maj) | 0.008905 |
| Cov / Var | **0.315343** (< ½ break-even) |
| Predicted tax Var−2Cov | **0.010429** |
| Observed ΔBrier | **0.010437** |
| Prediction error | **−8.1×10⁻⁶** |

---

## ESSC oppose slice (real)

| Quantity | Value |
|---|---:|
| ESSC applied | 632 / 708 |
| Oppose majority | **104** |
| Mean used / roster | 3.538 / 5.946 (**u = 0.595**) |
| Maj accuracy on oppose | **0.5769** |
| Shadow accuracy on oppose | **0.4231** |
| Aware Brier on oppose | 0.2612 |
| Majority Brier on oppose | 0.2438 |

---

## Day blocks (59 days)

| Quantity | Value |
|---|---:|
| Mean day Δ (Aware−Maj) | +0.010437 |
| Median day Δ | +0.012231 |
| Days Aware worse | **59.3%** |
| Days Aware better | **40.7%** |

---

## Claims baked (all true on this artifact)

1. Weather is spike-dominated (λ₁ ≥ 0.5)
2. Cov/Var below physicist break-even (½)
3. Variance-tax formula matches the observed gap (|err| < 10⁻⁴)
4. On oppose-slice, majority beats shadow
5. Majority leads raw Brier

**Bar unchanged:** crush Majority **0.162412** on this bed. Not done.

**Why majority wins (deeper):** see [`WHY_MAJORITY_WINS.md`](WHY_MAJORITY_WINS.md) —
majority is near-optimal on this λ₁ bed; even full-mass learners lose; the
missing organ is an emit-time Cov/Var>½ leave-maj rebate (or restoring
equal-weight full pooling).
