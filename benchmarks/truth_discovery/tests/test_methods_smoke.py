"""Smoke tests for literature TD methods on a tiny synthetic conflict set."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from methods import CATD, CRH, MajorityTD, StreamingCRH, TruthFinder


def _toy_claims():
    # two objects; source A reliable, B noisy
    rows = []
    for day in ("d1", "d2"):
        for obj, truth in (("o1", 10.0), ("o2", 20.0)):
            rows.append(
                {
                    "day": day,
                    "object": obj,
                    "source": "A",
                    "attribute": "temperature",
                    "value": truth,
                }
            )
            rows.append(
                {
                    "day": day,
                    "object": obj,
                    "source": "B",
                    "attribute": "temperature",
                    "value": truth + 5.0,
                }
            )
            rows.append(
                {
                    "day": day,
                    "object": obj,
                    "source": "C",
                    "attribute": "temperature",
                    "value": truth,
                }
            )
    return rows


def test_methods_return_truths_for_all_items():
    claims = _toy_claims()
    items = {(r["day"], r["object"], r["attribute"]) for r in claims}
    for cls in (MajorityTD, TruthFinder, CRH, CATD, StreamingCRH):
        result = cls().run(claims)
        assert items <= set(result.truths)
        assert result.ops > 0
        assert result.iterations >= 1
