# U1 synthesis

## Decision

Base: candidate A (minimal fit to live gate). Graft from B: none required for the done-when.

A keeps one loader (`load_catalog`), puts missing targets and back-edges on `Catalog`, and leaves `projects/` empty. B's `LinkReport` / dual `larger` edge counting / seed project file are clearer for later graph work, but they widen U1 past "records validate, targets exist, back-edges reported."

## Why A

- Laziness Protocol: twelve patterns + five schemas + one loader meet the unit check.
- Live gate unchanged: `catalog.schema.json` / `projects.schema.json`.
- Forward smaller-links so U2 can `decide` numeric order; a fixture still proves a downward link is reported.
- No project seed: projects schema is present and inert until a later unit needs it (same posture as the three unused schemas).

## Reopen B when

U2 or the sequencer needs first-class `Link` values or inverse-edge audits that A's `smaller`/`larger` arrays make painful.

## Implement

`docs/design/u1-sketch-a.md` verbatim for schemas, seeds, `catalog.py`, validate script stdout, and tests.
