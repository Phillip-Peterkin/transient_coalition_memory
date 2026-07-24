"""Gross-bug and protocol tests for ESSC (ESS-Shadow Sheath Completion)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(REPO / "src"))

from baselines import Majority  # noqa: E402
from contract_simulator import generate  # noqa: E402
from evaluate import AWARE_PARAMS, CELL_PARAMS, ESSC_PARAMS, run_model  # noqa: E402
from tcm import AwareCoalitionCellular  # noqa: E402


def _essc_cell(**extra):
    params = {**CELL_PARAMS, **AWARE_PARAMS, "min_delta": 0.01, **extra}
    return AwareCoalitionCellular(**params)


def test_essc_knobs_locked_in_dbsa_aware_params():
    assert AWARE_PARAMS["essc_enabled"] is True
    assert AWARE_PARAMS["essc_disable_christmas_bow"] is True
    assert ESSC_PARAMS["essc_credit_init"] == 0.20
    assert ESSC_PARAMS["essc_max_credit"] == 0.50


def test_essc_default_off_preserves_christmas_bow_path():
    """Sealed default: ESSC off → Christmas bow can still apply."""
    cell = AwareCoalitionCellular(**{**CELL_PARAMS, "min_delta": 0.01, "essc_enabled": False})
    key = ("wx", 0)
    reports = [("a", 0, 1), ("b", 0, 1), ("c", 0, 1), ("d", 0, 1)]
    for _ in range(25):
        _, tr = cell.predict(key, reports, t=0)
        cell.feedback(
            {"key": key, "truth": 1, "reports": reports, "trace": tr, "time": 1}
        )
    _p, tr = cell.predict(key, reports, t=100)
    assert tr["awareness"]["essc"]["essc_enabled"] is False
    assert "awareness_sharpness_applied" in tr["awareness"]


def test_essc_disables_christmas_majority_blend():
    cell = _essc_cell()
    key = ("wx", 0)
    reports = [("a", 0, 1), ("b", 0, 1), ("c", 0, 1), ("d", 0, 1)]
    for _ in range(20):
        _, tr = cell.predict(key, reports, t=0)
        cell.feedback(
            {"key": key, "truth": 1, "reports": reports, "trace": tr, "time": 1}
        )
    _, tr = cell.predict(key, reports, t=50)
    assert tr["awareness"].get("christmas_bow_off") is True
    assert tr["awareness"]["awareness_sharpness_applied"] is False
    assert tr["awareness"]["agreement_blend_weight"] == 0.0


def test_essc_does_not_inflate_used_count():
    """Selective stop held: used == active size, not full roster."""
    cell = _essc_cell(max_k=8, min_k=1, fe_cert_slack=0.0)
    key = ("k", 0)
    reports = [(f"s{i}", 0, 1) for i in range(6)]
    for _ in range(40):
        _, tr = cell.predict(key, reports, t=0)
        cell.feedback(
            {"key": key, "truth": 1, "reports": reports, "trace": tr, "time": 1}
        )
    _p, tr = cell.predict(key, reports, t=100)
    assert tr["used"] < len(reports)
    assert tr["used"] == len(tr["active"])
    unread_n = tr["awareness"]["essc"].get("essc_unread_n", 0)
    if unread_n > 0:
        assert tr["used"] + unread_n <= len(reports)


def test_essc_can_oppose_majority_without_vote_blend():
    """Gross-bug: ESSC must not convex-blend toward majority vote mean."""
    cell = _essc_cell(essc_credit_init=0.50, essc_max_credit=0.50, essc_lo_cap=2.0)
    key = ("trap", 0)
    for t in range(60):
        truth = t % 2
        reports = [
            ("c0", 0, 1 - truth),
            ("c1", 0, 1 - truth),
            ("c2", 0, 1 - truth),
            ("ind", 0, truth),
        ]
        _, tr = cell.predict(key, reports, t=t)
        cell.feedback(
            {
                "key": key,
                "truth": truth,
                "reports": reports,
                "trace": tr,
                "time": t + 1,
            }
        )
    reports = [("c0", 0, 1), ("c1", 0, 1), ("c2", 0, 1), ("ind", 0, 0)]
    p, tr = cell.predict(key, reports, t=1000)
    assert tr["majority_vote"] == 1
    essc = tr["awareness"]["essc"]
    assert essc.get("christmas_bow_off") is True
    assert tr["awareness"]["agreement_blend_weight"] == 0.0
    # Not a Christmas blend identity toward vote mean 0.75.
    vote_mean = 0.75
    if essc.get("essc_applied"):
        assert abs(p - vote_mean) > 1e-9 or essc.get("essc_opposes_majority")


def test_essc_no_pwdr_residual_fields():
    cell = _essc_cell()
    _, tr = cell.predict(("k", 0), [("a", 0, 1), ("b", 0, 0)], t=0)
    blob = str(tr)
    assert "pwdr_" not in blob


def test_essc_updates_only_on_queue_release():
    events = generate("independent_stable", seed=11, rounds=15)[:14]
    cell = AwareCoalitionCellular(**{**CELL_PARAMS, **AWARE_PARAMS, "min_delta": 0.01})
    result = run_model(events, cell)
    assert result["model_stats"]["essc_gate_updates"] == 0


def test_essc_runs_on_contract_and_stays_sparse():
    events = generate("correlated_stable", seed=5, rounds=120)
    cell = AwareCoalitionCellular(**{**CELL_PARAMS, **AWARE_PARAMS})
    result = run_model(events, cell)
    maj = run_model(events, Majority())
    assert result["n"] == 120
    assert result["avg_downstream_activated"] < maj["avg_downstream_activated"]
    assert 0.0 < result["brier"] < 1.0


def test_unread_rows_match_certificate_leftovers():
    """Unread for ESSC must be ACI leftover diversified rows, not a re-pass."""
    cell = _essc_cell()
    key = ("k", 0)
    reports = [(f"s{i}", 0, 1) for i in range(5)]
    for _ in range(30):
        _, tr = cell.predict(key, reports, t=0)
        cell.feedback(
            {"key": key, "truth": 1, "reports": reports, "trace": tr, "time": 1}
        )
    _p, tr = cell.predict(key, reports, t=99)
    unread = tr.get("unread_rows") or []
    active_sources = {s for s, *_ in tr["active"]}
    for row in unread:
        assert row[2] not in active_sources
    assert tr["used"] + len(unread) <= len(reports)
