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
