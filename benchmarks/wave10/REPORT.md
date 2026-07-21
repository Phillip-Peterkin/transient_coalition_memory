# Wave X — Compressed Reserve Breakthrough

## Scope

Wave X changed only the dormant-reserve mechanism. The memory architecture, fast/slow claim learning, temporary causal traces, source priors, world generator, delayed feedback, and traditional comparison remained unchanged.

The goal was to preserve the quality of fixed-k=8 cellular inference while reducing active recruitment toward 3–4 reports.

## Missing link

Wave IX kept dormant evidence eligible for learning, but inspected and updated reserve routes individually. Wave X compresses unrecruited evidence into two signed coalition sketches:

- dormant support for answer 0
- dormant support for answer 1

The gate certifies its decision against these aggregate reserve masses. Delayed feedback updates the dormant answer coalitions in aggregate rather than replaying every hidden route.

This separates:

- active evidence used for inference
- compressed dormant evidence used for certification and learning

## Fresh holdout results

| Method | Overall accuracy | Changed-fact accuracy | Brier | Avg. activated | P90 activated | Operations/correct |
|---|---:|---:|---:|---:|---:|---:|
| Provenance graph | 97.10% | 94.82% | 0.0226 | 12.00 | 12 | 24.7 |
| Fixed-k=8 cellular | 98.80% | 96.70% | 0.0151 | 8.00 | 8 | 64.8 |
| **Compressed-reserve cellular** | **98.80%** | **96.70%** | 0.0168 | **4.06** | **4** | **28.2** |
| Fixed-k=4 cellular | 98.21% | 95.66% | 0.0223 | 4.00 | 4 | 57.0 |

## Interpretation

The compressed-reserve system exactly matched fixed-k=8 cellular accuracy on the fresh holdout while activating 49.3% fewer reports.

It also beat the provenance graph by:

- 1.70 percentage points overall
- 1.88 percentage points on changed facts

The result is not explained by simply using k=4. Fixed-k=4 lost 1.04 percentage points of changed-fact accuracy compared with the compressed system at essentially the same active recruitment.

Therefore the dormant reserve is contributing useful certification and learning without becoming fully active during inference.

## Remaining limitation

Operations per correct answer are 28.2 versus 24.7 for the provenance graph. The quality/activation barrier is broken, but the cellular system has not yet beaten the graph on total counted operations. The remaining gap is narrow and concerns update implementation rather than inference quality.

## Honest conclusion

Wave X achieved the stated target: fixed-k=8 quality with roughly four active reports. This is the first result demonstrating that compressed dormant evidence can preserve high-quality adaptive learning without full evidence recruitment.
