# Wall-clock benchmark

Run the frozen Wave XI comparison with randomized execution order, warm-up, repeated trials, CPU time, wall time, and peak Python allocation tracking.

On `main`, historical wave imports need the wave dirs on `PYTHONPATH` (see [`docs/REPRODUCIBILITY.md`](../../docs/REPRODUCIBILITY.md)):

```bash
export PYTHONPATH="$PWD/benchmarks/wave4:$PWD/benchmarks/wave7:$PWD/benchmarks/wave9:$PWD/benchmarks/wave10:$PWD/benchmarks/wave11"
python benchmarks/runtime/wall_clock_benchmark.py
```

Results are written to `benchmarks/runtime/results/` (untracked). Timing is machine-dependent, so publish the generated environment metadata with any reported values.

For vision / claim boundaries when interpreting timings, see [`docs/NORTH_STAR.md`](../../docs/NORTH_STAR.md).
