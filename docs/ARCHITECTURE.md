# Architecture

TCM treats memory as a persistent adaptive substrate rather than a collection of retrieved records.

For the long-term vision, real-data honesty ledger, and anti-scope-creep rules, see [`NORTH_STAR.md`](NORTH_STAR.md). Canonical program writeup: [`TCM_Vision_and_Technical_Report.pdf`](TCM_Vision_and_Technical_Report.pdf).

## Inference

For each question, candidate reports are scored using direct evidence, fast claim state, slow claim state, and source reliability. The strongest candidates are recruited one at a time into a temporary coalition.

Recruitment is adaptive. Contradiction, disagreement between fast and slow memory, volatility, and time since feedback increase the amount of evidence required. Recruitment stops when the current decision is certified against the compressed dormant reserve or when the budget is exhausted.

## Dormant reserve

Evidence that is not activated is summarized as positive and negative coalition mass. This reserve is used to test whether omitted evidence could change the answer. It is also retained as a shadow eligibility signal for delayed learning.

## Learning

Feedback updates fast and slow claim states and source priors. Active evidence receives eligibility-weighted updates. Dormant evidence receives compressed aggregate updates, allowing the system to learn from information that was available but unnecessary for the immediate decision.

## Exact batching

Wave XI replaces repeated scalar recurrences inside each answer coalition with their exact closed-form equivalent. This reduces writes without changing the mathematical update sequence.

## Calibration

Wave XII evaluates temperature, Platt, and isotonic post-hoc calibration. The substrate, gate, and learning rules remain locked. Temperature scaling improves probability reliability without altering the binary decisions. This calibration advantage has been regime-dependent in later sandbox work (strong on synthetic/stock; weaker on weather) — see [`NORTH_STAR.md`](NORTH_STAR.md) item 9.

## Known architectural failure modes (not yet cured in this repo)

These are mechanism-level findings from real-data sandbox contact **ahead of** the frozen Wave XI code here. They are recorded so architecture descriptions stay honest across conversations:

1. **Self-sealing attractor (change detection).** Claim anchor can dominate report strength → fresh opposing evidence is shrunk → anchor-confirming reports recruit first → confident anchor lowers hazard → shallower recruitment → anchor protected. Core of the flip-detection failure.
2. **Confirmation-biased recruitment.** Ranking by `|strength|` includes the claim anchor, so gathering is not prior-neutral.
3. **Static memory-vs-world exchange rate.** Anchor weights / floors are hard-coded constants. Adversarial/noisy-source regimes reward strong anchors; trustworthy-source regimes punish them. Root of regime specialization.
4. **Independence assumption.** Recruitment counts, certificates, and op accounting treat reports as independent; block-correlated real evidence (e.g. stock sources agreeing ~91% within a day) breaks the sparse-coalition premise.
5. **Reserve truncation (pre-Wave-XV sandbox).** In dense-report worlds, reports beyond `max_k` could influence nothing — decision, certificate, or reserve learning — silently capping the "compressed dormant reserve."

Cure priority for future work (see fidelity rules in [`NORTH_STAR.md`](NORTH_STAR.md)): items 2–5 of the weakness ledger (attractor, biased recruitment, static exchange rate, regime specialization) before new surface features.

Real-data reproduction of the flip failure (locked Wave XI, no cures): [`../benchmarks/realdata_finance/REPORT.md`](../benchmarks/realdata_finance/REPORT.md).
