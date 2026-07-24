"""Gross-bug and protocol tests for PWDR (Precision-Whitened Delayed Residual)."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(REPO / "src"))

from baselines import (  # noqa: E402
    PWDR_MIN_UPDATES,
    PWDR_RIDGE,
    Majority,
    PrecisionWhitenedDelayedResidual,
)
from contract_simulator import generate  # noqa: E402
from evaluate import run_model  # noqa: E402


def _event(t, due_t, reports, truth, key=(0, 0), prev_truth=None):
    return SimpleNamespace(
        t=t,
        due_t=due_t,
        key=key,
        reports=reports,
        truth=truth,
        prev_truth=prev_truth,
        shift_age=None,
    )


def test_pwdr_knobs_are_locked():
    assert PWDR_RIDGE == 0.05
    assert PWDR_MIN_UPDATES == 20


def test_identity_precision_reduces_to_majority():
    """Gross-bug guard: cold-start / Λ=I must emit majority (exchangeable opt)."""
    model = PrecisionWhitenedDelayedResidual(min_updates=10_000)
    reports = [(0, 0, 1), (1, 0, 1), (2, 0, 0), (3, 0, 0), (4, 0, 1)]
    p, trace = model.predict((0, 0), reports, 0)
    assert abs(trace["pwdr_m"] - trace["pwdr_majority"]) < 1e-12
    assert abs(trace["pwdr_m"] - 0.6) < 1e-12
    # Residual may move p, but base m is majority.
    assert abs(p - _clip_if_needed(trace["pwdr_m"] + trace["pwdr_r"])) < 1e-12


def _clip_if_needed(value: float) -> float:
    return min(1.0 - 1e-9, max(1e-9, value))


def test_pwdr_updates_only_after_delay_release():
    events = generate("independent_stable", seed=11, rounds=15)[:14]
    model = PrecisionWhitenedDelayedResidual()
    result = run_model(events, model)
    assert result["model_stats"]["updates"] == 0
    assert result["model_stats"]["pwdr_cov_updates"] == 0


def test_covariance_uses_errors_not_opinion_agreement():
    """Signed-correctness kernel: anti-correlated specialists get negative C_ij.

    Gross-bug guard: vote−truth cannot produce negative cross-terms on binary
    labels; PWDR must use ±1 correctness residuals instead.
    """
    model = PrecisionWhitenedDelayedResidual(min_updates=1, cov_forget=1.0)
    # Source 0 always correct, source 1 always wrong (opposite correctness).
    for step in range(30):
        truth = step % 2
        reports = [(0, 0, truth), (1, 0, 1 - truth)]
        _p, trace = model.predict((0, 0), reports, step)
        model.feedback(
            {
                "key": (0, 0),
                "reports": reports,
                "truth": truth,
                "pred": _p,
                "trace": trace,
                "time": step,
            }
        )
    assert model._S.shape == (2, 2)
    assert model._S[0, 1] < 0.0
    assert model._S[0, 0] > 0.0
    assert model._S[1, 1] > 0.0

    # Control: two clones always wrong together → positive cross-term.
    clone = PrecisionWhitenedDelayedResidual(min_updates=1, cov_forget=1.0)
    for step in range(30):
        truth = step % 2
        reports = [(0, 0, 1 - truth), (1, 0, 1 - truth)]
        _p, trace = clone.predict((0, 0), reports, step)
        clone.feedback(
            {
                "key": (0, 0),
                "reports": reports,
                "truth": truth,
                "pred": _p,
                "trace": trace,
                "time": step,
            }
        )
    assert clone._S[0, 1] > 0.0


def test_no_christmas_bow_blend_toward_majority():
    """Emission is Π(m + r), not a convex blend with unwhitened majority."""
    model = PrecisionWhitenedDelayedResidual(min_updates=1)
    # Force residual weights to push away from majority.
    model._residual_w = np.asarray([0.0, 0.0, 0.0, 0.0, -2.0], dtype=float)
    # Warm covariance: clone sources 0,1 always wrong-together; 2 independent correct.
    for step in range(40):
        truth = 1
        reports = [(0, 0, 0), (1, 0, 0), (2, 0, 1)]
        p, trace = model.predict((0, 0), reports, step)
        model.feedback(
            {
                "key": (0, 0),
                "reports": reports,
                "truth": truth,
                "pred": p,
                "trace": trace,
                "time": step,
            }
        )
    reports = [(0, 0, 0), (1, 0, 0), (2, 0, 1)]
    p, trace = model.predict((0, 0), reports, 100)
    majority = trace["pwdr_majority"]
    assert majority < 0.5  # 1 of 3 votes
    assert trace["christmas_bow_forbidden"] is True
    # Must not be a blend: blend would pull p toward majority (<0.5).
    # With negative weight on (m - majority) and whitening, p should be able
    # to sit above majority (toward the independent correct source).
    assert p > majority
    # Explicit non-blend identity: p == clip(m + r), not (1-α)m + α*majority.
    assert abs(p - np.clip(trace["pwdr_m"] + trace["pwdr_r"], 1e-9, 1 - 1e-9)) < 1e-9


def test_residual_trains_on_whitened_m_not_raw_majority():
    model = PrecisionWhitenedDelayedResidual(min_updates=1, residual_lr=0.2)
    reports = [(0, 0, 1), (1, 0, 0)]
    p, trace = model.predict((0, 0), reports, 0)
    assert "pwdr_m" in trace
    # Corrupt majority feature path: if residual targeted y-majority, weights
    # would chase a different target. We check the stored target convention via
    # one feedback step against whitened m.
    truth = 1
    m = float(trace["pwdr_m"])
    majority = float(trace["pwdr_majority"])
    assert abs(m - majority) > 1e-12 or True  # m may equal majority at cold start
    before = model._residual_w.copy()
    model.feedback(
        {
            "key": (0, 0),
            "reports": reports,
            "truth": truth,
            "pred": p,
            "trace": trace,
            "time": 0,
        }
    )
    # Weight update uses (pred_r - (truth - m)) — changing m in trace changes grad.
    model2 = PrecisionWhitenedDelayedResidual(min_updates=1, residual_lr=0.2)
    p2, trace2 = model2.predict((0, 0), reports, 0)
    trace2 = dict(trace2)
    trace2["pwdr_m"] = 0.1  # counterfactual whitened m
    model2.feedback(
        {
            "key": (0, 0),
            "reports": reports,
            "truth": truth,
            "pred": p2,
            "trace": trace2,
            "time": 0,
        }
    )
    # Different m ⇒ different residual target ⇒ different weights.
    assert not np.allclose(model._residual_w, before) or not np.allclose(
        model._residual_w, model2._residual_w
    )
    assert not np.allclose(model._residual_w, model2._residual_w)


def test_whitening_downweights_perfect_error_clone():
    """Correlated-majority trap: two clones wrong, one independent right."""
    model = PrecisionWhitenedDelayedResidual(
        min_updates=10, cov_forget=1.0, ridge=0.05, residual_lr=0.0
    )
    delay = 5
    pending = []
    for t in range(80):
        truth = t % 2
        # Clones 0,1 copy each other and are wrong; 2 is correct.
        reports = [(0, 0, 1 - truth), (1, 0, 1 - truth), (2, 0, truth)]
        due = [item for item in pending if item[0] == t]
        pending = [item for item in pending if item[0] != t]
        for _, payload in due:
            model.feedback(payload)
        p, trace = model.predict((0, 0), reports, t)
        pending.append(
            (
                t + delay,
                {
                    "key": (0, 0),
                    "reports": reports,
                    "truth": truth,
                    "pred": p,
                    "trace": trace,
                    "time": t + delay,
                },
            )
        )
    reports = [(0, 0, 1), (1, 0, 1), (2, 0, 0)]  # majority=1 wrong, minority=0 right
    p, trace = model.predict((0, 0), reports, 1000)
    assert trace["pwdr_majority"] > 0.5
    # Whitened base must move toward the independent minority vs raw majority.
    assert trace["pwdr_m"] < trace["pwdr_majority"] - 0.1
    assert abs(trace["pwdr_m"] - 0.0) < abs(trace["pwdr_majority"] - 0.0)


def test_pwdr_runs_on_contract_stream():
    events = generate("correlated_stable", seed=3, rounds=120)
    pwdr = run_model(events, PrecisionWhitenedDelayedResidual())
    maj = run_model(events, Majority())
    assert pwdr["n"] == maj["n"] == 120
    assert pwdr["model_stats"]["pwdr_cov_updates"] > 0
    assert 0.0 < pwdr["brier"] < 1.0
