# Weather confirmation — active experimental architecture (not Wave XI)

Written **before** scoring virgin `confirmation2`.

## Architecture under test

**Subject:** `tcm.ActiveExperimentalCellular` / `ActiveCoalitionCellular`
(finance-sealed confirmation8 freeze).

Wave XI (`BatchedReserveCellular`) is the frozen **synthetic reference**. It is
**not** the real-data architecture under test and is **not** a pass/fail
comparator in this protocol. (The earlier Weather look that gated on Wave XI
lift used the wrong yardstick; that holdout is spent and is not re-gated here.)

## Lineage baselines (same events)

1. Persistence oracle (`prev_truth`, else 0.5)
2. Memoryless majority of model votes (trustworthy-source ceiling)
3. `SilenceEscapeCellular` — confirmed finance ancestor of ACI’s null channel

Wave XI may be printed as an archival footnote only; it does not enter the gate.

## Fixed ACI knobs (no Weather retune)

- `min_delta=0.15`
- `max_silence_hazard=0.55`
- `null_rho_gain=0.30`
- `null_pe_floor=0.35`, `null_pe_span=0.50`, `null_err_beta=0.30`
- `force_all_positive_null=True`
- `fe_cert_slack=0.0`

## Virgin universe

`confirmation2_universe.py` — 12 cities **disjoint** from the first Weather bed.
Same calendar, models, label/vote rules as `PROTOCOL.md`.
Data cache: `data_confirmation2/`.

## Scoring

- First 70% of days: causal warm-up only (not gated)
- Last 30% holdout: scored once
- Feedback due at first event on decision day + 2

## Pass condition (holdout)

Claim PASS only if sealed ACI satisfies all:

1. flip detection ≥ **0.45**
2. flip detection ≥ silence-escape flip (no regression vs lineage ancestor)
3. overall accuracy ≥ persistence − **0.01**
4. prediction-up rate ≤ **0.65**
5. non-flip accuracy ≥ **0.50**

Majority is reported for regime honesty; beating majority is **not** required.

## Fail / honesty

Fail once. No retune on confirmation2. This remains a **new** clean Weather
bed confirmation, not recovery of the old sandbox Weather final.
