# U2 synthesis

## Decision

Base: candidate A. Graft from B: none required — A already makes `catalog_to_lean.py` the sole writer and puts `--check` before `lake build`.

B's extra theorems (prefixes, reverse-edge witness, spans, preserving run) exceed the U2 done-when. Keep them for a later PR if a sequencer needs them.

## Implement

`docs/design/u2-sketch-a.md` verbatim.
