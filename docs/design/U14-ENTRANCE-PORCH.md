# U14 — Entrance porch

Contract for the unit after U13. Draft for agents; open a PR when acceptance is green. Do not merge from agents.

## Goal

Complete the seed district’s arrival sequence after the court gate: **gate → court → porch → hall**. 112 Entrance Transition and 130 Entrance Room gain a covered porch at the main door — still one Decided component, not a city.

## In scope

1. Author `a-porch` in `demo/build_district.py`: void place, `component: "porch"`, ring ~2 m deep against the hall south wall, patterns 110 / 112 / 130, sit-on `found-a`, side pier walls `w-porch-w` / `w-porch-e`, measure `m-porch-depth`, interface `if-main` between porch and hall.
2. WebGL: `addPorch` draws deck + posts + flat canopy — do **not** solid-extrude the porch as a room box. U13 walls still host the main door leaf.
3. Regenerate `demo/data/plan-model.json`. Spatial lint stays green.
4. Document here and in `AGENTS.md`. No new `pl` command, Lean edit, MCP tool, schema enum, or catalog pattern.

## Acceptance

```bash
uv run python demo/build_district.py
uv run python scripts/lint_spatial.py
uv run pytest tests/test_webgl_quality.py tests/test_spatial_structure.py tests/test_spatial_lint.py
# manual: python3 demo/serve.py → Openings — path → gate → court → porch canopy → main door
```

## Non-goals

- No second district / city / block continuum.
- No schema change (`component` stays a free string; `kind` is `void`).
- No change to `pl check` or judgment for 110 / 180.

## Still true

Stages still hide later work. Satisfaction is still the check report. Cite pattern numbers and names only.
