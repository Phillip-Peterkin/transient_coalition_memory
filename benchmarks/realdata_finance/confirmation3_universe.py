"""Third fresh company universe for skew-correction confirmation.

Disjoint from `universe.UNIVERSE`, `confirmation_universe`, and
`confirmation2_universe`. Selected before scoring from curated liquid US
equities with at least 35 in-window sentiment-labelled news rows. No price
outcomes, model scores, or flip rates were inspected during selection.
"""

CONFIRMATION3_UNIVERSE = [
    "AMAT", "APA", "AZO", "BIIB", "CMG", "CRWD", "DAL", "DE", "DVN", "EL",
    "ENPH", "FSLR", "FTNT", "GS", "ISRG", "MAR", "MS", "MU", "NET", "NOC",
    "NOW", "NXPI", "OXY", "PANW", "QCOM", "RMD", "SEDG", "TXN", "UPS", "ZS",
]
