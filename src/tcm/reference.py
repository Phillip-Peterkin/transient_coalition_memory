"""Load the frozen Wave XI reference implementation without duplicating it."""

from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _wave in ("wave4", "wave7", "wave9", "wave10", "wave11"):
    _path = str(_REPO_ROOT / "benchmarks" / _wave)
    if _path not in sys.path:
        sys.path.insert(0, _path)

from wave11_benchmark import BatchedReserveCellular, FairProvGraph  # noqa: E402
