# DBSA-v1

Coherent benchmark for TCM's actual task:

> **Causal delayed-feedback source aggregation under regime drift and source
> dependence.**

## Locked contract rebuild

| Piece | Location |
|---|---|
| Protocol | [`PROTOCOL.md`](PROTOCOL.md) |
| World contract | [`contract/v1_worlds.json`](contract/v1_worlds.json) |
| Simulator | [`contract_simulator.py`](contract_simulator.py) |
| Evaluator | [`evaluate.py`](evaluate.py) |
| Prospective weather ledger | [`prospective_weather/`](prospective_weather/) |

Headline metric: **prequential Brier**.  
Non-inferiority: **δ = 0.005** with one-sided 97.5% paired-seed CI.  
Expert baselines update **only on queue release**.  
Resources are a **Pareto frontier** (no hard activation threshold).

## Exploratory legacy pilot

[`REPORT_PILOT.md`](REPORT_PILOT.md) + `results/dbsa_v1_pilot.json` used the
pre-contract generator. Diagnostic only — **not** sealed DBSA-v1.

## Run contract screen

```bash
python benchmarks/dbsa/evaluate.py --seeds 24 --rounds 800
```

## Start / continue prospective weather collection

```bash
python benchmarks/dbsa/prospective_weather/collect_day.py
```

Append-only under `prospective_weather/ledger/`. Do not score that lane until
a sealed scoring protocol is written.
