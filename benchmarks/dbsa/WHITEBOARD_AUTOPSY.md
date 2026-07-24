# Whiteboard autopsy — six roles, one problem

Roles: biologist · neuroscientist · physicist · AI engineer · CS#1 (online learning) · CS#2 (aggregation).

**Bar held:** crush full-source majority on weather Brier **0.1624**.
Nothing below has softened that.

---

## The board (shared map)

```
                         WEATHER ≈ correlated_stable
                         majority = λ₁ / full-pool low-Var mean
                         Brier★ = 0.1624 @ ~5.95 sources
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          ▼                         ▼                         ▼
   CHRISTMAS BOW              ESSC @ ~3.54              PWDR
   Aware 0.1724               Aware 0.1728              0.2149
   blend → maj when aligned   shadow into p, bow OFF    m≈0.166 + r
   majority-ATTRACTING        selective stop kept       residual BOMB
          │                         │                         │
          │                         │                         │
   caps at parity             same ~+0.01 gap             +0.052 disaster
   cannot crush               oppose-slice FAIL           rejected
```

| Attempt | Weather Brier | Δ vs maj | Used | Fate |
|---|---:|---:|---:|---|
| Majority | **0.1624** | — | 5.95 | bar |
| Whitened base alone (PWDR m) | 0.1661 | +0.0037 | full | near maj |
| Christmas Aware | 0.1724 | +0.0100 | 3.56 | FS pass; not crush |
| Aware+ESSC | 0.1728 | +0.0104 | 3.54 | not crush |
| PWDR full | 0.2149 | +0.0525 | full | rejected |

Synthetic ESSC: **wins** drift / crossover / adversarial; **loses** `correlated_stable` (+0.020). Weather lives in the losing niche.

---

## The math the room agrees on

### 1. Majority-attracting bound (Christmas)

\[
p=(1-\alpha)m+\alpha\,\tilde p
\quad\Rightarrow\quad
\text{cannot systematically beat }m\text{ on Brier.}
\]

Bow is chemotaxis into the basin you must leave.

### 2. Residual bomb (PWDR)

\[
\mathrm{BS}(m+r)-\mathrm{BS}(m)
\approx 2\,\mathbb{E}[(m-y)r]+\mathbb{E}[r^2]
\]

Observed: \(m\) at 0.1661, \(m+r\) at 0.2149 ⇒ **+0.0488** from \(r\).
Delayed residual = variance tax, not private signal.

### 3. Spike / common-mode geometry (physics)

\[
C=\lambda_1 uu^\top+C_\perp,\qquad
N_{\mathrm{eff}}=\frac{(\sum w_i)^2}{\sum w_i^2}
\]

Majority ≈ projection on \(\lambda_1\). Weather is spike-dominated.
Off-spike mass pays:

\[
\Delta\mathrm{BS}\approx\mathrm{Var}(\delta p_\perp)
-2\,\mathrm{Cov}(\delta p_\perp,\,o-p_{\mathrm{maj}})
\]

- `correlated_stable` / weather: \(\mathrm{Cov}\approx 0\) → pure tax (+0.01…+0.02)
- drift / crossover: \(\mathrm{Cov}>0\) → synthetic wins

### 4. Variance tax of thin ESS (CS#2 / engineer)

\[
\mathrm{Var}(\bar v)=\frac{\sigma^2}{\mathrm{ESS}},\qquad
\mathrm{ESS}=\frac{n}{1+(n-1)\rho}
\]

Christmas delete and ESSC soft-shadow both run at \(n\approx 3.5\):

\[
u=\frac{3.54}{5.95}\approx 0.60
\quad\text{(~40\% mass idle or only gated logit nudge)}
\]

ESSC shadow does **not** restore \(\mathrm{ESS}_{\mathrm{maj}}\):

\[
\mathrm{logit}(p)\leftarrow\mathrm{logit}(p_{\mathrm{act}})+g\cdot\ell_{\mathrm{sh}},
\quad g\le 0.5,\quad \mathrm{ESS}_{\mathrm{block}}=1
\]

Soft complete ≠ full-pool average. Same ~+0.01 gap as Christmas.

### 5. Oppose-slice accounting (bio / eng)

\[
\Delta_{\mathrm{opp}}=0.261-0.244=+0.017
\quad(n=104)
\]

Dissent paid a **positive** Brier tax on weather. Crush bet failed its falsifier.

