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

### 14. Cure ablation v0 — which fixes actually work (finance/news)
Harness: [`benchmarks/realdata_finance/cures.py`](../benchmarks/realdata_finance/cures.py)
+ [`ablation.py`](../benchmarks/realdata_finance/ablation.py); writeup
[`REPORT_ABLATION.md`](../benchmarks/realdata_finance/REPORT_ABLATION.md).
Cures are grounded in the two Peterkin papers (HRF energetic gating; fitted
operator geometry) and toggled on the frozen Wave XI reference (empty cure set
reproduces it exactly). Paired bootstrap (5k) on holdout flip detection:

- **Independence/calibration (ledger 8) is the only robust win.** Source
  base-rate self-information weighting (+3.6 pts, p<0.001) and correlated-report
  down-weighting (+1.8 pts, p=0.008) are additive (+5.7 pts, 0.183→0.239,
  p<0.001), at equal accuracy, better Brier/ECE, and lower compute.
- **Anchor-dynamics cures did not help here.** Precision-weighted exchange rate
  (ledger 4) and prior-neutral recruitment (ledger 3) were null; surprise-driven
  hazard (ledger 2) was significantly *worse* on flips (−1.0 pt, p=0.001) —
  deeper recruitment just amplifies the ~90%-Positive news skew.
- **Lesson:** on a trustworthy-but-biased-source regime the dominant defect is
  the evidence *representation*, not the memory-vs-world balance. This corrected
  a wrong a-priori ranking (the value of testing all options, not one).
- Cure params were set a priori, not tuned on holdout; a fresh untouched slice
  is still needed to confirm a tuned calibration cure.

### 15. Brain-shaped transition investigation — fresh-company result
Harness: [`transition.py`](../benchmarks/realdata_finance/transition.py);
protocol: [`CONFIRMATION_PROTOCOL.md`](../benchmarks/realdata_finance/CONFIRMATION_PROTOCOL.md);
writeup: [`REPORT_TRANSITION.md`](../benchmarks/realdata_finance/REPORT_TRANSITION.md).

- Design: accumulated **confident** prediction errors ignite a temporary,
  hysteretic investigation state; during it, calibrated counter-evidence cannot
  be sign-reversed by stale memory. This is directly grounded in HRF energetic
  gating / precision-weighted error and tested after source calibration.
- Contact-only design looked promising (flip 0.221→0.287), but the
  pre-declared, disjoint 33-company (32 price-labeled) confirmation result was 0.240→0.255:
  **+1.5 pts, 95% CI −0.3 to +3.4; fails the pre-set +3-point gate.**
- Do **not** bake it into the active model. A generic prediction-error alarm
  signals that something may have changed but supplies no representation of
  *what* changed; its apparent contact gain did not generalize.
- Next hypothesis: semantic novelty / event identity in reports — a compact
  representation of what a story is about — is needed before a biologically
  inspired attention gate can distinguish a real new event from routine biased
  publisher flow.

### 16. Sensory relevance gate — fresh-company confirmation passed
Implementation: [`src/tcm/experimental.py`](../src/tcm/experimental.py)
(`SensoryGatedCellular`); input gate:
[`relevance.py`](../benchmarks/realdata_finance/relevance.py); protocol and
writeup:
[`RELEVANCE_CONFIRMATION_PROTOCOL.md`](../benchmarks/realdata_finance/RELEVANCE_CONFIRMATION_PROTOCOL.md)
and [`REPORT_RELEVANCE.md`](../benchmarks/realdata_finance/REPORT_RELEVANCE.md).

- Human-like premise: sensory evidence must be about the thing being decided.
  The raw feed often assigns clearly unrelated headlines to a company; memory
  must not update from them. With no relevant report, retain memory rather than
  treating a 50/50 empty input as “up.”
- Fixed combination: explicit title/company relevance + source base-rate
  calibration + correlated-report discounting. The frozen Wave XI reference
  remains unchanged. This was the first active **experimental** real-data
  front end; later superseded as the active model by Active Coalition
  Inference (ledger item 18) while remaining an archival confirmed step.
- Predeclared, disjoint second company universe (29 declared; 28 price-labeled)
  confirmation: flip detection **0.221→0.281** (+5.9 pts, 95% CI +1.2 to
  +10.7, p=0.006); overall accuracy 0.493→0.520 (uncertain, p=0.084);
  prediction-up 0.539→0.482; activation 1.13→0.40.
- This clears the +3-point fresh-company gate and is the first real-data cure
  to survive a fresh-company confirmation. It is **not** the final solution
  (still far below 45% flip target), and same-source/same-calendar validation
  is not independent-dataset replication.

### 17. Wave XVIII prediction-error trust — finance development gate failed
Protocol: [`WAVE_XVIII_PROTOCOL.md`](../benchmarks/realdata_finance/WAVE_XVIII_PROTOCOL.md);
implementation: `tcm.WaveXVIIITrustCellular`; writeup:
[`REPORT_WAVE_XVIII.md`](../benchmarks/realdata_finance/REPORT_WAVE_XVIII.md).

- Exact three-way mechanism: confident wrong prediction raises a per-item
  mistrust state; next decision recruits at most one report deeper, lowers the
  anchor, and protects fresh relevant counter-evidence. Confident correct
  feedback relaxes the same state.
- Finance development result: active sensory baseline flip 0.271; broad trust
  loop 0.402 but prediction-up 0.695; evidence-gated version 0.381 with
  prediction-up 0.667. **Neither clears the required 0.45 flip / ≤0.65-up
  gate.**
