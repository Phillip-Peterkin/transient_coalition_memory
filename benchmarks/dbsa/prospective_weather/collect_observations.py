#!/usr/bin/env python3
"""Append-only ERA5/archive daily observations for the prospective Weather lane.

Does not score models. Writes per-day observation snapshots used later for
warmer-than-yesterday labels.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from stations import STATIONS, assert_disjoint

ROOT = Path(__file__).resolve().parent
LEDGER = Path(os.environ.get("DBSA_WEATHER_LEDGER", str(ROOT / "ledger"))).resolve()
OBS_INDEX = LEDGER / "OBS_INDEX.jsonl"
USER_AGENT = "transient-coalition-memory-dbsa-prospective-obs/0.1"


def _get_json(url: str, retries: int = 5) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    delay = 2.0
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return json.load(response)
        except Exception:
            if attempt + 1 == retries:
                raise
            time.sleep(delay)
            delay = min(32.0, delay * 2)
    raise RuntimeError("unreachable")


def _canonical_bytes(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def fetch_station_range(
    symbol: str, lat: float, lon: float, start: date, end: date
) -> dict[str, float | None]:
    query = urllib.parse.urlencode(
        {
            "latitude": lat,
            "longitude": lon,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "daily": "temperature_2m_max",
            "timezone": "UTC",
        }
    )
    payload = _get_json(f"https://archive-api.open-meteo.com/v1/archive?{query}")
    daily = payload["daily"]
    out: dict[str, float | None] = {}
    for day_str, value in zip(daily["time"], daily["temperature_2m_max"]):
        out[day_str] = None if value is None else float(value)
    return out


def collect_observations(start: date, end: date) -> int:
    assert_disjoint()
    if end < start:
        raise SystemExit("--to must be on or after --from")

    print(f"fetch observations {start} → {end} for {len(STATIONS)} stations …")
    by_station: dict[str, dict[str, float | None]] = {}
    for symbol, lat, lon, name in STATIONS:
        print(f"  archive {symbol} ({name})")
        by_station[symbol] = fetch_station_range(symbol, lat, lon, start, end)
        time.sleep(0.25)

    written = 0
    day = start
    while day <= end:
        day_dir = LEDGER / day.isoformat()
        day_dir.mkdir(parents=True, exist_ok=True)
        obs_path = day_dir / "observation_snapshot.json"
        if obs_path.exists():
            print(f"skip existing observation day {day.isoformat()}")
            day += timedelta(days=1)
            continue

        stations = []
        for symbol, lat, lon, name in STATIONS:
            tmax = by_station[symbol].get(day.isoformat())
            stations.append(
                {
                    "symbol": symbol,
                    "name": name,
                    "lat": lat,
                    "lon": lon,
                    "day": day.isoformat(),
                    "tmax_obs": tmax,
                    "source_api": "open-meteo-archive",
                    "variable": "temperature_2m_max",
                }
            )

        collected_at = datetime.now(timezone.utc).isoformat()
        artifact = {
            "protocol": "dbsa_prospective_weather_obs_v1",
            "collected_at_utc": collected_at,
            "day_utc": day.isoformat(),
            "stations": stations,
            "scoring_forbidden": True,
        }
        raw = _canonical_bytes(artifact)
        digest = hashlib.sha256(raw).hexdigest()
        obs_path.write_bytes(
            json.dumps(artifact, indent=2, sort_keys=True).encode("utf-8")
        )
        (day_dir / "observation_sha256.txt").write_text(digest + "\n", encoding="utf-8")
        with OBS_INDEX.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {
                        "day_utc": day.isoformat(),
                        "collected_at_utc": collected_at,
                        "sha256": digest,
                        "path": str(
                            obs_path.relative_to(LEDGER.parent)
                            if LEDGER.parent in obs_path.parents
                            else obs_path
                        ),
                        "n_stations": len(stations),
                        "n_finite_tmax": sum(
                            1 for row in stations if row["tmax_obs"] is not None
                        ),
                    },
                    sort_keys=True,
                )
                + "\n"
            )
        written += 1
        print("wrote", obs_path)
        day += timedelta(days=1)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from", dest="date_from", type=date.fromisoformat, required=True)
    parser.add_argument("--to", dest="date_to", type=date.fromisoformat, required=True)
    args = parser.parse_args()
    n = collect_observations(args.date_from, args.date_to)
    print(f"wrote {n} new observation days")


if __name__ == "__main__":
    main()
