# Sensory relevance-gate confirmation protocol

Written before scoring the second fresh company universe.

## Fixed candidate

The candidate is exactly:

1. `source_calib + corr_downweight` (the earlier evidence-honesty cure);
2. explicit company-name/title relevance filtering; and
3. memory fallback when no relevant report arrives.

No new parameters are tuned. The company-name patterns are the transparent,
precision-first list in `relevance.py`.

## Fresh universe

`confirmation2_universe.py` declares 29 companies disjoint from both earlier
company sets. They were selected from raw news-row availability only, before
price labels or any model scores were inspected.

The feed and calendar are the same FMP-news / Yahoo-price sources, so this is
a fresh company-universe confirmation, not a separate-dataset replication.

## Scoring

- First 70% of dates: causal warm-up only.
- Last 30%: scored once.
- Compare the fixed relevance-gated model with calibrated TCM, on identical
  events.
- Report overall accuracy, flip detection, Brier score, average reports used,
  prediction-up rate, and paired-bootstrap confidence intervals.

## Pass condition

Bake the relevance gate into the active experimental model only if it:

1. improves held-out flip detection by at least 3 percentage points;
2. does not lower overall accuracy by more than 1 point; and
3. keeps prediction-up rate at or below 0.65.
