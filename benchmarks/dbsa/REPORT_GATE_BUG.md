# Bug find: false “no evidence” on large agreeing batches

Plain description: when many sources agreed, the system shrank each source’s
strength by the group size, then asked “is anyone informative?” using that
shrunken number. A room full of agreeing evidence looked empty, so the machine
ignored the votes and leaned against its memory instead. Aware’s
“agreement can be evidence” path never got a chance.

## Fix

- “Is anyone informative?” now uses each source’s **raw** strength.
- Group-size discount still applies when **adding** agreeing votes together
  (so cheerleaders are not counted as independent).

## Honesty

- This is a logic bugfix, not a knob retune.
- Spent Weather confirmation beds are **not** reopened as new wins.
- Post-fix 24-seed screen artifact:
  `results/dbsa_v1_contract_screen_after_gate_fix.json`
- Gate still **FAIL** overall (drift / copy worlds still lose), but
  correlated batches stop being falsely silenced.

Regression test: `tests/test_correlation_gate.py`.
