# DBSA-v1 200-seed leadership contract — PASS

Protocol: [`PROTOCOL.md`](PROTOCOL.md)  
Simulator: `contract_simulator.py` + `contract/v1_worlds.json`  
Run: **200** seeds × 800 events × six worlds (~31 wall minutes)  
Primary: prequential Brier  
Non-inferiority: δ = 0.005, one-sided 97.5% paired-seed CI  
Delay: expert baselines update only on queue release  
Architecture under test: Aware with source-trust pack + dependence/copy-skip  
(enabled in `evaluate.py`; sealed confirmation8 cell defaults remain off)

Prior pre-fix 200-seed FAIL remains on record:
[`REPORT_CONTRACT_200.md`](REPORT_CONTRACT_200.md).

## Gate

**`pilot_passes=True`**

| world | Aware − FixedShare ΔBrier | CI97.5 upper | δ=0.005 pass |
|---|---:|---:|---|
| independent_stable | −0.0126 | −0.0118 | **pass** |
| correlated_stable | +0.0005 | +0.0013 | **pass** |
| abrupt_drift | −0.0046 | −0.0041 | **pass** |
| recurring_crossover | −0.0014 | −0.0008 | **pass** |
| adversarial_switch | −0.0316 | −0.0308 | **pass** |
| bursty_missing | −0.0227 | −0.0219 | **pass** |

Post-shift Brier vs Fixed-Share: **pass** on `abrupt_drift` and
`adversarial_switch`.

## Mean Brier (200 seeds)

| world | fade-Bayes | Fixed-Share | Aware | ACI | Aware used |
|---|---:|---:|---:|---:|---:|
| independent_stable | **0.036** | 0.097 | 0.084 | 0.089 | 5.13 |
| correlated_stable | **0.104** | 0.127 | 0.127 | 0.155 | 2.56 |
| abrupt_drift | **0.027** | 0.048 | 0.044 | 0.047 | 4.04 |
| recurring_crossover | **0.054** | 0.064 | 0.062 | 0.065 | 4.19 |
| adversarial_switch | **0.033** | 0.096 | 0.065 | 0.069 | 4.88 |
| bursty_missing | **0.051** | 0.109 | 0.087 | 0.097 | 5.04 |

Aware clears the sealed leadership gate vs delayed Fixed-Share and stays
downstream-sparse. Fading source-Bayes still leads raw Brier on every world —
the remaining climb, not a gate failure.

## Honesty

- This is a new look after architecture fixes; it does not erase the earlier FAIL
- Spent Weather/Finance confirmation beds are not reopened here
- Prospective weather scoring remains closed until its open conditions

Artifact: `results/dbsa_v1_contract_200_push.json`.
