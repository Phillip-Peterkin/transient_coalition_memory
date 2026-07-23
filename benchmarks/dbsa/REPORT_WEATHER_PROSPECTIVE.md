# Prospective Weather sealed look — first open

Ledger: 60 forecast days (2026-05-25 → 2026-07-23), 60 observation days  
Events: **708** decision packets across **59** labeled days  
Stations: 12 (disjoint from spent Weather beds)  
Sources: 6 NWP `previous_day1`  
Collection: archive backfill of locked Open-Meteo APIs (disclosed)  
Artifact: `results/dbsa_weather_prospective_sealed.json`

## Gate vs delayed Fixed-Share

**Brier non-inferiority: FAIL** (δ=0.005)

| | |
|---|---:|
| Aware Brier | 0.1877 |
| Fixed-Share Brier | 0.1781 |
| Δ (Aware − FS) | +0.0096 |
| Day-block CI 97.5% upper | +0.0225 |

## Full rival table (primary = Brier)

| Method | Brier | Accuracy | Flip recall | False alarm | Used |
|---|---:|---:|---:|---:|---:|
| Persistence | 0.5268 | 0.476 | 0.000 | — | 5.95 |
| **Majority** | **0.1624** | 0.756 | 0.795 | — | 5.95 |
| Fixed-Share | 0.1781 | 0.744 | 0.749 | — | 5.95 |
| AdaHedge | 0.2316 | 0.747 | 0.765 | — | 5.95 |
| Fading Bayes | 0.1913 | 0.766 | 0.789 | — | 5.95 |
| Agree-discount Bayes | 0.1833 | 0.766 | 0.789 | — | 5.95 |
| ACI | 0.2147 | 0.675 | 0.657 | — | 2.99 |
| Aware | 0.1877 | 0.760 | 0.765 | — | 3.53 |

## Honest read

- This is **real weather**, not the synthetic accuracy-schedule world.
- Simple **majority** wins raw Brier here; fading Bayes does **not** dominate
  (supports the “home-field on synthetic” caution).
- Aware is sparse (~3.5 of ~6 reports) and near the pack, but does **not**
  clear the Fixed-Share non-inferiority gate on this first sealed look.
- No retune after this look.
