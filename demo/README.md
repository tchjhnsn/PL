# Seed district — owned plan symbology

Geometry-aware plan demo: **places**, directed **network** (centerlines + hierarchy), named **measures** (dimension strings), **interfaces**, door/window/tree symbology, and pattern diagram overlays.

## Owned layer

```text
pattern-language.plan-symbology
```

Semantic types can come from CityJSON/IFC/BOT. **How flow, measure, and openings look on the page is our layer.** Naive marketing dogfood is **deferred**.

## Run

```bash
uv run python demo/build_district.py   # validates SpatialStructure + writes data/
python3 demo/serve.py
# open http://127.0.0.1:8765/
# concept graph: http://127.0.0.1:8765/concepts.html
```

## Concept graph

`concepts.html` searches every node in `data/concept-graph.json`. Status chips (`have`, `partial`, `todo`, `placeholder`) and a layer menu narrow the list. A concept opens its `depends_on`, `parent_of`, `sibling_of`, `maps_to`, `specializes`, and `renders_as` neighbors in both directions, with source tags and a one-hop diagram. `build_district.py` copies the file from `docs/design/spatial-concept-graph.json`. Fetch needs the demo server — `file://` blocks it.

## Files

| File | Role |
|---|---|
| `data/plan-model.json` | SpatialStructure: places, network, measures, interfaces, openings, patterns |
| `data/concept-graph.json` | Copy of `docs/design/spatial-concept-graph.json` |
| `data/district.city.json` | CityJSON export (interchange) |
| `data/district.geojson` | GeoJSON sibling |
| `plan.js` / `index.html` | SVG plan renderer (flow + dims + symbology) |
| `concepts.js` / `concepts.html` | Knowledge-graph browser |
| `build_district.py` | Regenerates data; schema-validates plan-model |

## Schema / graph

- `schema/spatial-structure.schema.json` — not part of the catalog gate
- `docs/design/spatial-concept-graph.json` — regenerate: `python3 scripts/build_spatial_graph.py`
- Research notes: `docs/design/research/`
