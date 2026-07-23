# Finance / news real-data protocol (v0)

Frozen before the first confirmatory evaluation on this stream.
This is **not** the contaminated July 2011 stock gold setup recorded in
`docs/NORTH_STAR.md`.

## Dataset

| Field | Value |
|---|---|
| News corpus | Hugging Face `NickyNicky/finance-financialmodelingprep-stock-news-sentiments-rss-feed` (142k rows) |
| Price labels | Yahoo Finance daily adjusted closes via `yfinance` |
| Universe | Fixed 40 liquid US equities (see `universe.py`) |
| Calendar window | 2022-08-12 → 2023-10-04 (news span); prices pulled with a short pad |

## Decision problem

For each `(symbol, trading_day t)` with at least one usable news report aligned
to `t`:

- **Predict** whether the next trading-day close-to-close return is positive:
  `truth = 1{ close[t+1] > close[t] }`.
- **Reports** are articles with `sentiment ∈ {Positive, Negative}` published on
  calendar date `t` (non-trading dates map forward to the next session).
  Each report is `(source_id, context_id=0, y)` with `y=1` for Positive and
  `y=0` for Negative. `source_id` is a frozen map over publisher `site`.
- **Feedback delay** = 1 trading day (label known after the next close).
- **No parameter retuning** on this stream for v0: Wave XI locked cellular /
  provenance-graph hyperparameters from the research release.

## Splits (chronological, process-honest)

| Split | Trading days | Role |
|---|---|---|
| `contact` | first 70% of stream days | First contact / exploratory (may inform later design; **not** confirmatory) |
| `holdout` | last 30% of stream days | Held-out confirmatory for v0 locked models |

Touching `holdout` for mechanism changes retires it as a clean test bed
(NORTH_STAR fidelity rule 4).

## Required metrics

Always report:

1. Overall accuracy and Brier / ECE
2. **Persistence oracle** accuracy (`predict yesterday's direction`)
3. **Flip-detection** accuracy (subset where `truth_t != truth_{t-1}` for that symbol)
4. Average reports activated / ops accounting for TCM and fair provenance graph
5. Within-event source agreement (independence honesty)

## Explicit non-claims

- Synthetic Wave XI wins do not transfer by default.
- Headline accuracy without persistence / flip decomposition is not a win.
- Publisher sites are heavily Positive-skewed relative to a ~50% market base
  rate; that is part of the regime under test, not a bug to silently “fix.”
