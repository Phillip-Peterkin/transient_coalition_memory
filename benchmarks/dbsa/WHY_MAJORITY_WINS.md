# Why majority keeps winning — six-expert deep read

Not “our architecture is buggy.” What majority *is*, why it fits this
bed, and what organ we still lack.

**Evidence frozen:** [`BAKED_DIAGNOSIS.md`](BAKED_DIAGNOSIS.md) /
`results/dbsa_weather_baked_diagnosis.json`  
Majority **0.162412** @ 5.95 · Aware+ESSC **0.172849** @ 3.538 · gap **+0.010437**

Roles: biologist · neuroscientist · physicist · AI engineer · CS#1 · CS#2.

---

## The shared deeper claim

> On this λ₁-dominated, exchangeable weather bed, **equal-weight full-roster
> majority is the near-optimal aggregator** — the min-variance common-mode
> estimator / no-learning comparator. Leaving that pool without a live
> Cov/Var > ½ rebate is a pure variance tax (~0.01). Learning and selective
> dissent assume skill heterogeneity or regime flips the data do not supply.

Majority is not a dumb baseline we failed to dress up. On this niche, it is
the prize.

---

## What majority *is* (six readings, one object)

| Role | Majority is… |
|---|---|
| Biologist | Compulsory parallel sensing — every channel at full amplitude; residual noise cancels, shared weather mode stays |
| Neuroscientist | Equal-weight full-pool population readout (λ₁ / common-mode mean), not a selected subpopulation |
| Physicist | BLUE / exchangeable GLS fixed point when \(\Lambda\propto I\); projection onto leading mode of \(C\) |
| AI engineer | Static common-mode projector \(p=\bar v\) — no delayed skill model |
| CS#1 | No-learning comparator in \(\mathcal{C}_{\mathrm{static}}\) — delay cannot mis-credit it |
| CS#2 | Min-variance linear pool under near-exchangeable ballots |

---

## Why that fits *this* niche (numbers)

| Fact | Value | Reading |
|---|---:|---|
| λ₁ / Tr(C) | **0.550** | Spike-dominated — almost all useful signal is common-mode |
| Mean pairwise ρ | **0.455** | Highly correlated NWP clones, not independent experts |
| ESS (equal-w) | **1.832** | ~2 independent votes — but maj still averages **all** mass on that spike |
| Cov/Var (Aware leave) | **0.315** | Below physicist break-even ½ — leave-maj does not pay |
| Predicted tax Var−2Cov | **0.010429** | |
| Observed gap | **0.010437** | Tax **is** the gap (err ~10⁻⁵) |
| Maj wrong rate | **0.244** | Wrong often — still best Brier (calibration + Var win) |

**Critical evidence the room insisted on:** majority does not only beat sparse Aware.
It beats **full-mass learners** on the same bed:

| Full-mass method | Brier | vs Majority |
|---|---:|---:|
| **Majority** | **0.162412** | — |
| Fixed-Share | 0.178110 | +0.016 |
| Agree-discount Bayes | 0.183342 | +0.021 |
| Fading Bayes | 0.191295 | +0.029 |
| PWDR | 0.214939 | +0.053 |
| AdaHedge | 0.231642 | +0.069 |

So: not “we deleted ballots and they didn’t.” Even aggregators that keep all
sources and *learn* lose. On exchangeable spike data, loss-chasing reweights
noise in \(C_\perp\).

Synthetic niche split still holds: ESSC beats maj on drift / crossover —
habitats where common mode *moves*. Weather is correlated-stable. Wrong organism
for this niche if the plan is leave-majority.

---

## What we lack (missing organ — not missing knob)

Every role named the same hole in different dialects:

**An emit-time, undelayed signal that majority is wrong *now*, with live rebate**

\[
\frac{\mathrm{Cov}(\delta p,\, y-p_{\mathrm{maj}})}{\mathrm{Var}(\delta p)} \;>\; \tfrac12
\]

