# DBSA-v1 — causal delayed-feedback source aggregation

Written before any DBSA-v1 scores.

## Task

At decision time `t`, every method receives the same packet:

```text
(item_key, named binary reports available at t, t)
```

It must emit `P(truth=1)` immediately. The true label is released only at
`t + 14` events. No method may replay a label before that release, fit on a
future window, or use the simulator's hidden source/block/regime variables.

This is **causal delayed-feedback source aggregation under regime drift and
source dependence**. It is not static truth discovery: TruthFinder, CRH, and
CATD's standard whole-dataset inference is retained only as an appendix
reference, not a DBSA competitor.

## Simulator

Each world contains:

- 24 binary items with persistent latent truth
- 12 named sources in four blocks of three
- event-time feedback delay = 14
- every available source report is passed unchanged to every method

The six preregistered worlds are:

1. `independent_stable` — independent, stationary source quality
2. `correlated_stable` — strongly copied within-block reports
3. `abrupt_drift` — high- and low-quality source groups exchange competence
4. `recurring_crossover` — source competence repeatedly switches by regime
5. `adversarial_switch` — one source block becomes anti-reliable
6. `bursty_missing` — source blocks temporarily disappear

The simulator exposes only generated `(key, reports, truth, due_time)` events
to the evaluator. Hidden mechanism annotations are used only to score
post-shift recovery after prediction.

## Causal leaderboard

All rows receive the same reports and delayed labels:

1. Persistence
2. Equal-weight majority
3. Delayed Fixed-Share Hedge
4. Fading online source-reliability Bayes
5. Agreement-discounted fading Bayes
6. Sealed `ActiveExperimentalCellular` (ACI)
7. `AwareCoalitionCellular` (ACI + Mnemosheath)

Fixed Share is the primary nonstationary expert-advice comparator. The two
Bayes rows are delayed-label online truth-aggregation comparators; the
discounted row controls for a simple report-agreement correlation correction.
No method receives a source/block identity beyond the ordinary named source
ID present in reports.

## Metrics

Primary:

- prequential Brier loss
- prequential log loss

Safety / adaptation:

- accuracy
- flip recall: `P(predicted a change | truth changed)`
- change false-alarm rate: `P(predicted a change | truth stayed)`
- Brier loss in the first 120 events after a declared regime switch

Resources:

- wall and CPU seconds
- peak `tracemalloc` memory
- raw reports inspected
- downstream reports activated / scored

`activated` is not source-acquisition cost: ACI/Aware currently inspect every
provided report to calculate its evidence score before selecting active
reports. Claims are therefore limited to downstream activation efficiency.

## First sealed run

`evaluate.py --seeds 24 --rounds 800` is the first fixed pilot. It is a
screening run, **not** a leadership claim. The leadership-scale run is 200
fixed seeds per world, with an independent prospective real lane added before
claiming cross-domain leadership.

The pilot calls Aware promising only if it is Brier non-inferior to
Fixed-Share Hedge by at most 0.002 in every world *and* has lower mean
post-shift Brier in both `abrupt_drift` and `adversarial_switch`. A failure is
recorded without retuning DBSA-v1 parameters.
