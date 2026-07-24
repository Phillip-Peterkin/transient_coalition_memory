#!/usr/bin/env python3
"""Causal Weather stream: multi-model previous_day1 votes → next-day warmer."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from cities import CITIES, MODELS

ROOT = Path(__file__).resolve().parent
DEFAULT_DATA = ROOT / "data"


@dataclass(frozen=True)
class WeatherEvent:
    t: int
    day: str
    symbol: str
    key: tuple
    reports: list[tuple[int, int, int]]
    truth: int
    prev_truth: int | None
    split: str
    tmax_today: float
    tmax_tomorrow: float


class CleanWeatherStream:
    """Locked clean Weather bed (see PROTOCOL.md)."""

    def __init__(self, data_dir: Path | str = DEFAULT_DATA, contact_frac: float = 0.70):
        data_dir = Path(data_dir)
        self.observations = pd.read_parquet(data_dir / "observations_daily.parquet")
        self.forecasts = pd.read_parquet(
            data_dir / "forecasts_daily_previous_day1.parquet"
        )
        meta_path = data_dir / "download_meta.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text())
            self.models = list(meta["models"])
            self.city_symbols = [city["symbol"] for city in meta["cities"]]
        else:
            self.models = list(MODELS)
            self.city_symbols = [symbol for symbol, *_rest in CITIES]
        self.source_index = {model: index for index, model in enumerate(self.models)}
        self.symbol_index = {
            symbol: index for index, symbol in enumerate(self.city_symbols)
        }
        self.events = self._build_events(contact_frac)

    def _build_events(self, contact_frac: float) -> list[WeatherEvent]:
        obs = self.observations.copy()
        fcst = self.forecasts.copy()
        obs["date"] = pd.to_datetime(obs["date"])
        fcst["date"] = pd.to_datetime(fcst["date"])

        events: list[WeatherEvent] = []
        for symbol in self.city_symbols:
            o = obs[obs["symbol"] == symbol].sort_values("date").reset_index(drop=True)
            f = fcst[fcst["symbol"] == symbol].set_index("date")
            if len(o) < 3:
                continue
            prev_truth: int | None = None
            for i in range(len(o) - 1):
                today = o.iloc[i]
                tomorrow = o.iloc[i + 1]
                tmax_today = today["tmax_obs"]
                tmax_tomorrow = tomorrow["tmax_obs"]
                if pd.isna(tmax_today) or pd.isna(tmax_tomorrow):
                    continue
                truth = int(float(tmax_tomorrow) > float(tmax_today))
                tomorrow_date = pd.Timestamp(tomorrow["date"])
                if tomorrow_date not in f.index:
                    continue
                forecast_row = f.loc[tomorrow_date]
                reports: list[tuple[int, int, int]] = []
                for model in self.models:
                    value = forecast_row.get(model)
                    if value is None or (isinstance(value, float) and np.isnan(value)):
                        continue
                    vote = int(float(value) > float(tmax_today))
                    reports.append((self.source_index[model], 0, vote))
                if not reports:
                    continue
                day = str(pd.Timestamp(today["date"]).date())
                events.append(
                    WeatherEvent(
                        t=0,  # filled after global sort
                        day=day,
                        symbol=symbol,
                        key=(self.symbol_index[symbol], 0),
                        reports=reports,
                        truth=truth,
                        prev_truth=prev_truth,
                        split="",  # filled after day split
                        tmax_today=float(tmax_today),
                        tmax_tomorrow=float(tmax_tomorrow),
                    )
                )
                prev_truth = truth

        events.sort(key=lambda event: (event.day, event.symbol))
        days = sorted({event.day for event in events})
        cut = int(len(days) * contact_frac)
        cut = min(max(cut, 1), len(days) - 1)
        contact_days = set(days[:cut])
        stamped: list[WeatherEvent] = []
        for index, event in enumerate(events):
            stamped.append(
                WeatherEvent(
                    t=index,
                    day=event.day,
                    symbol=event.symbol,
                    key=event.key,
                    reports=event.reports,
                    truth=event.truth,
                    prev_truth=event.prev_truth,
                    split="contact" if event.day in contact_days else "holdout",
                    tmax_today=event.tmax_today,
                    tmax_tomorrow=event.tmax_tomorrow,
                )
            )
        return stamped

    def summary(self) -> dict:
        truths = np.asarray([event.truth for event in self.events], dtype=float)
        flips = [
            event
            for event in self.events
            if event.prev_truth is not None and event.truth != event.prev_truth
        ]
        agree = []
        for event in self.events:
            votes = [vote for _, _, vote in event.reports]
            if not votes:
                continue
            majority = int(sum(votes) >= (len(votes) / 2))
            agree.append(int(majority == event.truth))
        return {
            "n_events": len(self.events),
            "n_symbols": len({event.symbol for event in self.events}),
            "n_sources": len(self.models),
            "n_days": len({event.day for event in self.events}),
            "contact_events": sum(event.split == "contact" for event in self.events),
            "holdout_events": sum(event.split == "holdout" for event in self.events),
            "flip_events": len(flips),
            "truth_up_rate": float(truths.mean()) if len(truths) else float("nan"),
            "mean_reports": float(np.mean([len(event.reports) for event in self.events])),
            "majority_accuracy": float(np.mean(agree)) if agree else float("nan"),
            "sources": {index: model for model, index in self.source_index.items()},
            "label_rule": "tmax_obs[D+1] > tmax_obs[D]",
            "report_lead": "previous_day1",
            "no_weekly_median": True,
        }
