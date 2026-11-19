# AGENTS.md

Map for agents working in this repository. U0 is the empty-catalog scaffold. U1 is the seed catalog. Later units add checks and proofs; do not start them until this unit's check passes.

## What this is

A pattern-language catalog with a schema gate and a Lean library. U0 proves the repository builds and checks an empty catalog. It does not contain pattern records, schema documents, or a `pl` command. U0 left `PatternLanguage.Language` as an empty namespace. U1 adds five schemas, twelve seed records, and `load_catalog`. U2 adds the language laws and a generated building instantiation. U3 adds two generated IFC houses and `read_topology`. U4 adds `pl check`, one module per computed check, and `projects/seed-house.json`. U5 adds `pl sequence` and `pl step`. U6 adds a stdio MCP server with five tools over that core. U7 records a twelve-step seed-house run and a Blender add-on skeleton.

## Where things are

| Path | Holds |
|---|---|
| `schema/` | Five JSON Schemas: `catalog`, `projects`, `pattern-instance`, `check-report`, `step`. |
| `catalog/` | Twelve seed pattern records, `<number>-<slug>.json`. |
| `projects/` | `seed-house.json`, the twelve-pattern language. Empty in U1. |
| `fixtures/` | `pass-house.ifc`, `fail-house.ifc`, and a sibling `.expected.json` for each. Generated. Not scanned by the gate. |
| `runs/` | Timestamped run directories. Empty apart from `.gitkeep` until `drive_run.py` writes one. Not scanned by the gate. |
| `mcp/` | `server.py`, a stdio MCP server. No `__init__.py`. The SDK owns the `mcp` import. |
| `adapters/blender/` | Blender add-on: panel, `Session`, and `export_ifc` (Bonsai save-as via `bpy.ops.bim`). `bpy` stays in this directory. |
| `tools/e2e-effect/` | Effect-TS CLI wrapping `pl` / `drive_run` (headless + live). See `docs/design/E2E-BONSAI-EFFECT.md`. |
| `src/pattern_language/gate.py` | `DirectorySchemaMap`, frozen `CatalogScan`, and `scan(root)`. |
| `src/pattern_language/catalog.py` | `load_catalog`, `search`, `get`, `pattern_record`, `Catalog`, and `CatalogLoadError`. |
| `src/pattern_language/topology.py` | Frozen `Topology`, `Zone`, `Opening`, `Adjacency`, and `Boundary`. `read_ifc` / `write_ifc` are the only functions that import `ifcopenshell`. |
| `src/pattern_language/conditions/` | `CHECKS` and one module per computed check id. Pure: no file I/O and no IFC types. |
| `src/pattern_language/parameters.py` | `load_project` and `params_for`. |
| `src/pattern_language/checker.py` | `run` writes a check-report and validates it against `schema/check-report.schema.json`. |
| `src/pattern_language/sequence.py` | `index_before`, `order_ok`, `smaller_edges`, and `sequence`. Does not import the checker. |
| `src/pattern_language/step.py` | `preserving`, `Step`, `build_step`, and `step_json`. |
| `src/pattern_language/cli.py` | `pl check`, `pl sequence`, and `pl step`. |
| `src/pattern_language/runs.py` | `record_run`, `record_step`, `latest_report`, and `report_lines`. Calls `pl step` and `pl check`. |
| `scripts/validate_catalog.py` | Gate command. Prints back-edges, then `ok: N records`. Exit 0 when the scan has no errors and every link target exists. |
| `scripts/make_fixtures.py` | Writes the two houses and their expected JSON. `--check` compares graphs, not STEP bytes, and does not write into `fixtures/` on failure. |
| `scripts/drive_run.py` | Writes one run under `runs/<stamp>/`, or `--check` in a temporary directory. |
| `tests/` | Pytest for the seed catalog, empty trees, missing schemas, import boundary, Lean manifest, the two houses, and the stdio MCP client. |
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

`mcp/server.py` speaks MCP on stdio. The tools are `patterns_search`, `pattern_get`, `language_sequence`, `model_check`, and `model_step`. Search and lookup call `search`, `get`, and `pattern_record`. The other three call `sequence`, `run`, and `build_step` and return that JSON. Arguments and results are checked against the schema documents already in `schema/`. A violated check-report, and a step whose `preserved` is false, are successful tool results. 110 Main Entrance and 180 Window Place stay `needs_judgment` and stay out of `satisfied`. `tests/test_mcp.py` spawns `python mcp/server.py` and calls each tool on `fixtures/pass-house.ifc`, `fixtures/fail-house.ifc`, and `projects/seed-house.json`. Pass house then fail house, pattern 112, returns `preserved` false. There is no `mcp/__init__.py` and no new `pl` command.

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
- U4 adds `pl check`. U5 adds `pl sequence` and `pl step`. U6 adds the stdio server in `mcp/server.py`. U7 adds `scripts/drive_run.py` and the Blender add-on. U7 does not add a schema, a Lean edit, a `pl` command, or an MCP tool.
- Agents open draft pull requests and do not merge.
