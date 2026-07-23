#!/usr/bin/env python3
"""Build slim scored claim/gold parquet tables from raw Luna Dong dumps."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
STOCK_DIR = DATA / "clean_stock"
GOLD_DIR = DATA / "nasdaq_truth"
OUT = DATA / "slim"

# clean_stock columns: source, symbol, change%, last, open, change$, volume,
# high, low, prev close, ...
STOCK_ATTRS = {
    2: "change_pct",
    3: "last_price",
    4: "open_price",
    9: "prev_close",
}

CITY_ALIASES = {
    "new york": "new_york",
    "nws new york, ny": "new_york",
    "boston": "boston",
    "nws taunton, ma": "boston",
    "philadelphia": "philadelphia",
    "nws philadelphia, pa": "philadelphia",
    "baltimore": "baltimore",
    "washington": "washington",
    "nws baltimore, md/washington, d.c.": "washington",
    "chicago": "chicago",
    "nws chicago, il": "chicago",
    "denver": "denver",
    "nws denver-boulder, co": "denver",
    "denver co": "denver",
    "indianapolis": "indianapolis",
    "indianapolis in": "indianapolis",
    "nws indianapolis, in": "indianapolis",
    "memphis": "memphis",
    "memphis tn": "memphis",
    "nashville": "nashville",
    "nashville tn": "nashville",
    "milwaukee": "milwaukee",
    "milwaukee wi": "milwaukee",
    "detroit": "detroit",
    "detroit mi": "detroit",
    "los angeles": "los_angeles",
    "san francisco": "san_francisco",
    "san diego": "san_diego",
    "san jose": "san_jose",
    "seattle": "seattle",
    "portland": "portland",
    "phoenix": "phoenix",
    "houston": "houston",
    "dallas": "dallas",
    "austin": "austin",
    "san antonio": "san_antonio",
    "fort worth": "fort_worth",
    "charlotte": "charlotte",
    "jacksonville": "jacksonville",
    "columbus": "columbus",
    "el paso": "el_paso",
    "oklahoma city": "oklahoma_city",
    "las vegas": "las_vegas",
}


def parse_number(raw: str):
    if raw is None:
        return None
    s = str(raw).strip()
    if not s or s.lower() in {"na", "n/a", "-", "--"}:
        return None
    s = s.replace("$", "").replace(",", "").replace("%", "").replace("+", "")
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    if not m:
        return None
    return float(m.group(0))


def day_from_name(name: str) -> str:
    m = re.search(r"(\d{4}-\d{2}-\d{2})", name)
    return m.group(1) if m else name


def build_stock() -> None:
    claims = []
    for path in sorted(STOCK_DIR.glob("stock-*.txt")):
        day = day_from_name(path.name)
        for line in path.read_text(errors="replace").splitlines():
            parts = line.split("\t")
            if len(parts) < 4:
                continue
            source, symbol = parts[0].strip().lower(), parts[1].strip().lower()
            for idx, attr in STOCK_ATTRS.items():
                if idx >= len(parts):
                    continue
                val = parse_number(parts[idx])
                if val is None:
                    continue
                claims.append((day, symbol, source, attr, val))
    claims_df = pd.DataFrame(
        claims, columns=["day", "object", "source", "attribute", "value"]
    )

    gold_rows = []
    for path in sorted(GOLD_DIR.glob("*.txt")):
        day = day_from_name(path.name)
        for line in path.read_text(errors="replace").splitlines():
            parts = line.split("\t")
            if len(parts) < 4:
                continue
            symbol = parts[0].strip().lower()
            # gold: symbol, change%, last, open, change$, volume, high, low, prev...
            for attr, gidx in [
                ("change_pct", 1),
                ("last_price", 2),
                ("open_price", 3),
                ("prev_close", 8),
            ]:
                if gidx >= len(parts):
                    continue
                val = parse_number(parts[gidx])
                if val is None:
                    continue
                gold_rows.append((day, symbol, attr, val))
    gold_df = pd.DataFrame(gold_rows, columns=["day", "object", "attribute", "value"])
    claims_df = claims_df.merge(
        gold_df[["day", "object", "attribute"]].drop_duplicates(),
        on=["day", "object", "attribute"],
    )
    OUT.mkdir(parents=True, exist_ok=True)
    claims_df.to_parquet(OUT / "stock_claims.parquet", index=False)
    gold_df.to_parquet(OUT / "stock_gold.parquet", index=False)
    print(
        "stock",
        len(claims_df),
        "claims",
        claims_df.source.nunique(),
        "sources",
        gold_df.object.nunique(),
        "gold symbols",
    )


def norm_city(loc: str):
    loc = loc.strip().lower()
    loc = re.sub(r"\([^)]*\)", "", loc).strip()
    loc = re.sub(r"zone forecast:.*", "", loc).strip()
    if loc in CITY_ALIASES:
        return CITY_ALIASES[loc]
    head = loc.split(",")[0].strip()
    if head in CITY_ALIASES:
        return CITY_ALIASES[head]
    for key, val in CITY_ALIASES.items():
        if key in loc:
            return val
    if head and head not in {"nws"}:
        return re.sub(r"[^a-z0-9]+", "_", head)
    return None


def parse_weather_ts(ts: str):
    m = re.match(
        r"\w{3}\s+(\w{3})\s+(\d{1,2})\s+\d{2}:\d{2}:\d{2}\s+(\d{4})", ts.strip()
    )
    if not m:
        return None
    mon = {
        "jan": 1,
        "feb": 2,
        "mar": 3,
        "apr": 4,
        "may": 5,
        "jun": 6,
        "jul": 7,
        "aug": 8,
        "sep": 9,
        "oct": 10,
        "nov": 11,
        "dec": 12,
    }
    month = mon.get(m.group(1).lower())
    if not month:
        return None
    return f"{int(m.group(3)):04d}-{month:02d}-{int(m.group(2)):02d}"


def parse_temp(raw):
    if raw is None:
        return None
    s = str(raw).strip()
    if not s or s.upper() == "NA":
        return None
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    return float(m.group(0)) if m else None


def parse_cond(raw):
    if raw is None:
        return None
    s = str(raw).strip().lower()
    if not s or s in {"na", "n/a"}:
        return None
    s = re.sub(r"[^a-z\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s or None


def collapse(df: pd.DataFrame, with_source: bool) -> pd.DataFrame:
    keys = ["day", "object", "source", "attribute"] if with_source else ["day", "object", "attribute"]
    rows = []
    for key, group in df.groupby(keys):
        vals = list(group["value"])
        attr = key[-1]
        if attr == "temperature":
            value = float(pd.Series([float(v) for v in vals]).median())
        else:
            mode = pd.Series(vals).mode()
            value = mode.iloc[0] if len(mode) else vals[0]
        rows.append((*key, value) if with_source else (*key, value))
    cols = (
        ["day", "object", "source", "attribute", "value"]
        if with_source
        else ["day", "object", "attribute", "value"]
    )
    return pd.DataFrame(rows, columns=cols)


def build_weather() -> None:
    weather_claims = []
    gold_weather = []
    for path in sorted(DATA.glob("*.txt")):
        text = path.read_text(errors="replace").splitlines()
        if len(text) < 3:
            continue
        header = text[1].lower()
        if "temperature" not in header and "conditions" not in header:
            continue
        cols = text[1].split("\t")

        def find_col(preds):
            for i, col in enumerate(cols):
                cl = col.lower()
                if any(p in cl for p in preds):
                    return i
            return None

        loc_i = find_col(["location"])
        temp_i = find_col(["temperature"])
        cond_i = find_col(["condition"])
        source = path.stem.lower()
        is_gold = source == "weather_gov"
        for line in text[2:]:
            parts = line.split("\t")
            if loc_i is None or loc_i >= len(parts):
                continue
            day = parse_weather_ts(parts[0])
            city = norm_city(parts[loc_i])
            if not day or not city:
                continue
            if temp_i is not None and temp_i < len(parts):
                tv = parse_temp(parts[temp_i])
                if tv is not None:
                    row = (day, city, source, "temperature", tv)
                    (gold_weather if is_gold else weather_claims).append(row)
            if cond_i is not None and cond_i < len(parts):
                cv = parse_cond(parts[cond_i])
                if cv is not None:
                    row = (day, city, source, "conditions", cv)
                    (gold_weather if is_gold else weather_claims).append(row)

    claims = collapse(
        pd.DataFrame(
            weather_claims, columns=["day", "object", "source", "attribute", "value"]
        ),
        with_source=True,
    )
    gold = collapse(
        pd.DataFrame(
            gold_weather, columns=["day", "object", "source", "attribute", "value"]
        ),
        with_source=False,
    )
    claims = claims.merge(
        gold[["day", "object", "attribute"]].drop_duplicates(),
        on=["day", "object", "attribute"],
    )
    OUT.mkdir(parents=True, exist_ok=True)
    for attr, cast in [("temperature", float), ("conditions", str)]:
        c = claims[claims.attribute == attr].copy()
        g = gold[gold.attribute == attr].copy()
        c["value"] = c["value"].map(cast)
        g["value"] = g["value"].map(cast)
        c.to_parquet(OUT / f"weather_{attr}_claims.parquet", index=False)
        g.to_parquet(OUT / f"weather_{attr}_gold.parquet", index=False)
        print(attr, len(c), "claims", g.shape[0], "gold", c.source.nunique(), "sources")


def main() -> None:
    if not STOCK_DIR.exists():
        raise SystemExit("missing clean_stock/; run download_data.py")
    build_stock()
    build_weather()
    print("wrote", OUT)


if __name__ == "__main__":
    main()