- Trust loop contains a real change-response signal, but routine
  Positive/Negative finance messages do not provide enough trustworthy
  counter-evidence after the gate opens. Do **not** promote the class and do
  **not** run Weather.
- Weather cannot currently be the promised final test: no Weather harness,
  data, protocol, or locked untouched split is present in this repo; prior
  sandbox Weather contact and silver-label caveats remain. Recover the
  original locked split/harness first.

### 18. Active Coalition Inference — active experimental model (finance sealed)
Implementation: `tcm.ActiveCoalitionCellular` (alias
`ActiveExperimentalCellular`); protocol / writeups:
[`ACTIVE_COALITION_CONFIRMATION_PROTOCOL.md`](../benchmarks/realdata_finance/ACTIVE_COALITION_CONFIRMATION_PROTOCOL.md),
[`REPORT_ACTIVE_COALITION.md`](../benchmarks/realdata_finance/REPORT_ACTIVE_COALITION.md),
[`REPORT_ACTIVE_COALITION_CONFIRMATION.md`](../benchmarks/realdata_finance/REPORT_ACTIVE_COALITION_CONFIRMATION.md).

- One Friston-native cell: prior-free likelihood-ratio evidence; null-channel
  PE+|ρ| anti-prior mix; recruit by |Δ|; free-energy stop when unread mass
  cannot flip the posterior. Upstream session relevance still owns gating.
- Virgin `confirmation8` **passed** the predeclared gate: flip **0.526**,
  accuracy 0.517 (held vs clean), pred-up 0.537, nonflip 0.510. Edges sealed
  silence-escape on flip (~+3.5 pts on this world).
- **Bake status:** active experimental real-data TCM. **Not** a Wave XI
  foundation replacement. **Not** a regime-generality claim (no Weather
  harness; synthetic adversarial identity of Wave XI unchanged).
- confirmation8 is spent; do not retune on it.
- Synthetic adversarial boss (`benchmarks/aci_boss/`, Wave XI seeds
  `15300`–`15303`, sealed defaults): **FAIL** — fresh acc 0.960 vs Wave XI
  0.986 (−2.6 pts), changed-fact 0.929 vs 0.966 (−3.7 pts); also below fair
  graph on both. See
  [`REPORT_BOSS.md`](../benchmarks/aci_boss/REPORT_BOSS.md).
- Clean Weather bed (`benchmarks/realdata_weather/`): Open-Meteo
  `previous_day1` + ERA5 adjacent-day warmer; weekly-median banned.
  - Wrong yardstick (gate vs Wave XI) on first bed: **FAIL** — see
    [`REPORT_WEATHER_ACI_CONFIRMATION.md`](../benchmarks/realdata_weather/REPORT_WEATHER_ACI_CONFIRMATION.md).
  - Architecture-under-test look (sealed ACI vs persistence / majority /
    silence lineage) on virgin `confirmation2`: **PASS** — flip **0.733**
    (≥ silence 0.663; ≥0.45; acc vs persistence held). See
    [`REPORT_WEATHER_ARCHITECTURE_CONFIRMATION.md`](../benchmarks/realdata_weather/REPORT_WEATHER_ARCHITECTURE_CONFIRMATION.md).
  - Aware package (`AwareCoalitionCellular` + Mnemosheath) on virgin
    `confirmation3`: **PASS** — flip **0.868** vs sealed ACI **0.771**
    (+9.7 pts, p≈0); also clears silence / persistence / pred-up / nonflip
    gates. See
    [`REPORT_WEATHER_AWARE_CONFIRMATION.md`](../benchmarks/realdata_weather/REPORT_WEATHER_AWARE_CONFIRMATION.md).
    confirmation3 is spent; do not retune on it.
  New bed, not recovered sandbox Weather final. Wave XI remains synthetic
  reference only for real-data architecture claims.

### 19. Truth-discovery literature yardstick (Stock + Weather)
Reviewers from the truth-discovery field demand that field’s methods on the
canonical multi-source Stock/Weather fusion beds:

- **TruthFinder** (Yin et al. 2008), **CRH** (Li et al. 2014), **CATD**
  (Li et al. 2015), plus a streaming TD variant
- Efficiency (wall/CPU/activation), not accuracy alone

Harness: [`benchmarks/truth_discovery/`](../benchmarks/truth_discovery/)
(Luna Dong public dumps; slim scored tables committed). First look:
majority/TruthFinder are extremely strong where sources already agree with
gold; Aware is **not** ahead on Stock binary `last>prev` (acc 0.872 vs TD
majority 0.999 / Wave XI 0.990) and is slower wall-clock than ACI/Wave XI
while remaining activation-sparser. See
[`REPORT.md`](../benchmarks/truth_discovery/REPORT.md).

### 20. Causal delayed-feedback source aggregation — DBSA-v1 pilot failed
The coherent task is not static truth discovery: given named reports at time
`t`, predict before a delayed label arrives, then adapt through source drift
and dependence. DBSA-v1 gives every method the same packets and 14-event
feedback delay across independent, copied, drift, recurring-crossover,
adversarial, and missingness worlds.

First sealed pilot (24 fixed seeds × 800 events): **FAIL** for Aware. A
fading causal per-source Beta reliability filter wins Brier in every
nontrivial drift world; Aware fails its Fixed-Share non-inferiority and
post-shift recovery gates. It remains sparse downstream (about five of 12
reports activated) but is slower. No DBSA parameter retune follows the first
look. See [`REPORT_PILOT.md`](../benchmarks/dbsa/REPORT_PILOT.md).

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
