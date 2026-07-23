#!/usr/bin/env python3
"""Download locked Open-Meteo previous-run forecasts + ERA5 daily labels.

No model scoring. Writes slim parquet under data/ plus download_meta.json.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

from cities import CITIES, END_DATE, MODELS, START_DATE, TIMEZONE

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
USER_AGENT = "transient-coalition-memory-weather/0.1 (research; clean-harness)"


def _get_json(url: str, retries: int = 5) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    delay = 2.0
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                return json.load(response)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            if attempt + 1 == retries:
                raise
            time.sleep(delay)
            delay = min(32.0, delay * 2)
            print(f"retry {attempt + 1} after {exc}")
    raise RuntimeError("unreachable")


def fetch_archive_daily(lat: float, lon: float) -> pd.DataFrame:
    query = urllib.parse.urlencode(
        {
            "latitude": lat,
            "longitude": lon,
            "start_date": START_DATE,
            "end_date": END_DATE,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "timezone": TIMEZONE,
        }
    )
    payload = _get_json(f"https://archive-api.open-meteo.com/v1/archive?{query}")
    daily = payload["daily"]
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(daily["time"]),
            "tmax_obs": daily["temperature_2m_max"],
            "tmin_obs": daily["temperature_2m_min"],
            "precip_obs": daily["precipitation_sum"],
        }
    )
    return frame


def fetch_previous_day1_hourly(lat: float, lon: float) -> pd.DataFrame:
    # Need hours covering END_DATE for next-day forecasts on last decision day.
    query = urllib.parse.urlencode(
        {
            "latitude": lat,
            "longitude": lon,
            "start_date": START_DATE,
            "end_date": END_DATE,
            "hourly": "temperature_2m_previous_day1",
            "models": ",".join(MODELS),
            "timezone": TIMEZONE,
        }
    )
    payload = _get_json(
        f"https://previous-runs-api.open-meteo.com/v1/forecast?{query}"
    )
    hourly = payload["hourly"]
    frame = pd.DataFrame({"time": pd.to_datetime(hourly["time"])})
    for model in MODELS:
        key = f"temperature_2m_previous_day1_{model}"
        if key not in hourly:
            raise KeyError(f"missing {key} in previous-runs response")
        frame[model] = hourly[key]
    return frame


def daily_forecast_max(hourly: pd.DataFrame) -> pd.DataFrame:
    work = hourly.copy()
    work["date"] = work["time"].dt.floor("D")
    rows = []
    for day, group in work.groupby("date", sort=True):
        row = {"date": day}
        for model in MODELS:
            values = group[model].to_numpy(dtype=float)
            if np.all(np.isnan(values)):
                row[model] = np.nan
            else:
                row[model] = float(np.nanmax(values))
        rows.append(row)
    return pd.DataFrame(rows)


def download_universe(
    cities: list[tuple[str, float, float, str]],
    out_dir: Path,
    *,
    universe: str = "contact_bed",
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    obs_parts = []
    fcst_parts = []
    for symbol, lat, lon, name in cities:
        print(f"fetch {symbol} ({name}) …")
        obs = fetch_archive_daily(lat, lon)
        obs.insert(0, "symbol", symbol)
        obs_parts.append(obs)

        hourly = fetch_previous_day1_hourly(lat, lon)
        daily = daily_forecast_max(hourly)
        daily.insert(0, "symbol", symbol)
        fcst_parts.append(daily)
        time.sleep(0.4)

    observations = pd.concat(obs_parts, ignore_index=True)
    forecasts = pd.concat(fcst_parts, ignore_index=True)
    # Keep only complete locked models (drop sparse columns if any).
    keep_models = [model for model in MODELS if forecasts[model].notna().mean() >= 0.99]
    if keep_models != list(MODELS):
        print("warning: dropping incomplete models", set(MODELS) - set(keep_models))
    forecasts = forecasts[["symbol", "date", *keep_models]]
    observations.to_parquet(out_dir / "observations_daily.parquet", index=False)
    forecasts.to_parquet(out_dir / "forecasts_daily_previous_day1.parquet", index=False)

    meta = {
        "universe": universe,
        "source_forecasts": "Open-Meteo Previous Runs API",
        "source_observations": "Open-Meteo Archive API (ERA5 daily)",
        "lead": "previous_day1_only",
        "label_rule": "tmax_obs[D+1] > tmax_obs[D]",
        "vote_rule": "tmax_fcst_prev_day1[D+1] > tmax_obs[D]",
        "timezone": TIMEZONE,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "models": keep_models,
        "cities": [
            {
                "symbol": symbol,
                "lat": lat,
                "lon": lon,
                "name": name,
            }
            for symbol, lat, lon, name in cities
        ],
        "n_observation_rows": int(len(observations)),
        "n_forecast_rows": int(len(forecasts)),
        "forbidden": [
            "weekly_median_threshold",
            "undisclosed_city_filter",
            "analysis_as_report",
            "same_valid_time_nowcast_as_evidence",
        ],
    }
    (out_dir / "download_meta.json").write_text(json.dumps(meta, indent=2))
    print("wrote", out_dir / "observations_daily.parquet")
    print("wrote", out_dir / "forecasts_daily_previous_day1.parquet")
    print("wrote", out_dir / "download_meta.json")


def main() -> None:
    download_universe(CITIES, DATA, universe="contact_bed")


if __name__ == "__main__":
    main()
