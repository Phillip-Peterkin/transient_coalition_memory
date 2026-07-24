#!/usr/bin/env python3
"""Collection status for year_multi_domain (no scoring)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DBSA = ROOT.parent
sys.path.insert(0, str(DBSA / "prospective_weather"))


def weather_status() -> dict:
    ledger = DBSA / "weather_year_stress" / "ledger"
    os.environ["DBSA_WEATHER_LEDGER"] = str(ledger)
    try:
        from weather_stream import ledger_status

        st = ledger_status()
        return {
            "lane": "weather",
            "ledger": str(ledger),
            "n_forecast_days": st.get("n_forecast_days"),
            "n_observation_days": st.get("n_observation_days"),
            "n_events": st.get("n_events"),
            "n_labeled_decision_days": st.get("n_labeled_decision_days"),
            "forecast_span": st.get("forecast_span"),
            "open_forecast_days_met": st.get("open_forecast_days_met"),
            "open_label_days_met": st.get("open_label_days_met"),
            "scoring": "closed",
        }
    except Exception as exc:  # noqa: BLE001
        days = sorted([p.name for p in ledger.glob("20*") if p.is_dir()]) if ledger.exists() else []
        return {
            "lane": "weather",
            "ledger": str(ledger),
            "n_forecast_day_dirs": len(days),
            "span": [days[0], days[-1]] if days else None,
            "error": str(exc),
            "scoring": "closed",
        }


def _lane_events(path: Path, name: str) -> dict:
    idx = path / "INDEX.json"
    ev = path / "events.json"
    if idx.exists():
        meta = json.loads(idx.read_text())
        return {"lane": name, "ledger": str(path), **meta}
    if ev.exists():
        payload = json.loads(ev.read_text())
        return {
            "lane": name,
            "ledger": str(path),
            "n_events": payload.get("n_events"),
            "scoring": "closed",
        }
    return {"lane": name, "ledger": str(path), "n_events": 0, "scoring": "closed", "present": False}


def main() -> None:
    out = {
        "protocol": "year_multi_domain_status_v1",
        "scoring": "closed_until_SCORING_PROTOCOL_open_conditions",
        "primary_method": "aware_arousal",
        "lanes": [
            weather_status(),
            _lane_events(ROOT / "finance" / "ledger", "finance"),
            _lane_events(ROOT / "medical" / "ledger", "medical"),
        ],
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
