# U13 — Approach enclosure

Contract for the unit after U12. Draft for agents; open a PR when acceptance is green. Do not merge from agents.

## Goal

Make the seed district’s street → path → court → door sequence readable in WebGL by drawing SpatialStructure `walls` and hosting the approach opening in a garden wall — so 110 Main Entrance / 112 Entrance Transition no longer show a freestanding door on the path.

## In scope

1. Extrude `plan.walls` in `demo/webgl.js` at the Frames stage (and later): garden/court walls ~1.35 m, building walls ~2.7 m, balcony rails ~1.0 m. Leave a gap at each opening whose center lies on the wall segment.
2. Keep schema `openings[].component` as `door` | `window` (no schema churn). Relabel `a-door-approach` as **Court Gate** in `demo/build_district.py`; WebGL draws a short leaf + posts on garden walls.
3. Regenerate `demo/data/plan-model.json` from `build_district.py`. Spatial lint stays green.
4. Document here and in `AGENTS.md`. No new `pl` command, Lean edit, MCP tool, or catalog pattern.

## Acceptance

```bash
uv run python demo/build_district.py
uv run python scripts/lint_spatial.py
uv run pytest tests/test_webgl_quality.py tests/test_spatial_structure.py tests/test_spatial_lint.py
# manual: python3 demo/serve.py → Openings stage — path meets gate in w-court-s; main door on hall
```

## Non-goals

- No second district / city / block continuum.
- No purchased GLB houses, HDRI, or SSAO.
- No change to `pl check` or judgment for 110 / 180.

## Still true

Stages still hide later work. Satisfaction is still the check report. Cite pattern numbers and names only.
