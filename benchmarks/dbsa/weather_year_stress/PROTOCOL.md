# Weather Year-Stress — append-only collection

Sibling bed to `prospective_weather/` (Christmas 60-day lane). Same roster and
six NWP models; **disjoint calendar window**; separate ledger so Christmas
artifacts stay frozen.

## Locks

- Stations / models: import from `../prospective_weather/stations.py`
- Window: **2025-01-15 → 2026-01-14**
- Ledger: `ledger/` under this directory only
- Scoring: closed until [`SCORING_PROTOCOL.md`](SCORING_PROTOCOL.md) open conditions

## Collect

Collectors honor `DBSA_WEATHER_LEDGER` (absolute path to this `ledger/`).

```bash
export DBSA_WEATHER_LEDGER=/workspace/benchmarks/dbsa/weather_year_stress/ledger

python benchmarks/dbsa/prospective_weather/collect_day.py \
  --from 2025-01-15 --to 2026-01-14 --mode archive_backfill

python benchmarks/dbsa/prospective_weather/collect_observations.py \
  --from 2025-01-15 --to 2026-01-15
```

Do **not** write these days into `prospective_weather/ledger/`.
