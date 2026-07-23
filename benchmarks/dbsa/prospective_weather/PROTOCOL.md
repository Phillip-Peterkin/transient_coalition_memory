# Prospective Weather lane — append-only collection (started)

Collection begins **before** any scoring. This lane is part of DBSA's
cross-domain requirement, not a retune surface.

## Immutable roster

- 12 stations in `stations.py`, **disjoint** from spent Weather beds:
  contact (`cities.py`), `confirmation2`, `confirmation3`
- Six NWP sources (locked):
  `gfs_seamless`, `ecmwf_ifs025`, `icon_seamless`, `gem_seamless`,
  `meteofrance_seamless`, `jma_seamless`
- Lead: Open-Meteo `previous_day1` only
- Label (when later scored): adjacent-day ERA5/GHCN warmer — **not scored here**

## Append-only ledger rules

1. `collect_day.py` writes one daily artifact under `ledger/YYYY-MM-DD/`
2. Artifact includes forecast snapshot JSON + `sha256` of canonical bytes
3. `ledger/INDEX.jsonl` appends one line per successful collection
4. Never rewrite a prior day directory; corrections append a new dated note
5. No model evaluation imports this ledger until the sealed scoring protocol
   is **opened** — see [`SCORING_PROTOCOL.md`](SCORING_PROTOCOL.md)

## Why start now

Prospective means waiting for real forecasts and real outcomes. Starting the
immutable pipeline today is what makes a future sealed look possible.

Scoring protocol is drafted and **closed** until open conditions in
`SCORING_PROTOCOL.md` are met (60 collection days, sealed labels, prior
200-seed synthetic artifact).
