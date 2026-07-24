"""Seventh fresh company universe for diagnostic-contrast v2 confirmation.

Disjoint from `universe.UNIVERSE` and confirmation universes 1–6. Selected
before scoring from curated liquid names with at least 35 in-window
sentiment-labelled news rows. No price outcomes, model scores, or flip rates
were inspected during selection.

confirmation6 is spent: its first download included delisted `MRO`/`PXD`
tickers with null prices, and a score was accidentally observed on that
invalid panel. This universe replaces those names with `DOCN` and `TWST`
and is the sealed virgin look for v2.
"""

CONFIRMATION7_UNIVERSE = [
    "AAP", "AMT", "ANET", "BBY", "BKR", "BKNG", "CHKP", "CRL", "DOCN", "DPZ",
    "DRI", "ESS", "ETSY", "KMX", "LEN", "LIN", "LRCX", "LYV", "MAA", "MPWR",
    "PATH", "QSR", "RIO", "SMCI", "SRE", "TTD", "TWLO", "TWST", "UNP", "XPO",
]
