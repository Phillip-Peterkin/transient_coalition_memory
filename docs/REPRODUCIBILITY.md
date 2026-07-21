# Reproducibility

## Environment

Python 3.10 or newer is recommended.

```bash
pip install -r requirements.txt
```

## Reproduce the frozen reference comparison

```bash
python benchmarks/wave11/wave11_benchmark.py
```

This writes `results.json` and `summary.csv` into `benchmarks/wave11`.

## Reproduce calibration

```bash
python benchmarks/wave12/calibration_probe.py
```

This writes calibration outputs into `benchmarks/wave12`.

## Historical waves

Each historical script can be run directly from the repository root. The checked-in outputs preserve the original completed runs. Some earlier waves use larger searches and therefore take longer.

## Integrity notes

Wave XI uses two regression seeds and four fresh holdout seeds. Wave XII fits calibration only on development seeds and evaluates on untouched test seeds. Operation accounting counts scalar evidence reads and scalar state writes for both methods.
