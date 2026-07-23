"""Toggleable architectural cures for TCM, grounded in the author's two papers.

Each cure targets a specific weakness-ledger item (see docs/NORTH_STAR.md) and
is derived from a mechanism in the uploaded papers:

- `adaptive_exchange` (ledger 4)  ← HRF "precision-weighted prediction error /
  gain modulation": trust in memory (the claim anchor) and the learning gain on
  fresh evidence are modulated by a running estimate of how *wrong* memory has
  been.  When the anchor keeps mispredicting (regime shift), down-weight it and
  learn from the world faster — i.e. an online memory-vs-world exchange rate.

- `prior_neutral` (ledger 3)  ← HRF "activation energy crosses a gain-modulated
  threshold": recruitment order is driven by evidence *activation energy*
  (source reliability + direct signal), NOT by the claim anchor.  Gathering is
  decoupled from belief; the anchor still weights the decision.

- `surprise_hazard` (ledger 2)  ← HRF "adaptive threshold scales inversely with
  precision" + Fitted-Dynamics "spectral radius rises before a state
  transition".  Recruitment depth rises when recent prediction-error precision
  is low and when a local AR(1) operator on the belief series approaches
  criticality (|rho| -> 1), i.e. a change is imminent.

- `source_calib` (ledger 8)  ← precision-weighting of sources: each report is
  weighted by the self-information of its source's emission base rate (a
  90%-positive source says little when positive, a lot when negative).

- `corr_downweight` (ledger 8)  ← independence honesty: correlated within-event
  reports are down-weighted by an effective-count factor so redundant agreement
  is not counted as independent evidence.

Toggles are additive; with an empty cure set this class reproduces the frozen
`BatchedReserveCellular` exactly (verified in the ablation harness).
"""

from __future__ import annotations

import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
for _p in ("wave4", "wave7", "wave9", "wave10", "wave11"):
    sys.path.insert(0, str(REPO / "benchmarks" / _p))

from tcm import BatchedReserveCellular  # noqa: E402
from wave4_benchmark import EPS, sigmoid  # noqa: E402

ALL_CURES = (
    "adaptive_exchange",
    "prior_neutral",
    "surprise_hazard",
    "source_calib",
    "corr_downweight",
)


