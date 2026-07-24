#!/usr/bin/env python3
"""Collect virgin finance/news year lane (no scoring)."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
import yfinance as yf
from datasets import load_dataset

ROOT = Path(__file__).resolve().parent
LEDGER = ROOT / "ledger"
REPO_FINANCE = ROOT.parents[2] / "realdata_finance"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(REPO_FINANCE))

from universe_year import (  # noqa: E402
    NEWS_DATASET,
    YEAR_FINANCE_END,
    YEAR_FINANCE_START,
    YEAR_FINANCE_UNIVERSE,
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_news(symbols: list[str]) -> pd.DataFrame:
    ds = load_dataset(NEWS_DATASET, split="train")
    allowed = set(symbols)
    start = pd.Timestamp(YEAR_FINANCE_START)
    end = pd.Timestamp(YEAR_FINANCE_END)
    rows = []
    for row in ds:
        sym = row["symbol"]
        if sym not in allowed:
            continue
        sentiment = row["sentiment"]
        if sentiment not in ("Positive", "Negative"):
            continue
        day = pd.Timestamp(str(row["publishedDate"])[:10])
        if day < start or day > end:
            continue
        rows.append(
            {
                "symbol": sym,
                "date": day.strftime("%Y-%m-%d"),
                "published": str(row["publishedDate"]),
                "site": str(row["site"]),
                "sentiment": sentiment,
                "vote": 1 if sentiment == "Positive" else 0,
            }
        )
    news = pd.DataFrame(rows)
    if news.empty:
        raise RuntimeError("No news rows in year window for virgin universe")
    return news.sort_values(["date", "symbol", "site"]).reset_index(drop=True)


def fetch_prices(symbols: list[str]) -> pd.DataFrame:
    px = yf.download(
        symbols,
        start="2022-08-01",
        end="2023-08-25",
        auto_adjust=True,
        progress=False,
        threads=True,
    )
    if isinstance(px.columns, pd.MultiIndex):
        close = px["Close"].copy()
    else:
        close = px[["Close"]].copy()
        close.columns = [symbols[0]]
    close.index = pd.to_datetime(close.index).tz_localize(None)
    return close.sort_index()


def build_events(news: pd.DataFrame, prices: pd.DataFrame) -> list[dict]:
    # Map sites → stable source ids
    sites = sorted(news["site"].dropna().unique())
    site_id = {s: i for i, s in enumerate(sites)}
    trading_days = list(prices.index)
    events = []
    for sym in sorted(news["symbol"].unique()):
        if sym not in prices.columns:
            continue
        series = prices[sym].dropna()
        if series.empty:
            continue
        # Group news by calendar date → next trading session
        sub = news[news["symbol"] == sym]
        for day, grp in sub.groupby("date"):
            day_ts = pd.Timestamp(day)
            # session = first trading day >= news date
            future = [d for d in trading_days if d >= day_ts]
            if len(future) < 2:
                continue
            t0, t1 = future[0], future[1]
            if t0 not in series.index or t1 not in series.index:
                continue
            c0, c1 = float(series.loc[t0]), float(series.loc[t1])
            if c0 != c0 or c1 != c1:
                continue
            truth = int(c1 > c0)
            reports = []
            for row in grp.itertuples():
                reports.append([site_id[str(row.site)], 0, int(row.vote)])
            if not reports:
                continue
            events.append(
                {
                    "key": [sym, t0.strftime("%Y-%m-%d")],
                    "t": t0.strftime("%Y-%m-%d"),
                    "due_t": t1.strftime("%Y-%m-%d"),
                    "truth": truth,
                    "reports": reports,
                }
            )
    events.sort(key=lambda e: (e["t"], e["key"][0]))
    return events, site_id


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    LEDGER.mkdir(parents=True, exist_ok=True)
    events_path = LEDGER / "events.json"
    if events_path.exists() and not args.force:
        print("exists", events_path, "use --force to rebuild")
        return

    print("fetch news…", flush=True)
    news = fetch_news(YEAR_FINANCE_UNIVERSE)
    news.to_parquet(LEDGER / "news.parquet", index=False)
    symbols = sorted(news["symbol"].unique())
    print("symbols with news", len(symbols), "rows", len(news), flush=True)

    print("fetch prices…", flush=True)
    prices = fetch_prices(symbols)
    prices.to_parquet(LEDGER / "prices_close.parquet")

    events, site_id = build_events(news, prices)
    payload = {
        "protocol": "year_multi_domain_finance_v1",
        "window": [YEAR_FINANCE_START, YEAR_FINANCE_END],
        "universe": YEAR_FINANCE_UNIVERSE,
        "news_dataset": NEWS_DATASET,
        "n_events": len(events),
        "n_symbols": len({e["key"][0] for e in events}),
        "site_id": site_id,
        "mean_reports": float(pd.Series([len(e["reports"]) for e in events]).mean())
        if events
        else 0.0,
        "events": events,
    }
    blob = json.dumps(payload, indent=2).encode("utf-8")
    events_path.write_bytes(blob)
    (LEDGER / "sha256.txt").write_text(_sha(blob) + "\n")
    (LEDGER / "INDEX.json").write_text(
        json.dumps(
            {
                "n_events": len(events),
                "sha256": _sha(blob),
                "n_symbols": payload["n_symbols"],
                "scoring": "closed",
            },
            indent=2,
        )
    )
    print("WROTE", events_path, "events", len(events), flush=True)


if __name__ == "__main__":
    main()
