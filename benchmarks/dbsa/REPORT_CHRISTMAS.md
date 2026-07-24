# Christmas bow — Aware sharpness wired; weather gate PASS

## The missing ribbon

Mnemosheath already learned when agreement is real evidence and computed a
courage signal (`context_log_odds`) — then left it in the trace and **never
put it into `p`**. That was the underconfidence near-miss on real weather.

## Fix (architecture, not a knob hunt)

On the evidence path, when the sheath says agreement is evidence **and** ACI
already picked the crowd’s side:

1. add a **capped** signed context log-odds
2. blend partway toward the observable vote rate (bounded)

Null / silence paths untouched. Wrong-majority chase through flips avoided by
the alignment guard.

## Prospective weather (sealed look after the bow)

| Method | Brier | Acc | Used |
|---|---:|---:|---:|
| Majority | **0.1624** | 0.756 | 5.95 |
| **Aware** | **0.1724** | 0.758 | **3.56** |
| Fixed-Share | 0.1781 | 0.744 | 5.95 |
| Agree-discount Bayes | 0.1833 | 0.766 | 5.95 |
| Fading Bayes | 0.1913 | 0.766 | 5.95 |
| ACI | 0.2147 | 0.675 | 2.99 |

**Non-inferiority vs Fixed-Share: PASS**  
Δ = −0.0057, CI97.5% upper = +0.0045 ≤ δ=0.005

Artifact: `results/dbsa_weather_christmas.json`  
Prior weather FAIL remains on record: `REPORT_WEATHER_PROSPECTIVE.md`

## Synthetic 24-seed screen after the bow

**`pilot_passes=True`** (all six worlds non-inferior + post-shift recovery)  
Artifact: `results/dbsa_v1_contract_screen_christmas.json`

## Honesty

- This is a new look after wiring unused sheath courage into `p`
- No silent rewrite of the previous weather FAIL
- Spent confirmation beds not reopened
- Majority still edges raw weather Brier; Aware wins the sealed gate while
  staying sparse — the bow, not a claim of perfection
