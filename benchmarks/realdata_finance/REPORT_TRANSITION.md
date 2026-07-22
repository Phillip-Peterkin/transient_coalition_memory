# Transition-investigation circuit — fresh-company confirmation

## Plain result

**Do not bake this circuit into the active model.**

It looked promising while we designed it on old contact data: change detection
rose from 22% to 29%. On the pre-declared fresh-company test, it only rose from
24.0% to 25.5%. That result is too small and too uncertain to trust.

## What we tested

The circuit was inspired by the HRF energetic-gating paper:

1. Only a **confident wrong prediction** adds a warning signal.
2. Enough warnings open a short-lived **investigation mode**.
3. In that mode, calibrated evidence that disagrees with old memory cannot be
   turned around by the old memory.
4. The mode gradually closes, rather than staying permanently open.

It was always combined with the previously successful source-calibration and
correlation-discounting front end.

The exact values were chosen using old contact data and written into
`CONFIRMATION_PROTOCOL.md` *before* the fresh-company data was scored.

## Fresh-company result

The 33 declared confirmation companies were disjoint from the development
companies. They were chosen using news-row availability only, not price
outcomes or model scores. Yahoo returned no usable historical quote for WBA,
so its news rows had no label and were automatically excluded; 32 companies
contributed scored events. The first 70% of dates warmed up the model; only the
final 30% was scored (680 events, 325 change events).

| Model | Overall accuracy | Change detection | “Up” predictions | Reports used |
|---|---:|---:|---:|---:|
| Calibrated TCM | 47.1% | 24.0% | 53.5% | 1.15 |
| Investigation circuit | 46.9% | 25.5% | 56.0% | 1.15 |

The change-detection difference was **+1.5 points**, with a plausible range
from **−0.3 to +3.4 points**. Our pre-set pass bar was at least +3 points,
overall accuracy no worse than −1 point, and no “always up” behavior.
It failed that bar.

## What this means

This is useful, not a dead end:

- The earlier contact-only jump was mostly overfitting to the old companies.
- A prediction-error alarm by itself is not enough. It can tell the system
  “something may have changed,” but it cannot tell it **what the new situation
  is**.
- The current feed gives TCM only a source name and a Positive/Negative label.
  Humans also use the *meaning* of a headline: whether it describes a new
  event, a repeated press release, an earnings surprise, a lawsuit, a product
  failure, and so on.

The next architecture direction should therefore be **semantic novelty and
event identity**: give the system a compact representation of what a report is
about, let it recognize a genuinely new event pattern, then let the existing
calibrated evidence system decide whether that event should change belief.
That is a more human-like change detector than merely reacting harder after it
was wrong.
