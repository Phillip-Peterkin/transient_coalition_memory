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

## Results

- Contract screen (24-seed, sealed post-rebuild): **FAIL** —
  [`REPORT_CONTRACT_SCREEN.md`](REPORT_CONTRACT_SCREEN.md)
- Leadership synthetic contract (200-seed): **FAIL** —
  [`REPORT_CONTRACT_200.md`](REPORT_CONTRACT_200.md)
- Gate bug fix (false “no evidence” on large agreeing batches):
  [`REPORT_GATE_BUG.md`](REPORT_GATE_BUG.md)
- Source-trust regime pack:
  [`REPORT_SOURCE_FORGET.md`](REPORT_SOURCE_FORGET.md)
- Push screen (fade + floor + shift + dependence/copy-skip): **PASS** —
  [`REPORT_SCREEN_PUSH.md`](REPORT_SCREEN_PUSH.md)
- Exploratory pre-contract pilot: diagnostic only —
  [`REPORT_PILOT.md`](REPORT_PILOT.md)

## Run contract screen / leadership

```bash
# Screening (24 seeds)
python benchmarks/dbsa/evaluate.py --seeds 24 --rounds 800

# Leadership synthetic contract (200 seeds)
python benchmarks/dbsa/evaluate.py --seeds 200 --rounds 800 \
  --out benchmarks/dbsa/results/dbsa_v1_contract_200.json
```

## Start / continue prospective weather collection

```bash
python benchmarks/dbsa/prospective_weather/collect_day.py
```

Append-only under `prospective_weather/ledger/`. Scoring is sealed/closed —
see [`prospective_weather/SCORING_PROTOCOL.md`](prospective_weather/SCORING_PROTOCOL.md).
