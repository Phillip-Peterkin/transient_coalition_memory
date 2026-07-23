# Clean Weather data lock — purity PASS

Protocol: `PROTOCOL.md`  
Artifact: committed `data/` cache from Open-Meteo Previous Runs + Archive APIs.

## What was rejected

| Candidate taint | Disposition |
|---|---|
| Weekly-median silver threshold | **Banned** — labels are adjacent-day observed tmax only |
| Analysis / nowcast as evidence | **Banned** — reports are `previous_day1` only |
| Incomplete model (`cma_grapes_global`, ~9% gaps) | **Dropped** from locked source set |
| Undisclosed city set | **Locked** in `cities.py` (12 cities) before scoring |

## Locked stream summary

| marker | value |
|---|---:|
| events | 6936 |
| cities | 12 |
| sources | 6 |
| days | 578 |
| contact / holdout | 4848 / 2088 |
| flip events | 3486 |
| truth-up rate | 0.519 |
| mean reports | 6.0 |
| majority-vote accuracy | 0.868 |

Majority ~87% confirms the intended **trustworthy-source** regime (unlike finance publisher skew). Flip rate is high (~50%), so change detection is measurable.

## Honesty

This is a **new** clean Weather bed, not recovery of the original sandbox Weather
final. No TCM / ACI parameters were tuned against it. `purity_check.py` must
pass before any confirmatory scoring.
