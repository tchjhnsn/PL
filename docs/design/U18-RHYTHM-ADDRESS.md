# U18 — Frontage rhythm + address every parcel

Contract after U17. Draft for agents; open a PR when acceptance is green. Do not merge from agents.

## Goal

Finish Layer 2 grain: **named frontage rhythm** on each block face, and an **address node on every parcel** (including the workshop) so the network meets 110-scale address points.

## In scope

1. `m-frontage-rhythm-main` / `m-frontage-rhythm-cross` documenting plot-series grain (A–B and C–D).
2. `m-building-line-cross` setback face for the north block; Cross Street frontage interfaces.
3. Workshop address: `path-approach-w`, `w-door-approach`, `n-addr-w`, approach edges from the lane junction.
4. Address nodes remain for A (`n-door`), B, C, D, and workshop.
5. Docs + tests. No schema enum churn beyond existing measure kinds (`frontage` / `setback`). No `pl` / Lean / MCP.

## Acceptance

```bash
uv run python demo/build_district.py
uv run python scripts/lint_spatial.py
uv run pytest tests/test_webgl_quality.py tests/test_spatial_structure.py tests/test_cityjson_export.py
# manual: plan / WebGL network — five address nodes; rhythm measures present
```

## Non-goals

- No second district / MapLibre.
- No urban pattern catalog expansion.

## Still true

Cite pattern numbers and names only (110 Main Entrance for address points).
