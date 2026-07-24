# Room consensus — what must crush majority

Four voices argued (biologist, neuroscientist, physicist, AI engineer).
They disagreed on dialect. They agreed on the object.

**Held bar unchanged:** crush full-source majority on raw prequential Brier.
Fixed-Share parity / sparsity is not the destination. Christmas-bow
majority-attracting blend is **forbidden** in any candidate that claims crush.

---

## The argument (compressed)

| Voice | Insisted | Rejected |
|---|---|---|
| Biologist | Relatedness on **error** co-occurrence; epitope credit = residual after projecting out the clone; must be able to side with a low-*r* minority | Accuracy weights without anti-relatedness; Brownian densification inside the correlated cloud |
| Neuroscientist | Precision before pooling; common-mode rejection; remap when dependence chart drifts | Confidence = vote fraction; Christmas sharpen-when-aligned |
| Physicist | Majority is optimal under exchangeability; beat it only via precision \(\Lambda=C^{-1}\) where correlation spike \(\lambda_1\) is large; delayed martingale update of \(\Lambda\) | String-theory costume; blend toward majority; static weights |
| AI engineer | Ship a residual that predicts delayed majority/base error; romantic geometry without a residual head is theater; sparsity is a variance tax | FS non-inferiority as win; “just calibrate”; residual on *raw* majority without whitening |

**Fight that resolved:** DODR’s \(m+r\) is right *only if* \(m\) is already whitened.
Residual on raw majority forces \(r\) to undo common-mode contamination that
should never have entered the pool.

---

## CONSENSUS object

### PWDR — Precision-Whitened Delayed Residual

*(also floated as WDCQ / DWPS / WPRF — same mechanism)*

1. **Error kernel, not opinion kernel.**  
   Estimate source covariance \(C_t\) from **delayed error** co-occurrence
   (residuals vs revealed labels), not from forecast agreement.

2. **Whiten before pooling.**  
   \(\Lambda_t \approx C_t^{-1}\) (regularized / low-rank+diagonal OK).  
   Base belief \(m_t = \sigma(\mathbf{1}^\top \Lambda_t \boldsymbol{\ell}_t)\).  
   \(N_{\mathrm{eff}} = \mathbf{1}^\top \Lambda_t \mathbf{1}\) is diagnostic / quorum scale — not a win condition.  
   Raw majority is **not** the attractor.

3. **Delayed residual on the whitened base.**  
   Online \(r_t\) predicts \((y_{t-\tau} - m_{t-\tau})\) from whitened disagreement
   × context features. Emit \(p_t = \Pi(m_t + r_t)\) with proper prequential
   stacking. Credits accrue to mass orthogonal to the dominant common mode
   (“epitope credit”).

4. **Forbidden.**  
   Agreement blend toward unwhitened vote (Christmas bow path as crush strategy).  
   Softening δ. Claiming multi-provider or year-stress wins before those beds open.

---

## Shared falsifiable prediction

Pre-register before any PWDR look:

- On slices where \(\lambda_1(C)/\mathrm{Tr}(C)\) is in the **top** quantile
  (correlated-majority traps) **and** a low-relatedness minority opposes the
  bloc: PWDR raw Brier must beat full-source majority by a pre-set margin —
  especially when the eventual label matches the minority.
- On **low**-\(\lambda_1\) near-exchangeable slices: PWDR stays within ε of the
  better of {majority, fading Bayes}.
- Fail either slice ⇒ reject the implementation (object not instantiated).
- If gains appear only when already agreeing with majority ⇒ still Christmas-bow; veto.

---

## Non-negotiables the room signed

1. Crush majority on raw prequential Brier under spent-bed / no-silent-retune rules.
2. \(\Lambda\) from delayed **errors** before pooling.
3. Residual stacks on whitened \(m\), not on raw majority.
4. No metric softening while the idea matures.

**Status:** consensus on the missing object. Not yet implemented. Not yet scored.
Year-stress collection continues under a closed score. Metrics held.
