# Combined leave organ — six-role room

Roles: biologist · neuroscientist · physicist · AI engineer · CS#1 (online learning) · CS#2 (aggregation).

**Charge:** Take the leave-law idea seriously. Treat every failed *single* as negative
evidence. Ask whether a *combination* could clear Majority **0.162412** — and
whether Used **~3.5** is compatible with that.

**Bar held.** No silent retune. Spent beds frozen.

---

## Evidence locked (what not to do)

| Single (costume) | Weather Brier | Used | Lesson |
|---|---:|---:|---|
| Christmas bow | 0.172395 | ~3.56 | Majority-*attracting* blend cannot be the crush organ |
| Aware+ESSC (always leave, g=1) | 0.172849 | **3.538** | Soft shadow ≠ restored pool; oppose-slice loses |
| PWDR residual \(m+r\) | 0.214939 | 5.95 | Delayed additive private head detonates |
| Whitened base alone | 0.166096 | 5.95 | Chassis near maj is fine; gadgets hurt |
| Fixed-Share / fading Bayes | 0.178–0.191 | 5.95 | Full-mass learners lose on this bed |
| Pool-Restore (binary g∈{0,1}) | 0.162697 | 5.397 | Closes gap by *being* maj ~76%; delayed Cov/Var ~0.39 < ½ |

Baked geometry (708 events):

- λ₁/Tr = **0.550** · ρ̄ = **0.455** · ESS ≈ **1.83**
- Aware leave: Cov/Var = **0.315** (< ½) · tax Var−2Cov = **0.010429** ≈ gap **0.010437**

Synthetic still splits: ESSC crushes drift/crossover; taxes `correlated_stable`.

---

## Shared verdict

**Something popped — and it was hiding in the tax formula itself.**

The room had been debating a *binary* leave law:

\[
\text{emit leave iff }\frac{\mathrm{Cov}}{\mathrm{Var}}>\tfrac12
\quad\text{else emit majority.}
\]

That is the right break-even for **full** leave (\(g=1\)). Pool-Restore implemented
it and matched. It cannot crush here because ρ̂ stays ~0.39 < ½.

But the Brier increment for a **partial** leave

\[
p \;=\; p_{\mathrm{maj}} \;+\; g\,(p_{\mathrm{coalition}}-p_{\mathrm{maj}})
\]

is

\[
\Delta\mathrm{BS}(g)
\;=\;
g^2\,\mathrm{Var}(\delta p)\;-\;2g\,\mathrm{Cov}(\delta p,\,y-p_{\mathrm{maj}}).
\]

This is negative for every \(g\in(0,\,2\rho)\) whenever \(\rho=\mathrm{Cov}/\mathrm{Var}>0\).
The optimum is not “leave or don’t.” It is

\[
g^\star \;=\; \rho \;=\; \frac{\mathrm{Cov}}{\mathrm{Var}}.
\]

On the baked numbers: \(g^\star\approx 0.315\), expected \(\Delta\mathrm{BS}^\star=-\rho^2\mathrm{Var}\approx-0.00281\).

### Diagnostic probe (not yet a sealed score)

Same Aware+ESSC \(p_{\mathrm{coalition}}\) as DBSA default; same 708-event ledger:

| Emitter | Brier | Used (honest) | Notes |
|---|---:|---:|---|
| Majority | **0.162412** | 5.95 | bar |
| Aware+ESSC (\(g=1\)) | 0.172849 | 3.54 | always full leave — tax |
| Pool-Restore (\(g\in\{0,1\}\)) | 0.162697 | 5.40 | binary law |
| **Shrink \(g=0.315\) fixed** | **0.159579** | 5.95 | hindsight \(g^\star\) — illustrative |
| **ROPL online \(\hat g_t=\mathrm{clip}(\hat\rho_t,0,1)\)** | **0.160413** | 5.95 | delayed rolling window; **legal shape** |
| Online hard gate \(\hat\rho>½\) | 0.163124 | 5.56 | binary; no crush |

**Pop:** continuous rebate-optimal partial leave beats majority on this bed in
prequential probe; binary leave does not.

This is a *combination*, not a new single:

1. **Equal-gain pool** — \(p_{\mathrm{maj}}\) (what weather rewards)
2. **Coalition / micro-agent leave direction** — Aware+ESSC \(p_{\mathrm{coalition}}\) (what drift worlds reward)
3. **Physics gain** — \(g_t\approx\hat\rho_t\) (the missing organ, mis-specified as a hard gate)

---

## Six dialects (same object)

### Biologist
Assemblies don’t hard-switch off the population code. They *modulate* how far a
coalition pulls the tissue. ESSC was always-on recruitment of unread mass;
Christmas was chemotaxis into the crowd; Pool-Restore was an all-or-none molt.
The living move is **graded recruitment**: keep the equal-gain field, let the
coalition tug with gain \(g^\star\).

### Neuroscientist
λ₁ is the population mode. Sparse spikes that fully replace it pay a variance tax
(Cov/Var=0.315). Partial decoding — read the common mode, add a shrunk private
innovation — is how cortex mixes shared signal with feature residuals.
Binary leave was the wrong spike threshold; **shrink to ρ** is the right synaptic
weight on the leave pathway.

### Physicist
Break-even \(\rho>\tfrac12\) applies to \(g=1\). The risk function \(\Delta\mathrm{BS}(g)\)
is a parabola; minimum at \(g^\star=\rho\). We implemented the indicator
\(\mathbf{1}\{\rho>\tfrac12\}\) and called it the leave law. The actual leave law is
the **ridge coefficient** \(g^\star=\rho\). On this bed \(\rho\approx 0.32>0\) ⇒ crush
headroom exists even though full leave is taxed.

