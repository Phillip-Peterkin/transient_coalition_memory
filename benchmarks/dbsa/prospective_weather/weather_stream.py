"""Build causal delayed Weather events from the prospective ledger (no scoring)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from stations import MODELS, STATIONS

ROOT = Path(__file__).resolve().parent
LEDGER = ROOT / "ledger"


@dataclass(frozen=True)
class LedgerEvent:
    t: int
    day: str
    due_day: str
    due_t: int
    symbol: str
    key: tuple[int, int]
    reports: list[tuple[int, int, int]]
    truth: int
    prev_truth: int | None
    shift_age: None
    tmax_today: float
    tmax_tomorrow: float


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _forecast_days() -> list[str]:
    return sorted(path.parent.name for path in LEDGER.glob("*/forecast_snapshot.json"))


def _obs_days() -> list[str]:
    return sorted(path.parent.name for path in LEDGER.glob("*/observation_snapshot.json"))


def _obs_tmax(day: str) -> dict[str, float]:
    path = LEDGER / day / "observation_snapshot.json"
    if not path.exists():
        return {}
    payload = _load_json(path)
    out = {}
    for row in payload["stations"]:
        if row.get("tmax_obs") is not None:
            out[row["symbol"]] = float(row["tmax_obs"])
    return out


def _forecast_maxes(day: str) -> dict[str, dict[str, float]]:
    path = LEDGER / day / "forecast_snapshot.json"
    if not path.exists():
        return {}
    payload = _load_json(path)
    out: dict[str, dict[str, float]] = {}
    for row in payload["stations"]:
        models = {}
        for model, blob in row.get("models", {}).items():
            if blob and blob.get("daily_max") is not None:
                models[model] = float(blob["daily_max"])
        out[row["symbol"]] = models
    return out


def build_events() -> list[LedgerEvent]:
    """Decision on day D uses forecast snapshot for D+1 vs obs D; label is obs D+1>D."""
    symbol_index = {symbol: index for index, (symbol, *_rest) in enumerate(STATIONS)}
    source_index = {model: index for index, model in enumerate(MODELS)}
    forecast_days = set(_forecast_days())
    observation_days = set(_obs_days())

    raw: list[tuple] = []
    for symbol, *_rest in STATIONS:
        prev_truth: int | None = None
        for day in sorted(observation_days):
            day_d = date.fromisoformat(day)
            tomorrow = (day_d + timedelta(days=1)).isoformat()
            if tomorrow not in observation_days or tomorrow not in forecast_days:
                continue
            obs_today = _obs_tmax(day)
            obs_tomorrow = _obs_tmax(tomorrow)
            if symbol not in obs_today or symbol not in obs_tomorrow:
                continue
            fcst = _forecast_maxes(tomorrow).get(symbol, {})
            tmax_today = obs_today[symbol]
            tmax_tomorrow = obs_tomorrow[symbol]
            truth = int(tmax_tomorrow > tmax_today)
            reports: list[tuple[int, int, int]] = []
            for model in MODELS:
                if model not in fcst:
                    continue
                vote = int(fcst[model] > tmax_today)
                reports.append((source_index[model], 0, vote))
            if not reports:
                continue
            raw.append(
                (
                    day,
                    tomorrow,
                    symbol,
                    symbol_index[symbol],
                    reports,
                    truth,
                    prev_truth,
                    tmax_today,
                    tmax_tomorrow,
                )
            )
            prev_truth = truth

    raw.sort(key=lambda row: (row[0], row[2]))
    first_t_for_day: dict[str, int] = {}
    for index, row in enumerate(raw):
        first_t_for_day.setdefault(row[0], index)

    events: list[LedgerEvent] = []
    for index, row in enumerate(raw):
        day, tomorrow, symbol, sym_i, reports, truth, prev_truth, tmax_today, tmax_tom = row
        due_t = first_t_for_day.get(tomorrow)
        if due_t is None:
            due_t = index + 1
        due_t = max(int(due_t), index + 1)
        events.append(
            LedgerEvent(
                t=index,
                day=day,
                due_day=tomorrow,
                due_t=due_t,
                symbol=symbol,
                key=(sym_i, 0),
                reports=reports,
                truth=truth,
                prev_truth=prev_truth,
                shift_age=None,
                tmax_today=tmax_today,
                tmax_tomorrow=tmax_tom,
            )
        )
    return events


def ledger_status() -> dict:
    forecast_days = _forecast_days()
    obs_days = _obs_days()
    events = build_events()
    labeled_decision_days = sorted({event.day for event in events})
    return {
        "n_forecast_days": len(forecast_days),
        "n_observation_days": len(obs_days),
        "n_events": len(events),
        "n_labeled_decision_days": len(labeled_decision_days),
        "forecast_span": [forecast_days[0], forecast_days[-1]] if forecast_days else None,
        "open_forecast_days_met": len(forecast_days) >= 60,
        "open_label_days_met": len(labeled_decision_days) >= 45,
    }
