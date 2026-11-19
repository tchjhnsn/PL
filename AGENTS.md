# AGENTS.md

Map for agents working in this repository. U0 is the empty-catalog scaffold. U1 is the seed catalog. Later units add checks and proofs; do not start them until this unit's check passes.

## What this is

A pattern-language catalog with a schema gate and a Lean library. U0 proves the repository builds and checks an empty catalog. It does not contain pattern records, schema documents, or a `pl` command. U0 left `PatternLanguage.Language` as an empty namespace. U1 adds five schemas, twelve seed records, and `load_catalog`. U2 adds the language laws and a generated building instantiation. U3 adds two generated IFC houses and `read_topology`. U4 adds `pl check`, one module per computed check, and `projects/seed-house.json`.

## Where things are

| Path | Holds |
|---|---|
| `schema/` | Five JSON Schemas: `catalog`, `projects`, `pattern-instance`, `check-report`, `step`. |
| `catalog/` | Twelve seed pattern records, `<number>-<slug>.json`. |
| `projects/` | `seed-house.json`, the twelve-pattern language. Empty in U1. |
| `fixtures/` | `pass-house.ifc`, `fail-house.ifc`, and a sibling `.expected.json` for each. Generated. Not scanned by the gate. |
| `mcp/` | MCP surface. Empty in U1. |
| `adapters/blender/` | Blender adapter. Empty in U1. |
| `src/pattern_language/gate.py` | `DirectorySchemaMap`, frozen `CatalogScan`, and `scan(root)`. |
| `src/pattern_language/catalog.py` | `load_catalog`, `Catalog`, and `CatalogLoadError`. |
| `src/pattern_language/topology.py` | Frozen `Topology`, `Zone`, `Opening`, `Adjacency`, and `Boundary`. `read_ifc` / `write_ifc` are the only functions that import `ifcopenshell`. |
| `src/pattern_language/conditions/` | `CHECKS` and one module per computed check id. Pure: no file I/O and no IFC types. |
| `src/pattern_language/parameters.py` | `load_project` and `params_for`. |
| `src/pattern_language/checker.py` | `run` writes a check-report and validates it against `schema/check-report.schema.json`. |
| `src/pattern_language/cli.py` | `pl check`. The only subcommand. |
| `scripts/validate_catalog.py` | Gate command. Prints back-edges, then `ok: N records`. Exit 0 when the scan has no errors and every link target exists. |
| `scripts/make_fixtures.py` | Writes the two houses and their expected JSON. `--check` compares graphs, not STEP bytes, and does not write into `fixtures/` on failure. |
| `tests/` | Pytest for the seed catalog, empty trees, missing schemas, import boundary, Lean manifest, and the two houses. |
| `lean/` | Lake package `PatternLanguage`. `Language`, `Sequence`, `Preservation`, and generated `Instantiations/Buildings.lean`. |
| `docs/design/DESIGN.md` | Gate contract and unit boundary. |

## U1

`schema/` holds the five documents. `catalog/` holds the twelve records. Summaries and forces are our wording and carry `"draft": true`. `load_catalog` reports missing targets and back-edges after `scan` accepts the files. U1 left `projects/` with no JSON records.

## U2

`lean/PatternLanguage/` holds `Language`, `Sequence`, and `Preservation`. `scripts/catalog_to_lean.py` writes `lean/PatternLanguage/Instantiations/Buildings.lean` from `load_catalog`. `decide` proves that numeric order is a valid sequence for the twelve seed patterns. `--check` exits 1 when that file is stale. CI runs `--check` before `lake build`.

## U3

`topology.py` reads and writes IFC and is the only module that imports `ifcopenshell`, and only inside `read_ifc` and `write_ifc`. `fixtures/` holds `pass-house.ifc` and `fail-house.ifc`. Each computed pattern has a pass witness on one house and a fail witness on the other. 110 Main Entrance and 180 Window Place are judged and have no house. U3 does not evaluate a condition.

## U4

`conditions/` holds one module per computed `condition.check` id, and `CHECKS` is the only registry. `checker.py` calls `CHECKS[condition.check]` and does not branch on pattern number. `pl check <model.ifc> --language <project.json>` is the only subcommand. `projects/seed-house.json` selects all twelve patterns and sets `latitude_deg` to 40. On the pass house the ten computed instances are `satisfied`. On the fail house they are `violated`. 110 Main Entrance and 180 Window Place are `needs_judgment` with unanswered evidence, and they are absent from `satisfied`. The pass command exits 0. The fail command exits 1.

## Commands

```bash
uv sync
uv run pytest
uv run python scripts/validate_catalog.py
uv run python scripts/catalog_to_lean.py --check
uv run python scripts/make_fixtures.py --check
uv run pl check fixtures/pass-house.ifc --language projects/seed-house.json
uv run pl check fixtures/fail-house.ifc --language projects/seed-house.json
cd lean && lake build
```

CI runs `uv sync --frozen`, `uv run pytest`, `uv run python scripts/validate_catalog.py`, `uv run python scripts/catalog_to_lean.py --check`, `uv run pl check fixtures/pass-house.ifc --language projects/seed-house.json`, and `leanprover/lean-action` with `lake-package-directory: lean`. `uv sync --frozen` installs the IfcOpenShell wheel. Pytest runs `make_fixtures.py --check`. The gate prints `back-edges: 0` and `ok: 13 records`.

## Rules

- Cite pattern numbers and names only. Never copy book text.
- Core Python must not import `bpy`. `ifcopenshell` may be imported only inside `read_ifc` and `write_ifc` in `topology.py`.
- `lean/lake-manifest.json` keeps `packages` empty. Do not add Mathlib.
- Do not add pattern records, schema documents, or a `pl` command in U0.
- U4 adds `pl check` only. `sequence` and `step` stay later.
- Agents open draft pull requests and do not merge.
