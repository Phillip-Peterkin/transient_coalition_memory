#!/usr/bin/env python3
"""Download and cache the slim finance/news panel used by protocol v0."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import yfinance as yf
from datasets import load_dataset

from universe import NEWS_DATASET, PRICE_END, PRICE_START, UNIVERSE

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"


def fetch_news(symbols: list[str] = UNIVERSE) -> pd.DataFrame:
    ds = load_dataset(NEWS_DATASET, split="train")
    allowed = set(symbols)
    rows = []
    for row in ds:
        sym = row["symbol"]
        if sym not in allowed:
            continue
        sentiment = row["sentiment"]
        if sentiment not in ("Positive", "Negative"):
            continue
        score = row["sentimentScore"]
        if score is None:
            score = 0.5 if sentiment == "Positive" else -0.5
        rows.append(
            {
                "symbol": sym,
                "date": str(row["publishedDate"])[:10],
                "site": str(row["site"]),
                "sentiment": sentiment,
                "score": float(score),
            }
        )
    news = pd.DataFrame(rows)
    if news.empty:
        raise RuntimeError("No news rows matched the frozen universe")
    return news.sort_values(["date", "symbol", "site"]).reset_index(drop=True)


def fetch_prices(symbols: list[str]) -> pd.DataFrame:
    px = yf.download(
        symbols,
        start=PRICE_START,
        end=PRICE_END,
        auto_adjust=True,
        progress=False,
        threads=True,
    )
    if isinstance(px.columns, pd.MultiIndex):
        if "Close" in px.columns.get_level_values(0):
            close = px["Close"].copy()
        else:
            close = pd.concat(
                {t: px[t]["Close"] for t in symbols if t in px.columns.get_level_values(0)},
                axis=1,
            )
    else:
        close = px[["Close"]].copy()
        close.columns = [symbols[0]]
    close.index = pd.to_datetime(close.index).tz_localize(None)
    return close.sort_index()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    DATA.mkdir(parents=True, exist_ok=True)
    news_path = DATA / "news_slim.parquet"
    price_path = DATA / "prices_close.parquet"
    meta_path = DATA / "download_meta.json"

    if args.force or not news_path.exists():
        news = fetch_news()
        news.to_parquet(news_path, index=False)
    else:
        news = pd.read_parquet(news_path)

    symbols = sorted(news["symbol"].unique())
    if args.force or not price_path.exists():
        close = fetch_prices(symbols)
        close.to_parquet(price_path)
    else:
        close = pd.read_parquet(price_path)

    meta = {
        "news_dataset": NEWS_DATASET,
        "n_news_rows": int(len(news)),
        "symbols": symbols,
        "news_date_min": str(news["date"].min()),
        "news_date_max": str(news["date"].max()),
        "price_rows": int(len(close)),
        "price_cols": list(close.columns),
        "sites": sorted(news["site"].unique()),
    }
    meta_path.write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
