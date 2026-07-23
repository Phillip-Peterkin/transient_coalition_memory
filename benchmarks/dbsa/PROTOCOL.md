# DBSA-v1 — causal delayed-feedback source aggregation (contract rebuild)

Written before any contract-simulator sealed scores.

The first pilot under `simulator.py` is **exploratory only**
(`REPORT_PILOT.md`). It is **not** a leadership result. DBSA-v1 sealed
scoring uses only the declarative contract + `contract_simulator.py`.

## Task

At decision time `t`, every method receives the same packet:

```text
(item_key, named binary reports available at t, t)
```

It must emit `P(truth=1)` immediately. Labels enter a shared feedback queue
and are released only at the packet’s declared `due_t`. No method may use a
label before release, fit on a future window, or read hidden
source/block/regime fields.

This is **causal delayed-feedback source aggregation under regime drift and
source dependence**. Static TruthFinder / CRH / CATD whole-dataset inference
is appendix-only.

## Metric hierarchy (one leaderboard)

1. **Primary (headline):** prequential **Brier** loss
2. **Gates (must clear):** flip recall, change false-alarm rate, calibration
   (ECE), post-shift Brier recovery
3. **Frontier axes (not hard thresholds):** wall/CPU/peak memory, reports
   inspected, downstream reports activated

Resources are Pareto axes. There is **no** arbitrary “≤4 of 6 sources”
activation gate. Downstream activation is reported honestly: ACI/Aware inspect
every supplied report before selecting active ones.

## Non-inferiority margin (locked)

Against the primary causal expert baseline (delayed Fixed-Share Hedge):

- Margin **δ = 0.005** Brier
- Aware is Brier-non-inferior in a world only if the one-sided 97.5%
  paired-seed bootstrap CI **upper bound** on
  `(Aware Brier − FixedShare Brier)` is **≤ 0.005**

Raw mean gaps without a CI are not enough.

## Delay policy for expert baselines (locked)

Fixed-Share (and any later AdaHedge / Squint row) **assumes immediate losses
in the textbook form**. Under DBSA delays they:

1. predict at `t` using current weights only
2. enqueue the packet
3. **update weights only when the shared queue releases the label at `due_t`**

They are not given same-step oracle losses. This is the BOLD-style
queue-release adaptation, declared so the strongest expert baseline is not
accidentally hobbled or secretly advantaged.

## Simulator contract

Worlds live in `contract/v1_worlds.json`. Declared parameters only:

- `copy_graph` (source copying edges + probabilities)
- `accuracy_schedule` (drift / crossover / adversarial windows)
- `feedback_delay` (`fixed` or `geometric` distributions)
- `availability` (default presence + burst missingness)
- `source_blocks`, `n_items`, `n_sources`, `truth_flip_rate`

`contract_simulator.py` interprets that JSON. It must not import `tcm`.
The legacy `simulator.py` is frozen as the exploratory generator that produced
`REPORT_PILOT.md` and is **not** used for sealed DBSA-v1 scores.

Six preregistered worlds (same names as exploratory pilot):

1. `independent_stable`
2. `correlated_stable`
3. `abrupt_drift`
4. `recurring_crossover`
5. `adversarial_switch`
6. `bursty_missing`

v1 sealed delay: `{"type":"fixed","events":14}` in every world. Geometric
delay is supported by the contract schema for later stress lanes.

## Causal leaderboard rows

Same reports and delayed labels for all:

1. Persistence
2. Equal-weight majority
3. Delayed Fixed-Share Hedge (queue-release updates)
4. Fading online source-reliability Bayes
5. Agreement-discounted fading Bayes
6. Sealed `ActiveExperimentalCellular` (ACI)
7. `AwareCoalitionCellular`

## Sealed screening gate (contract rebuild)

`evaluate.py --seeds 24 --rounds 800` after this protocol is a screening run,
not cross-domain leadership.

Aware is screening-promising only if **all** hold:

1. Brier non-inferior to Fixed-Share under **δ = 0.005** CI rule in every world
2. Lower mean post-shift Brier than Fixed-Share in `abrupt_drift` and
   `adversarial_switch`
3. Flip-recall and change-FAR are reported (no retune if they degrade)

Failure is recorded without retuning DBSA-v1 parameters or ACI/Aware knobs.

Leadership still requires the 200-seed contract run **and** the prospective
weather lane (`prospective_weather/`) before any regime-general claim.

## Prospective weather lane

Started under `prospective_weather/`: append-only, timestamped, daily-hashed
collection of six NWP sources on an immutable station roster disjoint from
spent Weather beds. Scoring that lane is forbidden until the collection
protocol’s sealed look is declared separately.
