# Transient Coalition Memory

**Transient Coalition Memory (TCM)** is an experimental cellular memory architecture for streaming belief formation under contradiction, delayed feedback, and changing truth.

Instead of retrieving a permanent record, TCM recruits a temporary coalition of the most useful evidence. Dormant evidence is retained as a compressed reserve, can influence decision certification, and can receive delayed learning updates without being fully activated.

## Current result

On fresh held-out synthetic worlds, the exact-batched TCM implementation outperformed the tuned provenance-graph baseline while activating substantially less evidence.

| Method | Accuracy | Changed-fact accuracy | Average reports activated | Operations per correct answer |
|---|---:|---:|---:|---:|
| Provenance graph | 0.9678 | 0.9521 | 12.00 | 21.00 |
| Exact-batched TCM | **0.9860** | **0.9660** | **4.05** | **9.69** |

Raw TCM was initially underconfident relative to the provenance graph. A development-fitted temperature-scaling probe reduced expected calibration error from 0.0566 to 0.0109 on untouched test worlds while preserving classification decisions.

## Repository structure

- `benchmarks/wave4` through `benchmarks/wave12` preserve the experimental history, reports, raw results, and summaries.
- `benchmarks/realdata_weather/` is a **clean** live Weather harness (Open-Meteo previous-run forecasts + ERA5 labels; weekly-median lookahead banned). See its `PROTOCOL.md`.
- `src/tcm` exposes the frozen Wave XI reference classes.
- `docs/ARCHITECTURE.md` explains the mechanisms.
- `docs/REPRODUCIBILITY.md` gives exact run instructions.
- `tests/` contains lightweight invariance tests.

## Quick start

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python benchmarks/wave11/wave11_benchmark.py
python benchmarks/wave12/calibration_probe.py
pytest
```

## Scientific status

This repository is a research prototype. Its current evidence comes from controlled synthetic environments. The results support continued testing; they do not yet establish independent validation or superiority on real-world memory tasks.

**Formal title:** *Transient Coalition Memory: A Cellular Architecture for Sparse, Certified Belief Formation*

Author: Phillip Peterkin
