# Year Multi-Domain — sealed scoring protocol (not yet opened)

Written **before** any model scores these ledgers. Knobs for `aware_arousal`
are locked in `benchmarks/dbsa/evaluate.py` (`AROUSAL_PARAMS`).

## Why

Christmas weather + finance confirmation8 answer different niches with different
organs. The biology claim needs **one switch** across **multiple real worlds**
at year scale:

- When the roster is redundant → **thrift** (dormant sources, Used ≈ active)
- When truth needs the pool → **arouse** (ROPL / full equal-gain)

## Locked method

| Knob | Value |
|---|---|
| `arousal_enabled` | True |
| `thrift_rho_enter` | **0.5** |
| `rebate_window` | 120 |
| `rebate_min_updates` | 40 |
| ESSC | on (bow off) |
| Standalone ROPL / Pool-Restore | off (embedded / exclusive) |

## Per-lane tasks (immutable)

### Weather
- Same as `weather_year_stress/SCORING_PROTOCOL.md`
- Primary: prequential Brier; crush/diagnostic vs Majority + Fixed-Share δ=0.005

### Finance
- Decision: next-session close-to-close direction for virgin symbols
- Reports: publisher sentiment votes (Positive=1, Negative=0)
- Window: **2022-08-15 → 2023-08-14** (≈1y inside available HF corpus)
- Universe: `finance/universe_year.py` — disjoint from confirmation1–8 + v0 UNIVERSE
- Delay: 1 trading session
- Primary metrics: Brier, accuracy, Used; persistence + flip slices diagnostic

### Medical (FluSight)
- Decision: for each `(location, week)`, predict whether lab-confirmed flu
  hospital admissions **increase** next week:
  `truth = 1{ adm_{w+1} > adm_w }`
- Reports: locked FluSight models’ point/median forecasts → vote
  `1{ forecast_{w+1} > adm_w }` (or hub rate-change side when present)
- Locations: US national + locked state subset (see `medical/locations.py`)
- Span: FluSight 2023–24 and 2024–25 seasons as available (≥40 labeled weeks)
- Delay: 1 week (label after next week’s target seal)
- Primary: prequential Brier vs Majority of models; Fixed-Share diagnostic

## Open conditions (all required)

1. Weather year-stress open conditions met (full window hashed, ≥350 labeled days)
2. Finance year ledger sealed with ≥200 labeled decision events in-window
3. Medical ledger sealed with ≥40 labeled location-weeks and ≥4 models/event mean
4. This protocol’s git SHA recorded in the run artifact
5. Synthetic DBSA-v1 200-seed artifact present
6. Christmas weather + finance confirmation8 left **untouched**

Until then: **collect only. No evaluator scores.**

## Primary gates (when open — score once)

| Gate | Pass |
|---|---|
| Weather Brier | Aware-Arousal vs Majority: report crush/match/fail; vs FS δ=0.005 NI |
| Finance Brier | Aware-Arousal ≤ Majority + 0.005 (day-block NI) **or** crush |
| Medical Brier | Aware-Arousal ≤ Majority + 0.005 (week-block NI) **or** crush |
| Switch honesty | Report thrift_frac + mean Used per lane; thrift Used < truth Used |

Failing a lane fails that lane’s claim only; do not drop lanes post-hoc.

## Forbidden

- Retuning after any lane’s first look
- Claiming Used~3.5 crush without thrift_frac evidence
- Merging spent beds
- Scoring before open conditions
- Quietly shortening windows

## Status

**Protocol sealed. Scoring closed.** Collection in progress.
