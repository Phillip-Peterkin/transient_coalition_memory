# Weather Year-Stress — sealed scoring protocol (not yet opened)

Written **before** any model scores this ledger. This bed exists because the
Christmas 60-day PASS does **not** establish year / climate-band / provider /
missingness / outage / severe / seasonal claims.

Christmas knobs stay frozen. This is a new sealed look on a **disjoint**
calendar window, not a retune surface and not confirmation3.

## Why this bed

| Open question | How this bed addresses it |
|---|---|
| Full year? | ≥350 labeled decision days spanning 12 calendar months |
| Different climates? | Predeclared climate-band slices on the same 12-station roster |
| Different providers? | **Honest limit:** still Open-Meteo delivery of six NWPs — reports model-family leave-one-out / leave-two-out stress, **not** independent commercial APIs |
| Missing reports? | Natural missingness strata + predeclared drop-stress on sealed packets |
| Sensor outages? | Natural observation gaps (exclude day; never impute) + predeclared obs-drop stress |
| Severe weather? | Predeclared \|ΔTmax\| tail slice (locked thresholds below) |
| Seasonal transitions? | Predeclared NH meteorological-season boundaries + transition ±14-day windows |

## Immutable inputs

| Piece | Lock |
|---|---|
| Roster | Same as prospective: ATL PHL MSP MUC LIS HEL TPE KUL LIM NBO PER DXB |
| Spent beds | contact / confirmation2 / confirmation3 — never reused; Christmas ledger not merged |
| Sources | `gfs_seamless`, `ecmwf_ifs025`, `icon_seamless`, `gem_seamless`, `meteofrance_seamless`, `jma_seamless` |
| Lead | Open-Meteo `previous_day1` only |
| Delivery | Open-Meteo previous-runs + archive (disclosed) |
| Window | **2025-01-15 → 2026-01-14** (365 days), disjoint from Christmas scoring days (2026-05-25 → 2026-07-23) |
| Ledger | `benchmarks/dbsa/weather_year_stress/ledger/` only |
| Margin | **δ = 0.005** vs delayed Fixed-Share (same as DBSA-v1 / Christmas) |
| Method knobs | Sealed Christmas / confirmation stack — **no retune after open** |

## Predeclared slices (primary + stress)

Score **once** when open conditions hold. Report all rows below; do not drop
failing slices after the look.

### Primary gate

1. Full-window prequential Brier non-inferiority vs Fixed-Share (δ=0.005,
   one-sided 97.5% paired-day-block CI upper on Aware − FixedShare).

### Climate bands (station partitions — locked)

| Band | Stations |
|---|---|
| `humid_subtropical` | ATL, PHL, TPE |
| `continental_boreal` | MSP, MUC, HEL |
| `mediterranean_arid` | LIS, DXB |
| `tropical` | KUL, NBO, LIM |
| `southern_temperate` | PER |

Each band: report Brier + source-use for Aware / Fixed-Share / Majority.
Band non-inferiority is **diagnostic**, not a veto on the primary gate
(bands are small).

### Seasons (NH meteorological — locked)

| Season | Months (decision day) |
|---|---|
| Winter | Dec, Jan, Feb |
| Spring | Mar, Apr, May |
| Summer | Jun, Jul, Aug |
| Autumn | Sep, Oct, Nov |

Transition windows (diagnostic): ±14 days around Mar 1, Jun 1, Sep 1, Dec 1.

### Severe-weather slice (temperature-only proxy — locked)

On events with `|tmax_tomorrow − tmax_today| ≥ 5.0°C` (absolute), report the
same method table. This is a **tail proxy**, not a storm catalog. If the slice
has fewer than 80 events, report “underpowered” and do not claim a gate.

### Missing-report stress (locked)

1. **Natural:** stratify days by fraction of (station, model) slots with
   `daily_max is None` — bins `{0}`, `(0, 0.05]`, `(0.05, 1]`.
2. **Sealed drop stress** (applied only at eval, never rewriting ledger):
   independently drop each available report with `p ∈ {0.10, 0.25, 0.50}`
   using seed `year_stress_drop_v1` — same drops for every method.

### Sensor-outage stress (locked)

1. **Natural:** if `tmax_obs` missing, the station-day is excluded (no impute).
2. **Sealed obs-drop stress:** drop observation labels with `p ∈ {0.05, 0.15}`
   (seed `year_stress_obs_drop_v1`), excluding those events for all methods.

### Provider / model-family stress (locked — naming honesty)

Not independent providers. Diagnostic leave-outs on the six NWP families:

- Leave-one-model-out (six runs)
- Leave-out US-family `{gfs_seamless}` and EU-heavy `{ecmwf_ifs025, icon_seamless, meteofrance_seamless}` as two coarse groups

Label these rows **model-family stress**, never “multi-provider.”

## Open conditions (all required)

1. Forecast ledger covers **2025-01-15 → 2026-01-14** with valid hashes
2. ≥ **350** labeled decision days after observation seal
3. This scoring protocol’s git SHA recorded in the run artifact
4. Synthetic DBSA-v1 200-seed artifact still present
5. Christmas prospective ledger left **untouched** (no merges)

Until then: collect only. No evaluator scores this ledger.

## Forbidden

- Retuning ACI/Aware after seeing year-stress numbers
- Merging Christmas or spent confirmation ledgers into this bed
- Claiming “multi-provider” when only Open-Meteo delivery is used
- Dropping climate/season/severe slices after the look
- Quietly shortening the window after seeing errors

## Status

**Protocol sealed. Scoring closed.** Collection may use disclosed archive
backfill into `ledger/`. First look TBD after open conditions.
