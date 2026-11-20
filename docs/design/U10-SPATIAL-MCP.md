# U10 — Spatial MCP tools

Contract. Adds two stdio MCP tools over SpatialStructure. Does not change `pl check`, Lean, or Blender.

## Tools

| Tool | Input | Result |
|---|---|---|
| `spatial_get` | `plan` path; optional `place` id | Full validated plan JSON, or one place object when `place` is set |
| `model_measures` | `plan` path; optional `place` id; optional `kind` | Named measures (and `clear_width` when a place is given) |

Both call `load_spatial`. They open no IFC and import neither `ifcopenshell` nor `bpy`. A missing plan or schema failure is an error tool result. An empty measures list is a successful result.

## Acceptance

```bash
uv run pytest tests/test_mcp.py tests/test_spatial_structure.py tests/test_spatial_lint.py
uv run python scripts/lint_spatial.py
```

`list_tools` includes the original five plus `spatial_get` and `model_measures`. Seed `demo/data/plan-model.json` returns under `spatial_get`. `model_measures` with `place: "a-balcony"` reports depth 6.0 and `clear_width` 6.0.

## Non-goals

- No new `pl` command.
- No plan subject wired into `evaluate` / `CHECKS`.
- No Mathlib / Lean edit.
- No Blender change.

## Exit

Draft PR titled `U10 Spatial MCP tools`. Agents do not merge.
