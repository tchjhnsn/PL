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

## Commands

```bash
uv sync
uv run pytest
uv run python scripts/validate_catalog.py
cd lean && lake build
```

Cite pattern numbers and names only. Do not copy book text into this repository.
