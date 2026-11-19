# Design

## U0

U0 is a scaffold. The catalog builds, tests, and validates while `catalog/`, `projects/`, and `schema/` have no content beyond directory placeholders. There is no `pl` command, no pattern record, no schema document, no Mathlib dependency, and no Blender import.

## Gate

`scan(root)` reads JSON files under `catalog/` and `projects/`. Other directories, including `fixtures/`, are ignored. A file is a record when its name ends in `.json` and does not start with a dot.

`DirectorySchemaMap` loads `schema/<directory>.schema.json`. The file `schema/catalog.schema.json` covers records in `catalog/`. A nested file such as `schema/catalog/room.schema.json` covers `catalog/room/` and wins over a shorter prefix. The map is built from the `schema/` directory unless a caller passes one in.

`CatalogScan` is frozen. It records the root, the record paths, and the errors. `ok` is true when `errors` is empty.

An empty `catalog/` and `projects/` is valid, including trees that contain only `.gitkeep`. A missing `catalog/` or `projects/` directory is an error. A record whose directory has no schema is an error (`record without schema`). Records that have a schema are checked with JSON Schema draft 2020-12. Invalid JSON is an error and does not stop the rest of the scan.

`scripts/validate_catalog.py` scans the repository root by default, prints `ok: N records` on success, and prints each error to stderr with exit code 1.

## Lean

`lean/` is a Lake package named `PatternLanguage` pinned by `lean-toolchain` to `leanprover/lean4:v4.33.1`. The library glob is `.submodules PatternLanguage`, so Lake builds `PatternLanguage/Language.lean` without a root `PatternLanguage.lean` module. That module is an empty `PatternLanguage` namespace. `lake-manifest.json` lists no packages.

## Adapters

`adapters/blender/` and `mcp/` are reserved directories. The core package does not import `ifcopenshell` or `bpy`. Adapter code stays outside `src/pattern_language/`.

## Copyright

Cite pattern numbers and names only. Do not copy book text into records, schemas, comments, or docs.
