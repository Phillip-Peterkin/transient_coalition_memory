"""A transparent sensory-relevance gate for financial news.

The feed often attaches an equity symbol to articles whose title is plainly
about another company or a broad news item.  A human does not treat a coal,
Ukraine, or meme-stock headline as direct sensory evidence about Apple simply
because a data feed placed it in Apple's bucket.

This stream keeps every `(company, day)` decision but passes an article to TCM
only when its title explicitly mentions that company or a stable company name.
An empty relevant-report set is still a decision: TCM receives no new sensory
evidence and must rely on its existing state rather than fabricated support.
"""

from __future__ import annotations

import re

import pandas as pd

from tcm import SensoryGatedCellular
from stream import DecisionEvent, FinanceNewsStream
from universe import CONTACT_FRACTION

# Names intentionally favor precision over recall.  Broad sector stories may
# matter in a later model, but this first test asks a narrow question: does
# blocking obvious misattribution help?
COMPANY_PATTERNS = {
    "AAPL": (r"\bapple\b",),
    "ADBE": (r"\badobe\b",),
    "AMAT": (r"\bapplied materials\b",),
    "AMD": (r"\bamd\b", r"\badvanced micro devices\b"),
    "AMT": (r"\bamerican tower\b",),
    "AMZN": (r"\bamazon\b",),
    "APA": (r"\bapa corporation\b", r"\bapa corp\b"),
    "AVGO": (r"\bbroadcom\b",),
    "AZO": (r"\bautozone\b",),
    "BA": (r"\bboeing\b",),
    "BABA": (r"\balibaba\b",),
    "BAC": (r"\bbank of america\b",),
    "BIIB": (r"\bbiogen\b",),
    "BMY": (r"\bbristol[- ]myers\b",),
    "BKNG": (r"\bbooking holdings\b", r"\bbooking\.com\b"),
    "CCI": (r"\bcrown castle\b",),
    "CI": (r"\bcigna\b",),
    "CMG": (r"\bchipotle\b",),
    "COIN": (r"\bcoinbase\b",),
    "COST": (r"\bcostco\b",),
    "CRM": (r"\bsalesforce\b",),
    "CRWD": (r"\bcrowdstrike\b",),
    "CSCO": (r"\bcisco\b",),
    "CSX": (r"\bcsx\b",),
    "CVX": (r"\bchevron\b",),
    "DAL": (r"\bdelta air\b", r"\bdelta airlines\b"),
    "DE": (r"\bjohn deere\b", r"\bdeere\b"),
    "DG": (r"\bdollar general\b",),
    "DIS": (r"\bdisney\b",),
    "DVN": (r"\bdevon energy\b",),
    "EA": (r"\belectronic arts\b",),
    "ED": (r"\bconsolidated edison\b", r"\bcon edison\b"),
    "EFX": (r"\bequifax\b",),
    "EL": (r"\best[eé]e lauder\b",),
    "ENPH": (r"\benphase\b",),
    "FCX": (r"\bfreeport[- ]mcmoran\b",),
    "FSLR": (r"\bfirst solar\b",),
    "FTNT": (r"\bfortinet\b",),
    "GE": (r"\bgeneral electric\b",),
    "GM": (r"\bgeneral motors\b",),
    "GOOGL": (r"\bgoogle\b", r"\balphabet\b"),
    "GS": (r"\bgoldman sachs\b", r"\bgoldman\b"),
    "HUM": (r"\bhumana\b",),
    "IBM": (r"\bibm\b",),
    "INTC": (r"\bintel\b",),
    "IP": (r"\binternational paper\b",),
    "ISRG": (r"\bintuitive surgical\b",),
    "JNJ": (r"\bjohnson\s*&\s*johnson\b", r"\bj&j\b"),
    "JPM": (r"\bjpmorgan\b", r"\bj\.p\. morgan\b"),
    "KO": (r"\bcoca[- ]cola\b",),
    "KR": (r"\bkroger\b",),
    "LIN": (r"\blinde\b",),
    "LUV": (r"\bsouthwest airlines\b", r"\bsouthwest\b"),
    "MA": (r"\bmastercard\b",),
    "MAR": (r"\bmarriott\b",),
    "MCK": (r"\bmckesson\b",),
    "META": (r"\bmeta platforms\b", r"\bfacebook\b", r"\binstagram\b", r"\bwhatsapp\b"),
    "MPC": (r"\bmarathon petroleum\b",),
    "MS": (r"\bmorgan stanley\b",),
    "MSFT": (r"\bmicrosoft\b",),
    "MU": (r"\bmicron\b",),
    "NEE": (r"\bnextera\b",),
    "NEM": (r"\bnewmont\b",),
    "NET": (r"\bcloudflare\b",),
    "NFLX": (r"\bnetflix\b",),
    "NIO": (r"\bnio\b",),
    "NOC": (r"\bnorthrop\b",),
    "NOW": (r"\bservicenow\b", r"\bservice now\b"),
    "NVDA": (r"\bnvidia\b",),
    "NXPI": (r"\bnxp\b",),
    "NSC": (r"\bnorfolk southern\b",),
    "ORCL": (r"\boracle\b",),
    "OXY": (r"\boccidental\b",),
    "PANW": (r"\bpalo alto networks\b", r"\bpalo alto\b"),
    "PARA": (r"\bparamount\b",),
    "PEP": (r"\bpepsico\b", r"\bpepsi\b"),
    "PFE": (r"\bpfizer\b",),
    "PYPL": (r"\bpaypal\b",),
    "QCOM": (r"\bqualcomm\b",),
    "REGN": (r"\bregeneron\b",),
    "RF": (r"\bregions financial\b", r"\bregions bank\b"),
    "RMD": (r"\bresmed\b",),
    "ROP": (r"\broper technologies\b", r"\broper\b"),
    "SEDG": (r"\bsolaredge\b",),
    "SHOP": (r"\bshopify\b",),
    "SNAP": (r"\bsnapchat\b",),
    "STX": (r"\bseagate\b",),
    "TER": (r"\bteradyne\b",),
    "TFX": (r"\bteleflex\b",),
    "TSLA": (r"\btesla\b",),
    "TSN": (r"\btyson\b",),
    "TTWO": (r"\btake[- ]two\b",),
    "TXN": (r"\btexas instruments\b",),
    "UBER": (r"\buber\b",),
    "UPS": (r"\bunited parcel\b", r"\bups\b"),
    "VZ": (r"\bverizon\b",),
    "VRSK": (r"\bverisk\b",),
    "VRTX": (r"\bvertex pharmaceuticals\b", r"\bvertex\b"),
    "WBD": (r"\bwarner bros\b", r"\bwarner brothers\b"),
    "WMT": (r"\bwalmart\b",),
    "XOM": (r"\bexxon\b",),
    "ZS": (r"\bzscaler\b",),
}


