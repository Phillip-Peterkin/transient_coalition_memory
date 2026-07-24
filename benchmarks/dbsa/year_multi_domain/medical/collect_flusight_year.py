#!/usr/bin/env python3
"""Collect FluSight multi-model year lane into medical/ledger (no scoring)."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from io import StringIO
from pathlib import Path
from urllib.request import urlopen, Request

import pandas as pd

from locations import (
    FLUSIGHT_LOCATIONS,
    MEDICAL_WINDOW_END,
    MEDICAL_WINDOW_START,
    PREFERRED_MODELS,
)

ROOT = Path(__file__).resolve().parent
LEDGER = ROOT / "ledger"
HUB = "https://raw.githubusercontent.com/cdcepi/FluSight-forecast-hub/main"
API = "https://api.github.com/repos/cdcepi/FluSight-forecast-hub/contents"


def _get(url: str, retries: int = 4) -> bytes:
    last = None
    for i in range(retries):
        try:
            req = Request(url, headers={"User-Agent": "tcm-year-multi-domain/1.0"})
            with urlopen(req, timeout=120) as resp:
                return resp.read()
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(2**i)
    raise RuntimeError(f"fetch failed {url}: {last}")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_targets() -> pd.DataFrame:
    raw = _get(f"{HUB}/target-data/time-series.csv")
    df = pd.read_csv(StringIO(raw.decode("utf-8")))
    # Latest as_of per (location, target_end_date)
    df = df[df["target"] == "wk inc flu hosp"].copy()
    df = df.sort_values("as_of").groupby(["location", "target_end_date"], as_index=False).tail(1)
    df["target_end_date"] = pd.to_datetime(df["target_end_date"])
    df["observation"] = pd.to_numeric(df["observation"], errors="coerce")
    return df


def list_model_files(model: str) -> list[str]:
    raw = _get(f"{API}/model-output/{model}?ref=main")
    items = json.loads(raw.decode("utf-8"))
    if not isinstance(items, list):
        return []
    names = []
    start = pd.Timestamp(MEDICAL_WINDOW_START)
    end = pd.Timestamp(MEDICAL_WINDOW_END)
    for item in items:
        name = item.get("name", "")
        if not name.endswith(".csv"):
            continue
        day = name.split("-", 3)
        if len(day) < 3:
            continue
        try:
            ref = pd.Timestamp("-".join(day[:3]))
        except Exception:  # noqa: BLE001
            continue
        if start <= ref <= end:
            names.append(name)
    return sorted(names)


def parse_forecast_csv(model: str, filename: str, locations: set[str]) -> pd.DataFrame:
    raw = _get(f"{HUB}/model-output/{model}/{filename}")
    df = pd.read_csv(StringIO(raw.decode("utf-8")))
    need = {"reference_date", "horizon", "target", "location", "output_type", "output_type_id", "value"}
    if not need.issubset(df.columns):
        return pd.DataFrame()
    df = df[
        (df["target"] == "wk inc flu hosp")
        & (df["horizon"] == 1)
        & (df["output_type"] == "quantile")
        & (df["location"].astype(str).isin(locations))
    ].copy()
    if df.empty:
        return df
    # median quantile
    df["output_type_id"] = df["output_type_id"].astype(str)
    med = df[df["output_type_id"].isin(["0.5", "0.50"])].copy()
    if med.empty:
        return pd.DataFrame()
    med["model"] = model
    med["reference_date"] = pd.to_datetime(med["reference_date"])
    med["value"] = pd.to_numeric(med["value"], errors="coerce")
    return med[["reference_date", "location", "model", "value", "target_end_date"]]


def build_events(targets: pd.DataFrame, forecasts: pd.DataFrame) -> list[dict]:
    # Map observation by location + week end
    obs = {
        (str(r.location), pd.Timestamp(r.target_end_date).date().isoformat()): float(r.observation)
        for r in targets.itertuples()
        if pd.notna(r.observation)
    }
    events = []
    for (ref, loc), grp in forecasts.groupby(["reference_date", "location"]):
        ref_s = pd.Timestamp(ref).date().isoformat()
        # current week obs ≈ horizon 0 / previous week end = ref - 7d roughly
        # truth uses next week vs this week: target_end for horizon1 is usually ref+6d
        ted = pd.to_datetime(grp["target_end_date"].iloc[0]).date().isoformat()
        prev = (pd.Timestamp(ted) - pd.Timedelta(days=7)).date().isoformat()
        if (str(loc), ted) not in obs or (str(loc), prev) not in obs:
            continue
        adm_next = obs[(str(loc), ted)]
        adm_now = obs[(str(loc), prev)]
        truth = int(adm_next > adm_now)
        reports = []
        for row in grp.itertuples():
            vote = int(float(row.value) > adm_now)
            reports.append([str(row.model), 0, vote])
        if len(reports) < 2:
            continue
        events.append(
            {
                "key": [str(loc), ref_s],
                "t": ref_s,
                "due_t": ted,
                "truth": truth,
                "adm_now": adm_now,
                "adm_next": adm_next,
                "reports": reports,
            }
        )
    events.sort(key=lambda e: (e["t"], e["key"][0]))
    return events


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=None)
    args = ap.parse_args()
    LEDGER.mkdir(parents=True, exist_ok=True)
    models = args.models or PREFERRED_MODELS
    locations = set(FLUSIGHT_LOCATIONS)

    print("loading targets…", flush=True)
    targets = load_targets()
    (LEDGER / "targets_meta.json").write_text(
        json.dumps(
            {
                "n_rows": int(len(targets)),
                "window": [MEDICAL_WINDOW_START, MEDICAL_WINDOW_END],
                "locations": sorted(locations),
            },
            indent=2,
        )
    )

    frames = []
    for model in models:
        print("model", model, flush=True)
        try:
            files = list_model_files(model)
        except Exception as exc:  # noqa: BLE001
            print("  skip list", exc, flush=True)
            continue
        print("  files", len(files), flush=True)
        for i, name in enumerate(files):
            try:
                df = parse_forecast_csv(model, name, locations)
            except Exception as exc:  # noqa: BLE001
                print("  fail", name, exc, flush=True)
                continue
            if not df.empty:
                frames.append(df)
            if (i + 1) % 10 == 0:
                print(f"  {i+1}/{len(files)}", flush=True)
            time.sleep(0.05)

    if not frames:
        raise SystemExit("no forecast rows collected")
    forecasts = pd.concat(frames, ignore_index=True)
    events = build_events(targets, forecasts)
    payload = {
        "protocol": "year_multi_domain_medical_flusight_v1",
        "window": [MEDICAL_WINDOW_START, MEDICAL_WINDOW_END],
        "n_events": len(events),
        "n_models_seen": int(forecasts["model"].nunique()),
        "mean_reports": float(pd.Series([len(e["reports"]) for e in events]).mean())
        if events
        else 0.0,
        "events": events,
    }
    blob = json.dumps(payload, indent=2).encode("utf-8")
    out = LEDGER / "events.json"
    out.write_bytes(blob)
    (LEDGER / "sha256.txt").write_text(_sha(blob) + "\n")
    (LEDGER / "INDEX.json").write_text(
        json.dumps(
            {
                "n_events": len(events),
                "sha256": _sha(blob),
                "models": sorted(forecasts["model"].unique()),
                "scoring": "closed",
            },
            indent=2,
        )
    )
    print("WROTE", out, "events", len(events), flush=True)


if __name__ == "__main__":
    main()
