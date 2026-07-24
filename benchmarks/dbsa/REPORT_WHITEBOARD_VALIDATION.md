# Did the field experts get it?

**Verdict: YES — core autopsy confirmed (6/6 refined claims).**

No retune. No new object. Measurements only.
Artifact: `results/dbsa_whiteboard_validation.json`

---

## Claims tested

| # | Autopsy claim | Result | Evidence |
|---|---|---|---|
| C1 | Weather ≈ `correlated_stable` (spectrum) | **PASS** | Nearest world by λ₁ distance; weather λ₁=0.550, ρ̄=0.455 |
| C2 | Cov/Var below break-even on weather, above on drift | **PASS** | Weather Cov/Var=**0.315** < 0.5; abrupt_drift=**1.108** > 0.5 |
| C3 | On oppose-slice, majority more accurate than shadow | **PASS** | maj 0.577 vs shadow 0.423 (n=104) |
| C4 | Aware deploys less ballot mass than full roster | **PASS** | used 3.54 vs roster 5.95 (u≈0.60) |
| C5 | Variance-tax formula matches weather gap | **PASS** | Var−2Cov=**0.010429** vs ΔBrier=**0.010437** (abs err < 10⁻⁵) |
| C6 | `correlated_stable` same-sign gap; drift opposite | **PASS** | wx +0.010, corr_stable +0.007, abrupt_drift **−0.056** |

---

## Smoking gun

Physicist’s off-spike tax on weather:

\[
\Delta\mathrm{BS}\;\approx\;\mathrm{Var}(\delta p)-\,2\,\mathrm{Cov}(\delta p,\,y-p_{\mathrm{maj}})
\]

| | Value |
|---|---:|
| Predicted tax | 0.010429 |
| Observed Aware−Majority Brier | 0.010437 |

That is not hand-waving. The ~+0.01 weather ceiling is the variance tax.

---

## Spectra snapshot

| Lane | λ₁ frac | mean ρ | ESS (equal-w) | maj wrong rate |
|---|---:|---:|---:|---:|
| **weather** | **0.550** | **0.455** | 1.83 | 0.244 |
| correlated_stable | 0.435 | 0.381 | 2.31 | 0.120 |
| abrupt_drift | 0.372 | 0.203 | 3.71 | 0.043 |
| independent_stable | 0.342 | 0.281 | 2.93 | 0.043 |

Weather is the **most spike-dominated** lane measured. Nearest synthetic cousin: `correlated_stable`.

---

## Nuance (experts not perfect on wording)

- **ESS_equal ≈ 1.83 on weather** is lower than Aware’s raw used count (3.54). The prize is not “ESS number > used” — it is the **full-pool average under correlation**. Claim C4 is about ballot mass / aggregator geometry, not raw ESS>used.
- Abrupt-drift overall win (ΔBrier −0.056) is **not** because shadow oppose is accurate there (shadow acc on oppose ≈ 0.06). The Cov/Var rebate is real; the oppose-side story is messier. The niche-split claim still holds.

---

## Bottom line

The room’s arrow stands:

> Weather is λ₁-dominated / correlated-stable. Leaving majority without a live rebate (\(\mathrm{Cov}/\mathrm{Var}>\tfrac12\)) costs ~0.01 Brier — exactly the gap we’ve been kissing.

They got it. Metrics still held. Crush bar unchanged.
