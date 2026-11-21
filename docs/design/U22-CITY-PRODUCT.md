# U22 — City product chrome + object library

Contract after U21. Draft for agents; open a PR when acceptance is green. Do not merge from agents.

## Goal

Make the **top-level experience readable** (no process jargon in the rail) and start the **stampable object library** so the city grows from kits, not anonymous one-offs — applied research toward a metropolis.

## In scope

1. Rewrite WebGL + map rails: Seed City, Build order, Whole city / House A, plain pattern language.
2. `docs/design/PRODUCT.md` — who this is for.
3. Skills: `pl-demo-ux`, `pl-applied-research`.
4. Kit: `pattern_language.kits.frontage_lot` — stamp Lots I/J on Far East Block.
5. Extend Main/Cross/North to 150 m; five+ blocks; lint green.
6. Tests for chrome bans, kits, city span.

## Acceptance

```bash
uv run python demo/build_district.py
uv run python scripts/lint_spatial.py
uv run pytest tests/test_kits.py tests/test_webgl_quality.py tests/test_maplibre_city.py tests/test_spatial_structure.py
python3 demo/serve.py   # rail says Seed City / Build order — no “Decided stage viewer”
```

## Non-goals

- Full migration of every hand lot onto kits (incremental).
- New catalog pattern records.
- Breaking spatial lint rules for “interesting” cities.

## Still true

Cite pattern numbers and names only. Metropolis = compose kits under lint.
