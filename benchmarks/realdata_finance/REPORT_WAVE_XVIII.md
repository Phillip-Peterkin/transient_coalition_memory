# Wave XVIII — prediction-error-driven trust, finance development result

## Plain result

**Wave XVIII does not pass the finance development gate. Do not promote it to
the active model and do not run it on Weather.**

It did prove that the proposed brain-shaped loop has a real effect: it lifted
change detection from 27% to about 40% on the finance development slice. But
it did so by becoming too willing to predict “up” (~70%). The more careful
version only raised mistrust when the model had ignored relevant counter-
evidence; that reduced the bias but topped out around 38%, still below the
required 45%.

## What was implemented

For each item, a confident wrong prediction raises a local mistrust state.
Before that item's next decision, the same state:

1. increases hazard and recruits at most one more relevant report;
2. lowers the claim anchor's weight;
3. raises the floor beneath fresh relevant evidence that disagrees with stale
   memory.

Confident correct predictions relax the state. The zero-mistrust path exactly
matches `SensoryGatedCellular`; tests verify parity, wrong-error activation,
correct relaxation, item isolation, and all three next-decision controls.

## Finance-only development results

Scored period: 60 old finance development days, 1,227 decisions, 565 change
decisions. The active sensory baseline was:

| Model | Overall accuracy | Change detection | “Up” predictions | Reports used |
|---|---:|---:|---:|---:|
| Active sensory baseline | 49.1% | 27.1% | 56.8% | 0.79 |
| Wave XVIII, broad trust | 50.7% | 40.2% | 69.5% | 0.89 |
| Wave XVIII, evidence-gated trust | 50.5% | 38.1% | 66.7% | 0.81 |

The broad version fired its mistrust state after almost every loss, including
ordinary market noise and no-evidence situations. The evidence-gated version
only fires when a relevant current report already contradicted the prediction.
That is more sensible, but still fails the one-bar rule:

- target change detection: **45%**
- maximum observed: **40.2%**
- balanced prediction requirement: ≤65% “up”
- best evidence-gated version: **66.7% “up”**

Changing the decision threshold does not solve it: thresholds that remove the
up bias reduce change detection further. This is not a threshold-tuning issue.

## What this means

The trust loop is not nonsense. It makes the architecture more responsive to
genuine counter-evidence. But the remaining relevant finance feed is still
mostly a thin, biased Positive/Negative signal. When the model opens its gate,
there often is not enough reliable evidence on the other side to tell it what
the world changed *to*.

The active model therefore remains `SensoryGatedCellular`: first ensure the
story is about the company, then calibrate source bias and redundancy. Wave
XVIII remains a development prototype, not a result.

## Weather status

No Weather run occurred. This repository contains no Weather data, code,
protocol, or locked untouched split. It would be dishonest to create a new
Weather harness after finance development and call it the promised untouched
final test. Recovering the original Weather split/harness is required before
that final test can happen.
