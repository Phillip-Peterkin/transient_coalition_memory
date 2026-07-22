"""Fifth fresh company universe for diagnostic-contrast confirmation.

Disjoint from `universe.UNIVERSE` and confirmation universes 1–4. Selected
before scoring from curated liquid names with at least 35 in-window
sentiment-labelled news rows. No price outcomes, model scores, or flip rates
were inspected during selection. Ambiguous headline-token tickers excluded.

`GPS` and `SQ` were removed before any confirmation scoring because Yahoo no
longer serves historical closes under those symbols in this window (ticker
moves); replaced with unused `AFRM` and `CHWY` from the same coverage pool.
"""

CONFIRMATION5_UNIVERSE = [
    "AFRM", "BNTX", "CCL", "CHWY", "DDOG", "DKNG", "DOCU", "INTU", "JD", "LCID",
    "MAS", "MELI", "NCLH", "NDAQ", "OKTA", "PDD", "PG", "PINS", "RACE", "RCL",
    "ROKU", "SNOW", "SPOT", "STZ", "TMUS", "TOL", "ULTA", "UPST", "WTW", "XPEV",
]
