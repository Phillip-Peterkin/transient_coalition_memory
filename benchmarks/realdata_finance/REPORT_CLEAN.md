# Dead-pixel cleanup — session stream + clean evidence

Finance development only. Contact-tail scores chose the cells; the old holdout
was not used as a design knob. A holdout snapshot is included below as a
post-design measurement, not as a fresh confirmation.

## What was dirty

| Impurity | Legacy marker |
|---|---|
| Duplicate `(symbol, session)` decisions from calendar-date forward-mapping | 672 duplicates |
| Flip label vs previous *news event*, not previous trading session | many multi-day gaps |
| Memory could reverse a report's sign | **39.3%** of report rows |
| Source weight = emission rarity, not delayed correctness | not a correctness signal |

## What changed

1. **`SessionRelevanceFinanceNewsStream`**
   - Articles assigned by published time to the first 16:00 America/New_York
     session close at or after that time.
   - One decision per `(symbol, session)`.
   - Flip = adjacent trading-session label change in the price calendar.
2. **`CleanEvidenceCellular`**
   - Memory may shrink a report's weight to a tiny positive floor; it cannot
     flip the report's direction.
   - Source multipliers come from delayed correctness (Laplace hit rate).

Frozen Wave XI and the archival `SensoryGatedCellular` confirmation path are
unchanged.

## Stream purity markers

| Marker | Legacy relevance stream | Session relevance stream |
|---|---:|---:|
| Events | 6121 | 5464 |
| Duplicate symbol-session events | 672 | **0** |
| Flip events with adjacent-session labels | n/a (broken) | **2631 / 2631** |
| Events with no relevant reports | 2613 | 2191 |
| Relevant article fraction | 0.456 | 0.456 |

## Contact-tail model markers

Scored on the final 30% of contact days (`develop_clean.py`).

| Cell | Acc | Flip | Pred-up | Act | Sign-reversal |
|---|---:|---:|---:|---:|---:|
| A old stream + sensory | 0.491 | 0.271 | 0.568 | 0.79 | 0.393 |
| B session + sensory | 0.480 | 0.315 | 0.558 | 0.83 | 0.400 |
| C session + no sign-reversal | 0.490 | **0.401** | 0.703 | 0.79 | **0.000** |
| D session + clean evidence | **0.504** | **0.408** | 0.696 | 0.80 | **0.000** |

Paired vs cell B (session + sensory):

- C flip Δ **+8.6 pts** (p≈0.000)
- D flip Δ **+9.4 pts** (p≈0.000); accuracy Δ +2.3 pts (p≈0.076)

Internal marker gates: all passed (no duplicates, adjacent flips, zero
sign-reversal on the clean model).

## Plain-English read

Cleaning the clock and the flip definition alone moves change detection from
about **27% → 31%** on the contact tail. Stopping memory from reversing the
evidence is the big jump: about **31% → 41%**. Delayed source trust adds a
little more and slightly helps accuracy.

The cost is honest: once Positive news can no longer be silently turned into a
down vote by memory, prediction-up rises to ~70%. That is the publisher skew
showing itself, not a reason to put sign-reversal back.

Confidence on flips is still backwards on the clean cell (wrong flips are more
confident than correct ones). Empty-relevant decisions remain common (~40%).
Those are the next impurities, not solved here.

## Holdout snapshot (post-design, not confirmatory)

| Cell | Acc | Flip | Pred-up | Act |
|---|---:|---:|---:|---:|
| old sensory | 0.519 | 0.273 | 0.561 | 0.67 |
| session sensory | 0.527 | 0.350 | 0.574 | 0.74 |
| session clean evidence | 0.517 | **0.421** | 0.692 | 0.72 |

Same shape as the contact-tail story. Still short of a 45% change-detection
claim with controlled up-rate, and this holdout is no longer a virgin test bed
for these mechanisms.

## Status

- **Baked as development tools:** session stream + `CleanEvidenceCellular`.
- **Not promoted as a confirmed win:** up-rate bias and remaining empty/dirty
  inputs still block that claim.
- **Next:** confront Positive publisher skew without reintroducing sign
  reversal; then a fresh-company confirmation if a gate is met.
