# Wave XVIII — prediction-error-driven trust protocol

## One question

Can a per-item trust state improve **finance/news change detection to 45%**
without collapsing overall accuracy or sparse evidence use?

Finance/news is the sole development dataset. Synthetic and historical stock
remain regression checks only. No Weather result will be inspected or used
during design.

## Frozen base

- Frozen reference: `tcm.BatchedReserveCellular` (Wave XI), unchanged.
- Active real-data sensory front end: `tcm.SensoryGatedCellular` plus the
  title/company relevance stream.

## Wave XVIII state loop

Each item has `mistrust ∈ [0, 1]`.

After delayed feedback:

- A **confident wrong** prediction raises that item's mistrust.
- A **confident correct** prediction relaxes mistrust toward zero.
- Uncertain predictions do not trigger a state transition.

Before the next decision for that item, the same mistrust state drives all
three changes together:

1. hazard rises; at most one extra relevant report is recruited;
2. anchor weight falls; memory has less power over the decision;
3. the credible fresh-evidence floor rises; evidence opposing stale memory
   cannot be erased or sign-reversed by the anchor.

With `mistrust = 0`, the class must reproduce `SensoryGatedCellular` exactly.

## Development candidates (predeclared)

| Candidate | wrong-signal gain | correct relaxation | extra-hazard gain | anchor floor | fresh-evidence floor |
|---|---:|---:|---:|---:|---:|
| light | 0.50 | 0.30 | 0.15 | 0.55 | 0.50 |
| balanced | 0.75 | 0.40 | 0.25 | 0.35 | 0.75 |
| strong | 1.00 | 0.50 | 0.35 | 0.15 | 1.00 |

All use confidence threshold 0.20, one-extra-report cap, and finance/news
relevance filtering.

## Development decision rule

The finance development winner must meet all of:

1. change detection at least **45%**;
2. overall accuracy no worse than 1 point below the sensory baseline;
3. prediction-up rate ≤ 0.65;
4. average activated evidence ≤ sensory baseline + 0.25 report;
5. deterministic tests confirm zero-state parity, wrong-error activation,
   correct relaxation, item isolation, and all three next-decision controls.

If no candidate meets the rule, Wave XVIII does not proceed to Weather.

## Second small development test: isolate the trust loop

The first three-way cells may improve flip detection while over-predicting up.
If that happens, run only these four finance-development isolation cells before
discarding the mechanism:

1. hazard only;
2. anchor reduction only;
3. source-surprising fresh-evidence floor only;
4. full balanced loop, but fresh-evidence floor applies only to messages that
   are surprising for that source (not its routine Positive output).

The same 45% / accuracy / sparse-evidence / prediction-up selection rule
applies. This is still finance-only development, not a Weather look.

## Third small development test: evidence-gated prediction error

If broad prediction-error mistrust fires on ordinary market noise and produces
an “up” bias, test the same light / balanced / strong three-way loop with one
additional condition:

> Raise mistrust only when the model was confidently wrong **and** relevant
> current evidence already pointed against its prediction.

This makes the system distrust memory only when it ignored a sensory warning;
an unsupported wrong forecast is treated as unresolved environmental noise.
The original 45% / accuracy / sparse-evidence / prediction-up gate is
unchanged. This is finance-only development.

## Weather rule and current blocker

Weather is final-only: no mechanism or parameter will be designed against it.
However, this repository contains no Weather code, data, protocol, or
predeclared untouched split. The ledger also records previous Weather contact
and a silver-label lookahead issue. A Weather “clean shot” cannot be run until
the original locked Weather split/harness is recovered or supplied. Building
a new Weather harness after development would be a new test bed, not the
promised untouched final test.
