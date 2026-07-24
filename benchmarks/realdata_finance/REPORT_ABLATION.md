# Cure ablation v0 — testing all five improvement options

**Question.** Which of the five proposed improvements actually helps on the
untouched finance/news stream, and is the effect statistically real?

**Design.** Each cure is an independently toggleable modification of the frozen
Wave XI reference (`cures.py`, `CuredCellular`). With an empty cure set the
subclass reproduces `BatchedReserveCellular` **exactly**
(`null_reproduces_frozen = True`), so any change is attributable to the cure,
not to a reimplementation drift. Every comparison uses a paired bootstrap
(5,000 resamples) on the held-out split for overall accuracy and
flip-detection accuracy (`ablation.py`).

The cures are grounded in the two uploaded papers:

| Cure | Ledger item | Paper mechanism |
|---|---|---|
| `adaptive_exchange` | 4 (static exchange rate) | HRF: precision-weighted prediction error / gain modulation — anchor trust and learning gain modulated by how wrong memory has been |
| `prior_neutral` | 3 (biased recruitment) | HRF: activation energy crosses a gain-modulated threshold — recruit by evidence energy, not by the claim anchor |
| `surprise_hazard` | 2 (self-sealing attractor) | HRF adaptive threshold ∝ 1/precision + Fitted-Dynamics spectral radius rising before a transition (local AR(1) \|ρ\|) |
| `source_calib` | 8 (independence) | Precision-weighting: weight each report by the self-information of its source's emission base rate |
| `corr_downweight` | 8 (independence) | Independence honesty: shrink redundant within-event agreement by an effective-count factor |

## Held-out results (horizon = 1, next-session direction)

Baseline frozen TCM: accuracy 0.526, flip 0.183, activated 1.74, Brier 0.282.

| Cure | Acc Δ (95% CI) | p | Flip Δ (95% CI) | p | Activated | Brier |
|---|---|---:|---|---:|---:|---:|
| `adaptive_exchange` | +0.0026 [−0.001,+0.007] | 0.181 | −0.0052 [−0.011,+0.000] | 0.048 | 1.74 | 0.285 |
| `prior_neutral` | +0.0017 [−0.002,+0.006] | 0.317 | −0.0021 [−0.008,+0.004] | 0.422 | 1.80 | 0.282 |
| `surprise_hazard` | −0.0044 [−0.009,+0.000] | 0.066 | **−0.0103 [−0.019,−0.003]** | 0.001 | 1.80 | 0.281 |
| `source_calib` | +0.0009 [−0.010,+0.012] | 0.829 | **+0.0361 [+0.019,+0.054]** | <0.001 | 1.60 | 0.260 |
| `corr_downweight` | −0.0048 [−0.014,+0.005] | 0.304 | **+0.0175 [+0.004,+0.032]** | 0.008 | 1.59 | 0.262 |
| `calibrate_both` | −0.0004 [−0.013,+0.012] | 0.945 | **+0.0568 [+0.039,+0.075]** | <0.001 | 1.52 | 0.255 |
| `all_combined` | +0.0048 [−0.007,+0.016] | 0.387 | **+0.0526 [+0.036,+0.070]** | <0.001 | 1.67 | 0.254 |

## Findings (honest)

1. **My a priori ranking was wrong, and the test caught it.** I expected the
   static exchange rate (item 4) to be the master lever. On this stream it is
   not: `adaptive_exchange`, `prior_neutral`, and `surprise_hazard` produce **no
   significant flip-detection gain**, and `surprise_hazard` is significantly
   *worse* on flips (−1.0 pt, p=0.001). Deepening recruitment on surprise just
   pulls in more of the 90%-Positive news flood.

2. **The only robust win is the independence/calibration family (ledger 8).**
   `source_calib` (+3.6 pts, p<0.001) and `corr_downweight` (+1.8 pts, p=0.008)
   each significantly raise flip detection and are additive
   (`calibrate_both`: +5.7 pts, 0.183 → 0.239, p<0.001). They do this at
   **equal overall accuracy**, **better calibration** (Brier 0.282 → 0.255,
   ECE also down), and **lower compute** (1.74 → 1.52 reports activated). This
   is a clean Pareto improvement on exactly the axes the north star prioritizes.
   Both effects replicate on the contact split (source_calib +3.8, corr +0.9).

3. **Why calibration, not exchange rate?** The ledger notes TCM's static trust
   is tuned for *adversarial-stale-source* regimes. This stream is a
   *trustworthy-but-biased-source* regime: publishers are ~90% Positive while
   the market is ~50/50. The dominant defect here is the **evidence
   representation** (a Positive headline from a 90%-Positive source is treated
   as a full vote), not the memory-vs-world balance. Calibrating each report by
   its source's base-rate self-information, and discounting redundant agreement,
   directly attacks that — and it reallocates behavior from persistence-following
   toward genuine change response (non-flip accuracy drops 0.779 → 0.736 while
   flip accuracy rises).

4. **Longer-horizon robustness.** At 3- and 5-day horizons (`ablation_h3.json`,
   `ablation_h5.json`) the calibration cures still raise flip detection
   (source_calib flip 0.115 → 0.170 at h=3), but now at a cost to headline
   accuracy — because multi-day up-drift inflates baseline accuracy via
   persistence, and calibration trades that inflation for change response. This
   is ledger item 1 (persistence masquerading as accuracy) made visible.

## Non-claims

- These cure parameters were set a priori (documented defaults in `cures.py`),
  not tuned on the holdout. They are a first honest test, not an optimized
  result. Any follow-up that tunes on the holdout retires it as a clean bed.
- A +5.7-point flip-detection gain still leaves flip accuracy at ~0.24 — far
  from solved. Calibration is necessary, not sufficient.
- No claim of real-world trading value or superiority is made.

## Recommended next step

Promote `source_calib` + `corr_downweight` to the primary cure direction (it is
the evidence-honest, vision-aligned fix), and design a fresh untouched slice
(new tickers or a later time window) to confirm the tuned version — since the
current holdout has now informed this analysis.
