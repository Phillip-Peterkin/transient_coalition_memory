#!/usr/bin/env python3
"""Append-only daily collector for the DBSA prospective Weather lane.

Does not score models. Writes timestamped forecast snapshots + sha256 digests.
Supports single-day and inclusive date-range backfill from the locked API.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from stations import MODELS, STATIONS, assert_disjoint

ROOT = Path(__file__).resolve().parent
LEDGER = ROOT / "ledger"
INDEX = LEDGER / "INDEX.jsonl"
USER_AGENT = "transient-coalition-memory-dbsa-prospective/0.1"


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


def fetch_station_day(symbol: str, lat: float, lon: float, day: date) -> dict:
    # Capture previous_day1 hourly temps covering the target calendar day UTC.
    query = urllib.parse.urlencode(
        {
            "latitude": lat,
            "longitude": lon,
            "start_date": day.isoformat(),
            "end_date": day.isoformat(),
            "hourly": "temperature_2m_previous_day1",
            "models": ",".join(MODELS),
            "timezone": "UTC",
        }
    )
    payload = _get_json(
        f"https://previous-runs-api.open-meteo.com/v1/forecast?{query}"
    )
    hourly = payload["hourly"]
    models = {}
    for model in MODELS:
        key = f"temperature_2m_previous_day1_{model}"
        values = hourly.get(key)
        if values is None:
            models[model] = None
            continue
        finite = [float(value) for value in values if value is not None]
        models[model] = {
            "hourly_n": len(values),
            "finite_n": len(finite),
            "daily_max": max(finite) if finite else None,
        }
    return {
        "symbol": symbol,
        "lat": lat,
        "lon": lon,
        "day": day.isoformat(),
        "models": models,
        "source_api": "open-meteo-previous-runs",
        "lead": "previous_day1",
    }


def collect(
    day: date | None = None,
    *,
    collection_mode: str = "live",
    skip_existing: bool = False,
) -> Path | None:
    assert_disjoint()
    day = day or datetime.now(timezone.utc).date()
    day_dir = LEDGER / day.isoformat()
    if day_dir.exists():
        if skip_existing:
            print(f"skip existing ledger day {day_dir}")
            return None
        raise SystemExit(
            f"refusing to rewrite existing ledger day {day_dir}; append-only"
        )
    day_dir.mkdir(parents=True, exist_ok=False)

    collected_at = datetime.now(timezone.utc).isoformat()
    stations = []
    for symbol, lat, lon, name in STATIONS:
        print(f"collect {symbol} ({name}) for {day.isoformat()} …")
        row = fetch_station_day(symbol, lat, lon, day)
        row["name"] = name
        stations.append(row)
        time.sleep(0.25)

    artifact = {
        "protocol": "dbsa_prospective_weather_v1",
        "collected_at_utc": collected_at,
        "day_utc": day.isoformat(),
        "models": MODELS,
        "stations": stations,
        "scoring_forbidden": True,
        "collection_mode": collection_mode,
    }
    raw = _canonical_bytes(artifact)
    digest = hashlib.sha256(raw).hexdigest()
    artifact_path = day_dir / "forecast_snapshot.json"
    artifact_path.write_bytes(
        json.dumps(artifact, indent=2, sort_keys=True).encode("utf-8")
    )
    (day_dir / "sha256.txt").write_text(digest + "\n", encoding="utf-8")

    index_row = {
        "day_utc": day.isoformat(),
        "collected_at_utc": collected_at,
        "sha256": digest,
        "path": str(artifact_path.relative_to(ROOT)),
        "n_stations": len(stations),
        "n_models": len(MODELS),
        "collection_mode": collection_mode,
    }
    with INDEX.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(index_row, sort_keys=True) + "\n")
    print("wrote", artifact_path)
    print("sha256", digest)
    return artifact_path


def collect_range(start: date, end: date, *, collection_mode: str) -> list[Path]:
    if end < start:
        raise SystemExit("--to must be on or after --from")
    written: list[Path] = []
    day = start
    while day <= end:
        path = collect(day, collection_mode=collection_mode, skip_existing=True)
        if path is not None:
            written.append(path)
        day += timedelta(days=1)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--day", type=date.fromisoformat, default=None)
    parser.add_argument("--from", dest="date_from", type=date.fromisoformat, default=None)
    parser.add_argument("--to", dest="date_to", type=date.fromisoformat, default=None)
    parser.add_argument(
        "--mode",
        choices=("live", "archive_backfill"),
        default=None,
        help="Defaults to archive_backfill for ranges, live for single/today.",
    )
    args = parser.parse_args()
    if args.date_from or args.date_to:
        if not (args.date_from and args.date_to):
            parser.error("--from and --to must be used together")
        mode = args.mode or "archive_backfill"
        written = collect_range(args.date_from, args.date_to, collection_mode=mode)
        print(f"wrote {len(written)} new forecast days")
        return
    mode = args.mode or "live"
    collect(args.day, collection_mode=mode)


if __name__ == "__main__":
    main()
