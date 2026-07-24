# Arousal Dual-Mode + Year Multi-Domain

Biology switch + year-scale real data across weather / finance / medical.

## Organ (locked)

**Arousal Dual-Mode (`aware_arousal`)** in `AwareCoalitionCellular`:

| Mode | When | Emit | Used |
|---|---|---|---|
| **Truth (aroused)** | cold start or delayed ρ̂ < 0.5 | ROPL: \(p_{maj}+g(p_{coal}-p_{maj})\), \(g=\mathrm{clip}(\hat\rho,0,1)\) | full roster if \(g<1\) |
| **Thrift (dormant)** | delayed ρ̂ ≥ `thrift_rho_enter` (0.5) | Aware+ESSC coalition | active size |

Knobs: `evaluate.AROUSAL_PARAMS` — locked before scoring.

ROPL alone remains the pure-truth row (`aware_ropl`). Arousal *chooses*
when thrift is safe.

## Year multi-domain bed

`benchmarks/dbsa/year_multi_domain/`

| Lane | Window | Source |
|---|---|---|
| Weather | 2025-01-15 → 2026-01-14 | Open-Meteo year-stress ledger |
| Finance | 2022-08-15 → 2023-08-14 | HF news + Yahoo, virgin universe |
| Medical | 2023-10-14 → 2024-10-12 | CDC FluSight multi-model |

**Scoring closed** until `SCORING_PROTOCOL.md` open conditions (all lanes).

## Status

- Organ implemented + unit tests
- Protocols sealed; collection complete
- **First look scored once** — see [`REPORT_YEAR_MULTI_DOMAIN.md`](REPORT_YEAR_MULTI_DOMAIN.md)
- Arousal crushes majority on weather / finance / medical (3/3)
