# Real-data finance/news v0 — first locked-parameter run

**Status:** first contact with this stream. Wave XI hyperparameters locked.
No mechanism cures attempted. See [`PROTOCOL.md`](PROTOCOL.md).

## Stream

| | |
|---|---|
| Events | 6,121 news-bearing `(symbol, day)` decisions |
| Symbols | 38 liquid US equities |
| Publishers | 12 sites (Benzinga, GlobeNewswire, InvestorPlace, …) |
| Window | 2022-08-12 → 2023-10-04 |
| Label | next-session close-to-close direction (Yahoo Finance) |
| Truth up-rate | 0.496 |
| News Positive rate | 0.900 (severe bullish publisher skew) |
| Mean reports / event | 2.49 |
| Multi-source fraction | 0.378 |
| Mean within-event agreement | 0.837 |
| Flip events | 2,641 (43%) |

Chronological split: **contact** = first 70% of trading days (3,832 events);
**holdout** = last 30% (2,289 events).

## Holdout results (confirmatory for locked v0)

| Method | Accuracy | Flip accuracy | Non-flip accuracy | Avg activated | Brier | ECE |
|---|---:|---:|---:|---:|---:|---:|
| Persistence oracle | 0.5028 | 0.1445 | — | 0.00 | 0.497 | 0.497 |
| Memoryless majority | 0.5037 | **0.4923** | — | 2.40 | 0.482 | 0.474 |
| Dynamic Bayes | 0.5046 | **0.4933** | — | 2.40 | **0.265** | **0.075** |
| Fair provenance graph | 0.5177 | 0.3911 | — | 2.40 | 0.365 | 0.305 |
| **Exact-batched TCM** | **0.5264** | 0.1827 | — | **1.74** | 0.282 | 0.137 |

TCM pred-up rate on holdout: 0.569. Memoryless majority: 0.965 (follows the
90% Positive news flood). Market up-rate ≈ 0.50.

## What this says (honestly)

1. **Persistence is not the whole game here.** Unlike the contaminated July 2011
   stock setup (~89% persistence oracle), next-day equity direction in this
   window is near a coin flip. Headline accuracy gaps are small and must be
   read carefully.
2. **Flip detection failure reproduces on a new stream.** Locked TCM is worst
   among learning methods on flips (0.18) while memoryless majority / dynamic
   Bayes sit near 0.49. This matches NORTH_STAR ledger items 2–3 (self-sealing
   attractor, confirmation-biased recruitment) without using the old stock or
   weather beds.
3. **Sparse activation still holds.** TCM uses ~1.74 reports vs ~2.40 for full
   coalitions — the compute story survives; the change-response story does not.
4. **Publisher skew is the regime.** Evidence is ~90% Positive while labels are
   balanced. Methods that trust raw report majorities predict “up” almost
   always. TCM’s anchor resists that flood enough to edge accuracy, then fails
   when the world actually flips — a clean illustration of static
   memory-vs-world exchange rate (ledger item 4).
5. **Independence is limited.** Mean agreement 0.84; recruitment counts are not
   independent sample sizes.

## Non-claims

- This does **not** establish real-world superiority.
- Contact-split numbers are exploratory; holdout is the confirmatory slice for
  these locked weights only.
- No exchange-rate learning, evidence-led recruitment, or other cure was tested.

## Next mechanism work (priority from NORTH_STAR)

Cure ledger items 2–5 against this harness + held-out confirmation rules —
starting with an online memory-vs-world exchange rate — without retuning the
frozen Wave XI reference in place.
