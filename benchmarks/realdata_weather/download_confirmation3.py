#!/usr/bin/env python3
"""Download virgin confirmation3 Weather cities (no scoring)."""

from __future__ import annotations

from pathlib import Path

from confirmation3_universe import CITIES
from download_data import download_universe

ROOT = Path(__file__).resolve().parent


def main() -> None:
    download_universe(
        CITIES,
        ROOT / "data_confirmation3",
        universe="confirmation3",
    )


if __name__ == "__main__":
    main()