class CuredCellular(BatchedReserveCellular):
    """Frozen Wave XI reference plus independently toggleable cures."""

    name = "cured_cellular"

    def __init__(
        self,
        *,
        cures=(),
        # adaptive_exchange
        exch_err_target: float = 0.40,
        exch_anchor_floor: float = 0.25,
        exch_anchor_k: float = 0.9,
        exch_lr_k: float = 0.8,
        exch_forget_k: float = 0.06,
        # surprise_hazard
        haz_surprise_w: float = 0.35,
        haz_rho_w: float = 0.25,
        rho_window: int = 6,
        # calibrate
        cal_min: float = 0.3,
        cal_max: float = 3.0,
        err_beta: float = 0.25,
        **params,
    ):
        super().__init__(**params)
        self.cures = set(cures)
        unknown = self.cures - set(ALL_CURES)
        if unknown:
            raise ValueError(f"unknown cures: {sorted(unknown)}")

        self.exch_err_target = exch_err_target
        self.exch_anchor_floor = exch_anchor_floor
        self.exch_anchor_k = exch_anchor_k
        self.exch_lr_k = exch_lr_k
        self.exch_forget_k = exch_forget_k
        self.haz_surprise_w = haz_surprise_w
        self.haz_rho_w = haz_rho_w
        self.rho_window = rho_window
        self.cal_min = cal_min
        self.cal_max = cal_max
        self.err_beta = err_beta

        # Instrumentation shared by cures (updated every feedback; harmless to
        # the frozen path because the frozen methods never read these).
        self.err_ewma = defaultdict(lambda: 0.5)   # running |truth - p| per key
        self.belief_hist = defaultdict(list)        # recent fast-pref per key
        self.src_pos = defaultdict(lambda: 1.0)      # emission counts (Laplace)
        self.src_neg = defaultdict(lambda: 1.0)

    # ---- shared helpers -------------------------------------------------
    def _surprise(self, key) -> float:
        """0 when memory is at/under its error target, ->1 as it worsens."""
        excess = self.err_ewma[key] - self.exch_err_target
        if excess <= 0:
            return 0.0
        return min(1.0, excess / max(EPS, 1.0 - self.exch_err_target))

    def _rho_proxy(self, key) -> float:
        """|AR(1) coefficient| of the recent belief series for `key`."""
        hist = self.belief_hist[key]
        if len(hist) < 3:
            return 0.0
        x = hist[:-1]
        y = hist[1:]
        mx = sum(x) / len(x)
        my = sum(y) / len(y)
        num = sum((a - mx) * (b - my) for a, b in zip(x, y))
        den = sum((a - mx) ** 2 for a in x)
        if den <= EPS:
            return 0.0
        return min(1.0, abs(num / den))

    def _cal_weight(self, sk, y) -> float:
        pos, neg = self.src_pos[sk], self.src_neg[sk]
        p_emit = (pos if y == 1 else neg) / (pos + neg)
        info = -math.log(max(EPS, p_emit)) / math.log(2.0)  # 50/50 source -> 1.0
        return min(self.cal_max, max(self.cal_min, info))

    def _update_aux(self, e):
        key = e["key"]
        tr = e["trace"]
        err = abs(float(e["truth"]) - float(tr["p"]))
        self.err_ewma[key] = (1 - self.err_beta) * self.err_ewma[key] + self.err_beta * err
        fast_pref = self.cf[(key, 1)] - self.cf[(key, 0)]
        h = self.belief_hist[key]
        h.append(fast_pref)
        if len(h) > self.rho_window:
            del h[0]

    def _count_emissions(self, reports):
        for s, c, y in reports:
            if y == 1:
                self.src_pos[(s, c)] += 1.0
            else:
                self.src_neg[(s, c)] += 1.0

    # ---- recruitment (prior_neutral / calibrate) ------------------------
    def _rows(self, key, reports):
        if not ({"prior_neutral", "source_calib", "corr_downweight"} & self.cures):
            return super()._rows(key, reports)

        calibrate = "source_calib" in self.cures
        corr_dw = "corr_downweight" in self.cures
        prior_neutral = "prior_neutral" in self.cures

        # Independence honesty: shrink redundant within-event agreement.
        corr_scale = 1.0
        if corr_dw and len(reports) >= 2:
            ys = [y for _, _, y in reports]
            agree = 0
            total = 0
            for i in range(len(ys)):
                for j in range(i + 1, len(ys)):
                    agree += int(ys[i] == ys[j])
                    total += 1
            agree_frac = agree / total if total else 0.0
            n = len(reports)
            eff_n = 1.0 + (n - 1) * (1.0 - agree_frac)
            corr_scale = eff_n / n

        rows = []
        for s, c, y in reports:
            sg = 1 if y else -1
            ck = (key, y)
            anchor_term = self.wf * self.cf[ck] + self.ws * self.cs[ck]
            source_term = self.wsrc * self.src[(s, c)]
            cal = self._cal_weight((s, c), y) if calibrate else 1.0
            strength = (self.direct + anchor_term + source_term) * cal * corr_scale
            v = sg * strength
            if prior_neutral:
                # Recruit by activation energy (source reliability + direct),
                # NOT by the claim anchor: gathering is prior-neutral.
                recruit_mag = abs((self.direct + source_term) * cal)
            else:
                recruit_mag = abs(v)
            rows.append((recruit_mag, v, s, c, y, ck))
        rows.sort(key=lambda x: x[0], reverse=True)
        self.preview_ops += self.header_cost * len(rows)
        return rows

    # ---- prediction (surprise_hazard) -----------------------------------
    def predict(self, key, reports, t):
        if "surprise_hazard" not in self.cures:
            p, tr = super().predict(key, reports, t)
            self._count_emissions(reports)
            return p, tr
        p, tr = self._predict_surprise(key, reports, t)
        self.infer_reads += self.header_cost * len(reports) + tr["used"]
        self._count_emissions(reports)
        return p, tr

    def _predict_surprise(self, key, reports, t):
        """wave10 CompressedReserveCellular.predict with a surprise-aware gate."""
        rows = self._rows(key, reports)[: self.max_k]
        n = len(rows)
        suf_pos = [0.0] * (n + 1)
        suf_neg = [0.0] * (n + 1)
        for i in range(n - 1, -1, -1):
            v = rows[i][1]
            suf_pos[i] = suf_pos[i + 1] + (abs(v) if v >= 0 else 0.0)
            suf_neg[i] = suf_neg[i + 1] + (abs(v) if v < 0 else 0.0)

        ones = sum(y for _, _, y in reports)
        zeros = len(reports) - ones
        report_dis = min(ones, zeros) / (max(ones, zeros) + EPS)
        fast_pref = self.cf[(key, 1)] - self.cf[(key, 0)]
        slow_pref = self.cs[(key, 1)] - self.cs[(key, 0)]
        memory_conflict = float(fast_pref * slow_pref < 0)
        volatility = min(1.0, abs(fast_pref - slow_pref))
        age = max(0, t - self.last_fb[key])
        stale = min(1.0, age / 30.0)

        base_hazard = 0.45 * report_dis + 0.25 * memory_conflict + 0.20 * volatility + 0.10 * stale
        surprise = self._surprise(key)
        rho = self._rho_proxy(key)
        hazard = min(1.0, base_hazard + self.haz_surprise_w * surprise + self.haz_rho_w * rho)
        required = min(self.max_k, max(self.min_k, 1 + int(round(self.hazard_gain * hazard))))

        stop_reason = "budget"
        cert_shift = 1.0
        z = pos = neg = 0.0
        active = []
        for i, row in enumerate(rows):
            active.append(row)
            v = row[1]
            z += v
            if v >= 0:
                pos += abs(v)
            else:
                neg += abs(v)
            self.activation_ops += 1.0
            self.ops += 2
            if len(active) < required:
                continue
            rp = suf_pos[i + 1]
            rn = suf_neg[i + 1]
            if rp + rn <= EPS:
                stop_reason = "exhausted"
                cert_shift = 0.0
                break
            con = min(pos, neg) / (max(pos, neg) + EPS)
            cur = z * (1 - self.cg * con)
            fp = pos + rp
            fn = neg + rn
            full_z = fp - fn
            full_con = min(fp, fn) / (max(fp, fn) + EPS)
            full = full_z * (1 - self.cg * full_con)
            p_now = sigmoid(cur / max(self.temp, EPS))
            p_full = sigmoid(full / max(self.temp, EPS))
            cert_shift = abs(p_now - p_full)
            same = ((cur >= 0) == (full >= 0))
            reserve_mass = rp + rn
            robust = abs(cur) > self.certify_slack + reserve_mass * (1 - self.cg * min(1.0, con + 0.25))
            if same and robust and abs(cur) >= self.min_margin and cert_shift <= self.cert_delta:
                stop_reason = "compressed_certified"
                break

        con = min(pos, neg) / (max(pos, neg) + EPS)
        final = z * (1 - self.cg * con)
        p = sigmoid(final / max(self.temp, EPS))
        cut = len(active)
        shadow0 = sum(abs(r[1]) for r in rows[cut:] if r[4] == 0)
        shadow1 = sum(abs(r[1]) for r in rows[cut:] if r[4] == 1)
        trace = {
            "key": key,
            "p": p,
            "active": [(s, c, y, ck, abs(v)) for _, v, s, c, y, ck in active],
            "used": cut,
            "contradiction": con,
            "hazard": hazard,
            "required": required,
            "certificate_shift": cert_shift,
            "stop_reason": stop_reason,
            "shadow_mass": (shadow0, shadow1),
        }
        return p, trace

    # ---- learning (adaptive_exchange) -----------------------------------
    def feedback(self, e):
        if "adaptive_exchange" not in self.cures:
            super().feedback(e)
            self._update_aux(e)
            return
        self._feedback_adaptive(e)
        self._update_aux(e)

    def _feedback_adaptive(self, e):
        """Sequential-equivalent feedback with an online exchange rate.

        Faithful to the frozen recurrence (closed-form batching is only an
        ops optimization), but the anchor gain, evidence learning rate, and
        forgetting are modulated by how wrong memory has recently been.
        """
        tr = e["trace"]
        truth = e["truth"]
        key = e["key"]
        err = float(truth) - float(tr["p"])
        self.last_fb[key] = e.get("time", self.last_fb[key])

        surprise = self._surprise(key)
        # Down-weight the self-protecting anchor when it keeps being wrong;
        # speed up world-learning; forget stale memory faster.
        anchor_scale = max(self.exch_anchor_floor, 1.0 - self.exch_anchor_k * surprise)
        lr_scale = 1.0 + self.exch_lr_k * surprise
        fd = max(0.5, self.fd - self.exch_forget_k * surprise)
        sd = self.sd  # slow state kept stable

        active = tr["active"]
        den = sum(a[-1] for a in active) + EPS
        for s, c, y, ck, strength in active:
            correct = 1.0 if y == truth else -1.0
            elig = strength / den
            d = lr_scale * self.lr * correct * elig * (0.35 + abs(err))
            self.cf[ck] = fd * self.cf[ck] + d
            self.cs[ck] = sd * self.cs[ck] + 0.10 * d
            sk = (s, c)
            self.src[sk] = self.srd * self.src[sk] + 0.16 * d
            self.up += 3

        tk = (key, truth)
        fk = (key, 1 - truth)
        a = lr_scale * self.lr * (self.anchor * anchor_scale) * (0.25 + abs(err))
        self.cf[tk] = fd * self.cf[tk] + a
        self.cf[fk] = fd * self.cf[fk] - a
        self.cs[tk] = sd * self.cs[tk] + 0.08 * a
        self.cs[fk] = sd * self.cs[fk] - 0.08 * a
        self.up += 4

        m0, m1 = tr.get("shadow_mass", (0.0, 0.0))
        total = m0 + m1
        if total > EPS:
            for y, m in ((0, m0), (1, m1)):
                if m <= EPS:
                    continue
                ck = (key, y)
                correct = 1.0 if y == truth else -1.0
                rd = self.shadow_scale * lr_scale * self.lr * correct * (m / total) * (0.35 + abs(err)) * self.reserve_claim_gain
                self.cf[ck] = fd * self.cf[ck] + rd
                self.cs[ck] = sd * self.cs[ck] + 0.10 * rd
                self.up += 2
