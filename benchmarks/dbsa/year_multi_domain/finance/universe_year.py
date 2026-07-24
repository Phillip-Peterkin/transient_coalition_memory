"""Virgin finance universe for year_multi_domain (locked before scoring).

Disjoint from:
- benchmarks/realdata_finance/universe.py (v0)
- confirmation1–8 universes

Selected as liquid US names without inspecting year-window labels or model
scores for this bed.
"""

YEAR_FINANCE_UNIVERSE = [
    "ADP", "AEP", "AFL", "AJG", "ALL", "AMP", "APD", "APH", "AON", "ADI",
    "BALL", "BDX", "BEN", "BR", "BSX", "BX", "CB", "CDNS", "CEG", "CHD",
    "CI", "CME", "CNC", "CNP", "CPRT", "CTAS", "CTVA", "D", "DHI", "DLR",
    "DOW", "ECL", "EOG", "EQIX", "ETN", "EW", "EXC", "FANG", "FAST", "FIS",
]

# Inside the HF finance-news corpus span (PROTOCOL.md).
YEAR_FINANCE_START = "2022-08-15"
YEAR_FINANCE_END = "2023-08-14"
NEWS_DATASET = "NickyNicky/finance-financialmodelingprep-stock-news-sentiments-rss-feed"
