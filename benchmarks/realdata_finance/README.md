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

## Cure ablation

`cures.py` defines `CuredCellular`: the frozen Wave XI reference plus five
independently toggleable cures grounded in the two Peterkin papers (HRF
energetic gating; fitted operator geometry). With an empty cure set it
reproduces `BatchedReserveCellular` exactly.

```bash
python benchmarks/realdata_finance/ablation.py            # horizon 1 (primary)
python benchmarks/realdata_finance/ablation.py --horizon 3
```

Each cure is compared to the frozen baseline with a paired bootstrap (5,000
resamples) for accuracy and flip detection. Writeup: `REPORT_ABLATION.md`.

## Outputs

- `results/results.json` — baseline metrics by split (`contact`/`holdout`/`all`)
- `results/summary.csv` — flat table
- `results/ablation.json` — cure ablation with bootstrap CIs + paired tests
- `REPORT.md` — first locked-parameter writeup
- `REPORT_ABLATION.md` — five-cure ablation writeup

## Process honesty

- `contact` (first 70% of trading days) is first-contact exploratory territory.
- `holdout` (last 30%) is the confirmatory slice for locked v0 models.
- Mechanism changes informed by holdout retire it as a clean test bed.
