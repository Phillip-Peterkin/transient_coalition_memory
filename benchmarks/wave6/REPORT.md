# Wave VI — Event-Driven Routing Repair

## Objective
Replace repeated distributed hashing and full microscopic reads with persistent local routes. A route is created once, keeps fixed microscopic links, and exposes a cached local potential when activated. Delayed feedback replays the temporary route address rather than reconstructing it.

## Test discipline
- Three development worlds selected one of three cellular parameter packages.
- Eight fresh holdout worlds (9300–9307) were used for the primary result.
- Eight older Wave V worlds (7100–7107) were retained only as a regression set.
- Traditional baselines used their competent tuned configurations rather than intentionally weak versions.

## Fresh holdout result
| Method | Overall accuracy | Changed-fact accuracy | Brier | ECE | False certainty | Ops/correct |
|---|---:|---:|---:|---:|---:|---:|
| Dynamic Bayes | 96.67% | 93.26% | 0.0277 | 0.0087 | 0.79% | 12.4 |
| EWMA evidence | 96.12% | 93.89% | 0.0301 | 0.0151 | 1.44% | 12.5 |
| Provenance graph | 96.81% | **95.02%** | **0.0231** | **0.0088** | 0.50% | **24.8** |
| Event-routed cellular | 94.42% | 85.15% | 0.0791 | 0.1663 | **0.60%** | 114.7 |

## What improved
Wave V required about 410.9 counted operations per correct answer. Wave VI requires 114.7, a reduction of about 72.1%. Persistent routing therefore removed most of the addressing overhead.

## What failed
Accuracy fell. Changed-fact accuracy is 85.15%, compared with 95.02% for the provenance graph. The local route cache stopped propagating every microscopic cell change into all overlapping routes. This gained speed but weakened distributed interference and cross-coalition transfer.

## Causal ablation
| Variant | Overall accuracy | Changed-fact accuracy | Ops/correct |
|---|---:|---:|---:|
| Full event-routed system | 94.42% | 85.15% | 114.7 |
| No exact path channel | 94.05% | **85.33%** | 85.7 |

The path channel is now harmful on the fresh holdout: removing it improves changed-fact accuracy by 0.19 percentage points. That means the Wave V causal-path gain did not generalize once routing changed. The exact path memory is over-specializing to source-context-report combinations and preserving stale pathways after world changes.

## Interpretation
The efficiency repair is real, but it exposed a deeper design error. Exact path credit should not be a permanent accumulating memory channel. It should be a short-lived eligibility mechanism that transfers learning into claim and context structure, then decays almost completely. Permanent path weights behave like episodic memorization and interfere with reversal learning.

## Next repair
1. Convert path weights into rapidly decaying eligibility-only traces.
2. Transfer delayed credit into claim/context cells rather than retaining strong path state.
3. Reconcile overlapping routes lazily when activated, using a small sampled neighborhood rather than global reverse propagation.
4. Add online calibration on development feedback without changing decision labels.
5. Test under equal-operation budgets against the graph.

## Honest conclusion
Wave VI achieved a major efficiency gain but lost predictive quality. It does not beat the provenance graph. More importantly, the paired fresh ablation falsified the current permanent path-memory design. The next version should keep exact causal addresses for credit assignment while removing long-lived path beliefs.
