"""Session-honest finance/news stream.

Fixes the timing and flip impurities in the calendar-date stream:

1. Each article is assigned to exactly one trading session by published time,
   using a 16:00 America/New_York close cutoff.
2. There is at most one decision per `(symbol, session)`.
3. Flip labels compare adjacent trading sessions in the price calendar, not
   the previous news-bearing event (which can skip days or collide).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from relevance import COMPANY_PATTERNS, is_relevant
from stream import DecisionEvent, FinanceNewsStream
from universe import CONTACT_FRACTION

SESSION_TZ = "America/New_York"
SESSION_CLOSE_HOUR = 16
SESSION_CLOSE_MINUTE = 0


@dataclass
class SessionDecisionEvent(DecisionEvent):
    """Decision event with session-purity markers."""

    n_raw_articles: int = 0
    n_relevant_articles: int = 0
    adjacent_session: bool = False
    trading_gap: int | None = None


def session_close_utc(session_day: pd.Timestamp) -> pd.Timestamp:
    """Return the exchange close timestamp for a trading calendar day."""
    day = pd.Timestamp(session_day).tz_localize(None).normalize()
    local = day.tz_localize(SESSION_TZ).replace(
        hour=SESSION_CLOSE_HOUR,
        minute=SESSION_CLOSE_MINUTE,
        second=0,
        microsecond=0,
    )
    return local.tz_convert("UTC")


def assign_sessions(
    published: pd.Series,
    trading_days: pd.DatetimeIndex,
) -> pd.Series:
    """Map each publish timestamp to the first session whose close is >= it."""
    closes = pd.DatetimeIndex([session_close_utc(day) for day in trading_days])
    published_utc = pd.to_datetime(published, utc=True, errors="coerce")
    positions = closes.searchsorted(published_utc, side="left")
    assigned = pd.Series(pd.NaT, index=published.index, dtype="datetime64[ns]")
    valid = positions < len(trading_days)
    assigned.loc[valid] = trading_days[positions[valid]].tz_localize(None)
    return assigned


class SessionRelevanceFinanceNewsStream(FinanceNewsStream):
    """Relevance-gated stream with session cutoffs and adjacent-session flips."""

    def __init__(self, *args, require_relevant: bool = False, **kwargs):
        self.require_relevant = bool(require_relevant)
        self.total_articles = 0
        self.assigned_articles = 0
        self.relevant_articles = 0
        self.events_without_relevant_reports = 0
        self.dropped_unassigned_articles = 0
        super().__init__(*args, **kwargs)

    def _build_events(self) -> list[DecisionEvent]:
        if "title" not in self.news.columns or "published" not in self.news.columns:
            raise ValueError(
                "Session stream needs title/published columns; rerun download_data.py --force"
            )

        trading_days = pd.DatetimeIndex(self.close.index).tz_localize(None).normalize()
        news = self.news.copy()
        news["session"] = assign_sessions(news["published"], trading_days)
        self.total_articles = len(news)
        self.dropped_unassigned_articles = int(news["session"].isna().sum())
        news = news.dropna(subset=["session"]).copy()
        self.assigned_articles = len(news)
        news["session_day"] = pd.to_datetime(news["session"]).dt.strftime("%Y-%m-%d")

        day_set: list[str] = []
        provisional: list[dict] = []
        for (symbol, session_day), group in news.groupby(
            ["symbol", "session_day"], sort=True
        ):
            if symbol not in self.truth.columns:
                continue
            ts = pd.Timestamp(session_day)
            if ts not in self.truth.index:
                continue
            truth = self.truth.at[ts, symbol]
            if pd.isna(truth):
                continue

            relevant = group[group["title"].map(lambda title: is_relevant(title, symbol))]
            self.relevant_articles += len(relevant)
            reports = [
                (
                    self.source_ids[row["site"]],
                    0,
                    1 if row["sentiment"] == "Positive" else 0,
                )
                for _, row in relevant.iterrows()
            ]
            if not reports:
                self.events_without_relevant_reports += 1
                if self.require_relevant:
                    continue

            provisional.append(
                {
                    "day": session_day,
                    "symbol": symbol,
                    "reports": reports,
                    "truth": int(truth),
                    "n_sites": int(relevant["site"].nunique()) if len(relevant) else 0,
                    "n_raw_articles": int(len(group)),
                    "n_relevant_articles": int(len(relevant)),
                    "ts": ts,
                }
            )
            day_set.append(session_day)

        days = sorted(set(day_set))
        day_index = {day: index for index, day in enumerate(days)}
        cut = int(round(CONTACT_FRACTION * len(days)))
        cut = min(max(cut, 1), len(days) - 1) if len(days) > 1 else 0
        contact_days = set(days[:cut])

        trading_pos = {pd.Timestamp(day): i for i, day in enumerate(trading_days)}
        events: list[DecisionEvent] = []
        for row in sorted(provisional, key=lambda value: (value["day"], value["symbol"])):
            symbol = row["symbol"]
            day = row["day"]
            ts = row["ts"]
            item = self.item_ids[symbol]
            pos = trading_pos[ts]
            prev_truth = None
            trading_gap = None
            adjacent = False
            if pos > 0:
                prev_ts = trading_days[pos - 1]
                prev_val = self.truth.at[prev_ts, symbol]
                if not pd.isna(prev_val):
                    prev_truth = int(prev_val)
                    trading_gap = 1
                    adjacent = True
            events.append(
                SessionDecisionEvent(
                    t=day_index[day],
                    day=day,
                    symbol=symbol,
                    item=item,
                    key=(item, 0),
                    reports=row["reports"],
                    truth=row["truth"],
                    prev_truth=prev_truth,
                    split="contact" if day in contact_days else "holdout",
                    n_sites=row["n_sites"],
                    n_raw_articles=row["n_raw_articles"],
                    n_relevant_articles=row["n_relevant_articles"],
                    adjacent_session=adjacent,
                    trading_gap=trading_gap,
                )
            )
        return events

    def purity_markers(self) -> dict:
        """Stream-level markers for the dead-pixel audit."""
        keys = [(event.symbol, event.day) for event in self.events]
        duplicate_sessions = len(keys) - len(set(keys))
        gaps = []
        prev_pos: dict[str, int] = {}
        trading_days = list(pd.DatetimeIndex(self.close.index).normalize())
        trading_pos = {day: i for i, day in enumerate(trading_days)}
        for event in self.events:
            ts = pd.Timestamp(event.day)
            pos = trading_pos[ts]
            if event.symbol in prev_pos:
                gaps.append(pos - prev_pos[event.symbol])
            prev_pos[event.symbol] = pos
        gaps_arr = np.asarray(gaps, float) if gaps else np.asarray([], float)
        flip_events = [
            event
            for event in self.events
            if event.prev_truth is not None and event.truth != event.prev_truth
        ]
        return {
            "duplicate_symbol_session_events": int(duplicate_sessions),
            "news_event_gap_mean": float(gaps_arr.mean()) if len(gaps_arr) else float("nan"),
            "news_event_gap_frac_1": float((gaps_arr == 1).mean()) if len(gaps_arr) else float("nan"),
            "news_event_gap_frac_gt_1": float((gaps_arr > 1).mean()) if len(gaps_arr) else float("nan"),
            "flip_events_adjacent_session": int(
                sum(getattr(event, "adjacent_session", False) for event in flip_events)
            ),
            "flip_events": len(flip_events),
            "events_without_relevant_reports": self.events_without_relevant_reports,
            "relevant_article_fraction": self.relevant_articles
            / max(1, self.assigned_articles),
            "assigned_article_fraction": self.assigned_articles
            / max(1, self.total_articles),
            "dropped_unassigned_articles": self.dropped_unassigned_articles,
            "company_patterns": len(COMPANY_PATTERNS),
            "session_timezone": SESSION_TZ,
            "session_close": f"{SESSION_CLOSE_HOUR:02d}:{SESSION_CLOSE_MINUTE:02d}",
        }

    def summary(self) -> dict:
        summary = super().summary()
        summary.update(
            {
                "sensory_gate": "explicit_company_mention_in_title",
                "session_protocol": "close_cutoff_america_new_york",
                "flip_definition": "adjacent_trading_session",
            }
        )
        summary.update(self.purity_markers())
        return summary
