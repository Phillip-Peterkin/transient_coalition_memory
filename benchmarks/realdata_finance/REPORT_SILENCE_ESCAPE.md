# Silence escape — the missing jump (development)

Contact-tail only. No fresh-universe look in this cycle.

## The clue

On burned `confirmation3` autopsy (not used for tuning), **most flips had no
relevant news** (~65%). Under that silence, clean memory was
**anti-correlated** with the next move (r ≈ −0.26; on the development empty
flips, r ≈ −0.43).

The attractor was sealing the old regime exactly when the world was changing.
Cheerleader all-Positive coalitions behave like null sensation for the same
reason: they do not carry real directional information.

That is the other jump: not another weight on Positive headlines — a
**release valve** when sensation is null.

## Mechanism

`SilenceEscapeCellular` (on the session + clean-evidence stack):

1. Null sensation = no relevant reports, or all-Positive cheerleader coalition.
2. Escape hazard from prediction-error EWMA + belief AR(1) criticality `|rho|`.
3. Mix: `(1 - hazard) * memory + hazard * (1 - memory)`.
4. Mixed / negative reports keep ordinary clean evidence (sign-preserving).
5. Never reads the previous label (not a fade-`prev_truth` hack).

Aligned with HRF precision-weighted prediction error and fitted-dynamics
criticality before transitions.

## Predeclared contact grid

Fixed: `apply_to_all_positive=True`, `rho_gain=0.30`.

| pe_floor | pe_span | max_hazard | Acc | Flip | Non-flip | Pred-up |
|---:|---:|---:|---:|---:|---:|---:|
| clean baseline | | | 0.504 | 0.408 | 0.591 | 0.696 |
| 0.35 | 0.35 | 0.70 | 0.504 | 0.551 | 0.461 | 0.451 |
| **0.35** | **0.50** | **0.70** | **0.506** | **0.491** | **0.521** | **0.486** |
| 0.40 | 0.35 | 0.70 | 0.511 | 0.483 | 0.536 | 0.487 |

Gate: flip ≥ 45%, acc drop < 1 pt, pred-up ≤ 65%, **non-flip ≥ 50%**.

Selected winner: `pe_floor=0.35, pe_span=0.50, rho_gain=0.30, max_hazard=0.70`.

Paired vs clean on flips: **Δ +8.2 pts** (p≈0.003).

The sharper span=0.35 cell hits **+14 pts flip (55%)** but fails the non-flip
floor — recorded, not selected.

## Plain English

When the world goes quiet (or only cheers), and recent errors say memory is
wrong, **stop trusting the sticky story**. That recovers a large share of
change-detection that pure sensory weighting cannot touch.

## Status

- **Development freeze candidate:**
  `SessionRelevanceFinanceNewsStream` +
  `SilenceEscapeCellular(pe_floor=0.35, pe_span=0.50, rho_gain=0.30,
  max_hazard=0.70, apply_to_all_positive=True)`.
- **Not confirmed.** Needs a **new** virgin company universe and one sealed
  look. `confirmation3` is spent. Do not peek early.
