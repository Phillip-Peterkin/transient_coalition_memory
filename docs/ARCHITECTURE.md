# Architecture

TCM treats memory as a persistent adaptive substrate rather than a collection of retrieved records.

## Inference

For each question, candidate reports are scored using direct evidence, fast claim state, slow claim state, and source reliability. The strongest candidates are recruited one at a time into a temporary coalition.

Recruitment is adaptive. Contradiction, disagreement between fast and slow memory, volatility, and time since feedback increase the amount of evidence required. Recruitment stops when the current decision is certified against the compressed dormant reserve or when the budget is exhausted.

## Dormant reserve

Evidence that is not activated is summarized as positive and negative coalition mass. This reserve is used to test whether omitted evidence could change the answer. It is also retained as a shadow eligibility signal for delayed learning.

## Learning

Feedback updates fast and slow claim states and source priors. Active evidence receives eligibility-weighted updates. Dormant evidence receives compressed aggregate updates, allowing the system to learn from information that was available but unnecessary for the immediate decision.

## Exact batching

Wave XI replaces repeated scalar recurrences inside each answer coalition with their exact closed-form equivalent. This reduces writes without changing the mathematical update sequence.

## Calibration

Wave XII evaluates temperature, Platt, and isotonic post-hoc calibration. The substrate, gate, and learning rules remain locked. Temperature scaling improves probability reliability without altering the binary decisions.
