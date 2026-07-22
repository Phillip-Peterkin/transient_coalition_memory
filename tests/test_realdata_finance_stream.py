"""Smoke tests for the finance/news real-data stream (uses committed cache)."""

from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmarks" / "realdata_finance"))

from stream import FinanceNewsStream  # noqa: E402


def test_stream_builds_from_cache():
    stream = FinanceNewsStream(ROOT / "benchmarks" / "realdata_finance" / "data")
    assert stream.I >= 30
    assert len(stream.events) > 1000
    assert 0.4 < stream.summary()["truth_up_rate"] < 0.6
    e0 = stream.events[0]
    assert e0.reports
    assert all(len(r) == 3 for r in e0.reports)
    assert e0.truth in (0, 1)


def test_holdout_is_later_than_contact():
    stream = FinanceNewsStream(ROOT / "benchmarks" / "realdata_finance" / "data")
    contact_days = [e.day for e in stream.events if e.split == "contact"]
    holdout_days = [e.day for e in stream.events if e.split == "holdout"]
    assert contact_days
    assert holdout_days
    assert max(contact_days) <= min(holdout_days)


def test_locked_tcm_smoke_predict():
    from tcm import BatchedReserveCellular

    stream = FinanceNewsStream(ROOT / "benchmarks" / "realdata_finance" / "data")
    model = BatchedReserveCellular(
        lr=0.22,
        fast_decay=0.90,
        contradiction_gain=0.85,
        uncertainty_cost=0.38,
        temp=0.95,
        anchor=0.58,
        min_k=1,
        max_k=8,
        header_cost=0.08,
        cert_delta=0.08,
        hazard_gain=3.0,
        min_margin=0.0,
        shadow_scale=0.75,
        reserve_claim_gain=1.2,
        reserve_source_gain=0.0,
        certify_slack=0.0,
    )
    e = stream.events[0]
    p, tr = model.predict(e.key, e.reports, e.t)
    assert 0.0 <= p <= 1.0
    assert tr["used"] >= 1
    assert np.isfinite(p)


def _run_flip_accuracy(stream, model):
    from collections import defaultdict

    q = defaultdict(list)
    correct_flip = []
    for ev in stream.events:
        for fb in q.pop(ev.t, []):
            model.feedback(fb)
        p, tr = model.predict(ev.key, ev.reports, ev.t)
        q[ev.t + 1].append(
            {"key": ev.key, "reports": ev.reports, "truth": ev.truth,
             "pred": p, "trace": tr, "time": ev.t + 1}
        )
        if ev.split == "holdout" and ev.prev_truth is not None and ev.truth != ev.prev_truth:
            correct_flip.append(int((p >= 0.5) == ev.truth))
    return float(np.mean(correct_flip)) if correct_flip else float("nan")


def test_null_cure_reproduces_frozen_and_calibration_helps_flips():
    from tcm import BatchedReserveCellular

    from cures import CuredCellular
    from evaluate import CELL_PARAMS

    data = ROOT / "benchmarks" / "realdata_finance" / "data"
    frozen = _run_flip_accuracy(FinanceNewsStream(data), BatchedReserveCellular(**CELL_PARAMS))
    null = _run_flip_accuracy(FinanceNewsStream(data), CuredCellular(cures=(), **CELL_PARAMS))
    calib = _run_flip_accuracy(
        FinanceNewsStream(data),
        CuredCellular(cures=("source_calib", "corr_downweight"), **CELL_PARAMS),
    )
    # Empty cure set must reproduce the frozen reference exactly.
    assert abs(null - frozen) < 1e-9
    # Calibration must materially raise flip detection (documented ~+5.7 pts).
    assert calib > frozen + 0.03


def test_active_sensory_model_matches_confirmed_relevance_benchmark():
    from ablation import run_vectors
    from relevance import RelevanceFinanceNewsStream, RelevanceGatedCellular
    from evaluate import CELL_PARAMS
    from tcm import SensoryGatedCellular

    data = ROOT / "benchmarks" / "realdata_finance" / "data"
    benchmark = run_vectors(
        RelevanceFinanceNewsStream(data),
        RelevanceGatedCellular(**CELL_PARAMS),
        "holdout",
    )
    active = run_vectors(
        RelevanceFinanceNewsStream(data),
        SensoryGatedCellular(**CELL_PARAMS),
        "holdout",
    )
    assert np.allclose(active["p"], benchmark["p"], atol=1e-12)
    assert np.array_equal(active["correct"], benchmark["correct"])


