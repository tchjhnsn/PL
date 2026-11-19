# U7 synthesis

## Decision

Base: candidate B (run ledger — `prefix` snapshots of the pass house, `scripts/drive_run.py`, `record_run` / `record_step`, twelve preserving steps with growing `satisfied`, final `report.json` with the ten computed patterns).

Graft from A:

- `Session` transition table for §2.5 in `adapters/blender/bridge.py` (no socket; `connect` is the tested transition).
- `export_ifc` raises until Bonsai is wired.
- `adapters/blender/README.md` is the gated live path (Blender 4.x + Bonsai; outside the merge check).
- Panel draws `report unavailable` when there is no run; otherwise `report_lines` from the newest `report.json`.

## Why B

- The ledger shows the house grow; fixture-replay (A) logs the finished house on both sides of every step.
- `pl step` remains the sole writer of step JSON and the sole judge of `preserved`.
- CI never launches Blender; `--check` is the merge witness.

## Implement

`docs/design/u7-sketch-b.md` + the A grafts above.
