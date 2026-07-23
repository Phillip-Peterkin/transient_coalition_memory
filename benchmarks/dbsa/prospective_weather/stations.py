"""Immutable prospective Weather station roster (disjoint from spent beds)."""

from __future__ import annotations

# Spent symbols (must never reappear here):
# contact: NYC CHI DEN SEA LON BER TOK SYD SAO JNB DEL CAI
# confirmation2: LAX MIA TOR PAR MAD ROM SEL BKK MEX AKL IST RUH
# confirmation3: HOU PHX VAN AMS ATH WAW BCN SIN HKG BOG CPT MEL

STATIONS: list[tuple[str, float, float, str]] = [
    ("ATL", 33.7490, -84.3880, "Atlanta"),
    ("PHL", 39.9526, -75.1652, "Philadelphia"),
    ("MSP", 44.9778, -93.2650, "Minneapolis"),
    ("MUC", 48.1351, 11.5820, "Munich"),
    ("LIS", 38.7223, -9.1393, "Lisbon"),
    ("HEL", 60.1699, 24.9384, "Helsinki"),
    ("TPE", 25.0330, 121.5654, "Taipei"),
    ("KUL", 3.1390, 101.6869, "Kuala Lumpur"),
    ("LIM", -12.0464, -77.0428, "Lima"),
    ("NBO", -1.2921, 36.8219, "Nairobi"),
    ("PER", -31.9505, 115.8605, "Perth"),
    ("DXB", 25.2048, 55.2708, "Dubai"),
]

MODELS: list[str] = [
    "gfs_seamless",
    "ecmwf_ifs025",
    "icon_seamless",
    "gem_seamless",
    "meteofrance_seamless",
    "jma_seamless",
]

SPENT_SYMBOLS = {
    "NYC",
    "CHI",
    "DEN",
    "SEA",
    "LON",
    "BER",
    "TOK",
    "SYD",
    "SAO",
    "JNB",
    "DEL",
    "CAI",
    "LAX",
    "MIA",
    "TOR",
    "PAR",
    "MAD",
    "ROM",
    "SEL",
    "BKK",
    "MEX",
    "AKL",
    "IST",
    "RUH",
    "HOU",
    "PHX",
    "VAN",
    "AMS",
    "ATH",
    "WAW",
    "BCN",
    "SIN",
    "HKG",
    "BOG",
    "CPT",
    "MEL",
}


def assert_disjoint() -> None:
    symbols = {symbol for symbol, *_ in STATIONS}
    overlap = symbols & SPENT_SYMBOLS
    if overlap:
        raise RuntimeError(f"prospective stations overlap spent beds: {sorted(overlap)}")
