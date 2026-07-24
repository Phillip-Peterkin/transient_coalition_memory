"""Gross-bug tests for ROPL (CONSENSUS_COMBINED_LEAVE)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(REPO / "src"))

from baselines import Majority  # noqa: E402
from contract_simulator import generate  # noqa: E402
from evaluate import (  # noqa: E402
    AWARE_ROPL_PARAMS,
    CELL_PARAMS,
    ROPL_PARAMS,
    run_model,
)
from tcm import AwareCoalitionCellular  # noqa: E402


def _ropl(**extra):
    return AwareCoalitionCellular(**{**CELL_PARAMS, **AWARE_ROPL_PARAMS, **extra})


def test_ropl_knobs_locked():
    assert ROPL_PARAMS["ropl_enabled"] is True
    assert ROPL_PARAMS["ropl_g_mode"] == "covvar"
    assert ROPL_PARAMS["rebate_window"] == 120
    assert ROPL_PARAMS["rebate_min_updates"] == 40
    assert ROPL_PARAMS["pool_restore_enabled"] is False
    assert AWARE_ROPL_PARAMS["essc_enabled"] is True


def test_ropl_rejects_pool_restore_combo():
    with pytest.raises(ValueError, match="mutually exclusive"):
        AwareCoalitionCellular(
            **CELL_PARAMS,
            essc_enabled=True,
            ropl_enabled=True,
            pool_restore_enabled=True,
        )


def test_cold_start_g_zero_emits_majority():
    cell = _ropl()
    reports = [("a", 0, 1), ("b", 0, 1), ("c", 0, 0), ("d", 0, 1)]
    p, tr = cell.predict(("k", 0), reports, t=0)
    ro = tr["awareness"]["ropl"]
    assert ro["cold_start"] is True
    assert abs(ro["ropl_g"]) < 1e-12
    assert abs(p - ro["p_maj"]) < 1e-12
    assert abs(ro["p_maj"] - 0.75) < 1e-12
    # Honest used = full roster when g < 1.
    assert tr["used"] == len(reports)


def test_no_christmas_bow_under_ropl():
    cell = _ropl()
    reports = [("a", 0, 1), ("b", 0, 1), ("c", 0, 1)]
    for _ in range(15):
        _, tr = cell.predict(("k", 0), reports, t=0)
        cell.feedback(
            {"key": ("k", 0), "truth": 1, "reports": reports, "trace": tr, "time": 1}
        )
    _, tr = cell.predict(("k", 0), reports, t=50)
    assert tr["awareness"]["awareness_sharpness_applied"] is False
    assert tr["awareness"].get("christmas_bow_off") is True


def test_rebate_tracks_internal_not_emitted_shrink():
    """Gross-bug: Cov/Var must track coalition leave, not shrunk emit."""
    cell = _ropl(rebate_min_updates=5, rebate_window=50)
    key = ("k", 0)
    for t in range(60):
        truth = t % 2
        reports = [(f"s{i}", 0, truth) for i in range(4)]
        p, tr = cell.predict(key, reports, t=t)
        ro = tr["awareness"]["ropl"]
        assert "p_internal" in ro
        # Emitted is a shrink toward maj (unless g=1).
        if ro["ropl_g"] < 1.0 - 1e-12:
            assert tr["used"] == len(reports)
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
    assert 0.0 <= cell._last_ropl_g <= 1.0


def test_rebate_updates_only_after_delay_release():
    events = generate("independent_stable", seed=11, rounds=15)[:14]
    cell = _ropl()
    result = run_model(events, cell)
    assert result["model_stats"]["rebate_updates"] == 0


def test_ropl_g_clipped_to_unit_interval():
    cell = _ropl(rebate_min_updates=5, rebate_window=40)
    key = ("k", 0)
    for t in range(80):
        # Alternating truth with mixed votes → noisy leave direction.
        truth = 1 if (t // 3) % 2 == 0 else 0
        reports = [
            ("a", 0, truth),
            ("b", 0, truth),
            ("c", 0, 1 - truth),
            ("d", 0, truth),
        ]
        _, tr = cell.predict(key, reports, t=t)
        g = tr["awareness"]["ropl"]["ropl_g"]
        assert 0.0 <= g <= 1.0
        cell.feedback(
            {
                "key": key,
                "truth": truth,
                "reports": reports,
                "trace": tr,
                "time": t + 1,
            }
        )


def test_ropl_near_or_under_majority_on_correlated_stable():
    """ROPL should not regress like always-leave ESSC (+0.02) on this niche."""
    events = generate("correlated_stable", seed=3, rounds=200)
    ropl = run_model(events, _ropl())
    maj = run_model(events, Majority())
    # Soft bound: continuous shrink should stay near maj, not ESSC's tax.
    assert ropl["brier"] < maj["brier"] + 0.012
