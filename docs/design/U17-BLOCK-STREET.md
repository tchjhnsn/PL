# U17 — Block place + second street

Contract after U16. Draft for agents; open a PR when acceptance is green. Do not merge from agents.

## Goal

Make the seed district read as **true block morphology**: named `block` places, a second (local) street with a lane junction, and mid-block permeability — Layer 2 of the city roadmap.

## In scope

1. `block-south` (Lots A–B) and `block-north` (Lots C–D) as SpatialStructure places; lots parent to their block.
2. `street-cross` local ROW with `carriageway-cross` + `sidewalk-cross-n`; network junction `n-junc-cross` (lane × cross); vehicle edges on the cross street.
3. North lots face Cross Street (courts/gates/frontage interfaces); workshop shrinks south of the cross ROW.
4. `path-midblock` through-block passage (east of the pond) linking green ↔ Cross Street.
5. CityJSON: Cross Street as `Road` + `TrafficArea` children; blocks as `LandUse` `class: block`.
6. Docs + tests. No new `pl` command, Lean, MCP tool, or catalog pattern.

## Acceptance

```bash
uv run python demo/build_district.py
uv run python scripts/lint_spatial.py
uv run pytest tests/test_webgl_quality.py tests/test_spatial_structure.py tests/test_spatial_lint.py tests/test_cityjson_export.py
# manual: python3 demo/serve.py → District — two blocks, Cross Street, mid-block path
```

## Non-goals

- No MapLibre / multi-district city product.
- No full interiors for B/C/D/workshop.
- No change to Topology `pl check`.

## Still true

City remains the destination. Cite pattern numbers and names only.
