# DBSA-v1 200-seed contract — FAIL

Protocol: [`PROTOCOL.md`](PROTOCOL.md)  
Simulator: `contract_simulator.py` + `contract/v1_worlds.json`  
Run: **200** fixed seeds × 800 events × six worlds (~19 wall minutes)  
Primary: prequential Brier  
Non-inferiority: δ = 0.005, one-sided 97.5% paired-seed CI upper bound  
Delay: Fixed-Share and AdaHedge update only on queue release  
Resources: Pareto axes (no hard activation threshold)

No ACI/Aware retune after this look. Screen (24-seed) remains
[`REPORT_CONTRACT_SCREEN.md`](REPORT_CONTRACT_SCREEN.md).

## Gate

**`pilot_passes=False`**

| world | Aware vs Fixed-Share ΔBrier | CI97.5 upper | δ=0.005 pass |
|---|---:|---:|---|
| independent_stable | −0.0051 | −0.0042 | **pass** |
| correlated_stable | +0.0631 | +0.0644 | FAIL |
| abrupt_drift | +0.0904 | +0.0916 | FAIL |
| recurring_crossover | +0.0799 | +0.0811 | FAIL |
| adversarial_switch | +0.0045 | +0.0055 | FAIL |
| bursty_missing | −0.0134 | −0.0126 | **pass** |

Post-shift Brier vs Fixed-Share also fails in `abrupt_drift`
(Δ ≈ +0.215) and `adversarial_switch` (Δ ≈ +0.153).

Same qualitative pattern as the 24-seed screen: non-inferiority only on
`independent_stable` and `bursty_missing`.

## Method picture (mean Brier)

| world | fade-Bayes | Fixed-Share | AdaHedge | Aware | ACI |
|---|---:|---:|---:|---:|---:|
| independent_stable | **0.036** | 0.097 | 0.163 | 0.092 | 0.092 |
| correlated_stable | **0.104** | 0.127 | 0.185 | 0.190 | 0.192 |
| abrupt_drift | **0.027** | 0.048 | 0.214 | 0.139 | 0.140 |
| recurring_crossover | **0.054** | 0.064 | 0.225 | 0.144 | 0.144 |
| adversarial_switch | **0.033** | 0.096 | 0.202 | 0.101 | 0.103 |
| bursty_missing | **0.051** | 0.109 | 0.176 | 0.096 | 0.100 |

Fading causal source-Bayes remains the strongest nontrivial comparator.
Delayed AdaHedge is an honest expert row under the same queue-release
discipline; it does not beat Fixed-Share here (no share mixing / weaker
under delay+drift).

Aware stays downstream-sparse (~4–5 of 12 activated) and ~2× slower than ACI.

## Prospective weather

Collection continues; scoring protocol drafted and **closed**
([`prospective_weather/SCORING_PROTOCOL.md`](prospective_weather/SCORING_PROTOCOL.md)).
Open conditions not yet met (need ≥60 collection days).

Artifact: `results/dbsa_v1_contract_200.json`.
