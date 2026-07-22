# TCM North Star (stored context — do not dilute)

This file is the durable record of (1) the long-term vision, (2) what the
current research release actually is, (3) the real-data weakness ledger, and
(4) anti-scope-creep rules. Future work must pass the fidelity checks at the
bottom before it is considered in-scope.

**Status of this note:** acknowledged and stored. No cure work has been
started from this document alone.

---

## 1. Long-term vision (the dream)

A **General Dynamic Memory Architecture** — information treated like
**living populations**, not fixed database entries.

Beliefs and evidence should recruit, compete, go dormant, return from reserve,
and revise under delayed outcomes — temporary coalitions of useful evidence,
not exhaustive retrieval or permanent records.

This is the north star. Mechanisms, datasets, and wave numbers are means;
they are not the product.

---

## 2. What it currently is

Canonical written statement of the present research program:

- [`docs/TCM_Vision_and_Technical_Report.pdf`](TCM_Vision_and_Technical_Report.pdf)
  — Vision & Technical Report (v1.0 research program, Waves IV–XVI).

In short (from that report): TCM is a sparse, adaptive belief architecture
that recruits evidence until a decision is certified, preserves unused
evidence in reserve, and learns source/memory reliability from delayed
outcomes. Strongest demonstrated claim is architectural (favorable
accuracy–compute tradeoff under matched benchmarks); central open challenge
is change response on correlated, imperfect real-world data.

Repo code on `main` is the frozen Wave XI reference + historical waves /
calibration / wall-clock tooling. It is a research prototype, not the finished
general architecture.

---

## 3. Real-data weakness ledger (complete)

Learned after touching real-world data (sandbox waves ahead of what is frozen
in this repo). Treat as the honesty baseline for any "improvement" claim.

### 1. Persistence masquerading as accuracy
Headline accuracy on real data is mostly persistence, not detection. On Stock,
an oracle that predicts "same as yesterday" scores ~89.1% overall — TCM ~90.0%.
The accuracy lead over baselines is real but smaller than it looks once the
persistence prior is subtracted. Papers that claim the accuracy win without
this decomposition will get caught.

### 2. Change detection is the core failure — and it's architectural
- **Stock:** ~42–46% flip detection vs ~76% memoryless majority, ~63% dynamic
  Bayes.
- **Weather:** ~13.5–17.4% — catastrophic; TCM worst among methods tested
  (beaten by ~76 points in the worst comparison).
- Root-cause chain (mechanism-verified): claim anchor dominates report
  strength → fresh opposing evidence is shrunk (pre-Wave XV, literally
  sign-reversed) → anchor-confirming reports recruit first → coalition is
  selected to agree with memory → confident anchor lowers hazard → shallower
  recruitment → anchor protected. A **self-sealing attractor**.

### 3. Confirmation-biased recruitment
Recruitment ranks by `|strength|`, which includes the claim anchor. Gathering
is not prior-neutral — the architecture reads what it already believes.
(C7 evidence-led recruitment helps modestly; currently a post-contact
hypothesis, not a validated fix.)

### 4. Static prior/evidence exchange rate
Balance between trusting memory vs. trusting the world is a hard-coded
constant (anchor weights, floor). Real regimes differ on exactly this axis:
adversarial-stale-source regimes reward strong anchors (synthetic, stock);
trustworthy-source regimes punish them (weather). Single root of the regime
boundary; no fix so far touches it.