### AI engineer
Compose, don’t replace:

```
p_pool       ← equal-weight full roster          # compulsory co-activation
p_coalition  ← Aware+ESSC (bow off)              # disturb / recruit / compete
g_t          ← clip(rolling Cov/Var, 0, 1)       # delayed, label-honest
p_emit       ← p_pool + g_t * (p_coalition - p_pool)
```

Forbidden recycles: Christmas maj-attracting bow; PWDR delayed \(+r\) head;
binary Pool-Restore as the only gate; claiming Used~3.5 while \(p_{\mathrm{pool}}\)
reads the full roster.

### CS#1 (online learning)
Hard thresholding a noisy delayed \(\hat\rho_t\) at ½ throws away the only
identifiable advantage. Online regression of the leave residual on the maj
residual *is* the prequential estimate of \(g^\star\). Probe with window 120 /
min 40 / cold-start \(g=0\) already clears the bar (~0.1604). Lock those knobs
*before* sealed rescoring. Do not fit \(g\) on the baked 0.315 and call it a test.

### CS#2 (aggregation)
Majority is near-min-Var for the exchangeable spike. Full leave reweights off
that estimator and pays \(\mathrm{Var}-2\mathrm{Cov}\). Shrink-leave is James–Stein /
ridge toward the pool — the first combiner that respects both the diagnosis and
the coalition. **Incredible Used~3.5 crush is a different theorem:** it requires
\(p_{\mathrm{pool}}\) itself from ≤3.5 sources. Subset-pool probes fail
(k=3⇒0.166, k=2⇒0.175). Phase-1 crush ≠ phase-2 thrift.

---

## What the oracle says about “incredible”

| Ceiling | Brier | Used notes |
|---|---:|---|
| Oracle pick(Aware, maj) per event | ~0.129 | honest Used ~5.34 if maj counts full |
| Always thin equal-weight active | 0.189 | Used 3.54 — *worse* than Aware |
| Shrink \(g^\star\) with full maj | **~0.160** | Used **5.95** — crush, not thrift |
| Shrink \(g^\star\) with random k=3 pool | ~0.166 | no crush |

So:

- **Surpassing majority** with a legal combined organ looks *real* (probe).
- **Doing it at Used ~3.5** remains the extraordinary claim — not delivered by ROPL.
- Cheat that emits maj while reporting Used=3.5 is rejected unanimously.

---

## Named next object — ROPL

**Rebate-Optimal Partial Leave (ROPL)**  
(alias: Shrink-Leave · graded co-activation)

### Lock before scoring

| Knob | Proposed lock |
|---|---|
| `ropl_enabled` | True |
| Coalition path | Aware+ESSC (existing `AWARE_PARAMS`; Christmas bow off) |
| `ropl_window` | 120 |
| `ropl_min_updates` | 40 |
| `ropl_g_mode` | `covvar` — \(g_t=\mathrm{clip}(\hat\rho_t,0,1)\) |
| Cold start | \(g=0\) (emit majority) until min updates |
| Cov tracking | on \((p_{\mathrm{coalition}}-p_{\mathrm{maj}},\, y-p_{\mathrm{maj}})\) at feedback |
| Used accounting | **full roster whenever \(g_t<1\)** (honest) |

### Pass / fail

| Result | Criterion |
|---|---|
| **PASS** | raw Brier **< 0.162412** on prospective weather 708 |
| **FAIL** | ≥ maj; or crush only with hindsight-fixed \(g=0.315\); or Used sleight-of-hand |
| **Phase-2 (incredible)** | separate pre-registration: Brier < maj **and** Used ≤ 3.6 — not claimed by ROPL |

### Explicitly not ROPL

- Binary Pool-Restore (already scored; match costume)
- PWDR \(m+r\) revival
- Christmas bow
- Renaming to ACS/LKS before PASS
- Topology theater

---

## Why singles failed as a map (combination checklist)

| Need | Who had a piece | Who corrupted it |
|---|---|---|
| Equal-gain pool | Majority / Pool-Restore restore branch | ESSC never restored ESS_maj |
| Leave direction | Aware / ESSC / cues | Always-on \(g=1\); oppose on dependence noise |
| Rebate signal | Physics Cov/Var; PRG thermometer | Hard threshold at ½; delayed binary open |
| Partial gain | Christmas *family* \(m+\alpha\delta\) | Bow drove α toward maj-*attraction*, not \(α=\rho\) |
| Private residual | PWDR | Unshrunk delayed \(r\) (g≫ρ) |

ROPL = pool + coalition direction + \(g=\hat\rho\). The pieces were all on the
board; we only ever wired them as mutually exclusive singles.

---

## Ecosystem vision — where this sits

Micro-agents still recruit, contradict, certify, decay.
The substrate question becomes:

> How hard does this coalition pull against equal-gain co-activation *right now*?

Answer: **\(g_t\approx\hat\rho_t\)**, not “replace the tissue” and not “never leave.”

Adaptive topology remains phase-3 — after ROPL is scored under freeze protocol.
ACS/LKS rename remains gated on a real crush niche, not on this memo.

---

## Status

- Vision leave-law: **reframed** from binary to partial (ROPL).
- Probe suggests weather **crush is possible** at Used ≈ maj roster.
- Incredible Used~3.5: **not** implied; keep as harder sequel.
- **Next build:** implement ROPL behind locked knobs → unit tests → sealed
  weather + synthetic screen → `REPORT_ROPL.md`.
- Crush bar unchanged until that report.

Diagnostic numbers in this memo are **room probes**, not sealed leaderboard rows.
Seal only after code + locked params + artifact.
