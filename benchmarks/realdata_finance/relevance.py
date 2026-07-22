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
    "AA": (r"\balcoa\b",),
    "AAL": (r"\bamerican airlines\b",),
    "AAP": (r"\badvance auto\b",),
    "AAPL": (r"\bapple\b",),
    "ADBE": (r"\badobe\b",),
    "AFRM": (r"\baffirm\b",),
    "ALB": (r"\balbemarle\b",),
    "AMAT": (r"\bapplied materials\b",),
    "AMD": (r"\bamd\b", r"\badvanced micro devices\b"),
    "AMT": (r"\bamerican tower\b",),
    "AMZN": (r"\bamazon\b",),
    "ANET": (r"\barista networks\b", r"\barista\b"),
    "APA": (r"\bapa corporation\b", r"\bapa corp\b"),
    "ASML": (r"\basml\b",),
    "AVGO": (r"\bbroadcom\b",),
    "AZO": (r"\bautozone\b",),
    "BA": (r"\bboeing\b",),
    "BABA": (r"\balibaba\b",),
    "BAC": (r"\bbank of america\b",),
    "BBY": (r"\bbest buy\b",),
    "BIDU": (r"\bbaidu\b",),
    "BIIB": (r"\bbiogen\b",),
    "BKR": (r"\bbaker hughes\b",),
    "BMY": (r"\bbristol[- ]myers\b",),
    "BKNG": (r"\bbooking holdings\b", r"\bbooking\.com\b"),
    "BNTX": (r"\bbiontech\b",),
    "CBOE": (r"\bcboe\b", r"\bchicago board options\b"),
    "CCI": (r"\bcrown castle\b",),
    "CCL": (r"\bcarnival\b",),
    "CHKP": (r"\bcheck point\b", r"\bcheckpoint software\b"),
    "CHPT": (r"\bchargepoint\b",),
    "CHTR": (r"\bcharter communications\b", r"\bspectrum\b"),
    "CHWY": (r"\bchewy\b",),
    "CGC": (r"\bcanopy growth\b",),
    "CLLS": (r"\bcellectis\b",),
    "CRSP": (r"\bcrispr therapeutics\b", r"\bcrispr\b"),
    "CVNA": (r"\bcarvana\b",),
    "CI": (r"\bcigna\b",),
    "CMG": (r"\bchipotle\b",),
    "CNI": (r"\bcanadian national\b", r"\bcn railway\b", r"\bcn rail\b"),
    "COIN": (r"\bcoinbase\b",),
    "COO": (r"\bcooper companies\b", r"\bcoopercompany\b"),
    "COST": (r"\bcostco\b",),
    "CRL": (r"\bcharles river\b",),
    "CRM": (r"\bsalesforce\b",),
    "CRWD": (r"\bcrowdstrike\b",),
    "CSCO": (r"\bcisco\b",),
    "CSX": (r"\bcsx\b",),
    "CVX": (r"\bchevron\b",),
    "DAL": (r"\bdelta air\b", r"\bdelta airlines\b"),
    "DE": (r"\bjohn deere\b", r"\bdeere\b"),
    "DFS": (r"\bdiscover financial\b", r"\bdiscover\b"),
    "DDOG": (r"\bdatadog\b",),
    "DG": (r"\bdollar general\b",),
    "DIS": (r"\bdisney\b",),
    "DKNG": (r"\bdraftkings\b",),
    "DOCN": (r"\bdigitalocean\b",),
    "DOCU": (r"\bdocusign\b",),
    "DPZ": (r"\bdomino'?s\b", r"\bdominos\b"),
    "DRI": (r"\bdarden\b", r"\bolive garden\b"),
    "DVN": (r"\bdevon energy\b",),
    "EA": (r"\belectronic arts\b",),
    "ED": (r"\bconsolidated edison\b", r"\bcon edison\b"),
    "EDIT": (r"\beditas\b",),
    "EFX": (r"\bequifax\b",),
    "EL": (r"\best[eé]e lauder\b",),
    "ENPH": (r"\benphase\b",),
    "ESS": (r"\bessex property\b",),
    "ET": (r"\benergy transfer\b",),
    "ETSY": (r"\betsy\b",),
    "FCX": (r"\bfreeport[- ]mcmoran\b",),
    "FSLR": (r"\bfirst solar\b",),
    "FTNT": (r"\bfortinet\b",),
    "GE": (r"\bgeneral electric\b",),
    "GFS": (r"\bglobalfoundries\b", r"\bglobal foundries\b"),
    "GM": (r"\bgeneral motors\b",),
    "GRRR": (r"\bgorilla technology\b", r"\bgorilla\b"),
    "GOOGL": (r"\bgoogle\b", r"\balphabet\b"),
    "GPS": (r"\bthe gap\b", r"\bgap inc\b", r"\bold navy\b", r"\bbanana republic\b"),
    "GS": (r"\bgoldman sachs\b", r"\bgoldman\b"),
    "HII": (r"\bhuntington ingalls\b",),
    "HOOD": (r"\brobinhood\b",),
    "HPQ": (r"\bhewlett[- ]packard\b", r"\bhp inc\b", r"\bhp's\b"),
    "HUM": (r"\bhumana\b",),
    "IBN": (r"\bicici\b",),
    "IBM": (r"\bibm\b",),
    "INGR": (r"\bingredion\b",),
    "INTC": (r"\bintel\b",),
    "INTU": (r"\bintuit\b",),
    "IP": (r"\binternational paper\b",),
    "ISRG": (r"\bintuitive surgical\b",),
    "JD": (r"\bjd\.com\b", r"\bjingdong\b"),
    "JNJ": (r"\bjohnson\s*&\s*johnson\b", r"\bj&j\b"),
    "JPM": (r"\bjpmorgan\b", r"\bj\.p\. morgan\b"),
    "KMX": (r"\bcarmax\b",),
    "KO": (r"\bcoca[- ]cola\b",),
    "KR": (r"\bkroger\b",),
    "LCID": (r"\blucid\b",),
    "LECO": (r"\blincoln electric\b",),
    "LEN": (r"\blennar\b",),
    "LIN": (r"\blinde\b",),
    "LLY": (r"\beli lilly\b", r"\blilly\b"),
    "LNG": (r"\bcheniere\b",),
    "LPLA": (r"\blpl financial\b",),
    "LRCX": (r"\blam research\b",),
    "LULU": (r"\blululemon\b",),
    "LUV": (r"\bsouthwest airlines\b", r"\bsouthwest\b"),
    "LYV": (r"\blive nation\b",),
    "MA": (r"\bmastercard\b",),
    "MAA": (r"\bmid[- ]america apartment\b", r"\bmaa\b"),
    "MAR": (r"\bmarriott\b",),
    "MAS": (r"\bmasco\b",),
    "MCK": (r"\bmckesson\b",),
    "MELI": (r"\bmercadolibre\b", r"\bmercado libre\b"),
    "META": (r"\bmeta platforms\b", r"\bfacebook\b", r"\binstagram\b", r"\bwhatsapp\b"),
    "MPC": (r"\bmarathon petroleum\b",),
    "MPWR": (r"\bmonolithic power\b",),
    "MRNA": (r"\bmoderna\b",),
    "MRO": (r"\bmarathon oil\b",),
    "MS": (r"\bmorgan stanley\b",),
    "MSFT": (r"\bmicrosoft\b",),
    "MU": (r"\bmicron\b",),
    "NCLH": (r"\bnorwegian cruise\b",),
    "NDAQ": (r"\bnasdaq\b",),
    "NEE": (r"\bnextera\b",),
    "NEM": (r"\bnewmont\b",),
    "NET": (r"\bcloudflare\b",),
    "NFLX": (r"\bnetflix\b",),
    "NIO": (r"\bnio\b",),
    "NOC": (r"\bnorthrop\b",),
    "NOW": (r"\bservicenow\b", r"\bservice now\b"),
    "NVO": (r"\bnovo nordisk\b",),
    "NVDA": (r"\bnvidia\b",),
    "NXPI": (r"\bnxp\b",),
    "NSC": (r"\bnorfolk southern\b",),
    "OKTA": (r"\bokta\b",),
    "ORCL": (r"\boracle\b",),
    "OXY": (r"\boccidental\b",),
    "PANW": (r"\bpalo alto networks\b", r"\bpalo alto\b"),
    "PARA": (r"\bparamount\b",),
    "PATH": (r"\buipath\b",),
    "NOK": (r"\bnokia\b",),
    "OTCM": (r"\botc markets\b",),
    "PDD": (r"\bpdd holdings\b", r"\bpinduoduo\b", r"\btemu\b"),
    "PEP": (r"\bpepsico\b", r"\bpepsi\b"),
    "PFE": (r"\bpfizer\b",),
    "PG": (r"\bprocter\s*&\s*gamble\b", r"\bp&g\b"),
    "PH": (r"\bparker[- ]hannifin\b",),
    "PINS": (r"\bpinterest\b",),
    "PLD": (r"\bprologis\b",),
    "PLTR": (r"\bpalantir\b",),
    "PLUG": (r"\bplug power\b",),
    "PSA": (r"\bpublic storage\b",),
    "PTON": (r"\bpeloton\b",),
    "PXD": (r"\bpioneer natural\b", r"\bpioneer\b"),
    "PYPL": (r"\bpaypal\b",),
    "QCOM": (r"\bqualcomm\b",),
    "QSR": (r"\brestaurant brands\b", r"\bburger king\b", r"\btim hortons\b", r"\bpopeyes\b"),
    "RACE": (r"\bferrari\b",),
    "RBLX": (r"\broblox\b",),
    "RCL": (r"\broyal caribbean\b",),
    "REGN": (r"\bregeneron\b",),
    "RF": (r"\bregions financial\b", r"\bregions bank\b"),
    "RH": (r"\brh\b", r"\brestoration hardware\b"),
    "RIO": (r"\brio tinto\b",),
    "RIVN": (r"\brivian\b",),
    "RMD": (r"\bresmed\b",),
    "ROKU": (r"\broku\b",),
    "ROP": (r"\broper technologies\b", r"\broper\b"),
    "RXT": (r"\brackspace\b",),
    "SEDG": (r"\bsolaredge\b",),
    "SHOP": (r"\bshopify\b",),
    "SITC": (r"\bsite centers\b",),
    "SLB": (r"\bschlumberger\b", r"\bslb\b"),
    "SMCI": (r"\bsuper micro\b", r"\bsupermicro\b"),
    "SNAP": (r"\bsnapchat\b",),
    "SNOW": (r"\bsnowflake\b",),
    "SOFI": (r"\bsofi\b",),
    "SPOT": (r"\bspotify\b",),
    "SQ": (r"\bcash app\b", r"\bsquare, inc\b", r"\bblock, inc\b", r"\bsquare\b"),
    "SRE": (r"\bsempra\b",),
    "STLA": (r"\bstellantis\b",),
    "STX": (r"\bseagate\b",),
    "STZ": (r"\bconstellation brands\b",),
    "SUI": (r"\bsun communities\b",),
    "TER": (r"\bteradyne\b",),
    "TFX": (r"\bteleflex\b",),
    "TLRY": (r"\btilray\b",),
    "TM": (r"\btoyota\b",),
    "TMUS": (r"\bt[- ]mobile\b",),
    "TOL": (r"\btoll brothers\b",),
    "TSLA": (r"\btesla\b",),
    "TSN": (r"\btyson\b",),
    "TSM": (r"\btaiwan semiconductor\b", r"\btsmc\b"),
    "TTD": (r"\bthe trade desk\b", r"\btrade desk\b"),
    "TTWO": (r"\btake[- ]two\b",),
    "TWLO": (r"\btwilio\b",),
    "TWST": (r"\btwist bioscience\b", r"\btwist bio\b"),
    "TXN": (r"\btexas instruments\b",),
    "UAL": (r"\bunited airlines\b",),
    "UBER": (r"\buber\b",),
    "ULTA": (r"\bulta\b",),
    "UNP": (r"\bunion pacific\b",),
    "UPS": (r"\bunited parcel\b", r"\bups\b"),
    "UPST": (r"\bupstart\b",),
    "VEON": (r"\bveon\b",),
    "VZ": (r"\bverizon\b",),
    "VRSK": (r"\bverisk\b",),
    "VRTX": (r"\bvertex pharmaceuticals\b", r"\bvertex\b"),
    "WBD": (r"\bwarner bros\b", r"\bwarner brothers\b"),
    "WFC": (r"\bwells fargo\b",),
    "WKEY": (r"\bwiskey\b",),
    "WMS": (r"\badvanced drainage\b",),
    "WMT": (r"\bwalmart\b",),
    "WTW": (r"\bwillis towers\b", r"\bwtw\b"),
    "XOM": (r"\bexxon\b",),
    "XPEV": (r"\bxpeng\b",),
    "XPO": (r"\bxpo logistics\b", r"\bxpo\b"),
    "ZM": (r"\bzoom video\b", r"\bzoom\b"),
    "ZS": (r"\bzscaler\b",),
    "ASH": (r"\bashland\b",),
    "ALVO": (r"\balvotech\b",),
    "FMCC": (r"\bfreddie mac\b",),
    "FCF": (r"\bfirst commonwealth\b",),
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
