"""Invariance tests for the active experimental ACI cell."""

from pathlib import Path
import math
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmarks" / "realdata_finance"))

from evaluate import CELL_PARAMS  # noqa: E402
from tcm import (  # noqa: E402
    ActiveCoalitionCellular,
    ActiveExperimentalCellular,
)


def approx(a: float, b: float, tol: float = 1e-6) -> bool:
    return abs(a - b) <= tol


def test_active_experimental_alias_is_aci():
    assert ActiveExperimentalCellular is ActiveCoalitionCellular
    assert ActiveCoalitionCellular.confirmed_universe == "confirmation8"


def test_sealed_defaults_match_confirmation8_freeze():
    cell = ActiveCoalitionCellular(**CELL_PARAMS)
    assert cell.min_delta == 0.15
    assert cell.max_silence_hazard == 0.55
    assert cell.null_rho_gain == 0.30
    assert cell.null_pe_floor == 0.35
    assert cell.null_pe_span == 0.50
    assert cell.null_err_beta == 0.30
    assert cell.force_all_positive_null is True
    assert cell.fe_cert_slack == 0.0
    assert cell.source_forget == 1.0
    assert cell.source_share == 0.0
    assert cell.source_shift_window == 0


def test_empty_and_cheerleader_use_null_channel():
    cell = ActiveCoalitionCellular(**CELL_PARAMS)
    key = (0, 0)
    _, tr = cell.predict(key, [], t=0)
    assert tr["stop_reason"] == "silence_channel"
    assert tr["hazard"] > 0.0

    cell.cf[(key, 1)] = 5.0
    cell.cf[(key, 0)] = -5.0
    _, tr2 = cell.predict(key, [("s1", 0, 1), ("s2", 0, 1)], t=1)
    assert tr2["stop_reason"] == "null_diagnostic"
    assert approx(tr2["evidence_lo"], 0.0)


def test_report_delta_is_prior_free_and_discriminative():
    cell = ActiveCoalitionCellular(**CELL_PARAMS)
    key = (0, 0)
    for _ in range(20):
        cell.feedback(
            {
                "key": key,
                "truth": 1,
                "reports": [("s_good", 0, 1)],
                "trace": {"p": 0.6, "prior_p": 0.5},
                "time": 1,
            }
        )
        cell.feedback(
            {
                "key": key,
                "truth": 0,
                "reports": [("s_good", 0, 0)],
                "trace": {"p": 0.4, "prior_p": 0.5},
                "time": 2,
            }
        )
    for truth in (1, 0, 1, 0, 1, 0, 1, 0):
        cell.feedback(
            {
                "key": key,
                "truth": truth,
                "reports": [("s_cheer", 0, 1)],
                "trace": {"p": 0.5, "prior_p": 0.5},
                "time": 3,
            }
        )

    d_good_up = cell._report_delta("s_good", 1)
    d_good_down = cell._report_delta("s_good", 0)
    d_cheer = cell._report_delta("s_cheer", 1)
    assert d_good_up > 0.2
    assert d_good_down < -0.2
    assert abs(d_cheer) < abs(d_good_up) / 2

    cell.cf[(key, 1)] = 9.0
    cell.cf[(key, 0)] = -9.0
    assert approx(cell._report_delta("s_good", 1), d_good_up)

    _, tr = cell.predict(
        key, [("s_good", 0, 1), ("s_cheer", 0, 1), ("s_good", 0, 0)], t=4
    )
    assert tr["stop_reason"] in {"free_energy_certified", "budget"}
    assert tr["active"][0][0] == "s_good"


def test_null_channel_hazard_mixes_toward_anti_prior():
    cell = ActiveCoalitionCellular(max_silence_hazard=0.70, **CELL_PARAMS)
    key = (0, 0)
    for _ in range(30):
        cell.feedback(
            {
                "key": key,
                "truth": 0,
                "reports": [],
                "trace": {
                    "p": 0.9,
                    "prior_p": 0.9,
                    "stop_reason": "silence_channel",
                },
                "time": 5,
            }
        )
    cell.cf[(key, 1)] = 3.0
    cell.cf[(key, 0)] = -3.0
    cell.cs[(key, 1)] = 1.0
    cell.cs[(key, 0)] = -1.0
    p, tr = cell.predict(key, [], t=6)
    assert tr["stop_reason"] == "silence_channel"
    assert tr["hazard"] > 0.3
    assert tr["prior_p"] > 0.85
    assert p < tr["prior_p"]


