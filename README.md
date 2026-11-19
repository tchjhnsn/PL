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

## Commands

```bash
uv sync
uv run pytest
uv run python scripts/validate_catalog.py
uv run python scripts/catalog_to_lean.py --check
cd lean && lake build
```

Cite pattern numbers and names only. Do not copy book text into this repository.
