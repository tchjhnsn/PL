# AGENTS.md

Map for agents working in this repository. U0 is the empty-catalog scaffold. U1 is the seed catalog. Later units add checks and proofs; do not start them until this unit's check passes.

## What this is

A pattern-language catalog with a schema gate and a Lean library. U0 proves the repository builds and checks an empty catalog. It does not contain pattern records, schema documents, or a `pl` command. U0 left `PatternLanguage.Language` as an empty namespace. U1 adds five schemas, twelve seed records, and `load_catalog`. U2 adds the language laws and a generated building instantiation. U3 adds two generated IFC houses and `read_topology`. U4 adds `pl check`, one module per computed check, and `projects/seed-house.json`. U5 adds `pl sequence` and `pl step`. U6 adds a stdio MCP server with five tools over that core. U7 records a twelve-step seed-house run and a Blender add-on skeleton. U8 promotes SpatialStructure (`load_spatial`) as the validated plan mid-layer for the demo and future measure conditions.

## Where things are

| Path | Holds |
|---|---|
| `schema/` | Gate schemas: `catalog`, `projects`, `pattern-instance`, `check-report`, `step`. Also SpatialStructure, process-stage, survey, orientation-frame (not scanned by the catalog gate). |
| `catalog/` | Twelve seed pattern records, `<number>-<slug>.json`. |
| `projects/` | `seed-house.json`, the twelve-pattern language. Empty in U1. |
| `fixtures/` | `pass-house.ifc`, `fail-house.ifc`, and a sibling `.expected.json` for each. Generated. Not scanned by the gate. |
| `runs/` | Timestamped run directories. Empty apart from `.gitkeep` until `drive_run.py` writes one. Not scanned by the gate. |
| `mcp/` | `server.py`, a stdio MCP server. No `__init__.py`. The SDK owns the `mcp` import. |
| `adapters/blender/` | Blender add-on: panel, `Session`, and `export_ifc` (Bonsai save-as via `bpy.ops.bim`). `bpy` stays in this directory. |
| `tools/e2e-effect/` | Effect-TS CLI wrapping `pl` / `drive_run` (headless + live). See `docs/design/E2E-BONSAI-EFFECT.md`. |
| `demo/` | WebGL Decided stage viewer + SVG plan + concept browser (`python3 demo/serve.py` → http://127.0.0.1:8765/). Blender is optional; see `docs/design/WEBGL-ENTRY.md`. |
| `schema/ontology/` | Shared term definitions (`term.*`) linked from catalog `uses`. |
| `docs/design/SATISFACTION.md` | When `satisfied` is legal: orientation frame, tags, elevation. |
| `docs/design/DECIDED.md` | Survey → land → foundation → frame → openings; sync/async unlocks. |
| `docs/design/U8-SPATIAL-STRUCTURE.md` | U8 contract: SpatialStructure mid-layer acceptance. |
| `src/pattern_language/gate.py` | `DirectorySchemaMap`, frozen `CatalogScan`, and `scan(root)`. |
| `src/pattern_language/catalog.py` | `load_catalog`, `search`, `get`, `pattern_record`, `Catalog`, and `CatalogLoadError`. |
| `src/pattern_language/topology.py` | Frozen `Topology`, `Zone`, `Opening`, `Adjacency`, and `Boundary`. `read_ifc` / `write_ifc` are the only functions that import `ifcopenshell`. |
| `src/pattern_language/spatial_structure.py` | `load_spatial` (schema-validated), `places_with_role`, `measure_of` / `clear_width`, network edge helpers. No IFC / bpy. |
| `src/pattern_language/conditions/` | `CHECKS` and one module per computed check id. Pure: no file I/O and no IFC types. `plan_clearance.meets_clear_width` is a plan helper, not a registry entry. |
| `docs/design/U9-MEASURE-CONDITIONS.md` | U9 contract: plan clear-width reading for 167 without changing `pl check`. |
| `src/pattern_language/parameters.py` | `load_project` and `params_for`. |
| `src/pattern_language/checker.py` | `run` writes a check-report and validates it against `schema/check-report.schema.json`. |
| `src/pattern_language/sequence.py` | `index_before`, `order_ok`, `smaller_edges`, and `sequence`. Does not import the checker. |
| `src/pattern_language/step.py` | `preserving`, `Step`, `build_step`, and `step_json`. |
| `src/pattern_language/cli.py` | `pl check`, `pl sequence`, and `pl step`. |
| `src/pattern_language/runs.py` | `record_run`, `record_step`, `latest_report`, and `report_lines`. Calls `pl step` and `pl check`. |
| `scripts/validate_catalog.py` | Gate command. Prints back-edges, then `ok: N records`. Exit 0 when the scan has no errors and every link target exists. |
| `scripts/make_fixtures.py` | Writes the two houses and their expected JSON. `--check` compares graphs, not STEP bytes, and does not write into `fixtures/` on failure. |
| `scripts/drive_run.py` | Writes one run under `runs/<stamp>/`, or `--check` in a temporary directory. |
| `scripts/build_spatial_graph.py` | Regenerates `docs/design/spatial-concept-graph.json`. |
| `scripts/check_spatial_graph.py` | Integrity check for that concept graph. |
| `scripts/lint_spatial.py` | Plan geometry lint: lot/pad/shell overlap, sit-on containment, clearance gaps. |
| `src/pattern_language/spatial_lint.py` | Pure AABB helpers used by the lint script and `demo/build_district.py`. |
| `.agents/skills/` | Installed agent skills (`three-best-practices`, `threejs-spatial-data`, `threejs-testing`). |
| `tests/` | Pytest for the seed catalog, empty trees, missing schemas, import boundary, Lean manifest, the two houses, SpatialStructure, and the stdio MCP client. |
| `lean/` | Lake package `PatternLanguage`. `Language`, `Sequence`, `Preservation`, and generated `Instantiations/Buildings.lean`. |
| `docs/design/DESIGN.md` | Gate contract and unit boundary. |

## U1

`schema/` holds the five documents. `catalog/` holds the twelve records. Summaries and forces are our wording and carry `"draft": true`. `load_catalog` reports missing targets and back-edges after `scan` accepts the files. U1 left `projects/` with no JSON records.

## U2

`lean/PatternLanguage/` holds `Language`, `Sequence`, and `Preservation`. `scripts/catalog_to_lean.py` writes `lean/PatternLanguage/Instantiations/Buildings.lean` from `load_catalog`. `decide` proves that numeric order is a valid sequence for the twelve seed patterns. `--check` exits 1 when that file is stale. CI runs `--check` before `lake build`.

## U3

`topology.py` reads and writes IFC and is the only module that imports `ifcopenshell`, and only inside `read_ifc` and `write_ifc`. `fixtures/` holds `pass-house.ifc` and `fail-house.ifc`. Each computed pattern has a pass witness on one house and a fail witness on the other. 110 Main Entrance and 180 Window Place are judged and have no house. U3 does not evaluate a condition.

## U4

`conditions/` holds one module per computed `condition.check` id, and `CHECKS` is the only registry. `checker.py` calls `CHECKS[condition.check]` and does not branch on pattern number. `pl check <model.ifc> --language <project.json>` evaluates one model. `projects/seed-house.json` selects all twelve patterns and sets `latitude_deg` to 40. On the pass house the ten computed instances are `satisfied`. On the fail house they are `violated`. 110 Main Entrance and 180 Window Place are `needs_judgment` with unanswered evidence, and they are absent from `satisfied`. The pass command exits 0. The fail command exits 1. U4 does not order a sequence or record a step.

## U5

`sequence.py` is the Python twin of `Sequence.lean`. `order_ok` accepts ascending numbers on the induced smaller-edges. `pl sequence projects/seed-house.json` prints that list, which is `numericOrder` in `Buildings.lean`. `step.py` is the Python twin of `Preserving`. `pl step` runs the checker on two models and writes one step. Pass house then fail house has `preserved` false and exits 1, because 105 South Facing Outdoors leaves `satisfied`. The same house twice has `preserved` true and exits 0. 110 Main Entrance and 180 Window Place stay out of `satisfied`. CI runs `pl sequence` on the seed project. The pass-then-fail step stays in pytest.

## U6

`mcp/server.py` speaks MCP on stdio. The tools are `patterns_search`, `pattern_get`, `language_sequence`, `model_check`, `model_step`, `spatial_get`, and `model_measures`. Search and lookup call `search`, `get`, and `pattern_record`. Sequence/check/step call `sequence`, `run`, and `build_step`. Spatial tools call `load_spatial` / measure helpers. Arguments and results are checked against the schema documents already in `schema/`. A violated check-report, and a step whose `preserved` is false, are successful tool results. 110 Main Entrance and 180 Window Place stay `needs_judgment` and stay out of `satisfied`. `tests/test_mcp.py` spawns `python mcp/server.py` and calls each tool on `fixtures/pass-house.ifc`, `fixtures/fail-house.ifc`, `projects/seed-house.json`, and `demo/data/plan-model.json`. Pass house then fail house, pattern 112, returns `preserved` false. There is no `mcp/__init__.py` and no new `pl` command.

```bash
uv run python mcp/server.py
```

That process reads stdin until the client closes it. `uv run pytest` is the client check. CI does not launch the server, because the process would block.

## U7

`prefix` copies named spaces and openings out of the pass-house tables. `_pass_house` is `prefix` of every name. `record_run` checks that `sequence` on the seed project is `105, 106, 107, 110, 112, 127, 128, 130, 159, 167, 180, 190`, writes `model-00.ifc` through `model-12.ifc`, and calls `record_step` twelve times. Each step is `python -m pattern_language.cli step` with `--out`. Exit 1 raises `RunError` and the driver deletes the directory. `report.json` is `pl check` on `model-12.ifc`. The ten computed patterns are `satisfied`. 110 Main Entrance and 180 Window Place are `needs_judgment` and stay out of `satisfied`. Every logged step has `preserved` true. `model-12.ifc` reads back as the pass house.

`adapters/blender/` holds the add-on. The panel draws `report_lines` from the newest `report.json`, or `report unavailable`. `Session.act` is the transition table. `export_ifc` calls `bpy.ops.bim.save_project`. `bridge.py` is the only file that imports `bonsai`. The live path is `adapters/blender/README.md`. CI runs `drive_run.py --check` and does not launch Blender. U7 adds no schema, no Lean file, and no `pl` command.

```bash
uv run python scripts/drive_run.py --check
uv run python scripts/drive_run.py
```

## U8

`schema/spatial-structure.schema.json` validates plan mid-layer documents. It is **not** in the catalog gate scan. `load_spatial` is the only library entrypoint name. The seed district (`demo/data/plan-model.json`, rebuilt by `demo/build_district.py`) holds ROW + sidewalk + carriageway, at least ten network edges, and named measures including balcony depth and sidewalk clear width. Concept graph scripts rebuild and check `docs/design/spatial-concept-graph.json`. Demo serves WebGL (`/`), plan symbology (`/plan.html`), and concepts (`/concepts.html`). U8 adds no `pl` command, no MCP tool, no Lean edit, and no Blender change. Follow-on: U9 measure conditions over the plan (`docs/design/U9-MEASURE-CONDITIONS.md`).

```bash
uv run pytest tests/test_spatial_graph.py tests/test_spatial_structure.py
uv run python demo/build_district.py
python3 scripts/build_spatial_graph.py && python3 scripts/check_spatial_graph.py
```

## U9

`conditions/plan_clearance.py` defines `meets_clear_width(plan, place_id, minimum_m)` for SpatialStructure plans. It is **not** a `CHECKS` entry: 167 Six-Foot Balcony still goes through `six_foot_balcony.check` on Topology. The helper returns `True` / `False` / `None` from `clear_width` only; it opens no file and does not build Evidence. `evaluate` / `pl check` stay Topology-only. Contract: `docs/design/U9-MEASURE-CONDITIONS.md`. No new schema, Lean edit, MCP tool, or `pl` command.

```bash
uv run pytest tests/test_checks.py tests/test_spatial_structure.py tests/test_boundaries.py
uv run pl check fixtures/pass-house.ifc --language projects/seed-house.json
uv run pl check fixtures/fail-house.ifc --language projects/seed-house.json
```

## U10

`mcp/server.py` adds `spatial_get` and `model_measures` over SpatialStructure (`docs/design/U10-SPATIAL-MCP.md`). CI runs `scripts/lint_spatial.py`. Plan symbology draws land/foundation/pond/gravel and evergreen tree marks. No new `pl` command, Lean edit, or Blender change.

```bash
uv run pytest tests/test_mcp.py tests/test_spatial_lint.py
uv run python scripts/lint_spatial.py
```

## U11

`demo/build_district.py` exports CityJSON 2.0 with LoD0 footprints, `Road` → child `TrafficArea` (carriageway / sidewalk), `LandUse` lots, `WaterBody` pond, and `SolitaryVegetationObject` trees. Contract: `docs/design/U11-CITYJSON-LOD0.md`.

```bash
uv run python demo/build_district.py
uv run pytest tests/test_cityjson_export.py
```

## U12

Plan sheet judgment UI for 110 Main Entrance and 180 Window Place: evidence question plus Yes/No/Clear in `sessionStorage`. Does not change `pl check`. Contract: `docs/design/U12-JUDGMENT-UI.md`.

```bash
python3 demo/serve.py   # → /plan.html — answer 110 / 180
```

## U13

WebGL draws SpatialStructure `walls` with gaps at openings; `a-door-approach` is the court gate in `w-court-s` (street → path → gate → court → main door). No schema / `pl` / Lean / MCP change. Contract: `docs/design/U13-APPROACH-ENCLOSURE.md`.

```bash
uv run python demo/build_district.py
uv run python scripts/lint_spatial.py
uv run pytest tests/test_webgl_quality.py tests/test_spatial_structure.py tests/test_spatial_lint.py
```

## U14

Entrance porch `a-porch` between court and hall: deck + posts + canopy in WebGL (not a solid room). Completes gate → court → porch → door for 112 / 130. No schema / `pl` / Lean / MCP change. Contract: `docs/design/U14-ENTRANCE-PORCH.md`.

```bash
uv run python demo/build_district.py
uv run python scripts/lint_spatial.py
uv run pytest tests/test_webgl_quality.py tests/test_spatial_structure.py tests/test_spatial_lint.py
```

## U15

Street frontage / plot series: front courts + garden walls + gates on Lots B/C/D so the seed block reads as a series, not House A alone. Frontage measures and address nodes. No schema / `pl` / Lean / MCP change. Contract: `docs/design/U15-STREET-FRONTAGE.md`.

```bash
uv run python demo/build_district.py
uv run python scripts/lint_spatial.py
uv run pytest tests/test_webgl_quality.py tests/test_spatial_structure.py tests/test_spatial_lint.py
```

## U16

House storey fix: bedroom stacked on living, stair link, balcony east of upper room (no door onto living roof). Spatial lint allows stacked shells. Building-line measure on main street. WebGL `setCamera` for screenshot audit. Contract: `docs/design/U16-HOUSE-STOREY.md`.

```bash
uv run python demo/build_district.py
uv run python scripts/lint_spatial.py
uv run pytest tests/test_webgl_quality.py tests/test_spatial_lint.py
```

## U17

Block morphology: `block-south` / `block-north`, `street-cross` local ROW + lane junction, mid-block passage. North lots front the cross street. CityJSON Road/TrafficArea for the cross street. No `pl` / Lean / MCP. Contract: `docs/design/U17-BLOCK-STREET.md`.

```bash
uv run python demo/build_district.py
uv run python scripts/lint_spatial.py
uv run pytest tests/test_webgl_quality.py tests/test_spatial_structure.py tests/test_cityjson_export.py
```

## U18

Frontage rhythm measures on both block faces; building line on Cross Street; address every parcel including workshop (`n-addr-w`). No `pl` / Lean / MCP. Contract: `docs/design/U18-RHYTHM-ADDRESS.md`.

```bash
uv run python demo/build_district.py
uv run python scripts/lint_spatial.py
uv run pytest tests/test_webgl_quality.py tests/test_spatial_structure.py
```

## U19

Second block / multi-block neighborhood: `block-east`, `street-east`, `district-seed`, living/work parcel roles, Main Street enclosure measure. No `pl` / Lean / MCP. Contract: `docs/design/U19-SECOND-BLOCK.md`.

```bash
uv run python demo/build_district.py
uv run python scripts/lint_spatial.py
uv run pytest tests/test_webgl_quality.py tests/test_spatial_structure.py tests/test_cityjson_export.py
```

## U20

MapLibre city surface: `demo/map.html` figure–ground over `district.geojson`; linked from WebGL. No `pl` / Lean / MCP. Contract: `docs/design/U20-MAPLIBRE-CITY.md`.

```bash
uv run pytest tests/test_maplibre_city.py
python3 demo/serve.py   # → /map.html
```

## U21

2×2 city grid: `block-northeast`, `street-north`, East Street through to North; Seed City district. No `pl` / Lean / MCP. Contract: `docs/design/U21-CITY-GRID.md`.

```bash
uv run python demo/build_district.py
uv run python scripts/lint_spatial.py
uv run pytest tests/test_webgl_quality.py tests/test_spatial_structure.py tests/test_cityjson_export.py tests/test_maplibre_city.py
```

## U22

City product chrome (plain-language Seed City rail) + frontage-lot object kit stamping Far East Lots I/J. Product brief: `docs/design/PRODUCT.md`. Contract: `docs/design/U22-CITY-PRODUCT.md`.

```bash
uv run python demo/build_district.py
uv run pytest tests/test_kits.py tests/test_webgl_quality.py tests/test_maplibre_city.py
```

## U23

Real city fabric south of the seed neighborhood: `generate_city_fabric` (12×10 blocks, ~1 km) with **3 City Country Fingers**, schools, playgrounds, shops/market/grocery, town hall / police / bank / clinic, utilities, and residential frontage stamps. Kits: `program_place`, `city_fabric`. No catalog / Lean / `pl` / MCP. Contract: `docs/design/U23-REAL-CITY.md`.

```bash
uv run python demo/build_district.py
uv run python scripts/lint_spatial.py
uv run pytest tests/test_kits.py tests/test_spatial_structure.py tests/test_webgl_quality.py tests/test_cityjson_export.py tests/test_maplibre_city.py
```

## Commands

```bash
uv sync
uv run pytest
uv run python scripts/validate_catalog.py
uv run python scripts/catalog_to_lean.py --check
uv run python scripts/make_fixtures.py --check
uv run pl check fixtures/pass-house.ifc --language projects/seed-house.json
uv run pl check fixtures/fail-house.ifc --language projects/seed-house.json
uv run pl sequence projects/seed-house.json
uv run python scripts/drive_run.py --check
uv run pl step fixtures/pass-house.ifc fixtures/fail-house.ifc --language projects/seed-house.json --pattern 112
uv run pl step fixtures/pass-house.ifc fixtures/pass-house.ifc --language projects/seed-house.json --pattern 105
cd lean && lake build
```

CI runs `uv sync --frozen`, `uv run pytest`, `uv run python scripts/validate_catalog.py`, `uv run python scripts/catalog_to_lean.py --check`, `uv run pl check fixtures/pass-house.ifc --language projects/seed-house.json`, `uv run pl sequence projects/seed-house.json`, `uv run python scripts/drive_run.py --check`, and `leanprover/lean-action` with `lake-package-directory: lean`. `uv sync --frozen` installs the IfcOpenShell wheel. Pytest runs `make_fixtures.py --check`. The gate prints `back-edges: 0` and `ok: 13 records`. CI does not launch Blender.

## Rules

- Cite pattern numbers and names only. Never copy book text.
- Core Python must not import `bpy`. `bpy` may be imported only under `adapters/blender/`. `bonsai` may be imported only in `adapters/blender/bridge.py`. `ifcopenshell` may be imported only inside `read_ifc` and `write_ifc` in `topology.py`.
- `lean/lake-manifest.json` keeps `packages` empty. Do not add Mathlib.
- Do not add pattern records, schema documents, or a `pl` command in U0.
- U4 adds `pl check`. U5 adds `pl sequence` and `pl step`. U6 adds the stdio server in `mcp/server.py`. U7 adds `scripts/drive_run.py` and the Blender add-on. U7 does not add a schema, a Lean edit, a `pl` command, or an MCP tool. U8 adds SpatialStructure mid-layer helpers and docs; no new `pl` command or MCP tool. U9 adds `meets_clear_width` for plan measures; `CHECKS` and `pl check` stay Topology-only. U10 adds `spatial_get` / `model_measures` MCP tools and CI spatial lint. U11 expands CityJSON LoD0 + TrafficArea export. U12 adds plan-sheet judgment answers for 110 / 180. U13 draws approach enclosure walls / court gate in WebGL; no new `pl` command. U14 adds the entrance porch canopy between court and hall; no new `pl` command. U15 adds street frontage / plot-series courts on neighbor lots; no new `pl` command. U16 fixes stacked storeys / stair (no roof door) and adds a building-line measure; no new `pl` command. U17 adds block places + Cross Street junction; no new `pl` command. U18 adds frontage rhythm measures and workshop address; no new `pl` command. U19 adds East Block / multi-block district; no new `pl` command. U20 adds MapLibre city map surface; no new `pl` command. U21 closes a 2×2 city block grid; no new `pl` command. U22 rewrites demo chrome + stamps frontage-lot kits; no new `pl` command. U23 stamps real city fabric (green fingers + civic/commercial program); no new `pl` command.
- Agents open draft pull requests and do not merge.
- Agent skills for WebGL / city mesh work live under `.agents/skills/` (`three-best-practices`, `threejs-spatial-data`, `threejs-testing`, `threejs-procedural-architecture`, `threejs-procedural-buildings-and-cities`, `threejs-architecture-effects`).
