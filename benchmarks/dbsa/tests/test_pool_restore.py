"""Gross-bug tests for Pool-Restore Gate (WHY_MAJORITY_WINS)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(REPO / "src"))

from baselines import Majority  # noqa: E402
from contract_simulator import generate  # noqa: E402
from evaluate import (  # noqa: E402
    AWARE_POOL_RESTORE_PARAMS,
    CELL_PARAMS,
    POOL_RESTORE_PARAMS,
    run_model,
)
from tcm import AwareCoalitionCellular  # noqa: E402


def _prg(**extra):
    return AwareCoalitionCellular(
        **{**CELL_PARAMS, **AWARE_POOL_RESTORE_PARAMS, **extra}
    )


def test_pool_restore_knobs_locked():
    assert POOL_RESTORE_PARAMS["rebate_threshold"] == 0.5
    assert POOL_RESTORE_PARAMS["rebate_window"] == 120
    assert POOL_RESTORE_PARAMS["rebate_min_updates"] == 40
    assert AWARE_POOL_RESTORE_PARAMS["pool_restore_enabled"] is True


def test_cold_start_emits_majority_not_sparse_leave():
    cell = _prg()
    reports = [("a", 0, 1), ("b", 0, 1), ("c", 0, 0), ("d", 0, 1)]
    p, tr = cell.predict(("k", 0), reports, t=0)
    pr = tr["awareness"]["pool_restore"]
    assert pr["emitted_majority"] is True
    assert abs(p - pr["p_maj"]) < 1e-12
    assert abs(pr["p_maj"] - 0.75) < 1e-12
    # Honest used = full roster when emitting majority.
    assert tr["used"] == len(reports)


def test_rebate_updates_only_after_delay_release():
    events = generate("independent_stable", seed=11, rounds=15)[:14]
    cell = _prg()
    result = run_model(events, cell)
    assert result["model_stats"]["rebate_updates"] == 0


def test_no_christmas_bow_under_pool_restore():
    cell = _prg()
    reports = [("a", 0, 1), ("b", 0, 1), ("c", 0, 1)]
    for _ in range(15):
        _, tr = cell.predict(("k", 0), reports, t=0)
        cell.feedback(
            {"key": ("k", 0), "truth": 1, "reports": reports, "trace": tr, "time": 1}
        )
    _, tr = cell.predict(("k", 0), reports, t=50)
    assert tr["awareness"]["awareness_sharpness_applied"] is False
    assert tr["awareness"].get("christmas_bow_off") is True


def test_rebate_uses_internal_not_emitted_when_gated():
    """Gross-bug: Cov/Var must track leave attempt, not the maj overwrite."""
    cell = _prg(rebate_min_updates=5, rebate_window=50)
    key = ("k", 0)
    for t in range(60):
        truth = t % 2
        reports = [(f"s{i}", 0, truth) for i in range(4)]
        p, tr = cell.predict(key, reports, t=t)
        pr = tr["awareness"]["pool_restore"]
        assert "p_internal" in pr
        cell.feedback(
            {
                "key": key,
                "truth": truth,
                "reports": reports,
                "trace": tr,
                "time": t + 1,
            }
        )
    assert cell.rebate_updates > 0
    # Internal path recorded even when emitting maj.
    assert cell.pool_restore_emit_maj > 0


def test_pool_restore_matches_majority_when_rebate_stays_closed():
    """On correlated_stable, rebate should usually stay ≤½ → near majority."""
    events = generate("correlated_stable", seed=3, rounds=200)
    prg = run_model(events, _prg())
    maj = run_model(events, Majority())
    # Should be close to majority (cold-start + closed rebate), not ESSC's +0.02.
    assert abs(prg["brier"] - maj["brier"]) < 0.015
    assert prg["model_stats"]["pool_restore_emit_maj"] > prg["model_stats"][
        "pool_restore_emit_leave"
    ]
