#!/usr/bin/env python3
"""Download virgin confirmation2 Weather cities (no scoring)."""

from __future__ import annotations

from pathlib import Path

from confirmation2_universe import CITIES
from download_data import download_universe

ROOT = Path(__file__).resolve().parent


def main() -> None:
    download_universe(
        CITIES,
        ROOT / "data_confirmation2",
        universe="confirmation2",
    )


if __name__ == "__main__":
    main()
