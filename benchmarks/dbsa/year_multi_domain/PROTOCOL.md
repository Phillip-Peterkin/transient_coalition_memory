# Year Multi-Domain — append-only collection (sealed before scores)

Three real-data lanes under one year-scale honesty contract:

| Lane | Bed | Window (locked) |
|---|---|---|
| **Weather** | `../weather_year_stress/` (sibling ledger) | 2025-01-15 → 2026-01-14 |
| **Finance** | `finance/ledger/` (this tree) | 2022-08-15 → 2023-08-14 |
| **Medical** | `medical/ledger/` (this tree) | FluSight seasons spanning ≥40 labeled weeks |

**Scoring is closed** until [`SCORING_PROTOCOL.md`](SCORING_PROTOCOL.md) open conditions hold for **all** lanes that claim a gate.

This bed exists to test the **Arousal Dual-Mode** organ (thrift ESSC ↔ truth ROPL)
across niches — not to retune Christmas weather or finance confirmation8.

## Immutable rules

1. No scores until open conditions.
2. No retune of ACI / Aware / ESSC / ROPL / Arousal knobs after any lane opens.
3. Do not merge Christmas prospective weather, spent confirmation weather beds,
   or finance confirmation1–8 holdouts into these ledgers.
4. Each lane keeps its own ledger + hashes; cross-lane pooling is a declared
   secondary analysis only.
5. Primary method row for this bed: `aware_arousal` (biology switch).
   Comparators: Majority, Fixed-Share, Aware+ESSC, Aware+ROPL.

## Collect

See lane READMEs / collectors:

```bash
# Weather (existing year-stress ledger)
export DBSA_WEATHER_LEDGER=/workspace/benchmarks/dbsa/weather_year_stress/ledger
python3 benchmarks/dbsa/prospective_weather/collect_day.py \
  --from 2025-01-15 --to 2026-01-14 --mode archive_backfill
python3 benchmarks/dbsa/prospective_weather/collect_observations.py \
  --from 2025-01-15 --to 2026-01-15

# Finance (virgin year universe)
python3 benchmarks/dbsa/year_multi_domain/finance/collect_finance_year.py

# Medical (FluSight multi-model)
python3 benchmarks/dbsa/year_multi_domain/medical/collect_flusight_year.py
```

## Status helper

```bash
python3 benchmarks/dbsa/year_multi_domain/status.py
```
