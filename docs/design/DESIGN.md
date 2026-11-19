# Design

## U0

U0 is a scaffold. The catalog builds, tests, and validates while `catalog/`, `projects/`, and `schema/` have no content beyond directory placeholders. There is no `pl` command, no pattern record, no schema document, no Mathlib dependency, and no Blender import.

## U1

U1 adds five schema documents and twelve seed records. Pattern records live in `catalog/`. Project records live in `projects/`. U1 ships `schema/projects.schema.json` and leaves `projects/` empty. Schemas for `pattern-instance`, `check-report`, and `step` sit in the directory map for a later unit that adds those directories to the record roots. Field lists follow `DESIGN.full.md` §1.4. The twelve numbers and names are the seed in §1.5. Pattern-instance status names are the states in §2.4. The unit check is the U1 row of §3.3.

`scan` checks JSON Schema. An empty `catalog/` and `projects/` tree stays valid. Link existence and back-edges come from `load_catalog`. A missing target fails `scripts/validate_catalog.py`. A back-edge is printed on a successful load. Each stored smaller target in this seed is one of the twelve and greater than its source, so the command prints `back-edges: 0` and `ok: 12 records`.

Confidence is 2 on 105 South Facing Outdoors, 159 Light on Two Sides of Every Room, and 180 Window Place. The other nine records store 1 as a placeholder until each heading's asterisk count replaces it. Summaries and forces are our wording, with `draft` true.

## U2

The language laws live in `lean/PatternLanguage/`: `Language`, `Sequence`, and `Preservation`. `scripts/catalog_to_lean.py` generates `lean/PatternLanguage/Instantiations/Buildings.lean` from the seed catalog. `decide` proves that numeric order is a valid sequence for the twelve patterns. CI runs `catalog_to_lean.py --check` before `lake build` and fails when the generated file is stale.

## U3

U3 writes two IFC houses, `fixtures/pass-house.ifc` and `fixtures/fail-house.ifc`, and reads each one back into a frozen `Topology` of zones, adjacencies, boundaries, and openings. Each of the ten computed patterns has a pass witness on one house and a fail witness on the other. 110 Main Entrance and 180 Window Place are judged and have no house. Tests read zones, adjacency, window orientations, and heights. `make_fixtures.py --check` compares those graphs and the sibling `.expected.json` files. It does not compare STEP bytes. U3 does not evaluate a condition.

A window or door stores its host space in `ObjectType`. Facing is the outward normal of that host's footprint edge. `ifcopenshell` is imported only inside `read_ifc` and `write_ifc`.

## Gate

`scan(root)` reads JSON files under `catalog/` and `projects/`. Other directories, including `fixtures/`, are ignored. A file is a record when its name ends in `.json` and does not start with a dot.

`DirectorySchemaMap` loads `schema/<directory>.schema.json`. The file `schema/catalog.schema.json` covers records in `catalog/`. A nested file such as `schema/catalog/room.schema.json` covers `catalog/room/` and wins over a shorter prefix. The map is built from the `schema/` directory unless a caller passes one in.

`CatalogScan` is frozen. It records the root, the record paths, and the errors. `ok` is true when `errors` is empty.

An empty `catalog/` and `projects/` is valid, including trees that contain only `.gitkeep`. A missing `catalog/` or `projects/` directory is an error. A record whose directory has no schema is an error (`record without schema`). Records that have a schema are checked with JSON Schema draft 2020-12. Invalid JSON is an error and does not stop the rest of the scan.

`scripts/validate_catalog.py` scans the repository root by default, prints `ok: N records` on success, and prints each error to stderr with exit code 1.

## Lean

`lean/` is a Lake package named `PatternLanguage` pinned by `lean-toolchain` to `leanprover/lean4:v4.33.1`. The library glob is `.submodules PatternLanguage`, so Lake builds `PatternLanguage/Language.lean` without a root `PatternLanguage.lean` module. U0 left that module as an empty namespace. `lake-manifest.json` lists no packages.

## Adapters

`adapters/blender/` and `mcp/` are reserved directories. `topology.py` imports `ifcopenshell` only inside `read_ifc` and `write_ifc`. Nothing in this repository imports `bpy`. Adapter code stays outside `src/pattern_language/`.

## Copyright

Cite pattern numbers and names only. Do not copy book text into records, schemas, comments, or docs.
