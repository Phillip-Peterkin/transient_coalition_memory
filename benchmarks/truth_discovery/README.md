# Truth-discovery literature benchmark

Stock + Weather fusion beds from the truth-discovery literature, with that
field’s review methods — and efficiency.

## Why this harness

Sandbox Stock/Weather ledgers are incomplete or tainted. Reviewers who know
the TD literature will ask for:

1. **TruthFinder** (Yin et al. 2008)
2. **CRH** (Li et al. 2014)
3. **CATD** (Li et al. 2015)
4. A **streaming** TD variant
5. Wall/CPU efficiency vs TCM / Aware

This harness downloads the public Luna Dong fusion datasets and runs those
methods side-by-side with `AwareCoalitionCellular` (binary Stock track).

## Quick start

```bash
python benchmarks/truth_discovery/download_data.py
python benchmarks/truth_discovery/prepare_slim.py
python benchmarks/truth_discovery/evaluate.py
```

Slim scored tables live in `data/slim/` (committed). Raw zips are downloaded
on demand (large; not committed).

## Protocol

See [`PROTOCOL.md`](PROTOCOL.md).

## Outputs

- `results/truth_discovery_benchmark.json`
- `REPORT.md` (filled after the first sealed look)
