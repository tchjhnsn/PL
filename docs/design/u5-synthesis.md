# U5 synthesis

## Decision

Base: candidate B (Python twins of `ValidSequence` / `Preserving`; seed test parses `numericOrder` from Buildings.lean).

Graft from A: pass→fail house exits 1 with `preserved: false`; same house twice exits 0; CI adds `pl sequence` only.

## Why B

- DESIGN: sequencer matches the Lean definition on the seed
- Tests compare against generated Lean oracle, not a restated list

## Implement

`docs/design/u5-sketch-b.md` + A CLI/exit notes.
