# Active Coalition Inference confirmation protocol

Written **before** scoring the eighth fresh company universe.

## Fixed candidate

Exactly one frozen stack:

1. `SessionRelevanceFinanceNewsStream`
2. Baseline A: `tcm.CleanEvidenceCellular`
3. Baseline B: `tcm.SilenceEscapeCellular` with confirmed hyperparameters
   - `pe_floor=0.35`, `pe_span=0.50`, `rho_gain=0.30`, `max_hazard=0.70`
   - `apply_to_all_positive=True`
4. Candidate: `tcm.ActiveCoalitionCellular` with
   - `min_delta=0.15`
   - `max_silence_hazard=0.55`
   - `null_rho_gain=0.30`
   - `null_pe_floor=0.35`, `null_pe_span=0.50`, `null_err_beta=0.30`
   - `force_all_positive_null=True`
   - `fe_cert_slack=0.0`

No new parameters are tuned after this protocol is written.

## Fresh universe

`confirmation8_universe.py` — 30 companies disjoint from all earlier sets.
Price coverage validated before scoring.

## Scoring

- First 70% of stream days: causal warm-up only (not scored).
- Last 30% (`holdout`): scored once.
- Compare ACI vs clean and vs silence-escape on identical session events.

## Pass condition

Claim a confirmed win only if the candidate:

1. reaches held-out flip detection of at least **45%**;
2. does not lower overall accuracy by more than **1 point** vs clean;
3. keeps prediction-up rate at or below **0.65**; and
4. keeps non-flip accuracy at or above **50%**.

Pass or fail is recorded once. No retuning on this universe.
