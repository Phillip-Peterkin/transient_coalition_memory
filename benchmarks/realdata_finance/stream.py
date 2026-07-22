"""Build a streaming decision world from cached finance/news panels."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from universe import CONTACT_FRACTION

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"


@dataclass
class DecisionEvent:
    t: int
    day: str
    symbol: str
    item: int
    key: tuple
    reports: list
    truth: int
    prev_truth: int | None
    split: str
    n_sites: int


class FinanceNewsStream:
    """Event stream compatible with TCM report tuples `(source, context, y)`."""

    def __init__(self, data_dir: Path | None = None, horizon: int = 1):
        self.horizon = int(horizon)
        data_dir = Path(data_dir or DATA)
        news_path = data_dir / "news_slim.parquet"
        price_path = data_dir / "prices_close.parquet"
        if not news_path.exists() or not price_path.exists():
            raise FileNotFoundError(
                f"Missing cache under {data_dir}; run download_data.py first"
            )
        self.news = pd.read_parquet(news_path)
        self.close = pd.read_parquet(price_path)
        self.close.index = pd.to_datetime(self.close.index).tz_localize(None)

        sites = sorted(self.news["site"].unique())
        self.source_ids = {site: i for i, site in enumerate(sites)}
        self.id_to_source = {i: s for s, i in self.source_ids.items()}

        symbols = sorted(self.news["symbol"].unique())
        self.item_ids = {sym: i for i, sym in enumerate(symbols)}
        self.id_to_item = {i: s for s, i in self.item_ids.items()}

        # h-day-ahead return sign, labeled at day t (h=1 -> next session).
        ret = (self.close.shift(-self.horizon) / self.close - 1.0)
        self.truth = (ret > 0).astype(float).where(ret.notna())
        # Same-day direction for persistence oracle / previous truth.
        self.same_day_dir = (self.close.pct_change(fill_method=None) > 0).astype(float).where(
            self.close.pct_change(fill_method=None).notna()
        )

        self.events = self._build_events()
        self.T = 1 + max(e.t for e in self.events)
        self.I = len(self.item_ids)

    def _align_trading_day(self, date_str: str) -> pd.Timestamp | None:
        ts = pd.Timestamp(date_str)
        if ts in self.truth.index:
            return ts
        idx = self.truth.index.searchsorted(ts)
        if idx >= len(self.truth.index):
            return None
        return self.truth.index[idx]

    def _build_events(self) -> list[DecisionEvent]:
        day_set = []
        provisional = []
        for (sym, date_str), group in self.news.groupby(["symbol", "date"], sort=True):
            if sym not in self.truth.columns:
                continue
            ts = self._align_trading_day(date_str)
            if ts is None:
                continue
            y = self.truth.at[ts, sym]
            if pd.isna(y):
                continue
            reports = []
            for _, row in group.iterrows():
                sid = self.source_ids[row["site"]]
                y_rep = 1 if row["sentiment"] == "Positive" else 0
                reports.append((sid, 0, y_rep))
            if not reports:
                continue
            day = str(ts.date())
            provisional.append(
                {
                    "day": day,
                    "symbol": sym,
                    "reports": reports,
                    "truth": int(y),
                    "n_sites": int(group["site"].nunique()),
                    "ts": ts,
                }
            )
            day_set.append(day)

        days = sorted(set(day_set))
        day_index = {d: i for i, d in enumerate(days)}
        cut = int(round(CONTACT_FRACTION * len(days)))
        cut = min(max(cut, 1), len(days) - 1) if len(days) > 1 else 0
        contact_days = set(days[:cut])

        # Previous next-day-truth per symbol (for flip detection).
        prev_truth: dict[str, int] = {}
        events: list[DecisionEvent] = []
        for row in sorted(provisional, key=lambda r: (r["day"], r["symbol"])):
            sym = row["symbol"]
            day = row["day"]
            item = self.item_ids[sym]
            split = "contact" if day in contact_days else "holdout"
            events.append(
                DecisionEvent(
                    t=day_index[day],
                    day=day,
                    symbol=sym,
                    item=item,
                    key=(item, 0),
                    reports=row["reports"],
                    truth=row["truth"],
                    prev_truth=prev_truth.get(sym),
                    split=split,
                    n_sites=row["n_sites"],
                )
            )
            prev_truth[sym] = row["truth"]
        return events

    def persistence_prediction(self, event: DecisionEvent) -> float | None:
        """Predict tomorrow using today's realized direction (no news)."""
        ts = pd.Timestamp(event.day)
        if event.symbol not in self.same_day_dir.columns:
            return None
        if ts not in self.same_day_dir.index:
            return None
        val = self.same_day_dir.at[ts, event.symbol]
        if pd.isna(val):
            return None
        return float(val)

    def source_agreement(self, reports: list) -> float:
        if len(reports) < 2:
            return float("nan")
        ys = [y for _, _, y in reports]
        agree = 0
        total = 0
        for i in range(len(ys)):
            for j in range(i + 1, len(ys)):
                agree += int(ys[i] == ys[j])
                total += 1
        return agree / total if total else float("nan")

    def summary(self) -> dict:
        flips = [e for e in self.events if e.prev_truth is not None and e.truth != e.prev_truth]
        return {
            "n_events": len(self.events),
            "n_symbols": self.I,
            "n_sources": len(self.source_ids),
            "n_days": self.T,
            "contact_events": sum(e.split == "contact" for e in self.events),
            "holdout_events": sum(e.split == "holdout" for e in self.events),
            "flip_events": len(flips),
            "truth_up_rate": float(np.mean([e.truth for e in self.events])),
            "mean_reports": float(np.mean([len(e.reports) for e in self.events])),
            "mean_sites": float(np.mean([e.n_sites for e in self.events])),
            "multi_source_frac": float(np.mean([e.n_sites >= 2 for e in self.events])),
            "mean_source_agreement": float(
                np.nanmean([self.source_agreement(e.reports) for e in self.events])
            ),
            "sources": self.id_to_source,
        }
