# U16 — House storey fix (+ building line stub)

Contract after U15. Draft for agents; open a PR when acceptance is green. Do not merge from agents.

## Goal

Stop the dysfunctional **upper door onto the living roof**. Stack the bedroom on the living footprint, reach it by a stair, and put the balcony east of the upper room. Keep city Layer 1 moving with a named **building line** measure on the main street face.

## What was wrong

`a-bedroom` sat north of `a-living` with `floor_elevation_m: 3` while WebGL extruded non-balcony rooms from grade. `a-door-bed` on the shared wall sat at elevation 3 — above the living volume — so the leaf opened onto the living roof.

## In scope

1. Remodel House A: `a-bedroom` shares the living ring at elev 3.0; `a-balcony` east at elev 3.0; `a-stair` in the living; remove `a-door-bed`; balcony door from bedroom only.
2. WebGL: elevated rooms use `shellBottom = elev`; skip grade extrusion through the roof below; stair treads; no gable under an upper storey; wall gaps ignore upper openings on grade walls.
3. Spatial lint: same-XY shells allowed when storeys stack (upper floor ≥ lower ceiling).
4. Building line stub: named measure `m-building-line-main` along the House A/B front setback (Layer 1 item 3).
5. `__plWebgl.setCamera` / `setStage` / `setMode` for screenshot self-verify.
6. Docs + tests. No schema enum / `pl` / Lean / MCP.

## Acceptance

```bash
uv run python demo/build_district.py
uv run python scripts/lint_spatial.py
uv run pytest tests/test_webgl_quality.py tests/test_spatial_lint.py tests/test_spatial_structure.py
# manual: Openings + House A — upper door only to balcony; stair in living; no door onto living roof
```

## Non-goals

- No second block / MapLibre.
- No change to Topology `pl check` fixtures unless a later unit remaps IFC.

## Still true

City remains the destination. Cite pattern numbers and names only.
