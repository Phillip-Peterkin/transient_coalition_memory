# Weather confirmation protocol — sealed Active Coalition Inference

Written **before** scoring the clean Weather holdout.

## What this is / is not

| | |
|---|---|
| **This** | One confirmatory look of **finance-sealed** ACI on the clean Weather bed (`PROTOCOL.md` / `REPORT_PURITY.md`). |
| **Not** | Recovery of the old sandbox Weather final. |
| **Not** | A retune. confirmation8 freeze stays fixed. No Weather-informed knob changes. |

## Fixed candidate

`tcm.ActiveCoalitionCellular` with sealed confirmation8 defaults:

- `min_delta=0.15`
- `max_silence_hazard=0.55`
- `null_rho_gain=0.30`
- `null_pe_floor=0.35`, `null_pe_span=0.50`, `null_err_beta=0.30`
- `force_all_positive_null=True`
- `fe_cert_slack=0.0`

Wave XI cellular hyperparameters remain the locked set from finance/Wave XI.

## Baselines (same events)

1. Persistence oracle (`prev_truth`, else 0.5)
2. Memoryless majority of model votes
3. `BatchedReserveCellular` (frozen Wave XI)
4. `SilenceEscapeCellular` (confirmed finance ancestor; frozen silence knobs)

## Stream / split

`CleanWeatherStream` on committed `data/`:

- contact = first 70% of days (causal warm-up only; not scored for the gate)
- holdout = last 30% (scored once)

Feedback delay: label for day `D` uses observed `tmax[D+1]`, so feedback
becomes available at the first event on day `D+2` (no same-day label leak).

## Pass condition (holdout)

Claim a Weather confirmation **PASS** only if all hold for ACI:

1. flip detection ≥ **0.45**
2. flip detection ≥ Wave XI flip + **0.05** (material lift on the known failure)
3. overall accuracy ≥ persistence oracle − **0.01**
4. prediction-up rate ≤ **0.65**
5. non-flip accuracy ≥ **0.50**

Majority accuracy is reported for regime honesty; beating ~87% majority is
**not** required (trustworthy sources already form a strong ensemble).

## Fail / honesty

Fail is recorded once. No retuning on this Weather bed. A fail means
finance-sealed ACI does not yet clear the trustworthy-source regime gate.
Foundation / regime-generality claims remain blocked.
