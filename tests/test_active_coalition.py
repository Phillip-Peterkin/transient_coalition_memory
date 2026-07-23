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
