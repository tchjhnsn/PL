# Pattern language

U0 scaffold for an empty pattern-language catalog. The gate accepts an empty `catalog/` and `projects/` tree. Records without a schema fail validation.

## U1

Five JSON Schemas live in `schema/`: `catalog`, `projects`, `pattern-instance`, `check-report`, and `step`. Twelve seed records live in `catalog/`. `projects/` has no records. `load_catalog` reads the records `scan` accepted and reports missing link targets and back-edges.

From the repo root, `uv run python scripts/validate_catalog.py` prints:

```text
back-edges: 0
ok: 12 records
```

The Lean library is `PatternLanguage` on toolchain `leanprover/lean4:v4.33.1`. It has no dependencies.

## U2

`scripts/catalog_to_lean.py` renders `lean/PatternLanguage/Instantiations/Buildings.lean` from the seed catalog. The laws live in `lean/PatternLanguage/`. `decide` proves that numeric order is a valid sequence for the twelve patterns. `lake build` checks that proof.

```bash
uv run python scripts/catalog_to_lean.py
uv run python scripts/catalog_to_lean.py --check
cd lean && lake build
```

`--check` exits 0 when the committed file matches the render, and exits 1 without writing when the file is stale.

## U3

`scripts/make_fixtures.py` writes `fixtures/pass-house.ifc` and `fixtures/fail-house.ifc`, each with a sibling `.expected.json`. `read_topology` reads a house into zones, adjacency, window orientations, and heights. The ten computed patterns each have a pass witness on one house and a fail witness on the other. 110 Main Entrance and 180 Window Place have no house.

```bash
uv run python scripts/make_fixtures.py
uv run python scripts/make_fixtures.py --check
```

`--check` exits 0 when the committed graphs match a fresh write, and exits 1 without writing into `fixtures/` when a file is missing or stale. It compares graphs, not STEP bytes.

## Commands

```bash
uv sync
uv run pytest
uv run python scripts/validate_catalog.py
uv run python scripts/catalog_to_lean.py --check
uv run python scripts/make_fixtures.py --check
cd lean && lake build
```

Cite pattern numbers and names only. Do not copy book text into this repository.
