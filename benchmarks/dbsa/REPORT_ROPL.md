# ROPL first look — crushes majority on real weather

Implements the combined organ from [`CONSENSUS_COMBINED_LEAVE.md`](CONSENSUS_COMBINED_LEAVE.md):

\[
p \;=\; p_{\mathrm{maj}} \;+\; g_t\,(p_{\mathrm{coalition}}-p_{\mathrm{maj}}),
\quad
g_t=\mathrm{clip}(\widehat{\mathrm{Cov}/\mathrm{Var}},\,0,\,1)
\]

Coalition path = Aware+ESSC (Christmas bow off).  
\(g_t\) from **delayed** rolling Cov/Var on \((p_{\mathrm{internal}}-p_{\mathrm{maj}},\,y-p_{\mathrm{maj}})\).  
Cold start: \(g=0\) until `rebate_min_updates`.

**Bar held:** crush Majority **0.162412**.  
**Verdict: PASS — crushes majority.**

Artifact: `results/dbsa_ropl_first_look.json`

---

## Locked knobs (before scoring)

| Knob | Value |
|---|---|
| `ropl_enabled` | True |
| `ropl_g_mode` | `covvar` |
| `rebate_window` | 120 |
| `rebate_min_updates` | 40 |
| `pool_restore_enabled` | False (mutually exclusive) |
| ESSC stack | same as `ESSC_PARAMS` (bow off) |

Code: `AwareCoalitionCellular` + `evaluate.AWARE_ROPL_PARAMS`  
Method row: `aware_ropl`  
Defaults **off** for sealed non-DBSA cells.

---

## Gross-bug checks

- \(g_t\) uses **delayed** labels only (queue-release)
- Cov/Var tracks **p_internal** (coalition leave), not the shrunk emit
- Christmas bow off under ROPL
- Cold start → \(g=0\) → emit majority
- \(g\) clipped to \([0,1]\)
- Honest `used` = full roster whenever \(g<1\)
- ROPL ⊕ Pool-Restore rejected at construct
- Unit tests: `tests/test_ropl.py` (8 passed; 23 with ESSC/PRG suite)

---

## Prospective weather (708 events, 59 days)

### Method table

| Method | Brier | Acc | Used |
|---|---:|---:|---:|
| **Aware+ROPL** | **0.159122** | 0.761 | **5.946** |
| **Majority** | **0.162412** | 0.756 | 5.946 |
| Aware+Pool-Restore | 0.162697 | 0.767 | 5.397 |
| Aware+ESSC | 0.172849 | 0.761 | 3.538 |
| Fixed-Share | 0.178110 | 0.744 | 5.946 |
| Agree-discount Bayes | 0.183342 | 0.766 | 5.946 |
| Fading Bayes | 0.191295 | 0.766 | 5.946 |
| PWDR | 0.214939 | 0.698 | 5.946 |
| ACI | 0.214657 | 0.675 | 2.990 |

| Quantity | Value |
|---|---:|
| Δ ROPL − Majority | **−0.003290** |
| Internal counterfactual (always \(g=1\)) | 0.172849 |
| Mean \(g_t\) | **0.329** |
| Median \(g_t\) | 0.354 |
| Final \(\hat\rho\) | 0.367 |
| \(g=0\) / partial / full frac | 0.119 / **0.881** / 0.000 |
| Days better / worse / tie (59) | **0.508** / 0.373 / 0.119 |

---

## What changed vs failed singles

| Single | Failure mode | ROPL fix |
|---|---|---|
| ESSC \(g=1\) | Full leave tax (+0.010) | Shrink to \(\hat\rho\approx0.33\) |
| Pool-Restore \(g\in\{0,1\}\) | Waits for \(\rho>½\); mostly maj | Continuous \(g=\hat\rho\) |
| Christmas bow | Majority-*attracting*; can't pass | Bow off; blend *is* \(g^\star\) toward skill |
| PWDR \(+r\) | Unshrunk delayed residual bomb | Same direction, ridge-shrunk |

---

## Synthetic 24-seed × 400 rounds (mean Brier)

| World | Majority | Aware+ESSC | Pool-Restore | **ROPL** | Δ ROPL−Maj |
|---|---:|---:|---:|---:|---:|
| independent_stable | 0.0756 | 0.0760 | 0.0716 | **0.0686** | **−0.0069** |
| correlated_stable | 0.0998 | 0.1200 | 0.1008 | **0.0995** | **−0.0004** |
| abrupt_drift | 0.0882 | 0.0363 | 0.0384 | **0.0374** | **−0.0508** |
| recurring_crossover | 0.0956 | 0.0524 | 0.0549 | **0.0556** | **−0.0400** |
| adversarial_switch | 0.0614 | 0.0489 | 0.0474 | **0.0460** | **−0.0154** |
| bursty_missing | 0.0801 | 0.0771 | 0.0744 | **0.0724** | **−0.0077** |

ROPL keeps drift/crossover crush and **does not eat** the correlated_stable tax.

---

## Honesty

- Crush majority on raw prequential Brier: **PASS**
- Knobs locked before scoring; no hindsight-fixed \(g=0.315\)
- Honest Used ≈ maj roster (**5.946**) — **not** the Used~3.5 incredible bar
- Incredible sparse crush remains a separate sequel
- No ACS/LKS rename from this alone; organ earned a name (**ROPL**)
- No silent retune after look

---

## Status

Weather barrier broken under freeze protocol.  
Next (optional): phase-2 pre-registration for Used ≤ 3.6 **and** Brier < maj — not claimed here.
