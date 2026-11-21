# U15 — Street frontage / plot series

Contract for the unit after U14. Draft for agents; open a PR when acceptance is green. Do not merge from agents.

## Goal

Make the seed district read as a **plot series** on the street (and green), not one finished House A approach beside orphan massings. Front courts, garden walls, and gates on Lots B / C / D reuse the U13 enclosure vocabulary so the block face starts to look like a city street wall.

## In scope

1. Set back foundations/massings B, C, D; author `b-court`, `c-court`, `d-court` with street/green garden walls and gates (`b-door-approach`, …). Stub `path-approach-b` from the main sidewalk into Court B.
2. Named frontage measures (`m-frontage-a`…`d`) and frontage interfaces; network address nodes for B/C/D.
3. WebGL: existing `buildWalls` / gate leaf apply (wall ids contain `court`). No new schema enum, `pl` command, Lean, or MCP tool.
4. Regenerate `plan-model.json` (+ CityJSON / pattern-components). Spatial lint stays green.
5. Document here and in `AGENTS.md`.

## Acceptance

```bash
uv run python demo/build_district.py
uv run python scripts/lint_spatial.py
uv run pytest tests/test_webgl_quality.py tests/test_spatial_structure.py tests/test_spatial_lint.py
# manual: python3 demo/serve.py → Openings — Main Street shows gated courts A and B in series
```

## Non-goals

- No second block, MapLibre, or new catalog patterns.
- No full interiors for B/C/D (massing stays).
- No change to `pl check` / judgment for 110 / 180.

## Still true

City is the destination; this unit is Layer 1 (finish the seed block face). Cite pattern numbers and names only.
