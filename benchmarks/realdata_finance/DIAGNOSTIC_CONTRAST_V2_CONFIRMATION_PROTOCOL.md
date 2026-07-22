# Diagnostic-contrast v2 confirmation protocol

Written **before** scoring the seventh fresh company universe.

## Fixed candidate

Exactly one frozen stack:

1. `SessionRelevanceFinanceNewsStream`
2. Baseline A: `tcm.CleanEvidenceCellular`
3. Baseline B: `tcm.SilenceEscapeCellular` with confirmed hyperparameters
   - `pe_floor=0.35`, `pe_span=0.50`, `rho_gain=0.30`, `max_hazard=0.70`
   - `apply_to_all_positive=True`
4. Candidate: `tcm.DiagnosticContrastCellular` (v2 laws) with
   - `pe_floor=0.35`, `pe_span=0.50`, `rho_gain=0.30`, `max_hazard=0.70`
   - `apply_to_all_positive=False` (slot law owns null)
   - `cheerleader_contrast_scale=1.0`
   - `contrast_margin=0.08`
   - `survival_gain=1.0`
   - `preserve_recruit_scale=0.0`

No new parameters are tuned after this protocol is written. No other mechanism
is tested on this universe in the same cycle.

## Fresh universe

`confirmation7_universe.py` declares 30 companies disjoint from all earlier
company sets. Selected from curated liquid names using only in-window news-row
availability (≥35 sentiment-labelled rows). Price coverage is validated before
scoring.

`confirmation6` is spent and invalid as a sealed look: its download included
delisted tickers with null prices and a score was observed on that broken panel.

Same FMP-news / Yahoo-price sources and calendar window as v0.

## Scoring

- First 70% of stream days: causal warm-up only (not scored).
- Last 30% (`holdout`): scored once.
- Compare v2 vs clean and vs silence-escape on identical session events.

## Pass condition

Claim a confirmed win only if the candidate:

1. reaches held-out flip detection of at least **45%**;
2. does not lower overall accuracy by more than **1 point** vs clean;
3. keeps prediction-up rate at or below **0.65**; and
4. keeps non-flip accuracy at or above **50%**.

Pass or fail is recorded once. No retuning on this universe.
