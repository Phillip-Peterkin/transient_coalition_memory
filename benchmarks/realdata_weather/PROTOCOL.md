# Clean Weather harness protocol (v1)

A **new** trustworthy-source weather test bed. This is **not** recovery of the
old sandbox Weather split (that harness is absent; its silver standard had
weekly-median lookahead and undisclosed city/T choices).

Weather remains final-only for mechanism design: no ACI / TCM knobs may be
tuned against this stream. First contact is for purity validation and locked
baselines only.

## Corruption rules this bed refuses

| Old taint | Clean rule |
|---|---|
| Weekly-median threshold (lookahead into the week) | **Forbidden.** Labels use only adjacent-day observations. |
| Undisclosed city filter / T cap | Cities, dates, models locked in `cities.py` / this protocol before scoring. |
| Stitched “best” forecasts that include analysis at valid time | Reports use Open-Meteo **`previous_day1`** only (forecast issued ~24h before valid time). |
| Reanalysis masquerading as sensory evidence | ERA5 archive is the **label/observation** organ only, never a report source. |

## Task

For each city and calendar day `D` (UTC):

- **Label:** `1` iff observed daily `temperature_2m_max` on `D+1` >
  observed daily max on `D` (next-day warmer). Ties → `0`.
- **Reports:** one vote per NWP model. Vote `1` iff that model’s
  `previous_day1` forecast daily max on `D+1` > observed max on `D`.
- **Flip:** label differs from the previous event’s label for that city
  (adjacent decision days).

This matches the finance harness shape: delayed truth, multi-source reports,
persistence-heavy base rate, flip detection as the stress metric.

## Locked sources (Open-Meteo Previous Runs API)

1. `gfs_seamless`
2. `ecmwf_ifs025`
3. `icon_seamless`
4. `gem_seamless`
5. `meteofrance_seamless`
6. `jma_seamless`

(`cma_grapes_global` was probed and dropped: ~9% missing days on the locked
window — incomplete sources are not allowed in the locked set.)

## Locked cities

See `cities.py` (12 globally distributed cities). No city may be added or
dropped after the first confirmatory look is declared.

## Locked calendar

- Start: `2024-06-01`
- End observation day: `2025-12-31` (last decision day `2025-12-30`)
- Timezone for daily aggregates: `UTC` (explicit; not local civil day)

ERA5 archive lag is avoided by ending well before “today.”

## Splits

Chronological by UTC date across all cities:

- **contact:** first 70% of decision days
- **holdout:** last 30%

Contact may be inspected for purity / baseline smoke. Holdout is confirmatory
for locked models only. Any mechanism change informed by holdout retires it.

## Required honesty metrics

Every scored run must report:

1. overall accuracy
2. persistence-oracle accuracy
3. flip accuracy + nonflip accuracy
4. prediction-up rate
5. mean reports activated (for cellular methods)

## Non-claims

- Passing here is **not** recovery of the original sandbox Weather final.
- This bed alone does not authorize Wave XI foundation replacement.
- Live APIs can revise archives; the committed `data/` cache is the locked
  artifact for reproduction.