### 6. Disagreement ≠ regime flip (CS#1)

Gate merit \(\eta_t\propto g(\delta_t)\):

- flip worlds: \(\delta\) spikes **with** true advantage → win
- correlated_stable: \(\delta>0\) as **dependence noise** → spurious oppose credited under delay

\[
\|g_t-\hat g_t\|
\;\le\;
L\|w_t-w_{t-d}\|+\varepsilon^{\mathrm{sh}}_t
\]

Delay × shadow error eats the thin edge to 0.1624.

---

## What went wrong (merged, ruthless)

1. **Wrong niche.** Weather ≈ `correlated_stable`. Mechanisms that crush on drift are maladaptive here.
2. **Christmas cannot crush** — majority-attracting by construction.
3. **PWDR residual** — base was fine; delayed \(r\) was toxic (+0.05).
4. **ESSC soft-shadow ≠ restored ESS** — same sparsity tax as Christmas (~+0.01), new lipstick.
5. **Oppose-majority without a live “maj wrong now” cue** — 104 opposes, lose the slice.
6. **Disagreement level \(\delta\) as gate** — buys learning rate on the wrong days under correlation.
7. **Synth optimism** — drift wins validated the wrong mixture for weather deployment.

---

## What still looks right (keep on the board)

| Keep | Why |
|---|---|
| Crush majority on raw Brier | the only destination |
| Whitened / full-pool base near 0.166 | chassis not dead |
| No PWDR / no `m+r` | residual bomb is real |
| No Christmas-as-crush | caps at parity |
| No hard ballot deletion | Christmas proved the delete tax |
| Selective stop as *protocol*, not as win | sparsity ≠ skill |
| Regime split (drift WIN / correlated FAIL) | map is anisotropic — informative |
| Gross bug hygiene | signed-correctness, Λ∝I⇒maj, ACI leftovers, string IDs |

---

## ONE ARROW (room consensus)

```
weather ≈ correlated_stable / λ₁-dominated
        │
        ▼
majority’s prize = full-pool low Var(¯v)  (ESS ≈ mid–high single digits)
        │
        ├── Christmas: attract into that basin (cannot pass it)
        ├── PWDR: keep m≈maj, then delayed r detonates Var
        └── ESSC: thin active + gated logit shadow
                  never restores ESS_maj
                  oppose fires without undelayed “maj wrong” signal
        │
        ▼
ΔBrier ≈ +0.01 on weather   (same ceiling, three costumes)
```

**Causal sentence:** Excess Brier is a **spike-conditional variance tax** — off-λ₁ / thin-ESS / delayed-oppose mass only pays when \(\mathrm{Cov}(\delta p_\perp, o-p_{\mathrm{maj}})>0\); on weather that Cov is ≈0, so every “clever” leave-majority move costs ~0.01 (or much more if you stack a residual).

---

## Open questions the room forced (unanswered — next chalk)

1. **Bio / metric:** At *emit time*, what observable has \(\mathbb{P}(\mathrm{maj\ wrong}\mid\mathrm{signal})\) high enough that \(\mathbb{E}[\Delta\mathrm{BS}\mid\mathrm{oppose}]<0\) on weather — or do we stop opposing?
2. **Neuro:** Smallest precision-gated, \(c\)-orthogonal private increment that goes *below* 0.1624 on correlated_stable?
3. **Physics:** Estimate per-regime \(\mathrm{Cov}(\delta p_\perp,o-p_{\mathrm{maj}})/\mathrm{Var}(\delta p_\perp)\) and gate off-spike mass only when ratio \(>\tfrac12\)?
4. **Engineer:** On the 104 oppose cases, is the edge negative *before* any stacking, or only after delay?
5. **CS#1:** Gate on \(\dot\delta\) / volatility of disagreement, not level of \(\delta\)?
6. **CS#2:** If selective stop stays, what aggregator restores \(\mathrm{ESS}\approx\mathrm{ESS}_{\mathrm{maj}}\) in *vote-mean units* without Christmas blend — or is weather’s bar majority’s variance, and only ESS-matched full mass can crush it?

---

## Status

Autopsy complete. **Validation: experts got it (6/6 refined claims).**
See `REPORT_WHITEBOARD_VALIDATION.md` — variance-tax formula matches the
weather gap to ~10⁻⁵. **No new object locked. No retune.**
PWDR rejected. ESSC scored: weather FAIL, synthetic niche-split explained.
Metrics held.
