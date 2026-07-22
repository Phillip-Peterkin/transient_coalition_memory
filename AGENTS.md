# Transient Coalition Memory

Research prototype: a Python (>=3.10) package plus a set of frozen benchmark
scripts. No services/servers — everything runs as one-shot CLI scripts.

**North star (read before proposing cures):** [`docs/NORTH_STAR.md`](docs/NORTH_STAR.md)
— long-term vision (General Dynamic Memory Architecture / living populations),
canonical vision PDF, real-data weakness ledger, and anti-scope-creep rules.
Do not start mechanism work from chat alone without checking that file.

## Cursor Cloud specific instructions

Dependencies live in a virtualenv at `.venv` (created by the startup update
script, which also runs `pip install -e .` so the `tcm` package is importable).
Use `.venv/bin/python` / `.venv/bin/pytest`.

### How to run things
- Tests: `.venv/bin/pytest` (config in `pyproject.toml`).
- Public API demo: `import tcm` exposes the frozen `BatchedReserveCellular`
  (TCM) and `FairProvGraph` (baseline) reference classes. See `README.md`
  "Quick start" and `docs/REPRODUCIBILITY.md` for the documented commands.
- Calibration probe: `benchmarks/wave12/calibration_probe.py`.
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
