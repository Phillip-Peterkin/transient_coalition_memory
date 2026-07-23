"""EXPLORATORY legacy generator — not used for sealed DBSA-v1 scores.

Kept only so `REPORT_PILOT.md` remains reproducible. Sealed evaluation must
import `contract_simulator.generate` against `contract/v1_worlds.json`.
"""

from __future__ import annotations

raise ImportError(
    "benchmarks.dbsa.simulator is the exploratory legacy generator. "
    "Use contract_simulator.generate for sealed DBSA-v1 scoring."
)
