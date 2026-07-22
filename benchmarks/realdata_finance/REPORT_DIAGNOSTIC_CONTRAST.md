# Diagnostic contrast — development screen

## Question

Can DCAI's architectural laws be baked into TCM's silence-escape cell (not as
wrappers) and improve contact-tail finance change detection?

## What was baked

`tcm.DiagnosticContrastCellular` subclasses `SilenceEscapeCellular`:

1. **Slot preservation** — `preserve_cloud` (all reports paraphrase memory
   direction) is null sensation, *in addition to* confirmed cheerleader-null
   (all-Positive).
2. **Typed paraphrase demotion** — on slot-edit sensation, memory-agreeing
   reports are scaled down in recruitment ranking.
3. **Escape hazard** — keep silence-escape PE+|ρ| **sum**. Noisy-OR survival
   over those two scalars failed hard on contact (flip collapsed ~49% → ~40%).

## Contact-tail result (development `data/`)

| cell | acc | flip | nonflip | pred-up |
|---|---:|---:|---:|---:|
| clean baseline | 0.504 | 0.408 | 0.591 | 0.696 |
| silence escape (frozen) | 0.506 | 0.491 | 0.521 | 0.486 |
| dcai slot0.35 | 0.507 | 0.502 | 0.512 | 0.496 |
| **dcai slot0.50** | **0.514** | **0.509** | **0.519** | **0.492** |
| dcai slot0.65 | 0.513 | 0.504 | 0.522 | 0.495 |

Selected winner: `slot_preserve_scale=0.50` (gate pass; best flip lift vs silence;
vs silence flip Δ≈+0.019, p≈0.12 on contact — modest, not dramatic).

## Ablation honesty

- Slot-null **replacing** cheerleader-null → up-skew returns (~0.71), gate fail.
- PE/ρ noisy-OR survival → large flip regression.
- Preserve-cloud + demotion + sum escape → modest contact lift over silence.

## Next

Frozen one-shot on virgin `confirmation5` vs clean and silence-escape.
No retune on that universe.
