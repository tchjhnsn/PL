# U4 synthesis

## Decision

Base: candidate B (one module per `condition.check` id; checker only does `CHECKS[id]`).

Graft from A:
- Judged 110 / 180 → `needs_judgment` with unanswered evidence; absent from `satisfied`
- `projects/seed-house.json` selects all twelve patterns
- `pl check` is the only live subcommand

## Why B

- DESIGN §3.2 layout: `conditions/` registry + one module per check
- Model the Domain: table/registry over branching on pattern number
- Matches U3 shared houses: ten computed pass on pass-house, fail on fail-house

## Implement

`docs/design/u4-sketch-b.md` for registry/modules/CLI; A for judged status and seed project.
