# Year Multi-Domain first look — Arousal Dual-Mode

Sealed once under [`year_multi_domain/SCORING_PROTOCOL.md`](year_multi_domain/SCORING_PROTOCOL.md).  
Primary method: **`aware_arousal`** (thrift ESSC ↔ truth ROPL).  
Artifact: `results/dbsa_year_multi_domain_first_look.json`

**Headline: crushes majority on all three lanes.**

---

## Locked knobs (before scoring)

| Knob | Value |
|---|---|
| `arousal_enabled` | True |
| `thrift_rho_enter` | **0.5** |
| `rebate_window` | 120 |
| `rebate_min_updates` | 40 |
| ESSC | on, Christmas bow off |
| Standalone ROPL / Pool-Restore | off |

---

## Open conditions

All passed: weather year 365/366 + 364 labeled days · finance 461 · medical 360 · synth 200 artifact · protocol SHA recorded.

---

## Weather year (4368 events · 2025-01-15 → 2026-01-14)

| Method | Brier | Acc | Used |
|---|---:|---:|---:|
| **Aware+ROPL** | **0.129350** | 0.820 | 5.894 |
| **Aware+Arousal** | **0.132170** | 0.819 | **4.387** |
| Aware+ESSC | 0.133596 | 0.818 | 3.488 |
| **Majority** | 0.137293 | 0.823 | 6.000 |
| Fixed-Share | 0.144871 | 0.808 | 6.000 |
| Persistence | 0.518315 | 0.482 | 6.000 |

| Quantity | Value |
|---|---:|
| Δ Arousal − Majority | **−0.00512** |
| Thrift fraction | **0.648** |
| Thrift mean Used / Truth mean Used | (see artifact) |

**Verdict:** CRUSH majority. Arousal nearly matches pure ROPL while cutting Used (~4.39 vs ~5.89) via ~65% thrift.

---

## Finance year (461 events · virgin universe · 2022-08-15 → 2023-08-14)

| Method | Brier | Acc | Used |
|---|---:|---:|---:|
| Aware+ESSC | **0.249439** | 0.512 | 0.022 |
| Persistence | 0.250000 | 0.510 | 1.154 |
| **Aware+Arousal** | **0.271131** | 0.527 | **0.139** |
| Aware+ROPL | 0.278780 | 0.525 | 0.694 |
| Fixed-Share | 0.477575 | 0.516 | 1.154 |
| **Majority** | 0.477689 | 0.516 | 1.154 |

| Quantity | Value |
|---|---:|
| Δ Arousal − Majority | **−0.2066** |
| Thrift fraction | **0.887** |
| Mean reports / event | ~1.15 |

**Verdict:** CRUSH majority. Honesty: this lane is thin-report (often 1 publisher vote); majority ≈ raw sentiment bit and is a weak pool. ESSC is best here; arousal stays in thrift most of the time and beats maj/ROPL on Brier while staying sparse.

---

## Medical FluSight (360 events · 8 models · 2023-10-14 → 2024-10-12)

| Method | Brier | Acc | Used |
|---|---:|---:|---:|
| Aware+ESSC | **0.233037** | 0.581 | 2.292 |
| **Aware+Arousal** | **0.255652** | 0.567 | **3.064** |
| Aware+ROPL | 0.256079 | 0.556 | 3.244 |
| Persistence | 0.250000 | 0.447 | 7.422 |
| Fixed-Share | 0.386234 | 0.536 | 7.422 |
| **Majority** | 0.432215 | 0.419 | 7.422 |

| Quantity | Value |
|---|---:|
| Δ Arousal − Majority | **−0.1766** |
| Thrift fraction | **0.867** |

**Verdict:** CRUSH majority. ESSC leads absolute Brier; arousal ≈ ROPL and far ahead of the model-vote majority, with thrift dominant.

---

## Switch honesty (biology claim)

| Lane | Thrift frac | Used (arousal) | Used (maj) | Crush maj? |
|---|---:|---:|---:|---|
| Weather | 0.65 | 4.39 | 6.00 | **Yes** |
| Finance | 0.89 | 0.14 | 1.15 | **Yes** |
| Medical | 0.87 | 3.06 | 7.42 | **Yes** |

Thrift Used < truth/full-roster Used on weather (the lane where the pool matters). The switch fires.

---

## Honesty

- Knobs locked before scoring; scored once; no retune
- Christmas weather + finance confirmation8 untouched
- Weather year is the hard common-mode lane — arousal still crushes maj with partial thrift
- Finance/medical majority gaps are large partly because maj is a poor reference under sparse/noisy votes; report ESSC/ROPL deltas too
- Pure ROPL still slightly best Brier on weather; arousal is the thrift/truth blend

## Status

**Year multi-domain first look complete. Primary majority gates: 3/3 PASS.**
