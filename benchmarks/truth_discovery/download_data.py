#!/usr/bin/env python3
"""Download Luna Dong Stock + Weather fusion datasets (no scoring)."""

from __future__ import annotations

import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
BASE = "https://lunadong.com/datasets"
FILES = {
    "clean_stock.zip": f"{BASE}/clean_stock.zip",
    "nasdaq_truth.zip": f"{BASE}/nasdaq_truth.zip",
    "weather.zip": f"{BASE}/weather.zip",
}
USER_AGENT = "transient-coalition-memory-td/0.1 (research)"


def _fetch(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 1000:
        print("have", dest)
        return
    print("fetch", url)
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=180) as response, dest.open("wb") as out:
        out.write(response.read())
    print("wrote", dest, dest.stat().st_size)


def _unzip(path: Path, dest: Path) -> None:
    print("unzip", path.name)
    with zipfile.ZipFile(path) as zf:
        zf.extractall(dest)
    # weather zip extracts txt into DATA root; stock into subdirs


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    for name, url in FILES.items():
        zip_path = DATA / name
        _fetch(url, zip_path)
        _unzip(zip_path, DATA)
    print("done — run prepare_slim.py next")


if __name__ == "__main__":
    main()
