#!/usr/bin/env python3
"""Cache the fifth untouched company universe for diagnostic-contrast confirmation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from confirmation5_universe import CONFIRMATION5_UNIVERSE
from download_data import fetch_news, fetch_prices
from universe import NEWS_DATASET

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data_confirmation5"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    DATA.mkdir(parents=True, exist_ok=True)
    news_path = DATA / "news_slim.parquet"
    price_path = DATA / "prices_close.parquet"
    meta_path = DATA / "download_meta.json"

    if args.force or not news_path.exists():
        news = fetch_news(CONFIRMATION5_UNIVERSE)
        news.to_parquet(news_path, index=False)
    else:
        import pandas as pd

        news = pd.read_parquet(news_path)
    symbols = sorted(news["symbol"].unique())

    if args.force or not price_path.exists():
        prices = fetch_prices(symbols)
        prices.to_parquet(price_path)
    else:
        import pandas as pd

        prices = pd.read_parquet(price_path)

    meta = {
        "role": "untouched_diagnostic_contrast_confirmation",
        "news_dataset": NEWS_DATASET,
        "selection": (
            "disjoint fixed universe; curated liquid names; "
            "selected from raw news-row coverage only"
        ),
        "declared_symbols": CONFIRMATION5_UNIVERSE,
        "downloaded_symbols": symbols,
        "n_news_rows": int(len(news)),
        "news_date_min": str(news["date"].min()),
        "news_date_max": str(news["date"].max()),
        "price_rows": int(len(prices)),
    }
    meta_path.write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
