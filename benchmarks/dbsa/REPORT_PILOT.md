# Exploratory causal aggregation pilot — FAIL (not sealed DBSA-v1)

**Status: exploratory diagnostic only.** This run used the legacy
`simulator.py` before the declarative contract rebuild. It is **not** the
DBSA-v1 sealed leadership / screening result. See rebuilt
[`PROTOCOL.md`](PROTOCOL.md) and `contract_simulator.py`.

Run: 24 fixed seeds × 800 events × six worlds  
Feedback: label release exactly 14 events after prediction  
Candidate: `AwareCoalitionCellular` (sealed ACI defaults + Mnemosheath)

Every method saw the same reports at decision time and only received
source-outcome feedback when its label entered the shared queue.

## Result

**`pilot_passes=False`**. No parameter change follows this result.

| world | Aware Brier | Fixed-Share Brier | Fading Bayes Brier | best causal row |
|---|---:|---:|---:|---|
| independent stable | 0.083 | 0.095 | **0.028** | Fading Bayes |
| correlated stable | 0.185 | 0.126 | 0.103 | **Majority (0.100)** |
| abrupt drift | 0.129 | 0.045 | **0.021** | Fading Bayes |
| recurring crossover | 0.132 | 0.062 | **0.045** | Fading Bayes |
| adversarial switch | 0.092 | 0.094 | **0.026** | Fading Bayes |
| bursty missing | 0.084 | 0.106 | **0.041** | Fading Bayes |

The frozen pilot gate required Aware to stay within +0.002 Brier of
Fixed-Share in every world and improve post-shift Brier in both abrupt
worlds. It failed:

- Brier non-inferiority fails in correlated stable, abrupt drift, and recurring
  crossover.
- Post-shift Brier is worse than Fixed-Share in abrupt drift
  (**0.285 vs 0.071**) and adversarial switch (**0.300 vs 0.155**).

## Efficiency

| method | downstream activated (independent) | events/s (independent) |
|---|---:|---:|
| Majority / causal Bayes / Fixed-Share | 12.00 | 14k–92k |
| sealed ACI | 5.14 | 3,545 |
| Aware | **5.14** | 1,763 |

Aware preserves sparse downstream activation but is slower than ACI and every
simple causal comparator in this pilot. All methods inspect every supplied
report; `activated` is **not** report-acquisition cost.

## Reading

1. The new benchmark is doing its job: it separates the architecture's sparse
   selection behavior from reliable online aggregation.
2. A simple fading per-source Beta reliability filter is the strong causal
   baseline here. It uses the same delayed labels, but forgets old evidence as
   source quality changes.
3. ACI/Aware's sealed likelihood counts are cumulative; no DBSA-v1 mechanism
   makes them forget an obsolete source regime. That is a plausible cause of
   the large post-shift loss, not a proven causal diagnosis.
4. The simulator alone cannot establish leadership. The 200-seed run and an
   untouched real lane remain requirements for any positive claim; this pilot
   already blocks one.

Artifact: `results/dbsa_v1_pilot.json`.
