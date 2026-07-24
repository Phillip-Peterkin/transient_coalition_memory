# Christmas bow — Aware sharpness wired; weather gate PASS

## Read these two cards before hanging the stocking

### 1. Bed provenance (what the number is worth)

**This was not confirmation3.** confirmation3 is spent and was not touched.

Gate bed: **`benchmarks/dbsa/prospective_weather/`** — fresh sealed lane.

| Lock | Value |
|---|---|
| Roster | ATL PHL MSP MUC LIS HEL TPE KUL LIM NBO PER DXB |
| Overlap with spent contact / confirmation2 / confirmation3 | **none** |
| Sources | six NWP `previous_day1` (locked) |
| Non-inferiority margin | **δ = 0.005** predeclared in `SCORING_PROTOCOL.md` before scoring |
| Open conditions | 60 forecast days, ≥45 labeled days, protocol present, synthetic 200 artifact |

**Credibility:** full weight as a **fresh-bed** weather finding under a predeclared gate — not a rerun on a spent confirmation bed.

**Look sequencing (still say out loud):** look #1 on this same fresh ledger failed
(`REPORT_WEATHER_PROSPECTIVE.md`, Aware Brier 0.1877). The Christmas number is
look #2 after wiring unused sheath courage into `p`. The FAIL stays on the
record; the bed is still the prospective one, not confirmation3.

Collection used disclosed **archive backfill** of the locked Open-Meteo APIs
(not two months of wall-clock waiting).

### 2. Majority still beats Aware on raw error

Say it before a reviewer does:

> **Aware matches Fixed-Share quality at ~60% of sources; raw majority remains ahead on this lane, at full evidence cost.**

| Method | Brier | Sources used |
|---|---:|---:|
| **Majority** | **0.1624** | 5.95 (full) |
| Aware | 0.1724 | **3.56 (~60%)** |
| Fixed-Share | 0.1781 | 5.95 (full) |

Frontier framing absorbs this only because the majority gap is stated **first**.

---

## The missing ribbon

Mnemosheath already learned when agreement is real evidence and computed a
courage signal (`context_log_odds`) — then left it in the trace and **never
put it into `p`**. That was the underconfidence near-miss on look #1.

## Fix (architecture, not a knob hunt)

On the evidence path, when the sheath says agreement is evidence **and** ACI
already picked the crowd’s side:

1. add a **capped** signed context log-odds
2. blend partway toward the observable vote rate (bounded)

Null / silence paths untouched. Wrong-majority chase through flips avoided by
the alignment guard.

## Prospective weather — look #2 after the bow

| Method | Brier | Acc | Used |
|---|---:|---:|---:|
| **Majority** | **0.1624** | 0.756 | 5.95 |
| Aware | 0.1724 | 0.758 | **3.56** |
| Fixed-Share | 0.1781 | 0.744 | 5.95 |
| Agree-discount Bayes | 0.1833 | 0.766 | 5.95 |
| Fading Bayes | 0.1913 | 0.766 | 5.95 |
| ACI | 0.2147 | 0.675 | 2.99 |

**Non-inferiority vs Fixed-Share: PASS**  
Δ = −0.0057, CI97.5% upper = +0.0045 ≤ δ=0.005

Artifact: `results/dbsa_weather_christmas.json`  
Prior FAIL on this bed: `REPORT_WEATHER_PROSPECTIVE.md`

## Synthetic 24-seed screen after the bow

**`pilot_passes=True`** (all six worlds non-inferior + post-shift recovery)  
Artifact: `results/dbsa_v1_contract_screen_christmas.json`

## Honesty checklist

- Fresh prospective bed ≠ confirmation3 (spent, untouched)
- Predeclared δ=0.005
- Look #1 FAIL kept; look #2 is post-bow
- **Majority remains ahead on raw Brier at full evidence cost**
- Aware’s claim on this lane is Fixed-Share quality at ~60% sources, not raw leadership over majority
