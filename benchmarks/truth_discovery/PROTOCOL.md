# Truth-discovery literature benchmark (Stock + Weather)

Written to answer the review yardstick: classic multi-source Stock and Weather
fusion, with that field’s own methods, plus efficiency.

## Datasets (canonical)

| Bed | Source | Notes |
|---|---|---|
| **Stock** | Luna Dong fusion set (Li et al., VLDB 2013) — July 2011, ~55 sources | `clean_stock` + `nasdaq_truth` gold (NASDAQ-100) |
| **Weather** | Luna Dong weather fusion set — 18 web sources, 30 US cities | Temperature / Conditions; gold = `weather_gov` after city alignment |

Download: https://lunadong.com/fusionDataSets.htm  
Script: `download_data.py` → slim tables under `data/slim/`.

These are **not** the contaminated sandbox Stock process ledger and **not** the
weekly-median Weather silver standard. They are the public literature fusion
beds reviewers cite. Known gold quirks (Stock nasdaq contamination noted in
`docs/NORTH_STAR.md`) remain; we report them, we do not “fix” gold.

## Methods under test

| Method | Citation | Role |
|---|---|---|
| Majority / Median | trivial | equal-weight baseline |
| **TruthFinder** | Yin, Han, Yu 2008 | canonical iterative reliability |
| **CRH** | Li et al. SIGMOD 2014 | strong heterogeneous baseline |
| **CATD** | Li et al. VLDB 2015 | confidence-aware / long-tail sources |
| **StreamingCRH** | online CRH (day-ordered) | closest streaming TD analogue |
| Memoryless majority (binary) | — | TCM API reference |
| `AwareCoalitionCellular` | this repo | packaged ACI + Mnemosheath |
| Sealed ACI / Wave XI | this repo | lineage footnotes on binary track |

## Tasks

### A. Attribute fusion (literature primary)

- Stock attributes: `change_pct`, `last_price`, `open_price` on NASDAQ-100 gold rows
- Weather attributes: `temperature` (°F), `conditions` (normalized string)
- Continuous metrics: MAE, RMSE
- Categorical / discrete metrics: error rate (1 − exact-match after TruthFinder-style rounding for continuous-as-categorical where needed)
- Continuous truths: MAE/RMSE against gold; also report rounded-match @ε

### B. Binary streaming track (TCM-native, same Stock bed)

- **Do not** use `sign(change_pct)` against nasdaq gold — that label is
  degenerate (~99–100% up every day; NORTH_STAR §7 contamination).
- Object: `(day, symbol)`; vote = `last_price > prev_close` per source
- Gold: nasdaq `last_price > prev_close` (~48% up; real flips)
- Chronological days; feedback due next trading day
- Metrics: accuracy, flip accuracy, pred-up, avg activated, wall/cpu

## Efficiency (required)

For every method report:

1. wall seconds
2. CPU seconds
3. peak tracemalloc bytes
4. claims processed / sec (fusion track)
5. avg activated reports (cellular / majority binary track)

## Honesty

- No retune of Aware/ACI knobs on these beds in this protocol’s first look.
- Stock gold contamination (NORTH_STAR §7) can cap absolute accuracy; relative
  ranking vs TD methods is still the claim under test.
- Weather city↔NWS alignment is imperfect; only aligned `(day, city, attr)`
  rows enter the scored set (recorded in slim meta).
