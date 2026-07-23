# Clean Weather harness (v1)

Live, untainted weather data for TCM’s trustworthy-source regime test.

This is a **new** bed. It does **not** claim to be the recovered sandbox Weather
final. The old silver standard’s weekly-median lookahead is explicitly banned.

## What is locked

| Piece | Choice |
|---|---|
| Forecasts | Open-Meteo Previous Runs API, **`previous_day1` only** |
| Observations / labels | Open-Meteo Archive (ERA5 daily `temperature_2m_max`) |
| Label | next day warmer: `tmax[D+1] > tmax[D]` |
| Votes | each model’s prev-day1 daily max tomorrow `>` today’s observed max |
| Cities | 12 locked in `cities.py` |
| Calendar | `2024-06-01` … `2025-12-31` UTC |
| Models | GFS, ECMWF IFS 0.25°, ICON, GEM, Météo-France, JMA (CMA dropped: gaps) |

## Setup

```bash
pip install -r benchmarks/realdata_weather/requirements.txt
python benchmarks/realdata_weather/download_data.py   # refreshes data/
python benchmarks/realdata_weather/purity_check.py    # must pass
```

Committed slim parquet under `data/` is the reproduction artifact if APIs drift.

## Protocol

See [`PROTOCOL.md`](PROTOCOL.md). No mechanism tuning on this stream. Holdout is
confirmatory for locked models only.

## Status

Purity lock **PASS**. Sealed ACI Weather confirmation **FAIL** (flip 0.783 vs
Wave XI 0.845; missed +5pt lift gate). See
`REPORT_WEATHER_ACI_CONFIRMATION.md`. No retune. Still **not** a claim of
recovering the original sandbox Weather final.
