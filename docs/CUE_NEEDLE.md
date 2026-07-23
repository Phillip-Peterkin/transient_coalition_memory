# Cue needle — selective admission

Cleanup rewrite after the overgrowth audit: Mnemosheath no longer stamps the
next cue from a lineage list. Candidates compete; bits are admitted only on
delayed predictive merit.

## Gate

30 candidate cues, **2 signals + 28 noise**, delayed feedback:

- admit exactly `{sig_a, sig_b}`
- never admit `noise_*`

See `tests/test_cue_needle.py`.

## Admission rule

1. Update each fired cue’s **own** delayed stats (agreement or absence path)
2. Require `samples >= n_min`
3. Best merit ≥ `merit_hi` and lead over `max(best_rival, noise_floor)` ≥ `lead_hi`
4. Hold that lead for `hysteresis` consecutive feedbacks
5. Admit one neutral newborn (no parent-stat inheritance)
6. Seed cues mark admitted without duplication

## Deleted as learning policy

- `_next_cue_for_split` / `CUE_ORDER` fallback growth
- Stage-0 double-advance hack (grow caps now seed-aware)
- Parent statistic inheritance on mitosis
