# AGENTS.md

Map for agents working in this repository. U0 is the empty-catalog scaffold. U1 is the seed catalog. Later units add checks and proofs; do not start them until this unit's check passes.

## What this is

A pattern-language catalog with a schema gate and a Lean library. U0 proves the repository builds and checks an empty catalog. It does not contain pattern records, schema documents, or a `pl` command. U0 left `PatternLanguage.Language` as an empty namespace. U1 adds five schemas, twelve seed records, and `load_catalog`. U2 adds the language laws and a generated building instantiation.

## Where things are

| Path | Holds |
|---|---|
| `schema/` | Five JSON Schemas: `catalog`, `projects`, `pattern-instance`, `check-report`, `step`. |
| `catalog/` | Twelve seed pattern records, `<number>-<slug>.json`. |
| `projects/` | JSON project records. Empty in U1. |
| `fixtures/` | Fixtures. Empty in U1. Not scanned by the gate. |
| `mcp/` | MCP surface. Empty in U1. |
| `adapters/blender/` | Blender adapter. Empty in U1. |
| `src/pattern_language/gate.py` | `DirectorySchemaMap`, frozen `CatalogScan`, and `scan(root)`. |
| `src/pattern_language/catalog.py` | `load_catalog`, `Catalog`, and `CatalogLoadError`. |
| `scripts/validate_catalog.py` | Gate command. Prints back-edges, then `ok: N records`. Exit 0 when the scan has no errors and every link target exists. |
| `tests/` | Pytest for the seed catalog, empty trees, missing schemas, import boundary, and Lean manifest. |
| `lean/` | Lake package `PatternLanguage`. `Language`, `Sequence`, `Preservation`, and generated `Instantiations/Buildings.lean`. |
| `docs/design/DESIGN.md` | Gate contract and unit boundary. |

## U1

`schema/` holds the five documents. `catalog/` holds the twelve records. Summaries and forces are our wording and carry `"draft": true`. `load_catalog` reports missing targets and back-edges after `scan` accepts the files. `projects/` has no JSON records.

## U2

`lean/PatternLanguage/` holds `Language`, `Sequence`, and `Preservation`. `scripts/catalog_to_lean.py` writes `lean/PatternLanguage/Instantiations/Buildings.lean` from `load_catalog`. `decide` proves that numeric order is a valid sequence for the twelve seed patterns. `--check` exits 1 when that file is stale. CI runs `--check` before `lake build`.

## Commands

```bash
uv sync
uv run pytest
uv run python scripts/validate_catalog.py
uv run python scripts/catalog_to_lean.py --check
cd lean && lake build
```

CI runs `uv sync --frozen`, `uv run pytest`, `uv run python scripts/validate_catalog.py`, `uv run python scripts/catalog_to_lean.py --check`, and `leanprover/lean-action` with `lake-package-directory: lean`.

## Rules

- Cite pattern numbers and names only. Never copy book text.
- Core Python must not import `ifcopenshell` or `bpy`.
- `lean/lake-manifest.json` keeps `packages` empty. Do not add Mathlib.
- Do not add pattern records, schema documents, or a `pl` command in U0.
- Do not add a `pl` command.
- Agents open draft pull requests and do not merge.
