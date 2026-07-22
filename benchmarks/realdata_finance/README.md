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

## Active experimental model

`tcm.SensoryGatedCellular` is the first real-data front end that survived a
predeclared fresh-company check. It works with `RelevanceFinanceNewsStream`:
only titles that explicitly name the company become reports; sensory silence
keeps the existing memory. The model also calibrates publisher base-rate bias
and discounts redundant same-direction reports.

Fresh-company confirmation: change detection 22.1% → 28.1% (+5.9 pts,
p=0.006), while using 64% fewer reports. It remains experimental; full limits
are in `REPORT_RELEVANCE.md`.

### Dead-pixel cleanup (development)

`SessionRelevanceFinanceNewsStream` + `tcm.CleanEvidenceCellular` fix the next
impurities: session cutoffs, adjacent-session flips, no sign-reversal by
memory, and delayed-correctness source trust. Contact-tail change detection
moves to ~41% with zero sign-reversal, but prediction-up rises to ~70% because
publisher Positive skew is no longer hidden. Details: `REPORT_CLEAN.md`.

### Skew correction (development; confirmation failed)

`tcm.SkewCorrectedCellular` subtracts publisher Positive base-rate inflation
from all-Positive coalitions. Contact-tail looked strong (~47% flip), but the
predeclared virgin `confirmation3` look **failed** (42.2% flip, no gain vs
clean). Details: `REPORT_SKEW.md`, `REPORT_SKEW_CONFIRMATION.md`.

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
- `REPORT_TRANSITION.md` — failed fresh-company test of the brain-shaped
  transition-investigation circuit (not baked in)
- `REPORT_RELEVANCE.md` — successful fresh-company confirmation of the active
  sensory relevance front end
- `REPORT_WAVE_XVIII.md` — finance-development failure of the three-part
  prediction-error trust loop (not promoted; no Weather run)
- `REPORT_CLEAN.md` — session/cutoff + sign-preserving evidence cleanup and
  the new purity / performance markers
- `REPORT_SKEW.md` — publisher Positive base-rate correction (contact only)
- `REPORT_SKEW_CONFIRMATION.md` — virgin confirmation3 **fail** (42.2% flip)

## Process honesty

- `contact` (first 70% of trading days) is first-contact exploratory territory.
- `holdout` (last 30%) is the confirmatory slice for locked v0 models.
- Mechanism changes informed by holdout retire it as a clean test bed.
