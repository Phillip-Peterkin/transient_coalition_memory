# DBSA-v1 contract screen — FAIL

Protocol: contract rebuild in [`PROTOCOL.md`](PROTOCOL.md)  
Simulator: `contract_simulator.py` + `contract/v1_worlds.json`  
Run: 24 fixed seeds × 800 events × six worlds  
Primary: prequential Brier  
Non-inferiority: δ = 0.005, one-sided 97.5% paired-seed CI upper bound  
Delay: Fixed-Share updates only on queue release  
Resources: Pareto axes (no hard activation threshold)

Exploratory pre-contract pilot remains diagnostic-only
([`REPORT_PILOT.md`](REPORT_PILOT.md)).

## Gate

**`pilot_passes=False`**

| world | Aware vs Fixed-Share ΔBrier | CI97.5 upper | δ=0.005 pass |
|---|---:|---:|---|
| independent_stable | −0.0046 | −0.0022 | **pass** |
| correlated_stable | +0.0598 | +0.0632 | FAIL |
| abrupt_drift | +0.0897 | +0.0934 | FAIL |
| recurring_crossover | +0.0808 | +0.0833 | FAIL |
| adversarial_switch | +0.0051 | +0.0079 | FAIL |
| bursty_missing | −0.0133 | −0.0111 | **pass** |

Post-shift Brier vs Fixed-Share also fails in `abrupt_drift` and
`adversarial_switch` (Aware worse).

## Strongest causal comparator

Fading online source-Bayes remains the Brier leader in every nontrivial
drift/adversarial/missing world on this contract screen. Aware stays
downstream-sparse (~4–5 of 12 activated) and slower.

## Prospective weather

Append-only collection started: `prospective_weather/ledger/2026-07-23/`
(`sha256` recorded in `INDEX.jsonl`). No scoring of that lane yet.

Artifact: `results/dbsa_v1_contract_screen.json`.
No retune follows this screen.
