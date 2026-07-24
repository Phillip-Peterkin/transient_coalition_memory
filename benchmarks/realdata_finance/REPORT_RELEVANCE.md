# Sensory relevance gate — successful fresh-company confirmation

## Plain result

**This is now the active experimental TCM front end.**

The system first asks a simple human question before it forms a coalition:

> Is this story actually about the company I am deciding about?

If the answer is no, the story does not get to rewrite that company’s memory.
If no relevant story remains, the system keeps its current memory instead of
turning an empty input into an accidental “up” guess.

This is paired with the earlier confirmed evidence rules:

1. A source that says Positive almost all the time contributes little when it
   says Positive; a rare message from that source carries more information.
2. Several same-direction stories are not counted as separate independent
   votes.

The implementation is `tcm.SensoryGatedCellular`; the title-based input gate
is `relevance.RelevanceFinanceNewsStream`.

## Why this was needed

The feed often placed plainly unrelated titles in a company’s article bucket.
For example, an Apple bucket included headlines about coal, Ukraine, and
Brazilian election advertising. A person would not count those as evidence
about Apple. The frozen model had no way to know that.

## Fresh-company confirmation

This result was locked before scoring in
[`RELEVANCE_CONFIRMATION_PROTOCOL.md`](RELEVANCE_CONFIRMATION_PROTOCOL.md).
The 29 declared companies were separate from both earlier company groups and
were selected by raw story availability only. Yahoo had no usable historical
quote for PARA, so 28 companies supplied price-labeled events.

The first 70% of dates only warmed up the online model. The final 30% was
scored once: 521 decisions, including 253 change events.

| Model | Overall accuracy | Change detection | “Up” predictions | Reports used | Brier |
|---|---:|---:|---:|---:|---:|
| Calibrated TCM | 49.3% | 22.1% | 53.9% | 1.13 | 0.256 |
| **Sensory-gated TCM** | **52.0%** | **28.1%** | 48.2% | **0.40** | 0.256 |

The change-detection gain is **+5.9 points**. Paired bootstrap range:
**+1.2 to +10.7 points; p=0.006**. It clears the pre-set pass bar of +3
points, loses no overall accuracy, and does not become an “always up” system.

## What it means

This is a real win, but not the final cure:

- It is the first mechanism that improved change detection on a fresh company
  group after being designed elsewhere.
- It uses about **64% less** incoming evidence, because it declines to process
  misattributed stories.
- It reaches 28%, not the 45% first-win target. The major change-blindness
  problem remains.
- It confirms that **sensory relevance comes before memory updating**. We
  cannot solve a memory problem while allowing irrelevant inputs to become
  evidence.

## Scientific limits

- This is a fresh-company test within the same FMP-news / Yahoo-price source
  and calendar, not an independent-dataset replication.
- The explicit company-name dictionary favors precision over recall. It may
  discard genuinely relevant broad-sector reports. The next version should
  learn event relevance from richer text while preserving the same causal,
  no-future-look rule.
- Overall-accuracy improvement is positive but uncertain on this sample
  (+2.7 points, p=0.084). The confirmed result is specifically the
  change-detection improvement.
