"""Brain-shaped change-investigation circuit for calibrated TCM.

This is deliberately different from the earlier ``adaptive_exchange`` cure.
That cure adjusted memory trust all the time and lost on real data.  This
module implements a narrower loop suggested by the HRF paper:

1. A clearly wrong prediction builds a local prediction-error signal.
2. Enough error *ignites* a temporary investigation state.
3. While investigating, credible reports that contradict the old belief cannot
   be sign-reversed or buried by that belief.
4. The state decays gradually (hysteresis), rather than closing immediately.

The circuit does not blindly recruit more reports.  The first ablation showed
that "more attention when surprised" amplified the 90%-Positive news flood.
It changes how credible counter-evidence is allowed to affect a decision.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
sys.path.insert(0, str(ROOT))

from cures import CuredCellular  # noqa: E402


class TransitionInvestigator(CuredCellular):
    """Calibrated TCM with a temporary, hysteretic counter-evidence mode."""

    name = "transition_investigator"

    def __init__(
        self,
        *,
        error_decay: float = 0.65,
        ignite_threshold: float = 0.95,
        confidence_floor: float = 0.20,
        investigate_decay: float = 0.72,
        anchor_floor: float = 0.25,
        counterevidence_floor: float = 0.75,
        **params,
    ):
        # The first real-data ablation established this as the working sensory
        # front end.  The new circuit tests only the state-transition loop.
        cures = set(params.pop("cures", ()))
        cures.update(("source_calib", "corr_downweight"))
        super().__init__(cures=cures, **params)

        self.error_decay = error_decay
        self.ignite_threshold = ignite_threshold
        self.confidence_floor = confidence_floor
        self.investigate_decay = investigate_decay
        self.anchor_floor = anchor_floor
        self.counterevidence_floor = counterevidence_floor

        self.error_pressure = defaultdict(float)
        self.investigation = defaultdict(float)
        self.investigation_ignitions = 0
        self.protected_counter_reports = 0
        self.investigation_predictions = 0

    def _anchor_side(self, key):
        """Return the currently preferred answer, or None before any memory."""
        pref = (
            self.cf[(key, 1)]
            - self.cf[(key, 0)]
            + self.cs[(key, 1)]
            - self.cs[(key, 0)]
        )
        if abs(pref) < 1e-12:
            return None
        return 1 if pref > 0 else 0

    def _rows(self, key, reports):
        """Calibrated rows, with a protected counter-evidence bridge when open."""
        # This begins as CuredCellular._rows(source_calib + corr_downweight).
        corr_scale = 1.0
        if len(reports) >= 2:
            ys = [y for _, _, y in reports]
            agree = sum(ys[i] == ys[j] for i in range(len(ys)) for j in range(i + 1, len(ys)))
            total = len(ys) * (len(ys) - 1) / 2
            agree_frac = agree / total if total else 0.0
            effective_n = 1.0 + (len(ys) - 1) * (1.0 - agree_frac)
            corr_scale = effective_n / len(ys)

        opening = self.investigation[key]
        old_side = self._anchor_side(key)
        rows = []
        protected = 0
        for s, c, y in reports:
            sign = 1.0 if y else -1.0
            ck = (key, y)
            source_term = self.wsrc * self.src[(s, c)]
            calibration = self._cal_weight((s, c), y)
            # Sensory activation energy: direct evidence + source-specific
            # reliability, calibrated for each publisher's base-rate bias.
            sensory = (self.direct + source_term) * calibration * corr_scale
            anchor = (self.wf * self.cf[ck] + self.ws * self.cs[ck]) * calibration * corr_scale

            if opening > 0:
                anchor *= 1.0 - opening * (1.0 - self.anchor_floor)
            strength = sensory + anchor

            # The key brain-like rule: once a prediction-error state is open,
            # credible counter-evidence may not be turned into evidence for the
            # old belief by a large stale anchor.  It still has to clear a
            # sensory floor; we do not invent a vote.
            if opening > 0 and old_side is not None and y != old_side:
                floor = self.counterevidence_floor * sensory
                if strength < floor:
                    strength = floor
                    protected += 1

            vote = sign * strength
            rows.append((abs(vote), vote, s, c, y, ck))

        self.protected_counter_reports += protected
        rows.sort(key=lambda row: row[0], reverse=True)
        self.preview_ops += self.header_cost * len(rows)
        return rows

    def predict(self, key, reports, t):
        # Hysteresis: investigation persists through multiple opportunities to
        # sample the world, then decays rather than remaining permanently open.
        self.investigation[key] *= self.investigate_decay
        p, trace = super().predict(key, reports, t)
        self.investigation_predictions += int(self.investigation[key] > 0)
        trace["investigation"] = self.investigation[key]
        trace["error_pressure"] = self.error_pressure[key]
        return p, trace

    def feedback(self, event):
        p = float(event["trace"]["p"])
        truth = float(event["truth"])
        key = event["key"]
        confidence = 2.0 * abs(p - 0.5)

        super().feedback(event)

        # A correct outcome drains the pending warning.  A near-coin-flip
        # miss does not enter the warning circuit at all: brains do not launch
        # a state-change investigation after a guess they barely committed to.
        pressure = self.error_pressure[key] * self.error_decay
        if int(p >= 0.5) != int(truth) and confidence >= self.confidence_floor:
            pressure += confidence
        self.error_pressure[key] = pressure

        # Ignition requires accumulated prediction failure (not one noisy
        # report); this produces a reversible state-change investigation.
        if pressure >= self.ignite_threshold:
            self.investigation[key] = 1.0
            self.error_pressure[key] = 0.0
            self.investigation_ignitions += 1

    def stats(self):
        stats = super().stats()
        stats["investigation_ignitions"] = self.investigation_ignitions
        stats["investigation_predictions"] = self.investigation_predictions
        stats["protected_counter_reports"] = self.protected_counter_reports
        return stats
