# Transient Coalition Memory

Research prototype: a Python (>=3.10) package plus a set of frozen benchmark
scripts. No services/servers — everything runs as one-shot CLI scripts.

## Read first (transparency across conversations)

| Doc | Why |
|---|---|
| [`docs/NORTH_STAR.md`](docs/NORTH_STAR.md) | Long-term vision (General Dynamic Memory Architecture / living populations), canonical vision PDF pointer, **complete real-data weakness ledger**, anti-scope-creep rules. **Mandatory before proposing cures.** |
| [`docs/TCM_Vision_and_Technical_Report.pdf`](docs/TCM_Vision_and_Technical_Report.pdf) | What the research program currently is (Waves IV–XVI). |
| [`README.md`](README.md) | Public summary: synthetic results + scientific-status honesty. |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Frozen mechanisms + known architectural failure modes. |
| [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) | Exact run commands and `main`-branch `/mnt/data` gotchas. |

Do not start mechanism work from chat alone without checking `docs/NORTH_STAR.md`.
Prefer curing ledger items 2–5 (self-sealing attractor, confirmation-biased
recruitment, static exchange rate, regime specialization) over new surface
features. Do not rewrite archival `benchmarks/wave*/REPORT.md` files.

Active real-data entrypoint: `benchmarks/realdata_finance/` (download + evaluate).
Treat its chronological `holdout` split as confirmatory for locked weights only.

## Cursor Cloud specific instructions

Dependencies live in a virtualenv at `.venv` (created by the startup update
script, which also runs `pip install -e .` so the `tcm` package is importable).
Use `.venv/bin/python` / `.venv/bin/pytest`.

### How to run things
- Tests: `.venv/bin/pytest` (config in `pyproject.toml`).
- Public API: `import tcm` exposes frozen `BatchedReserveCellular` (TCM) and
  `FairProvGraph` (baseline). See `README.md` and `docs/REPRODUCIBILITY.md`.
- Calibration probe: `benchmarks/wave12/calibration_probe.py` (needs `PYTHONPATH`
  below on `main`).
- Wall-clock benchmark: `benchmarks/runtime/wall_clock_benchmark.py`
  (writes into `benchmarks/runtime/results/`, which is untracked).

### Non-obvious gotcha: `/mnt/data` paths on `main`
The raw historical wave scripts (`benchmarks/wave4`..`wave11`) hardcode
`/mnt/data` for BOTH their cross-wave imports and their output dirs — this is
leftover from the original code-interpreter sandbox and is intentional on
`main`. Consequences:
- `python benchmarks/wave11/wave11_benchmark.py` (and other wave scripts) will
  NOT run standalone on `main` (`ModuleNotFoundError: wave10_benchmark`), and
  `wave11` also tries to write to `/mnt/data/wave11`.
- The portable, rewritten versions are generated for the
  `release/v1.0-research-code` branch by
  `.github/workflows/portable-release-fix.yml`.

To run the portable entrypoints on `main`, put the wave dirs on `PYTHONPATH`
so `wave11_benchmark` (imported by the probe / wall-clock script) resolves its
cross-wave imports:
```
export PYTHONPATH="$PWD/benchmarks/wave4:$PWD/benchmarks/wave7:$PWD/benchmarks/wave9:$PWD/benchmarks/wave10:$PWD/benchmarks/wave11"
```
Importing `tcm` first also wires these paths (see `src/tcm/reference.py`), so
scripts that `import tcm` before touching the wave modules work without the
export. The checked-in `benchmarks/wave12/{results.json,summary.csv}` are
deterministic and re-running the probe reproduces them exactly.

### Lint
No linter/formatter is configured in this repo (no ruff/flake8/black/pylint).
