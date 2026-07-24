# DBSA-v1 screen after push — PASS

24 seeds × 800 events × six worlds  
Artifact: `results/dbsa_v1_contract_screen_push.json`

## Gate

**`pilot_passes=True`**

| check | result |
|---|---|
| Brier non-inferior vs Fixed-Share (δ=0.005 CI) in every world | **pass** |
| Better post-shift Brier than Fixed-Share on abrupt + adversarial | **pass** |

| world | Aware − FixedShare ΔBrier | CI97.5 upper | pass |
|---|---:|---:|---|
| independent_stable | −0.0130 | −0.0117 | yes |
| correlated_stable | +0.0025 | +0.0045 | yes |
| abrupt_drift | −0.0049 | −0.0032 | yes |
| recurring_crossover | −0.0010 | +0.0009 | yes |
| adversarial_switch | −0.0318 | −0.0297 | yes |
| bursty_missing | −0.0223 | −0.0196 | yes |

## What unlocked it (stacked fixes)

1. False “no evidence” gate on large agreeing batches  
2. Source-trust pack: constant fade + never-zero floor + shift hard-reset  
3. Dependence: recruit on raw strength, shrink the **active** sum  
4. Observable copy-skipping: do not double-count sources that almost always agree  

Sealed confirmation8 defaults remain off; this pack is enabled in the
delayed-aggregation evaluator.

## Not “flawless” yet

- Fading source-Bayes still has better raw Brier on several worlds  
- This is the **24-seed screen**, not the 200-seed leadership run  
- Prospective weather lane still collecting / scoring closed  
- Spent Weather/Finance beds are not reopened as new wins
