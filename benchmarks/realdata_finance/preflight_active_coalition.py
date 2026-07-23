#!/usr/bin/env python3
"""Invariant checks for ActiveCoalitionCellular before any scoring.

Fails loud on coding mistakes. Does not tune. Does not touch confirmation data.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(ROOT))

from evaluate import CELL_PARAMS  # noqa: E402
from tcm import ActiveCoalitionCellular  # noqa: E402


def approx(a: float, b: float, tol: float = 1e-6) -> bool:
    return abs(a - b) <= tol


def main() -> None:
    cell = ActiveCoalitionCellular(**CELL_PARAMS)
    key = (0, 0)

    # 1) Cold start, empty → silence channel; PE starts at 0.5 ⇒ mild hazard.
    p, tr = cell.predict(key, [], t=0)
    assert tr["stop_reason"] == "silence_channel", tr
    assert tr["hazard"] > 0.0, tr
    assert 0.0 < p < 1.0

    # 2) All-Positive is forced null (cheerleader), not FE evidence.
    reports = [("s1", 0, 1), ("s2", 0, 1), ("s3", 0, 1)]
    cell.cf[(key, 1)] = 5.0
    cell.cf[(key, 0)] = -5.0
    p2, tr2 = cell.predict(key, reports, t=1)
    assert tr2["stop_reason"] == "null_diagnostic", tr2
    assert approx(tr2["evidence_lo"], 0.0), tr2
    assert tr2["prior_p"] > 0.9, tr2["prior_p"]

    # 3) After discriminative learning, Δ must be prior-free and signed correctly.
    cell2 = ActiveCoalitionCellular(**CELL_PARAMS)
    # Teach s_good: says 1 when up, 0 when down.
    for _ in range(20):
        cell2.feedback(
            {
                "key": key,
                "truth": 1,
                "reports": [("s_good", 0, 1)],
                "trace": {"p": 0.6, "prior_p": 0.5},
                "time": 1,
            }
        )
        cell2.feedback(
            {
                "key": key,
                "truth": 0,
                "reports": [("s_good", 0, 0)],
                "trace": {"p": 0.4, "prior_p": 0.5},
                "time": 2,
            }
        )
    # Cheerleader source: always says 1 regardless of truth.
    for truth in (1, 0, 1, 0, 1, 0, 1, 0):
        cell2.feedback(
            {
                "key": key,
                "truth": truth,
                "reports": [("s_cheer", 0, 1)],
                "trace": {"p": 0.5, "prior_p": 0.5},
                "time": 3,
            }
        )

    d_good_up = cell2._report_delta("s_good", 1)
    d_good_down = cell2._report_delta("s_good", 0)
    d_cheer = cell2._report_delta("s_cheer", 1)
    assert d_good_up > 0.2, d_good_up
    assert d_good_down < -0.2, d_good_down
    assert abs(d_cheer) < abs(d_good_up) / 2, (d_cheer, d_good_up)

    # Memory poison must not change deltas.
    cell2.cf[(key, 1)] = 9.0
    cell2.cf[(key, 0)] = -9.0
    assert approx(cell2._report_delta("s_good", 1), d_good_up)

    # Mixed batch (not all-Positive) so the FE evidence path is taken.
    p3, tr3 = cell2.predict(key, [("s_good", 0, 1), ("s_cheer", 0, 1), ("s_good", 0, 0)], t=4)
    assert tr3["stop_reason"] in {"free_energy_certified", "budget"}, tr3
    assert tr3["used"] >= 1
    # Strongest |Δ| should be s_good.
    assert tr3["active"][0][0] == "s_good", tr3["active"]

    # 4) Null-channel PE precision → anti-prior mix under silence.
    cell3 = ActiveCoalitionCellular(max_silence_hazard=0.70, **CELL_PARAMS)
    for _ in range(30):
        # High posterior error under null (predicted up, truth down).
        cell3.feedback(
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
    cell3.cf[(key, 1)] = 3.0
    cell3.cf[(key, 0)] = -3.0
    cell3.cs[(key, 1)] = 1.0
    cell3.cs[(key, 0)] = -1.0
    p4, tr4 = cell3.predict(key, [], t=6)
    assert tr4["stop_reason"] == "silence_channel", tr4
    assert tr4["hazard"] > 0.3, tr4
    assert tr4["prior_p"] > 0.85, tr4["prior_p"]
    assert p4 < tr4["prior_p"], (p4, tr4["prior_p"])

    # 5) Free-energy certificate: unread mass cannot flip.
    cell4 = ActiveCoalitionCellular(min_delta=0.01, fe_cert_slack=0.0, **CELL_PARAMS)
    for _ in range(40):
        cell4.feedback(
            {
                "key": key,
                "truth": 1,
                "reports": [("a", 0, 1)],
                "trace": {"p": 0.7, "prior_p": 0.5},
                "time": 1,
            }
        )
        cell4.feedback(
            {
                "key": key,
                "truth": 0,
                "reports": [("b", 0, 0)],
                "trace": {"p": 0.3, "prior_p": 0.5},
                "time": 2,
            }
        )
    # Strong a=1 plus weak noise.
    p5, tr5 = cell4.predict(
        key,
        [("a", 0, 1), ("noise1", 0, 1), ("noise2", 0, 0)],
        t=3,
    )
    assert tr5["used"] >= 1
    if tr5["stop_reason"] == "free_energy_certified":
        unread = tr5["unread_mass"]
        post = tr5["prior_lo"] + tr5["evidence_lo"]
        assert abs(post) > unread - 1e-9, (post, unread)

    # 6) Feedback does not call parent path that would mix memory into src strengths.
    cell5 = ActiveCoalitionCellular(**CELL_PARAMS)
    cell5.feedback(
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
    assert cell5.src_vote_up[("z", 1)] > cell5.laplace
    assert math.isfinite(cell5.cf[(key, 1)])

    print("preflight_active_coalition: ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
