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

`tcm.ActiveCoalitionCellular` (alias `tcm.ActiveExperimentalCellular`) with
`SessionRelevanceFinanceNewsStream` is the active experimental TCM for this
harness. Wave XI (`BatchedReserveCellular`) stays the frozen synthetic
reference.

ACI: prior-free likelihood-ratio evidence; null channel (empty / cheerleader /
near-zero Δ) via PE+|ρ| anti-prior mix; recruit by |Δ|; free-energy certify
when unread mass cannot flip. Sealed virgin `confirmation8`: flip **52.6%**,
pred-up **53.7%**, gate passed. Defaults match that freeze. Details:
`REPORT_ACTIVE_COALITION.md`, `REPORT_ACTIVE_COALITION_CONFIRMATION.md`.

### Lineage (confirmed ancestors / failed screens)

- **Relevance** (`SensoryGatedCellular`): first fresh-company PASS (flip 28.1%).
  `REPORT_RELEVANCE.md`.
- **Clean evidence** (development): session cutoffs + sign-preserving trust.
  `REPORT_CLEAN.md`.
- **Skew correction**: confirmation3 **FAIL**. `REPORT_SKEW_CONFIRMATION.md`.
- **Silence escape**: confirmation4 **PASS** (flip 52.2%) — ACI null-channel
  ancestor. `REPORT_SILENCE_ESCAPE_CONFIRMATION.md`.
- **Diagnostic contrast v1/v2**: confirmation5/7 **FAIL**.

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
- `REPORT_SILENCE_ESCAPE.md` — PE/rho null-sensation escape (development)
- `REPORT_SILENCE_ESCAPE_CONFIRMATION.md` — virgin confirmation4 **PASS**
  (52.2% flip)
- `REPORT_ACTIVE_COALITION.md` — ACI contact-tail freeze
- `REPORT_ACTIVE_COALITION_CONFIRMATION.md` — virgin confirmation8 **PASS**
  (52.6% flip); active experimental bake

## Process honesty

- `contact` (first 70% of trading days) is first-contact exploratory territory.
- `holdout` (last 30%) is the confirmatory slice for locked v0 models.
- Mechanism changes informed by holdout retire it as a clean test bed.
