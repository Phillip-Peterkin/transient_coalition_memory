# ACI synthetic adversarial boss protocol

Written **before** scoring. This is the hardest confirmatory look available
in-repo after Active Coalition Inference was baked as the active experimental
real-data model.

## What this is / is not

| | |
|---|---|
| **This test** | Synthetic adversarial `World` regression: sealed ACI vs frozen Wave XI vs fair provenance graph on the Wave XI seed suite. |
| **Not this test** | Weather (promised untouched final / trustworthy-source boss). No Weather harness, data, or locked split exists in this repo. Inventing one after development is forbidden. |
| **Not a retune** | confirmation8 is spent. ACI hyperparameters stay at the sealed finance freeze. |

## Fixed candidate

Exactly one frozen cell:

`tcm.ActiveCoalitionCellular` with sealed confirmation8 defaults:

- `min_delta=0.15`
- `max_silence_hazard=0.55`
- `null_rho_gain=0.30`
- `null_pe_floor=0.35`, `null_pe_span=0.50`, `null_err_beta=0.30`
- `force_all_positive_null=True`
- `fe_cert_slack=0.0`

Wave XI cellular hyperparameters remain the locked Wave X/XI set
(`lr=0.22`, … `certify_slack=0.0`). Graph baseline stays
`lr=0.12`, `decay=0.98`, `claim=0.5`.

## Worlds and seeds

Same generator and seeds as Wave XI (`benchmarks/wave4` `World`,
`benchmarks/wave11`):

- Sanity / regression seeds: `15200`, `15201` (reported; not gated)
- **Boss holdout (gated):** `15300`, `15301`, `15302`, `15303`

ACI has never been tuned on these worlds. Score once.

## Methods

1. `FairProvGraph` — fair ops provenance baseline  
2. `BatchedReserveCellular` — frozen Wave XI reference  
3. `ActiveCoalitionCellular` — sealed active experimental ACI  

## Pass condition (fresh holdout means)

Claim a synthetic-adversarial boss **PASS** only if all hold:

1. ACI accuracy ≥ Wave XI accuracy − **0.015**
2. ACI changed-fact accuracy ≥ Wave XI changed-fact − **0.025**
3. ACI accuracy ≥ FairProvGraph accuracy
4. ACI changed-fact accuracy ≥ FairProvGraph changed-fact

Ops / activation are reported for honesty; they are **not** pass gates
(ACI’s read budget and null channel are not Wave XI’s certificate).

## Fail / honesty

- Fail is recorded once. No retuning on these seeds.
- A fail means the finance-sealed ACI cell is **not** Wave XI–compatible on
  adversarial synthetic worlds — foundation replacement remains blocked.
- Weather remains the true regime-generality boss when/if the locked harness
  is recovered.
