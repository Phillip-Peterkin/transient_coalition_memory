# Active Coalition Inference — development

## The cake

One Friston-native cell (`ActiveCoalitionCellular`):

- Prior never enters report strength (likelihood ratios only)
- Silence / all-Positive / near-zero-Δ clouds = null channel with PE+|ρ|
  anti-prior mix (precision that continuation is failing)
- Discriminative reports recruit by |Δ|, certify when unread mass cannot flip
- Prior and evidence meet once at the posterior

## Contact-tail

| cell | acc | flip | nonflip | pred-up |
|---|---:|---:|---:|---:|
| clean | 0.504 | 0.408 | 0.591 | 0.696 |
| silence | 0.506 | 0.491 | 0.521 | 0.486 |
| **ACI md0.15/sh0.55/ρ0.3** | **0.501** | **0.502** | **0.500** | **0.498** |

Gate: pass. Selected winner frozen for confirmation8.

## Preflight

`preflight_active_coalition.py` — prior-leak, null channel, FE certificate,
silence PE — all checks passed before scoring.
