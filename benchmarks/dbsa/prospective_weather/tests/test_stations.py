from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from stations import SPENT_SYMBOLS, STATIONS, assert_disjoint


def test_prospective_stations_are_disjoint_from_spent_beds():
    assert_disjoint()
    symbols = {symbol for symbol, *_ in STATIONS}
    assert not (symbols & SPENT_SYMBOLS)
    assert len(symbols) == 12
