# U8 — SpatialStructure mid-layer

Contract for the unit after U7. Draft for agents; open a PR when acceptance is green. Do not merge from agents.

## Goal

Promote the **SpatialStructure** document (places, directed `network`, named `measures`, `interfaces`) from demo-only JSON into a **validated product mid-layer** that the plan-symbology sheet and future conditions can share — without replacing IFC/CityJSON interchange or adding Mathlib.

## Already landed (pre-unit scaffold)

| Artifact | Role |
|---|---|
| `schema/spatial-structure.schema.json` | Schema (not in catalog gate) |
| `demo/build_district.py` + `data/plan-model.json` | Seed district instance |
| `demo/plan.js` / `concepts.html` | Plan + concept-graph UI |
| `docs/design/spatial-concept-graph.json` | Exhaustive concept graph |
| `src/pattern_language/spatial_structure.py` | Pure load/query helpers |
| `tests/test_spatial_graph.py`, `tests/test_spatial_structure.py` | Integrity + helpers |

## In scope

1. Keep schema **out of** `scripts/validate_catalog.py` / gate scan (catalog stays pattern-record focused).
2. Stabilize `spatial_structure.load_spatial` + measure/edge queries; document in AGENTS.md.
3. Seed district must remain schema-valid: ROW + sidewalk + carriageway, ≥10 network edges, named measures including balcony depth and sidewalk clear width.
4. Concept graph regenerates cleanly (`scripts/build_spatial_graph.py` + `check_spatial_graph.py`).
5. Demo serves plan + figure–ground + concepts browser.

## Acceptance

```bash
uv run pytest tests/test_spatial_graph.py tests/test_spatial_structure.py
uv run python demo/build_district.py
python3 scripts/build_spatial_graph.py && python3 scripts/check_spatial_graph.py
# manual: python3 demo/serve.py → /  and /concepts.html
```

No new `pl` command in U8 unless a later amendment requires `pl spatial validate`.

## Non-goals

- No book text; cite pattern numbers/names only.
- No Mathlib; no Lean edit required for U8.
- No new MCP tool in U8 (defer to U9+).
- No Blender/`bpy` changes.
- No Naive/marketing dogfood.
- Do not make SpatialStructure a CityGML ADE; map *to* CityGML/BOT in the concept graph instead.

## API name

Library entrypoint is `pattern_language.spatial_structure.load_spatial` (schema-validated). An earlier draft called this `load_structure`; do not add a second name.

## Follow-on (brief)

Sidewalk/carriageway already in the seed district scaffold (not deferred).

| Unit | Focus |
|---|---|
| U9 | Conditions over measures/network — [`U9-MEASURE-CONDITIONS.md`](U9-MEASURE-CONDITIONS.md) |
| U10 | MCP tools: `spatial_get` / `model_measures` |
| U11 | LoD0 CityJSON parity + finer TrafficArea splits where still thin |
| U12 | Judgment evidence UI for 110 / 180 on the plan sheet |

## Exit

When acceptance is green, open a **draft** PR titled `U8 SpatialStructure mid-layer`. Agents do not merge.
