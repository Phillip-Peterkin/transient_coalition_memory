#!/usr/bin/env python3
"""Sealed year-multi-domain evaluator — refuses until open conditions."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DBSA = ROOT.parent
REPO = DBSA.parents[1]
sys.path.insert(0, str(DBSA))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(ROOT))

from status import main as status_main  # noqa: E402


SCORING_PROTOCOL = ROOT / "SCORING_PROTOCOL.md"


def _git_sha(path: Path) -> str:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD:" + str(path.relative_to(REPO))],
                cwd=REPO,
                text=True,
            ).strip()
        )
    except Exception:
        return "unknown"


def open_conditions() -> dict:
    # Import status JSON via subprocess-less call
    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    with redirect_stdout(buf):
        status_main()
    status = json.loads(buf.getvalue())
    lanes = {lane["lane"]: lane for lane in status["lanes"]}
    weather = lanes.get("weather", {})
    finance = lanes.get("finance", {})
    medical = lanes.get("medical", {})
    synth = DBSA / "results" / "dbsa_v1_contract_200_push.json"
    if not synth.exists():
        synth = DBSA / "results" / "dbsa_v1_contract_200.json"
    checks = {
        "weather_forecast_year_ready": bool(weather.get("open_forecast_days_met"))
        or int(weather.get("n_forecast_days") or weather.get("n_forecast_day_dirs") or 0)
        >= 365,
        "weather_labels_ge_350": bool(weather.get("open_label_days_met"))
        or int(weather.get("n_labeled_decision_days") or 0) >= 350,
        "finance_events_ge_200": int(finance.get("n_events") or 0) >= 200,
        "medical_events_ge_40": int(medical.get("n_events") or 0) >= 40,
        "scoring_protocol_present": SCORING_PROTOCOL.exists(),
        "synthetic_200_artifact_present": synth.exists(),
    }
    return {
        "checks": checks,
        "all_passed": all(checks.values()),
        "status": status,
        "scoring_protocol_git_sha": _git_sha(SCORING_PROTOCOL),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="debug only; default refuses")
    args = ap.parse_args()
    gate = open_conditions()
    print(json.dumps(gate, indent=2))
    if not gate["all_passed"] and not args.force:
        raise SystemExit(
            "SCORING CLOSED — year_multi_domain open conditions not met. Collect only."
        )
    raise SystemExit(
        "Open conditions met, but first-look scorer not yet wired for all three "
        "lanes in this commit — collect/status only. Do not invent scores."
    )


if __name__ == "__main__":
    main()
