# Seed district — WebGL entry + plan symbology

**Entry level:** Three.js WebGL over SpatialStructure (`index.html` / `webgl.js`).  
**Optional advanced:** Blender + Bonsai IFC path (`adapters/blender/`, `docs/design/E2E-BONSAI-EFFECT.md`).  
**2D companion:** SVG plan symbology at `plan.html`.

Naive marketing dogfood is **deferred**. See `docs/design/WEBGL-ENTRY.md`.

## Owned layer

```text
pattern-language.plan-symbology
```

Semantic types can come from CityJSON/IFC/BOT. Plan marks and WebGL materials are our layer.

## Run

```bash
uv run python demo/build_district.py   # validates SpatialStructure + writes data/
python3 demo/serve.py
# WebGL entry:  http://127.0.0.1:8765/
# 2D plan:      http://127.0.0.1:8765/plan.html
# concept graph: http://127.0.0.1:8765/concepts.html
```

## Concept graph

`concepts.html` searches every node in `data/concept-graph.json`. Status chips (`have`, `partial`, `todo`, `placeholder`) and a layer menu narrow the list. A concept opens its `depends_on`, `parent_of`, `sibling_of`, `maps_to`, `specializes`, and `renders_as` neighbors in both directions, with source tags and a one-hop diagram. `build_district.py` copies the file from `docs/design/spatial-concept-graph.json`. Fetch needs the demo server — `file://` blocks it.

## Files

| File | Role |
|---|---|
| `data/plan-model.json` | SpatialStructure: places, network, measures, interfaces, openings, patterns |
| `data/pass-report.json` | Seed check statuses for WebGL pattern chips |
| `data/concept-graph.json` | Copy of `docs/design/spatial-concept-graph.json` |
| `data/district.city.json` | CityJSON export (interchange) |
| `data/district.geojson` | GeoJSON sibling |
| `webgl.js` / `index.html` | **Entry:** Three.js extrusions + pattern focus |
| `plan.js` / `plan.html` | SVG plan renderer (flow + dims + symbology) |
| `concepts.js` / `concepts.html` | Knowledge-graph browser |
| `build_district.py` | Regenerates data; schema-validates plan-model |

## Schema / graph

- `schema/spatial-structure.schema.json` — not part of the catalog gate
- `docs/design/spatial-concept-graph.json` — regenerate: `python3 scripts/build_spatial_graph.py`
- Research notes: `docs/design/research/`
