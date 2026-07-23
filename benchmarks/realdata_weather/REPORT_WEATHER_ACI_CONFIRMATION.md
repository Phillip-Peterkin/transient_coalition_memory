# Weather ACI confirmation — FAIL

Protocol: `WEATHER_ACI_CONFIRMATION_PROTOCOL.md` (written before scoring)  
Bed: clean Open-Meteo Weather (`previous_day1` + ERA5 adjacent-day warmer)  
Candidate: finance-sealed `ActiveCoalitionCellular` (confirmation8 freeze; no retune)

## Holdout scores

| method | acc | flip | nonflip | pred-up | act | flips |
|---|---:|---:|---:|---:|---:|---:|
| persistence | 0.502 | 0.000 | 1.000 | 0.509 | 0.00 | 1040 |
| majority | 0.877 | 0.891 | 0.864 | 0.505 | 6.00 | 1040 |
| Wave XI | **0.814** | **0.845** | 0.782 | 0.507 | 4.02 | 1040 |
| silence escape | 0.672 | 0.685 | 0.659 | 0.299 | 2.70 | 1040 |
| **ACI sealed** | 0.777 | 0.783 | 0.771 | 0.396 | 2.75 | 1040 |

## Gate

| rule | result |
|---|---|
| flip ≥ 0.45 | **pass** (0.783) |
| flip ≥ Wave XI + 0.05 | **FAIL** (0.783 vs 0.845; Δ=−0.062) |
| acc ≥ persistence − 0.01 | **pass** (+0.275) |
| pred-up ≤ 0.65 | **pass** (0.396) |
| nonflip ≥ 0.50 | **pass** (0.771) |

**`passes_predeclared_gate=False`**

## Reading

On this clean trustworthy-source bed, multi-model day-ahead forecasts are
strong (majority flip **89.1%**). Frozen Wave XI already rides that signal
well (flip **84.5%**). Finance-sealed ACI clears the absolute flip floor and
holds accuracy vs persistence, but **does not lift** Wave XI on the core
metric — it trails by ~6 flip points.

Likely mechanism stress: `force_all_positive_null` / null-channel laws shaped
for finance cheerleader silence treat unanimous warmer votes as non-diagnostic,
exactly when trustworthy models agree for real. That is a regime mismatch, not
a license to retune on this bed.

This is a **new** Weather bed confirmation, not the recovered sandbox Weather
final. No retuning. Regime-generality / foundation claims remain blocked.
