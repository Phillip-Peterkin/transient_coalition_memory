# Source-trust regime pack

Claim memory already faded. Source trust did not — that was wrong for a
machine that must track changing reliability.

Three pieces (your framing), all default **off** so sealed confirmation8 is
unchanged:

1. **Constant fade** (`source_forget=0.985`) — baseline repair; same idea as
   the winning fading source tracker. Simple; still a fixed constant.
2. **Never-zero floor** (`source_share=0.03`) — Fixed-Share-style mix toward
   the Laplace prior so a disgraced source can re-earn trust and a hero can
   be disowned quickly.
3. **Shift-triggered hard discount** (`source_shift_window=12`, gap `0.35`,
   discount `0.15`) — per-source mini change-point: when recent errors jump
   above the long-run rate, crush that source’s old history. Mnemosheath
   idea pointed at sources: “this source just became someone else.”

## Where enabled

Delayed-aggregation evaluator (`evaluate.py`) turns the pack on for ACI/Aware.
Cell defaults remain `forget=1`, `share=0`, `shift_window=0`.

## Honesty

- Not a silent rewrite of spent Weather/Finance confirmation wins
- Direction: keep improving with use under drift — not “already flawless”
- Screen artifact after this pack:
  `results/dbsa_v1_contract_screen_source_forget.json`
