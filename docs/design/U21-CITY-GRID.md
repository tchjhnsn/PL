# U21 — 2×2 city grid

Contract after U20. Draft for agents; open a PR when acceptance is green. Do not merge from agents.

## Goal

Answer “are we ready to build a city?” with a **closed 2×2 block grid**: four blocks, four street axes (Main / Cross / East / North), every parcel addressed — a city *fragment* you can read on MapLibre and orbit in WebGL.

## In scope

1. `block-northeast` with Lots G/H (courts, gates, massings, addresses, rhythm).
2. Extend `street-east` through Cross to North; add `street-north` closing the north edge; lane joins North Street.
3. District labeled **Seed City**; city-span measures; CityJSON Road for North Street.
4. Docs + tests. No new catalog patterns, `pl`, Lean, or MCP.

## Acceptance

```bash
uv run python demo/build_district.py
uv run python scripts/lint_spatial.py
uv run pytest tests/test_webgl_quality.py tests/test_spatial_structure.py tests/test_cityjson_export.py tests/test_maplibre_city.py
# manual: /map.html + WebGL District — four blocks in a grid
```

## Non-goals

- Procedural city generator / infinite grid.
- Urban pattern catalog expansion.
- Photoreal city twin.

## Still true

Cite pattern numbers and names only. House A stays the detailed Decided witness; other lots stay massing.
