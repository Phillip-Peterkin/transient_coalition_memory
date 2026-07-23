# Skew-correction confirmation protocol

Written **before** scoring the third fresh company universe.

## Fixed candidate

Exactly one frozen stack:

1. `SessionRelevanceFinanceNewsStream` (16:00 America/New_York session cutoff,
   adjacent-session flips, title/company relevance gate);
2. `tcm.CleanEvidenceCellular` as the session baseline (sign-preserving memory,
   delayed source trust); and
3. `tcm.SkewCorrectedCellular(base_rate_scale=1.5)` as the sole candidate
   (same clean evidence, plus all-Positive cheerleader base-rate correction).

No new parameters are tuned after this protocol is written. No other mechanisms
are tested on this universe in the same cycle.

## Fresh universe

`confirmation3_universe.py` declares 30 companies disjoint from all earlier
company sets. They were selected from curated liquid US equities using only
in-window news-row availability (≥35 sentiment-labelled rows). Price labels and
model scores were not inspected during selection.

Same FMP-news / Yahoo-price sources and calendar window as v0.

## Scoring

- First 70% of stream days: causal warm-up only (not scored).
- Last 30% (`holdout`): scored once.
- Compare skew-corrected vs clean evidence on identical session events.
- Report accuracy, flip detection, non-flip accuracy, Brier, prediction-up rate,
  average activated evidence, and paired-bootstrap intervals.

## Pass condition

Claim a confirmed development win only if the skew candidate:

1. reaches held-out flip detection of at least **45%**;
2. does not lower overall accuracy by more than **1 point** vs the clean
   session baseline on this universe; and
3. keeps prediction-up rate at or below **0.65**.

Pass or fail is recorded once. No retuning on this universe.
