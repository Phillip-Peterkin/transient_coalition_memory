# Truth-discovery literature benchmark — first look

Protocol: `PROTOCOL.md`  
Methods: Majority/Median, TruthFinder, CRH, CATD, StreamingCRH, plus
Aware / sealed ACI / Wave XI on the binary Stock track.

## Datasets

| Bed | Claims (slim) | Sources | Gold |
|---|---:|---:|---|
| Stock (NASDAQ-100 attrs) | 402,964 | 55 | nasdaq_truth |
| Weather temperature | 2,640 | 13 | weather_gov aligned |
| Weather conditions | 2,981 | 15 | weather_gov aligned |
| Stock binary `last>prev` | ~83k votes | 55 | nasdaq last>prev (~48% up) |

Raw dumps: Luna Dong fusion sets (`download_data.py`). Change% gold is
degenerate (~99% up) — binary track uses `last>prev_close` instead.

## Attribute fusion (quality)

### Stock `last_price` (MAE ↓ better)

| method | MAE | accuracy@¢ | wall s | claims/s |
|---|---:|---:|---:|---:|
| majority_median | **0.0004** | **0.993** | **0.30** | **370k** |
| truthfinder | 0.0004 | 0.993 | 0.96 | 117k |
| catd | 0.0006 | 0.991 | 4.02 | 28k |
| crh | 0.087 | 0.849 | 3.39 | 33k |
| streaming_crh | 0.194 | 0.849 | 1.73 | 65k |

### Weather `temperature` (°F)

| method | MAE | wall s | claims/s |
|---|---:|---:|---:|
| majority_median | **0.620** | **0.013** | **200k** |
| truthfinder | 0.644 | 0.032 | 83k |
| streaming_crh | 0.741 | 0.061 | 43k |
| catd | 0.747 | 0.064 | 41k |
| crh | 0.748 | 0.051 | 52k |

### Weather `conditions` (exact normalized string)

All methods are weak (~0.20–0.22 accuracy) — label vocabulary mismatch across
sites dominates. Treat as a stress test, not a ranking crown.

## Binary Stock track (`last>prev_close`) + efficiency

| method | acc | flip | act | wall s | events/s |
|---|---:|---:|---:|---:|---:|
| TD majority / TF / CRH / CATD / stream | **0.999** | — | all votes | 0.3–0.8 | — |
| Wave XI | 0.990 | 0.978 | 4.96 | 1.11 | **1888** |
| sealed ACI | 0.871 | 0.920 | 3.53 | 1.57 | 1338 |
| **Aware** | 0.872 | 0.912 | **3.52** | 3.16 | 664 |

## Reading

1. **Yardstick is live.** Literature Stock/Weather + TruthFinder/CRH/CATD/
   StreamingCRH run in-repo with wall/CPU/peak memory.
2. **On these fusion beds, simple majority is extremely strong** (sources
   mostly agree with gold on last price / last>prev). Beating TD methods here
   is a high bar — not the adversarial synthetic regime.
3. **Aware is not yet ahead** of Wave XI or TD majority on Stock binary
   accuracy/flip; it is **sparser** (lower activation) but **slower** (~3×
   Wave XI wall, ~2× ACI) because Mnemosheath work is paid every event.
4. Weather temperature favors majority/TruthFinder on MAE; Aware was not
   scored on continuous fusion (cellular API is binary/report votes).

## Efficiency verdict

| claim | evidence |
|---|---|
| TD batch methods are cheap on fusion | 30k–370k claims/s; sub-second to a few seconds on Stock attrs |
| Aware costs more wall time than ACI / Wave XI | 3.16s vs 1.57s / 1.11s on same binary events |
| Aware stays activation-sparse vs Wave XI | 3.52 vs 4.96 avg activated |

No Aware/ACI retune was performed on these beds.

## Artifacts

`results/truth_discovery_benchmark.json`