def test_feedback_updates_likelihood_tables():
    cell = ActiveCoalitionCellular(**CELL_PARAMS)
    key = (0, 0)
    cell.feedback(
        {
            "key": key,
            "truth": 1,
            "reports": [("z", 0, 1)],
            "trace": {
                "p": 0.6,
                "prior_p": 0.55,
                "active": [("z", 0, 1, (key, 1), 0.2)],
            },
            "time": 9,
        }
    )
    assert cell.src_vote_up[("z", 1)] > cell.laplace
    assert math.isfinite(cell.cf[(key, 1)])


def test_default_source_trust_pack_preserves_sealed_accumulation():
    cell = ActiveCoalitionCellular(**CELL_PARAMS)
    assert cell.source_forget == 1.0
    assert cell.source_share == 0.0
    assert cell.source_shift_window == 0
    key = (0, 0)
    for _ in range(10):
        cell.feedback(
            {
                "key": key,
                "truth": 1,
                "reports": [("z", 0, 1)],
                "trace": {"p": 0.6, "prior_p": 0.5, "stop_reason": "budget"},
                "time": 1,
            }
        )
    # No fading / floor / shift: 10 exact increments on top of Laplace.
    assert approx(cell.src_vote_up[("z", 1)], cell.laplace + 10.0)
    assert cell.source_shift_events == 0


def test_source_forget_lets_recent_regime_dominate():
    cell = ActiveCoalitionCellular(source_forget=0.9, **CELL_PARAMS)
    key = (0, 0)
    # Long good regime: source always right saying 1 when truth is 1.
    for step in range(40):
        cell.feedback(
            {
                "key": key,
                "truth": 1,
                "reports": [("z", 0, 1)],
                "trace": {"p": 0.7, "prior_p": 0.5, "stop_reason": "budget"},
                "time": step,
            }
        )
    good_delta = cell._report_delta("z", 1)
    # Regime flip: source now always wrong (still says 1 when truth is 0).
    for step in range(40, 80):
        cell.feedback(
            {
                "key": key,
                "truth": 0,
                "reports": [("z", 0, 1)],
                "trace": {"p": 0.7, "prior_p": 0.5, "stop_reason": "budget"},
                "time": step,
            }
        )
    flipped_delta = cell._report_delta("z", 1)
    assert good_delta > 0.2
    assert flipped_delta < 0.0


def test_source_share_keeps_escape_hatch_both_ways():
    cell = ActiveCoalitionCellular(source_forget=1.0, source_share=0.05, **CELL_PARAMS)
    key = (0, 0)
    for step in range(30):
        cell.feedback(
            {
                "key": key,
                "truth": 1,
                "reports": [("hero", 0, 1)],
                "trace": {"p": 0.7, "prior_p": 0.5, "stop_reason": "budget"},
                "time": step,
            }
        )
    # Floor mix prevents pure one-hot accumulation; opposite cell stays alive.
    assert cell.src_vote_up[("hero", 0)] > cell.laplace * 0.5
    for step in range(30, 50):
        cell.feedback(
            {
                "key": key,
                "truth": 0,
                "reports": [("hero", 0, 1)],
                "trace": {"p": 0.7, "prior_p": 0.5, "stop_reason": "budget"},
                "time": step,
            }
        )
    # After disgrace, saying 1 should no longer look strongly "up".
    assert cell._report_delta("hero", 1) < 0.5


def test_source_shift_hard_discounts_persona_change():
    cell = ActiveCoalitionCellular(
        source_forget=1.0,
        source_share=0.0,
        source_shift_window=8,
        source_shift_gap=0.30,
        source_shift_discount=0.10,
        **CELL_PARAMS,
    )
    key = (0, 0)
    for step in range(40):
        cell.feedback(
            {
                "key": key,
                "truth": 1,
                "reports": [("z", 0, 1)],
                "trace": {"p": 0.7, "prior_p": 0.5, "stop_reason": "budget"},
                "time": step,
            }
        )
    before = cell.src_vote_up[("z", 1)]
    for step in range(40, 55):
        cell.feedback(
            {
                "key": key,
                "truth": 0,
                "reports": [("z", 0, 1)],
                "trace": {"p": 0.7, "prior_p": 0.5, "stop_reason": "budget"},
                "time": step,
            }
        )
    assert cell.source_shift_events >= 1
    # Hard discount must have bitten the old good mass, not only added wrongs.
    assert cell.src_vote_up[("z", 1)] < before
