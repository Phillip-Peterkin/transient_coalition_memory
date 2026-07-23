"""Fixed equity universe for finance/news real-data v0.

Symbols that collide with common headline tokens (EPS, ESG, CEO, …) are
intentionally excluded. This list is frozen for protocol v0.
"""

UNIVERSE = [
    "AAPL", "MSFT", "AMZN", "NVDA", "META", "TSLA", "GOOGL", "AMD", "NFLX", "DIS",
    "BA", "JPM", "BAC", "WMT", "XOM", "CVX", "PFE", "JNJ", "V", "MA",
    "COST", "PEP", "KO", "INTC", "CSCO", "ORCL", "CRM", "ADBE", "NIO", "BABA",
    "COIN", "UBER", "PYPL", "SHOP", "SNAP", "VZ", "IBM", "GE", "F", "GM",
]

NEWS_DATASET = "NickyNicky/finance-financialmodelingprep-stock-news-sentiments-rss-feed"
PRICE_START = "2022-08-01"
PRICE_END = "2023-10-20"
CONTACT_FRACTION = 0.70
