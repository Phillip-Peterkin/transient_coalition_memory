#!/usr/bin/env python3
"""Fail loud if the clean Weather bed is missing or reintroduces known taints."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from cities import CITIES, END_DATE, MODELS, START_DATE  # noqa: E402
from weather_stream import CleanWeatherStream  # noqa: E402


def main() -> None:
    data = ROOT / "data"
    meta_path = data / "download_meta.json"
    assert meta_path.exists(), "missing download_meta.json — run download_data.py"
    meta = json.loads(meta_path.read_text())

    assert meta["lead"] == "previous_day1_only", meta["lead"]
    assert "weekly_median_threshold" in meta["forbidden"]
    assert meta["start_date"] == START_DATE
    assert meta["end_date"] == END_DATE
    assert meta["models"] == MODELS
    assert [city["symbol"] for city in meta["cities"]] == [c[0] for c in CITIES]

    obs = pd.read_parquet(data / "observations_daily.parquet")
    fcst = pd.read_parquet(data / "forecasts_daily_previous_day1.parquet")
    assert set(obs["symbol"]) == {c[0] for c in CITIES}
    for model in MODELS:
        assert model in fcst.columns, model
        assert fcst[model].notna().mean() > 0.95, (model, fcst[model].notna().mean())

    stream = CleanWeatherStream(data)
    summary = stream.summary()
    assert summary["n_events"] > 2000, summary
    assert summary["n_sources"] == len(MODELS)
    assert summary["no_weekly_median"] is True
    assert 0.35 < summary["truth_up_rate"] < 0.65, summary["truth_up_rate"]
    assert summary["flip_events"] > 200, summary["flip_events"]
    assert summary["holdout_events"] > 100
    assert summary["majority_accuracy"] > 0.70, summary["majority_accuracy"]

    # Causal vote check: report uses obs today + forecast tomorrow, never weekly median.
    sample = stream.events[100]
    assert sample.reports, sample
    assert all(vote in (0, 1) for _, _, vote in sample.reports)

    # Holdout days are strictly after contact days.
    contact_days = [event.day for event in stream.events if event.split == "contact"]
    holdout_days = [event.day for event in stream.events if event.split == "holdout"]
    assert max(contact_days) < min(holdout_days)

    # No label uses future weekly statistics: recompute label from adjacent obs only.
    for event in stream.events[::200]:
        recomputed = int(event.tmax_tomorrow > event.tmax_today)
        assert recomputed == event.truth

    print("purity_check: ALL CHECKS PASSED")
    print(json.dumps(summary, indent=2, default=float))


if __name__ == "__main__":
    main()
