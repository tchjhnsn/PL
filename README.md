# Pattern language

U0 scaffold for an empty pattern-language catalog. `catalog/` and `projects/` contain no records, `schema/` contains no schema documents, and the gate accepts that empty tree. Records without a schema fail validation.

The Lean library is `PatternLanguage` on toolchain `leanprover/lean4:v4.33.1`. It has no dependencies.

## Commands

```bash
uv sync
uv run pytest
uv run python scripts/validate_catalog.py
cd lean && lake build
```

Cite pattern numbers and names only. Do not copy book text into this repository.