def test_relevance_gate_rejects_misattribution_and_keeps_direct_evidence():
    from relevance import is_relevant

    assert is_relevant("Apple's new product ships next month", "AAPL")
    assert not is_relevant("Judge revives Obama-era ban on coal sales", "AAPL")
    assert is_relevant("Nvidia announces a new AI platform", "NVDA")


def test_wave_xviii_zero_trust_reproduces_sensory_model():
    from collections import defaultdict

    from relevance import RelevanceFinanceNewsStream
    from tcm import SensoryGatedCellular, WaveXVIIITrustCellular
    from evaluate import CELL_PARAMS

    data = ROOT / "benchmarks" / "realdata_finance" / "data"
    left = SensoryGatedCellular(**CELL_PARAMS)
    right = WaveXVIIITrustCellular(mistrust_gain=0.0, correct_relaxation=0.0, **CELL_PARAMS)
    left_q, right_q = defaultdict(list), defaultdict(list)
    stream = RelevanceFinanceNewsStream(data)

    for event in stream.events[:120]:
        for feedback in left_q.pop(event.t, []):
            left.feedback(feedback)
        for feedback in right_q.pop(event.t, []):
            right.feedback(feedback)
        lp, lt = left.predict(event.key, event.reports, event.t)
        rp, rt = right.predict(event.key, event.reports, event.t)
        assert np.isclose(lp, rp)
        left_q[event.t + 1].append(
            {"key": event.key, "reports": event.reports, "truth": event.truth,
             "pred": lp, "trace": lt, "time": event.t + 1}
        )
        right_q[event.t + 1].append(
            {"key": event.key, "reports": event.reports, "truth": event.truth,
             "pred": rp, "trace": rt, "time": event.t + 1}
        )


def test_wave_xviii_confident_error_changes_all_three_next_decision_controls():
    from tcm import WaveXVIIITrustCellular
    from evaluate import CELL_PARAMS

    model = WaveXVIIITrustCellular(**CELL_PARAMS)
    key = (17, 0)
    model.feedback({"key": key, "reports": [], "truth": 0, "trace": {"p": 0.9, "active": []}})
    assert model.mistrust[key] > model.recruit_threshold

    _, trace = model.predict(key, [(0, 0, 1), (1, 0, 0)], t=1)
    assert trace["hazard"] >= trace["base_hazard"]
    assert trace["extra_recruited"] == 1
    assert trace["anchor_scale"] < 1.0
    assert trace["fresh_evidence_floor"] > 0.0


def test_wave_xviii_confident_success_relaxes_only_its_item():
    from tcm import WaveXVIIITrustCellular
    from evaluate import CELL_PARAMS

    model = WaveXVIIITrustCellular(**CELL_PARAMS)
    key_a, key_b = (1, 0), (2, 0)
    model.mistrust[key_a] = 0.8
    model.feedback({"key": key_a, "reports": [], "truth": 1, "trace": {"p": 0.9, "active": []}})
    assert 0.0 <= model.mistrust[key_a] < 0.8
    assert model.mistrust[key_b] == 0.0


def test_wave_xviii_can_require_ignored_counterevidence():
    from tcm import WaveXVIIITrustCellular
    from evaluate import CELL_PARAMS

    model = WaveXVIIITrustCellular(require_counterevidence=True, **CELL_PARAMS)
    key = (5, 0)
    # Wrong, but all relevant reports agreed with the incorrect prediction:
    # do not blame memory for an unsupported environmental surprise.
    model.feedback(
        {"key": key, "reports": [(0, 0, 1)], "truth": 0, "trace": {"p": 0.9, "active": []}}
    )
    assert model.mistrust[key] == 0.0
    # Wrong while a relevant report pointed the other way: raise mistrust.
    model.feedback(
        {"key": key, "reports": [(0, 0, 0)], "truth": 0, "trace": {"p": 0.9, "active": []}}
    )
    assert model.mistrust[key] > 0.0