so that \(\mathbb{E}[\Delta\mathrm{BS}\mid\mathrm{leave}]<0\).

Without that organ:

- selective stop thins the pool that cancels residual noise
- shadow/oppose fires on dependence noise (oppose: maj acc **0.577** > shadow **0.423**, n=104)
- delayed learners credit stale merit and wander off λ₁
- “awareness” becomes an anti-organ on this bed

We have selection, attention, residual, shadow. We do **not** have forced
equal-amplitude pooling *or* a verified leave-maj rebate. Those are different
organs; we counterfeited both.

---

## Counterfeits (looked like the organ, weren’t)

| Costume | What it pretended | What it actually did | Score |
|---|---|---|---|
| Christmas bow | Courage / sharpness | Chemotaxis **into** maj — cannot pass it | 0.172395 |
| ESSC shadow | Restore unread mass / ESS | Soft logit nudge; ESS_maj never restored; oppose loses | 0.172849 |
| PWDR residual | Private skill off maj | Base ≈ maj (0.166); delayed \(r\) detonates | 0.214939 |
| FS / sparsity “win” | Frontier skill | Checkpoint, not crush | FS 0.178 |
| Synth drift crush | Weather proof | Wrong niche | — |

Whitened / full-pool base alone (**0.166096**) is the tell: the chassis near
majority is fine; every “clever” add-on is where the blood is.

---

## Deeper claim (one line each)

| Role | Majority wins because… |
|---|---|
| Bio | The only free lunch here is residual-noise cancellation from equal-weight use of nearly all six sources; awareness removes that lunch |
| Neuro | On a λ₁ population, low-Var common-mode pooling is the prize; leave-λ₁ without Cov rebate is spike-conditional tax |
| Physics | Majority is the min-Var common-mode estimator; every off-spike departure with Cov/Var<½ is pure tax (~0.01) |
| Engineer | Equal-weight maj *is* near-Bayes for this exchangeable generator; learning assumes heterogeneity/flips the data don’t supply |
| CS#1 | Under delay on a spike bed, the no-learning maj *is* the hard comparator — delay mis-credits everyone who adapts |
| CS#2 | Spike + exchangeable ρ ⇒ equal-weight full vote is variance-optimal; leave-λ₁ (delete **or** reweight) is structurally taxed |

---

## Evidence hooks (do not lose these)

1. **Tax = gap:** 0.010429 ≈ 0.010437  
2. **Learners lose too:** FS / fading Bayes / AdaHedge / PWDR all > maj  
3. **Oppose loses:** maj 0.577 > shadow 0.423 on n=104  
4. **Spectrum:** λ₁=0.550, ρ=0.455, ESS=1.832  
5. **m-only ≈ maj:** 0.166 vs 0.162 — base ok, gadgets hurt  
6. **Niche split:** correlated_stable / weather tax; drift rebate

---

## Dangers the room flagged

- Building a *smarter selector* for a niche that rewards *dumb full pooling*
- Shipping drift-validated crush machinery into weather’s correlated-stable bed
- Treating disagreement level δ as “maj wrong now” (it’s dependence noise here)
- Concluding “majority is unbeatable forever” (drift worlds falsify that) — or the opposite, that any leave-maj gadget will do

---

## Status

Evidence clear. Diagnosis deepened.

**Tried (a)+(b) as Pool-Restore Gate** — see [`REPORT_POOL_RESTORE.md`](REPORT_POOL_RESTORE.md):
weather Brier **0.162697** vs Majority **0.162412** (Δ **+0.000285**).
Gap closed. **Still no crush.** Delayed Cov/Var rebate stays ~0.39 < ½ on
weather, so the gate mostly restores majority (76% of events).

Crush bar unchanged: beat **0.162412**. Next leave cue must be better than
delayed rolling Cov/Var — or admit match is the honest ceiling on this bed.
