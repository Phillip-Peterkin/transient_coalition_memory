# Prospective Weather — sealed scoring protocol (not yet opened)

Written **before** any model scores this ledger. Collection continues under
[`PROTOCOL.md`](PROTOCOL.md). **Do not run evaluators against this lane until
the open conditions below are met.**

This document freezes the scoring contract so future looks cannot quietly
reshape the task after seeing outcomes.

## Task (same as DBSA-v1)

Causal delayed-feedback source aggregation:

1. At calendar day `D`, each station is one item.
2. Decision packet at `D` is the six locked NWP `previous_day1` binary reports
   available that day (warmer-than-yesterday forecast bits derived only from
   forecasts present in the day artifact).
3. Emit `P(truth=1)` immediately.
4. Label is adjacent-day observed warmer (ERA5/GHCN warmer) for that station.
5. Label is released only after the observation day is sealed in the ledger
   (fixed natural delay: forecast day → next day’s observation). Methods update
   only on that release — same queue-release discipline as synthetic DBSA.

No method may use future forecasts, future observations, spent Weather beds, or
hidden source quality fields.

## Immutable inputs

| Piece | Lock |
|---|---|
| Stations | `stations.py` roster (12), disjoint from contact / confirmation2 / confirmation3 |
| Sources | six NWP models listed in collection protocol |
| Lead | Open-Meteo `previous_day1` only |
| Artifacts | append-only `ledger/YYYY-MM-DD/` + `INDEX.jsonl` hashes |
| Spent beds | contact, confirmation2, confirmation3 — never reused here |

If a day directory is missing or hash-mismatched, that day is excluded; it is
never rewritten.

## Open conditions (all required)

Scoring may begin only when **all** hold:

1. At least **60** consecutive collection days with valid `INDEX.jsonl` hashes
2. At least **45** of those days have sealed observation labels available for
   every roster station used in scoring
3. This scoring protocol file’s git SHA is recorded in the scoring run artifact
4. Synthetic DBSA-v1 200-seed contract artifact already exists under
   `benchmarks/dbsa/results/` (cross-domain claim needs both lanes)

Until then: collect only. No ACI/Aware/baseline evaluation imports this ledger.

## Metric hierarchy (identical to DBSA-v1)

1. Primary: prequential **Brier**
2. Gates: flip recall, change FAR, ECE, post-shift Brier (define shift windows
   from observable calendar season breaks only — declared at open, not after)
3. Resources: Pareto axes (inspected / activated / wall / CPU)

Non-inferiority vs delayed Fixed-Share: **δ = 0.005**, one-sided 97.5%
paired-seed (or paired-day-block) CI upper bound on
`(Aware Brier − FixedShare Brier) ≤ 0.005`.

## Methods (same rows as synthetic contract)

Persistence, Majority, Fixed-Share Hedge, AdaHedge, FadingSourceBayes,
AgreementDiscountedBayes, sealed ACI, Aware — all with queue-release updates
only. ACI/Aware knobs remain the sealed Weather/confirmation stack values; no
retune on this ledger.

## Forbidden until open

- Computing any method’s Brier / log-loss / accuracy on this ledger
- Peeking at observation labels to choose hyperparameters
- Dropping stations or sources after seeing errors
- Merging spent Weather confirmation beds into this roster

## Bootstrap note

To reach open conditions without waiting two calendar months, the locked
Open-Meteo previous-runs / archive APIs may be used for an
`archive_backfill` fill of consecutive days. Artifacts are still append-only
and hash-sealed. This is disclosed in scoring outputs
(`collection_includes_archive_backfill`). It is not a retune surface.

## Status

Collection may be live or archive-backfill. Scoring opens only when the
conditions above all hold; then `evaluate_weather.py` may run once.
