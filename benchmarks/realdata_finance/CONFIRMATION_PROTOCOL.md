# Transition-investigation confirmation protocol

This file is written before running the confirmation universe.

## Purpose

Test one brain-shaped change-investigation circuit selected using the old,
already-contacted development period. This is not a test of every idea again.

## Fixed candidate

The contact-only development script selected `long_strong` under its declared
selection rule:

```text
error_decay = 0.60
ignite_threshold = 0.75
confidence_floor = 0.20
investigate_decay = 0.88
anchor_floor = 0.20
counterevidence_floor = 0.75
```

It is always paired with the previously established sensory fix:
`source_calib + corr_downweight`.

## Fresh universe

`confirmation_universe.py` declares 33 companies disjoint from the original
development universe. They were selected by raw news-row availability only,
before any price outcomes or model scores were inspected.

The same FMP-news / Yahoo-price source and calendar window are used. This is
therefore a **fresh company-universe confirmation**, not an independent
dataset replication.

## Scoring

- First 70% of trading days: causal warm-up only; its metrics are not used for
  selection.
- Last 30%: confirmation only.
- Compare fixed transition circuit against calibrated TCM on overall accuracy,
  flip accuracy, Brier score, activation count, and prediction-up rate.
- Report paired-bootstrap confidence intervals. There is no follow-up tuning
  against this slice.

## Pass condition

The circuit deserves to be baked into the active experimental model only if it:

1. improves held-out flip detection by at least 3 percentage points;
2. does not lower overall accuracy by more than 1 point;
3. keeps prediction-up rate at or below 0.65 (not an “always up” strategy).