### 5. Regime specialization (master weakness)
TCM wins decisively in adversarial/noisy-source regimes (synthetic #1,
stock #1) and is dead last in trustworthy-source, fast-crossing regimes
(weather). Not regime-general as shipped. The synthetic generator it was
shaped on matches one slice of reality.

### 6. Adaptive gate loses its edge on real data
- Stock: fixed-k4 ties the adaptive gate on cost and slightly beats it on
  accuracy; certificate value unproven outside synthetic.
- Dense-report worlds (48 reports): pre-Wave-XV truncation meant reports
  beyond `max_k` influenced nothing — decision, certificate, or reserve
  learning. The "compressed dormant reserve" was silently capped.

### 7. Fragility to benchmark truth quality (Stock gold contamination)
Report–gold agreement collapses to ~0.45 on 2–3 of 21 days; gold says
89–100% of stocks rose *every day* of July 2011 — implausible vs market
history. Evaluation against a partially corrupted yardstick caps measurable
flip detection for any model, and some TCM "errors" may not be errors.
Model failure vs label noise is not yet cleanly separable.

### 8. Block-correlated evidence breaks the coalition premise
Stock sources agree ~91.3% within a day — ~48 reports ≈ one effective
observation. Premise (recruit a sparse coalition of *independent* evidence)
degrades when evidence is redundant. Recruitment counts, op accounting, and
certification treat reports as independent; reality does not.

### 9. Calibration advantage doesn't survive regime change
Best-in-class Brier/ECE on synthetic and stock; on weather, dynamic Bayes
beats TCM on both (~0.019/0.020 vs ~0.087/0.088). Calibration story is
regime-dependent too.

### 10. Information-theoretic ceiling on flip detection (stock)
With an ~11% flip prior and block evidence at ~76% detection / ~46% false
alarm, Bayes posterior of a flip is ~0.17. Part of the stock flip gap is
unrecoverable by *any* model — but this excuse does **not** apply to weather,
where evidence is good and TCM still fails.

### 11. Process contamination of the current evidence base
- C7/C8 designed *after* seeing weather — hypotheses, not validated fixes.
- Stock has informed multiple design decisions (floor, conviction gate,
  hazard memory) — no longer a clean test bed.
- Weather silver standard has mild lookahead (weekly-median threshold) and
  rests on undisclosed choices (city filter, T cap) a reviewer could remake
  differently.

### 12. What we still don't know
- Whether *any* anchor-based memory architecture can be regime-general, or
  whether the exchange rate must be learned online (Wave XVIII's premise).
- Whether C7/C8-style fixes generalize or are weather-shaped.
- Whether an online exchange-rate mechanism can raise flip detection on the
  new finance/news stream without sacrificing adversarial-regime wins.

### 13. Finance/news stream v0 (new, first contact in-repo)
Harness: [`benchmarks/realdata_finance/`](../benchmarks/realdata_finance/)
(protocol + locked Wave XI params; not the July 2011 stock gold setup).

- Multi-publisher news (HF FMP RSS sentiments) → next-day equity direction
  (Yahoo). Window 2022-08 → 2023-10; 6,121 events; chronological
  contact/holdout 70/30.
- Persistence oracle ≈ 0.50 here (near coin-flip days) — persistence is **not**
  masquerading as accuracy the way it did on the old stock bed.
- Locked TCM holdout: accuracy **0.526** (edges persistence / graph) but flip
  accuracy **0.183** vs ~0.49 for memoryless majority / dynamic Bayes.
  Self-sealing attractor reproduced on a fresh stream.
- Publisher evidence is ~90% Positive while labels are balanced; independence
  is limited (mean agreement ~0.84).
- Holdout remains confirmatory only for these locked weights; mechanism work
  informed by holdout must retire or replace that split.

### One-paragraph summary
TCM is a strong architecture for adversarial, noisy-source regimes — where
it is genuinely state of the art on accuracy, cost, and calibration — but it
carries a static trust-memory-over-world assumption baked into recruitment,
the anchor, and the gate, and that assumption fails in trustworthy-source
regimes to the point of being the worst method tested. The flip-detection
weakness is partly fixable mechanism (evidence floor shipped), partly
dataset ceiling (stock), and partly an unvalidated open problem (weather,
regime generality).

---

## 4. Anti-scope-creep / vision fidelity rules

Before any substantive change is proposed or merged, it must answer yes to
these — or be explicitly marked as out-of-vision exploratory work:

1. **Living populations, not a better database.** Does the change reinforce
   recruit / certify / reserve / delayed-learn dynamics, or does it drift
   toward denser retrieval, permanent records, or black-box fine-tuning that
   erases the architecture story?
2. **Regime honesty.** Does the evaluation report adversarial *and*
   trustworthy-source regimes (at least synthetic + stock + weather class),
   with persistence-oracle and flip-detection decomposition — not headline
   accuracy alone?
3. **Exchange-rate awareness.** If the change does not touch the static
   memory-vs-world exchange rate (ledger item 4), say so explicitly; do not
   claim "regime generality."
4. **No silent contamination.** Development contact with a dataset removes
   that dataset as a clean confirmatory test. Held-out / untouched splits and
   process notes are mandatory.
5. **Independence honesty.** If evidence is block-correlated, do not treat
   report count as independent sample size in claims, certificates, or ops.
6. **Vision over wave numbers.** Prefer fewer mechanism changes that serve
   the General Dynamic Memory Architecture over a pile of regime-shaped
   patches (C7/C8-class) that win one dataset and fade the dream.
7. **Cure before feature.** When returning to "the beginning of where the
   repo is," prioritize curing ledger items 2–5 (self-sealing attractor,
   confirmation-biased recruitment, static exchange rate, regime
   specialization) over new surface features.

When in doubt: **preserve the dream, name the tradeoff, do not paper over
persistence as intelligence.**

---

## 5. Related docs (keep these in sync)

| Doc | Role |
|---|---|
| [`README.md`](README.md) | Index of all docs in this folder |
| [`TCM_Vision_and_Technical_Report.pdf`](TCM_Vision_and_Technical_Report.pdf) | Canonical Vision & Technical Report |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Frozen mechanisms + known failure modes |
| [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) | How to run / reproduce on `main` |
| [`../README.md`](../README.md) | Public entry point: vision vs shipped results |
| [`../AGENTS.md`](../AGENTS.md) | Agent / Cursor Cloud operating notes |
| [`../benchmarks/realdata_finance/`](../benchmarks/realdata_finance/) | Finance/news real-data harness + v0 report |

If this ledger or the vision statement changes, update the README scientific-status
section and the Architecture "known failure modes" section in the same change.
