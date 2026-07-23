# DBSA-v1

The coherent benchmark for TCM's actual task:

> **Causal delayed-feedback source aggregation under regime drift and source
> dependence.**

It is not static truth discovery. All rows see the same named source reports,
predict before outcome arrival, and update only when the shared delayed-label
queue releases truth.

## Run

```bash
python benchmarks/dbsa/evaluate.py --seeds 24 --rounds 800
```

The first sealed pilot is a **FAIL** for Aware: see
[`REPORT_PILOT.md`](REPORT_PILOT.md). No retune is authorized from that result.

## Contents

- `PROTOCOL.md` — frozen data-generating worlds, rows, metrics, and pilot gate
- `simulator.py` — six deterministic, hidden-regime source worlds
- `baselines.py` — causal baselines only
- `evaluate.py` — one shared feedback-queue evaluator
- `results/dbsa_v1_pilot.json` — exact first-run artifact
