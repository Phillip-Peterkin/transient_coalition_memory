# Transient Coalition Memory

**Transient Coalition Memory (TCM)** is an experimental cellular memory architecture for streaming belief formation under contradiction, delayed feedback, and changing truth.

Instead of retrieving a permanent record, TCM recruits a temporary coalition of the most useful evidence. Dormant evidence is retained as a compressed reserve, can influence decision certification, and can receive delayed learning updates without being fully activated.

## Long-term vision vs. this repo

| | |
|---|---|
| **Dream** | A **General Dynamic Memory Architecture** — information treated like living populations, not fixed database entries. |
| **This repo today** | Frozen Wave XI reference + historical synthetic waves / calibration / wall-clock tooling. A research prototype, not the finished general architecture. |
| **Full vision writeup** | [`docs/TCM_Vision_and_Technical_Report.pdf`](docs/TCM_Vision_and_Technical_Report.pdf) |
| **North star + real-data honesty ledger** | [`docs/NORTH_STAR.md`](docs/NORTH_STAR.md) — read before proposing cures; anti-scope-creep rules live there. |

## Synthetic result (what this repo currently ships)

On fresh held-out synthetic worlds, the exact-batched TCM implementation outperformed the tuned provenance-graph baseline while activating substantially less evidence.

| Method | Accuracy | Changed-fact accuracy | Average reports activated | Operations per correct answer |
|---|---:|---:|---:|---:|
| Provenance graph | 0.9678 | 0.9521 | 12.00 | 21.00 |
| Exact-batched TCM | **0.9860** | **0.9660** | **4.05** | **9.69** |

Raw TCM was initially underconfident relative to the provenance graph. A development-fitted temperature-scaling probe reduced expected calibration error from 0.0566 to 0.0109 on untouched test worlds while preserving classification decisions.

## Scientific status (transparent)

- Strongest **shipped** evidence is synthetic (this repo). Results support continued testing; they do **not** establish independent validation or superiority on real-world memory tasks.
- Sandbox contact with real data (stock, weather) — **ahead of what is frozen here** — exposed a regime boundary: TCM is strong in adversarial/noisy-source regimes and weak (often worst) in trustworthy-source, fast-crossing regimes. Flip detection, not headline accuracy, is the core failure. See the complete ledger in [`docs/NORTH_STAR.md`](docs/NORTH_STAR.md).
- In-repo finance/news harness ([`benchmarks/realdata_finance/`](benchmarks/realdata_finance/)): locked Wave XI on a 2022–2023 multi-publisher news → next-day direction stream again shows weak flip detection (~0.18 holdout) despite a small accuracy edge over persistence. Persistence is ~50% here (not the old stock artifact).
- Headline accuracy on persistence-heavy real data can look like a win while mostly reflecting a "same as yesterday" prior. Any claim must report persistence-oracle and flip-detection decompositions.

**Formal title:** *Transient Coalition Memory: A Cellular Architecture for Sparse, Certified Belief Formation*

Author: Phillip Peterkin

## Documentation map

| Doc | Purpose |
|---|---|
| [`docs/NORTH_STAR.md`](docs/NORTH_STAR.md) | Vision, current state, real-data weakness ledger, anti-scope-creep rules |
| [`docs/TCM_Vision_and_Technical_Report.pdf`](docs/TCM_Vision_and_Technical_Report.pdf) | Canonical Vision & Technical Report (Waves IV–XVI) |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Mechanisms in the frozen reference + known architectural failure modes |
| [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) | Exact run instructions, including `main`-branch path gotchas |
| [`AGENTS.md`](AGENTS.md) | Cursor Cloud / agent operating notes |
| [`benchmarks/runtime/README.md`](benchmarks/runtime/README.md) | Wall-clock benchmark |
| [`benchmarks/realdata_finance/`](benchmarks/realdata_finance/) | Finance/news real-data harness (active) |
| `benchmarks/wave*/REPORT.md` | Frozen historical wave reports (archival; do not rewrite) |

## Repository structure

- `benchmarks/wave4` through `benchmarks/wave12` preserve the experimental history, reports, raw results, and summaries.
- `src/tcm` exposes the frozen Wave XI reference classes (`BatchedReserveCellular`, `FairProvGraph`).
- `tests/` contains lightweight invariance tests.

## Quick start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
pip install -e .          # makes `import tcm` work
pytest
```

Reproduce the frozen synthetic comparison and calibration (details and `main`-branch path notes in [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md)):

```bash
# Required on `main` so historical wave scripts resolve each other:
export PYTHONPATH="$PWD/benchmarks/wave4:$PWD/benchmarks/wave7:$PWD/benchmarks/wave9:$PWD/benchmarks/wave10:$PWD/benchmarks/wave11"
python benchmarks/wave12/calibration_probe.py
python benchmarks/runtime/wall_clock_benchmark.py
```

> **Gotcha on `main`:** raw `benchmarks/wave4`..`wave11` scripts hardcode `/mnt/data` for imports and outputs (original code-interpreter sandbox). They do **not** run standalone. Portable rewrites are produced for `release/v1.0-research-code` by `.github/workflows/portable-release-fix.yml`. Prefer the `tcm` package, the calibration probe, and the wall-clock script as above.
