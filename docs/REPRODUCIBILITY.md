# Reproducibility

Related: [`NORTH_STAR.md`](NORTH_STAR.md) (what claims are and aren't fair to make), [`ARCHITECTURE.md`](ARCHITECTURE.md), root [`README.md`](../README.md).

## Environment

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .            # editable install so `import tcm` works
```

Use `.venv/bin/python` / `.venv/bin/pytest` if you prefer not to activate.

## `main`-branch path gotcha (important)

Historical wave scripts (`benchmarks/wave4` … `wave11`) hardcode `/mnt/data` for **both** cross-wave imports and output directories. That path came from the original code-interpreter sandbox and is intentional on `main`.

Consequences on `main`:

- `python benchmarks/wave11/wave11_benchmark.py` (and sibling wave scripts) will **not** run standalone (`ModuleNotFoundError` on earlier waves) and would try to write under `/mnt/data/...`.
- Portable, rewritten versions are generated for the `release/v1.0-research-code` branch by `.github/workflows/portable-release-fix.yml`.

Workaround for portable entrypoints on `main` — put the wave dirs on `PYTHONPATH`:

```bash
export PYTHONPATH="$PWD/benchmarks/wave4:$PWD/benchmarks/wave7:$PWD/benchmarks/wave9:$PWD/benchmarks/wave10:$PWD/benchmarks/wave11"
```

Importing `tcm` first also wires these paths (see `src/tcm/reference.py`), so scripts that import the public package before touching wave modules work without the export.

## Reproduce calibration (recommended on `main`)

```bash
export PYTHONPATH="$PWD/benchmarks/wave4:$PWD/benchmarks/wave7:$PWD/benchmarks/wave9:$PWD/benchmarks/wave10:$PWD/benchmarks/wave11"
python benchmarks/wave12/calibration_probe.py
```

Writes into `benchmarks/wave12` (repo-relative). Checked-in `results.json` / `summary.csv` are deterministic; re-running regenerates them.

## Reproduce wall-clock timing

```bash
export PYTHONPATH="$PWD/benchmarks/wave4:$PWD/benchmarks/wave7:$PWD/benchmarks/wave9:$PWD/benchmarks/wave10:$PWD/benchmarks/wave11"
python benchmarks/runtime/wall_clock_benchmark.py
```

Writes into `benchmarks/runtime/results/` (untracked; machine-dependent). See [`../benchmarks/runtime/README.md`](../benchmarks/runtime/README.md).

## Reproduce the frozen Wave XI comparison

On `main`, prefer calling `tcm.BatchedReserveCellular` / `tcm.FairProvGraph` (or the wall-clock script, which uses `wave11_benchmark.run`) rather than invoking `wave11_benchmark.py`'s `main()` — that `main()` still targets `/mnt/data/wave11` for outputs.

On `release/v1.0-research-code` (after the portable-repair workflow), the documented command is:

```bash
python benchmarks/wave11/wave11_benchmark.py
```

and it writes `results.json` / `summary.csv` into `benchmarks/wave11`.

## Public API smoke test

```bash
python -c "from tcm import BatchedReserveCellular, FairProvGraph, SensoryGatedCellular; print('ok')"
pytest
```

## Finance / news real-data harness

```bash
pip install -r benchmarks/realdata_finance/requirements.txt
python benchmarks/realdata_finance/download_data.py   # refresh cache (committed slim parquet also works offline)
python benchmarks/realdata_finance/evaluate.py
```

Protocol, splits, and non-claims: `benchmarks/realdata_finance/PROTOCOL.md`.
First locked-parameter writeup: `benchmarks/realdata_finance/REPORT.md`.

The active experimental real-data front end uses
`tcm.SensoryGatedCellular` with the title/company input gate in
`benchmarks/realdata_finance/relevance.py`. Its predeclared fresh-company
confirmation is documented in `benchmarks/realdata_finance/REPORT_RELEVANCE.md`.

## Historical waves

Each historical script and its checked-in outputs preserve the original completed run. Some earlier waves use larger searches and therefore take longer. Treat `benchmarks/wave*/REPORT.md` as archival; do not rewrite them to match later narrative.

## Integrity notes

- Wave XI uses two regression seeds and four fresh holdout seeds.
- Wave XII fits calibration only on development seeds and evaluates on untouched test seeds.
- Operation accounting counts scalar evidence reads and scalar state writes for both methods.
- Synthetic wins in this repo are **not** a claim of real-world superiority. Real-data sandbox findings (stock/weather) and required claim decompositions are in [`NORTH_STAR.md`](NORTH_STAR.md).
