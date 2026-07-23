"""Causal headline-novelty contexts for the finance/news stream.

The current harness reduces every article to Positive or Negative.  Humans do
more: they recognize whether a report is a fresh event ("plant fire", "fraud
case", "earnings miss") or another version of a familiar publisher routine.

This module does not use a language model or future prices.  For each company,
it compares an article's title tokens only with that company's earlier titles.
The result is a two-state report context:

* context 0: routine / semantically similar to recent company news
* context 1: novel relative to recent company news

TCM can then learn a separate source population for routine and novel reports.
It is an intentionally small test of whether event identity contains useful
change information before adding a larger semantic mechanism.
"""

from __future__ import annotations

import re
from collections import deque

import pandas as pd

from stream import DecisionEvent, FinanceNewsStream
from universe import CONTACT_FRACTION

STOPWORDS = {
    "about", "after", "against", "and", "announces", "are", "as", "at", "be",
    "by", "company", "for", "from", "has", "in", "into", "is", "its", "new",
    "of", "on", "or", "reports", "shares", "stock", "the", "to", "with",
}


def title_tokens(title: str, symbol: str) -> set[str]:
    """Small transparent lexical representation; no pre-trained language model."""
    words = re.findall(r"[a-z]{3,}", title.lower())
    symbol = symbol.lower()
    return {word for word in words if word not in STOPWORDS and word != symbol}


class SemanticFinanceNewsStream(FinanceNewsStream):
    """Finance stream with causal routine-vs-novel report contexts."""

    def __init__(
        self,
        *args,
        novelty_threshold: float = 0.70,
        history_size: int = 12,
        min_history: int = 3,
        **kwargs,
    ):
        self.novelty_threshold = novelty_threshold
        self.history_size = history_size
        self.min_history = min_history
        self._novelty_values: list[float] = []
        super().__init__(*args, **kwargs)

    def _with_novelty_context(self) -> pd.DataFrame:
        if "title" not in self.news.columns or "published" not in self.news.columns:
            raise ValueError(
                "Semantic stream needs title/published columns; rerun download_data.py --force"
            )
        news = self.news.copy()
        news["_context"] = 0
        news["_novelty"] = 0.0

        for symbol, indexes in news.groupby("symbol", sort=False).groups.items():
            ordered = news.loc[indexes].sort_values("published")
            history: deque[set[str]] = deque(maxlen=self.history_size)
            for index, row in ordered.iterrows():
                tokens = title_tokens(row["title"], symbol)
                if len(history) < self.min_history or not tokens:
                    novelty = 0.0
                else:
                    # 1 - Jaccard similarity to the closest remembered story.
                    similarity = max(
                        len(tokens & old) / max(1, len(tokens | old))
                        for old in history
                    )
                    novelty = 1.0 - similarity
                news.at[index, "_novelty"] = novelty
                news.at[index, "_context"] = int(
                    len(history) >= self.min_history and novelty >= self.novelty_threshold
                )
                history.append(tokens)
        self._novelty_values = list(news["_novelty"])
        self.news_with_context = news
        return news

    def _build_events(self) -> list[DecisionEvent]:
        news = self._with_novelty_context()
        day_set = []
        provisional = []
        for (symbol, date_str), group in news.groupby(["symbol", "date"], sort=True):
            if symbol not in self.truth.columns:
                continue
            ts = self._align_trading_day(date_str)
            if ts is None:
                continue
            truth = self.truth.at[ts, symbol]
            if pd.isna(truth):
                continue
            reports = [
                (
                    self.source_ids[row["site"]],
                    int(row["_context"]),
                    1 if row["sentiment"] == "Positive" else 0,
                )
                for _, row in group.iterrows()
            ]
            if not reports:
                continue
            day = str(ts.date())
            provisional.append(
                {
                    "day": day,
                    "symbol": symbol,
                    "reports": reports,
                    "truth": int(truth),
                    "n_sites": int(group["site"].nunique()),
                }
            )
            day_set.append(day)

        days = sorted(set(day_set))
        day_index = {day: i for i, day in enumerate(days)}
        cut = int(round(CONTACT_FRACTION * len(days)))
        cut = min(max(cut, 1), len(days) - 1) if len(days) > 1 else 0
        contact_days = set(days[:cut])
        previous_truth: dict[str, int] = {}
        events = []
        for row in sorted(provisional, key=lambda value: (value["day"], value["symbol"])):
            symbol = row["symbol"]
            day = row["day"]
            item = self.item_ids[symbol]
            events.append(
                DecisionEvent(
                    t=day_index[day],
                    day=day,
                    symbol=symbol,
                    item=item,
                    key=(item, 0),
                    reports=row["reports"],
                    truth=row["truth"],
                    prev_truth=previous_truth.get(symbol),
                    split="contact" if day in contact_days else "holdout",
                    n_sites=row["n_sites"],
                )
            )
            previous_truth[symbol] = row["truth"]
        return events

    def summary(self) -> dict:
        summary = super().summary()
        summary.update(
            {
                "semantic_context": "causal_title_jaccard_novelty",
                "novelty_threshold": self.novelty_threshold,
                "history_size": self.history_size,
                "novel_report_fraction": float(
                    self.news_with_context["_context"].mean()
                    if hasattr(self, "news_with_context")
                    else 0.0
                ),
            }
        )
        return summary
