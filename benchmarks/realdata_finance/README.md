# Real-data harness: financial news → next-day direction

First **untouched** real-data stream in this repository for Transient Coalition
Memory. Protocol details and non-claims: [`PROTOCOL.md`](PROTOCOL.md).
Vision / weakness ledger: [`docs/NORTH_STAR.md`](../../docs/NORTH_STAR.md).

## What it tests

Multi-publisher financial news (Benzinga, GlobeNewswire, InvestorPlace, …)
produces sparse report coalitions for liquid US equities. The label is the
**next trading day's close-to-close direction** from Yahoo Finance.

This is past pure simulation: real publishers, real prices, delayed feedback,
and the metrics the north star demands (persistence oracle + flip detection).

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
pip install -r benchmarks/realdata_finance/requirements.txt
```

## Run

```bash
python benchmarks/realdata_finance/download_data.py   # caches slim parquet under data/
python benchmarks/realdata_finance/evaluate.py        # writes results/
```

Locked Wave XI cellular / provenance-graph hyperparameters are used — no
retuning on this stream in v0.

## Outputs

- `results/results.json` — full metrics by split (`contact` / `holdout` / `all`)
- `results/summary.csv` — flat table
- `REPORT.md` — human-readable first-run writeup (generated after evaluation)

## Process honesty

- `contact` (first 70% of trading days) is first-contact exploratory territory.
- `holdout` (last 30%) is the confirmatory slice for locked v0 models.
- Mechanism changes informed by holdout retire it as a clean test bed.
