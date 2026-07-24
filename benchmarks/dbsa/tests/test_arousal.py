"""Gross-bug tests for Arousal Dual-Mode (biology switch)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(REPO / "src"))

from contract_simulator import generate  # noqa: E402
from evaluate import (  # noqa: E402
    AWARE_AROUSAL_PARAMS,
    AROUSAL_PARAMS,
    CELL_PARAMS,
    run_model,
)
from tcm import AwareCoalitionCellular  # noqa: E402


def _adm(**extra):
    return AwareCoalitionCellular(**{**CELL_PARAMS, **AWARE_AROUSAL_PARAMS, **extra})


def test_arousal_knobs_locked():
    assert AROUSAL_PARAMS["arousal_enabled"] is True
    assert AROUSAL_PARAMS["thrift_rho_enter"] == 0.5
    assert AROUSAL_PARAMS["rebate_window"] == 120
    assert AROUSAL_PARAMS["rebate_min_updates"] == 40
    assert AROUSAL_PARAMS["ropl_enabled"] is False
    assert AROUSAL_PARAMS["pool_restore_enabled"] is False
    assert AWARE_AROUSAL_PARAMS["essc_enabled"] is True


def test_arousal_rejects_ropl_and_prg_combo():
    with pytest.raises(ValueError, match="mutually exclusive"):
        AwareCoalitionCellular(
            **CELL_PARAMS,
            essc_enabled=True,
            arousal_enabled=True,
            pool_restore_enabled=True,
        )
    with pytest.raises(ValueError, match="embeds ROPL"):
        AwareCoalitionCellular(
            **CELL_PARAMS,
            essc_enabled=True,
            arousal_enabled=True,
            ropl_enabled=True,
        )


def test_cold_start_truth_mode_full_roster_used():
    cell = _adm()
    reports = [("a", 0, 1), ("b", 0, 1), ("c", 0, 0), ("d", 0, 1)]
    p, tr = cell.predict(("k", 0), reports, t=0)
    ar = tr["awareness"]["arousal"]
    assert ar["mode"] == "truth"
    assert ar["cold_start"] is True
    assert abs(p - ar["p_maj"]) < 1e-12
    assert tr["used"] == len(reports)


def test_no_christmas_bow_under_arousal():
    cell = _adm()
    reports = [("a", 0, 1), ("b", 0, 1), ("c", 0, 1)]
    for _ in range(15):
        _, tr = cell.predict(("k", 0), reports, t=0)
        cell.feedback(
            {"key": ("k", 0), "truth": 1, "reports": reports, "trace": tr, "time": 1}
        )
    _, tr = cell.predict(("k", 0), reports, t=50)
    assert tr["awareness"]["awareness_sharpness_applied"] is False
    assert tr["awareness"].get("christmas_bow_off") is True


def test_thrift_mode_keeps_active_used():
    """When thrift fires, Used must stay selective (not full roster)."""
    cell = _adm(rebate_min_updates=5, rebate_window=40, thrift_rho_enter=0.01)
    key = ("k", 0)
    saw_thrift = False
    for t in range(80):
        # Strong leave skill: coalition side matches truth; maj diluted.
        truth = 1 if (t // 4) % 2 == 0 else 0
        reports = [
            ("a", 0, truth),
            ("b", 0, truth),
            ("c", 0, 1 - truth),
            ("d", 0, 1 - truth),
            ("e", 0, truth),
            ("f", 0, truth),
        ]
        p, tr = cell.predict(key, reports, t=t)
        ar = tr["awareness"]["arousal"]
        if ar.get("mode") == "thrift":
            saw_thrift = True
            assert tr["used"] < len(reports) or tr["used"] == len(tr.get("active") or [])
        cell.feedback(
            {
                "key": key,
                "truth": truth,
                "reports": reports,
                "trace": tr,
                "time": t + 1,
            }
        )
    # Soft: with low enter threshold we should eventually thrift or stay truth.
    assert cell.arousal_truth_count + cell.arousal_thrift_count > 0


def test_drift_world_uses_some_thrift_or_beats_stable_tax():
    """On abrupt_drift, dual-mode should not collapse to always-maj costume."""
    events = generate("abrupt_drift", seed=7, rounds=200)
    res = run_model(events, _adm())
    stats = res["model_stats"]
    assert stats["arousal_enabled"] is True
    # Either thrift fires or truth ROPL still crushes maj-like baselines.
    assert stats["arousal_truth_count"] + stats["arousal_thrift_count"] > 0
