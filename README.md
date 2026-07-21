# Transient Coalition Memory

**Transient Coalition Memory (TCM)** is an experimental cellular memory architecture for streaming belief formation under contradiction, delayed feedback, and changing truth.

Knowledge is not stored as a permanent symbolic record. Evidence is distributed across a substrate and assembled into temporary coalitions for inference. Dormant evidence can still participate in certification and delayed learning without being fully activated.

## Version 1.0 result

On the current synthetic streaming provenance benchmark, the exact-batched cellular implementation achieved a dominant accuracy-compute frontier against a tuned provenance-graph baseline on fresh held-out seeds:

| Method | Accuracy | Changed-world accuracy | Avg. reports activated | Operations per correct |
|---|---:|---:|---:|---:|
| Provenance graph | 0.9678 | 0.9521 | 12.00 | 21.00 |
| Exact-batched TCM | **0.9860** | **0.9660** | **4.05** | **9.69** |

Raw TCM was less well calibrated than the provenance graph because it was underconfident. A separate development-fitted temperature-scaling probe reduced TCM expected calibration error from 0.0566 to 0.0109 on untouched test worlds while preserving classification decisions.

## Core mechanisms

- Distributed claim and source state
- Temporary evidence coalitions
- Sparse certified recruitment
- Compressed dormant reserve
- Delayed eligibility-based learning
- Exact closed-form coalition batching
- Post-hoc temperature calibration

## Repository layout

- `src/wave11_benchmark.py` — exact-batched reference benchmark
- `src/calibration_probe.py` — held-out calibration experiment
- `docs/ARCHITECTURE.md` — frozen Version 1.0 design
- `reports/` — benchmark and calibration reports
- `results/` — raw outputs and summaries

## Scientific status

This is a research prototype. Present evidence comes from synthetic worlds. The result is a foundation for replication, ablation, wall-clock profiling, and evaluation on external temporal-provenance datasets. It should not yet be represented as independently validated or as a general replacement for existing memory architectures.

## Formal title

**Transient Coalition Memory: A Cellular Architecture for Sparse, Certified Belief Formation**

Author: Phillip Peterkin