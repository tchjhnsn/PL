# AGENTS.md

Map for agents working in this repository. U0 is the empty-catalog scaffold. Later units add records and schemas; do not start them from this tree.

## What this is

A pattern-language catalog with a schema gate and a Lean library. U0 proves the repository builds and checks an empty catalog. It does not contain pattern records, schema documents, or a `pl` command.

## Where things are

| Path | Holds |
|---|---|
| `schema/` | JSON Schemas, one `*.schema.json` per record directory. Empty in U0. |
| `catalog/` | JSON pattern records. Empty in U0. |
| `projects/` | JSON project records. Empty in U0. |
| `fixtures/` | Fixtures. Empty in U0. Not scanned by the gate. |
| `mcp/` | MCP surface. Empty in U0. |
| `adapters/blender/` | Blender adapter. Empty in U0. |
| `src/pattern_language/gate.py` | `DirectorySchemaMap`, frozen `CatalogScan`, and `scan(root)`. |
| `scripts/validate_catalog.py` | Gate command. Exit 0 when the scan has no errors. |
| `tests/` | Pytest for the empty tree, missing schemas, import boundary, and Lean manifest. |
| `lean/` | Lake package `PatternLanguage`. Module `PatternLanguage.Language` is an empty namespace. |
| `docs/design/DESIGN.md` | Gate contract and unit boundary. |

## Commands

```bash
uv sync
uv run pytest
uv run python scripts/validate_catalog.py
cd lean && lake build
```

CI runs `uv sync --frozen`, `uv run pytest`, `uv run python scripts/validate_catalog.py`, and `leanprover/lean-action` with `lake-package-directory: lean`.

## Rules

- Cite pattern numbers and names only. Never copy book text.
- Core Python must not import `ifcopenshell` or `bpy`.
- `lean/lake-manifest.json` keeps `packages` empty. Do not add Mathlib.
- Do not add pattern records, schema documents, or a `pl` command in U0.
- Agents open draft pull requests and do not merge.
