"""Sixth fresh company universe for diagnostic-contrast v2 confirmation.

Disjoint from `universe.UNIVERSE` and confirmation universes 1–5. Selected
before scoring from curated liquid names with at least 35 in-window
sentiment-labelled news rows. No price outcomes, model scores, or flip rates
were inspected during selection. Ambiguous headline-token tickers excluded.

`MRO` and `PXD` were removed before any confirmation scoring because Yahoo no
longer serves historical closes under those symbols in this window (corporate
actions); replaced with unused `DOCN` and `TWST` from the same coverage pool.
"""

CONFIRMATION6_UNIVERSE = [
    "AAP", "AMT", "ANET", "BBY", "BKR", "BKNG", "CHKP", "CRL", "DOCN", "DPZ",
    "DRI", "ESS", "ETSY", "KMX", "LEN", "LIN", "LRCX", "LYV", "MAA", "MPWR",
    "PATH", "QSR", "RIO", "SMCI", "SRE", "TTD", "TWLO", "TWST", "UNP", "XPO",
]
