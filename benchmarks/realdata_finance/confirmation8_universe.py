"""Eighth fresh company universe for Active Coalition Inference confirmation.

Disjoint from `universe.UNIVERSE` and confirmation universes 1–7. Selected
before scoring from curated names with usable in-window news coverage and
validated Yahoo price history. No price outcomes, model scores, or flip rates
were inspected during selection.

Coverage note: after seven prior confirmation universes, remaining liquid
names with ≥35 news rows are scarce; this set allows ≥25 labelled rows when
price history is complete.
"""

CONFIRMATION8_UNIVERSE = [
    "ALVO", "ASH", "CGC", "CHPT", "CHTR", "CLLS", "CRSP", "CVNA", "EDIT", "FCF",
    "FMCC", "GFS", "GRRR", "IBN", "INGR", "LECO", "NOK", "OTCM", "PH", "PLUG",
    "PSA", "RH", "RXT", "SITC", "SLB", "SUI", "TLRY", "VEON", "WKEY", "WMS",
]
