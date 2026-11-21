# U20 — MapLibre city surface

Contract after U19. Draft for agents; open a PR when acceptance is green. Do not merge from agents.

## Goal

Ship the Layer 4 **city product surface**: a MapLibre figure–ground map over `district.geojson`, linked from the WebGL Decided viewer. WebGL stays the detail/Decided path; the map is the neighborhood glance.

## In scope

1. `demo/map.html` + `demo/map.js` — MapLibre GL from CDN; load `data/district.geojson`.
2. Figure–ground paint: buildings solid dark; streets mid-gray; lots/green softer; district envelope invisible; network centerlines by hierarchy.
3. Click → selected place label in the rail; fit bounds to features.
4. Link from `index.html` “Also”. Contract + AGENTS + smoke test (file presence / feature count hook).
5. No `pl` / Lean / MCP / schema change. No Cesium.

## Acceptance

```bash
uv run python demo/build_district.py
uv run pytest tests/test_maplibre_city.py
python3 demo/serve.py   # → /map.html — three blocks readable as figure–ground
```

## Non-goals

- Pattern overlay judgment UI at street scale (later).
- Vector tiles / MVT pipeline.
- Photoreal 3D extrusion as the default city view.

## Still true

Cite pattern numbers and names only. Visual language: `docs/design/VISUAL-LANGUAGE.md`.
