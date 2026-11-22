# U23 — Real city fabric

## Goal

Grow past the seed neighborhood into city quarters with continuous green fingers
and civic/commercial program — readable as a city on WebGL and MapLibre.

## Contract

- Continuous **3 City Country Fingers** (full-column parks, not per-block crumbs)
- Schools, playgrounds, shop bays / market / grocery, town hall, police, bank, clinic, utilities
- Country fringe + country road south of each quarter
- Two quarters: `district-metro` + `district-metro-east` (~2 km span)
- WebGL: **no fog**; orbit far / ground sized for metro zoom-out
- Rail: City (not “neighborhood”); plain language
- No new `pl` / Lean / catalog / MCP

## Commands

```bash
uv run python demo/build_district.py
uv run python scripts/lint_spatial.py
uv run pytest tests/test_kits.py tests/test_spatial_structure.py tests/test_webgl_quality.py
```
