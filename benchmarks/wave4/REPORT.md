# Wave IV Benchmark Report

## Test design

All methods received the same reports, contexts, delayed feedback, world changes, source reliability reversals, and stale misinformation. Hyperparameters were selected on separate development worlds and evaluated on untouched test worlds.

## Results

| Method | Overall accuracy | Changed-fact accuracy | Brier score | Operations per correct | Memory states |
|---|---:|---:|---:|---:|---:|
| majority | 0.969 | 0.867 | 0.103 | 12.4 | 1008 |
| bayes_source | 0.957 | 0.873 | 0.035 | 12.5 | 72 |
| dynamic_bayes | 0.967 | 0.931 | 0.027 | 12.4 | 72 |
| ewma_evidence | 0.962 | 0.936 | 0.030 | 12.5 | 36 |
| provenance_graph | 0.975 | 0.955 | 0.018 | 24.6 | 180 |
| cellular_causal | 0.973 | 0.921 | 0.027 | 37.0 | 3780 |
| cellular_adaptive | 0.977 | 0.933 | 0.023 | 26.7 | 4068 |

## Main finding

The tuned provenance graph remained the strongest method for changed facts and calibration. The adaptive cellular repair exceeded every other baseline in overall accuracy, but did not surpass the provenance graph on adaptation efficiency. Therefore no superiority claim is justified.

## Mechanism accounting

- Majority vote succeeded through redundancy and recent-window smoothing.
- Static Bayesian source updating succeeded through accumulated source-context reliability, but adapted slowly after reversals.
- Dynamic Bayesian updating and exponentially weighted evidence succeeded through controlled forgetting.
- The provenance graph succeeded by retaining explicit source-context weights and aggressively updating claim nodes after delayed outcomes.
- The cellular system succeeded through claim-specific fast memory, slower lineage memory, causal eligibility traces, and recruitment that expanded under unresolved contradiction.

## Cellular component test

| Condition | Overall accuracy | Changed-fact accuracy | Operations per correct |
|---|---:|---:|---:|
| full | 0.975 | 0.934 | 26.8 |
| no_path | 0.975 | 0.934 | 26.8 |
| no_fast_claim | 0.898 | 0.687 | 29.6 |
| fixed_full_recruitment | 0.975 | 0.934 | 36.9 |
| weak_claim_specific | 0.978 | 0.937 | 26.8 |

The component test indicates that fast claim-specific memory is essential. Removing it causes the largest collapse. Exact path weighting provides a smaller contribution. Adaptive recruitment saves computation, but full recruitment can sometimes improve accuracy at additional cost.

## Next repair

The provenance graph's advantage comes from explicit claim nodes that remain cleanly addressable. The cellular system still distributes claim identity too broadly across path states. The next version should preserve distributed storage while introducing a compact reversible address for each active claim coalition, allowing exact delayed credit without maintaining a conventional full graph.