def is_relevant(title: str, symbol: str) -> bool:
    patterns = COMPANY_PATTERNS.get(symbol, (rf"\b{re.escape(symbol.lower())}\b",))
    text = title.lower()
    return any(re.search(pattern, text) is not None for pattern in patterns)


class RelevanceFinanceNewsStream(FinanceNewsStream):
    """Finance stream that retains every event but filters irrelevant reports."""

    def __init__(self, *args, **kwargs):
        self.total_articles = 0
        self.relevant_articles = 0
        self.events_without_relevant_reports = 0
        super().__init__(*args, **kwargs)

    def _build_events(self) -> list[DecisionEvent]:
        if "title" not in self.news.columns:
            raise ValueError("Relevance stream needs titles; rerun download_data.py --force")
        day_set = []
        provisional = []
        for (symbol, date_str), group in self.news.groupby(["symbol", "date"], sort=True):
            if symbol not in self.truth.columns:
                continue
            ts = self._align_trading_day(date_str)
            if ts is None:
                continue
            truth = self.truth.at[ts, symbol]
            if pd.isna(truth):
                continue

            self.total_articles += len(group)
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

            day = str(ts.date())
            provisional.append(
                {
                    "day": day,
                    "symbol": symbol,
                    "reports": reports,
                    "truth": int(truth),
                    "n_sites": int(relevant["site"].nunique()),
                }
            )
            day_set.append(day)

        days = sorted(set(day_set))
        day_index = {day: index for index, day in enumerate(days)}
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
                "sensory_gate": "explicit_company_mention_in_title",
                "relevant_article_fraction": self.relevant_articles / max(1, self.total_articles),
                "events_without_relevant_reports": self.events_without_relevant_reports,
            }
        )
        return summary


class RelevanceGatedCellular(SensoryGatedCellular):
    """Backward-compatible benchmark name for the active experimental model."""

    name = "relevance_gated_cellular"
