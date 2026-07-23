# Silence-escape confirmation protocol

Written **before** scoring the fourth fresh company universe.

## Fixed candidate

Exactly one frozen stack:

1. `SessionRelevanceFinanceNewsStream`
2. Baseline: `tcm.CleanEvidenceCellular`
3. Candidate: `tcm.SilenceEscapeCellular` with frozen hyperparameters
   - `pe_floor=0.35`
   - `pe_span=0.50`
   - `rho_gain=0.30`
   - `max_hazard=0.70`
   - `apply_to_all_positive=True`

No new parameters are tuned after this protocol is written. No other mechanism
is tested on this universe in the same cycle.

## Fresh universe

`confirmation4_universe.py` declares 30 companies disjoint from all earlier
company sets. Selected from curated liquid names using only in-window news-row
availability (≥35 sentiment-labelled rows).

Same FMP-news / Yahoo-price sources and calendar window as v0.

## Scoring

- First 70% of stream days: causal warm-up only (not scored).
- Last 30% (`holdout`): scored once.
- Compare silence-escape vs clean evidence on identical session events.
- Report accuracy, flip detection, non-flip accuracy, prediction-up rate,
  average activated evidence, and paired-bootstrap intervals.

## Pass condition

Claim a confirmed win only if the candidate:

1. reaches held-out flip detection of at least **45%**;
2. does not lower overall accuracy by more than **1 point** vs clean on this
   universe;
3. keeps prediction-up rate at or below **0.65**; and
4. keeps non-flip accuracy at or above **50%**.

Pass or fail is recorded once. No retuning on this universe.
