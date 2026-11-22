# U19 — Second block / multi-block neighborhood

Contract after U18. Draft for agents; open a PR when acceptance is green. Do not merge from agents.

## Goal

Grow the seed from one block pair into a **multi-block neighborhood**: East Street between South and East blocks, a `district-seed` container, land-use roles on parcels, and a Main Street enclosure H:W stub — Layer 3 of the city roadmap.

## In scope

1. Extend Main + Cross ROWs to ~120 m; add `street-east` linking Main × Cross.
2. `block-east` with Lots E/F, courts, gates, massings, addresses, frontage rhythm.
3. `district-seed` parent for the three blocks; WebGL skips district/block envelopes (lots/streets draw ground).
4. Parcel roles: `living` on house lots, `work` on workshop.
5. `m-enclosure-main` section stub from `enclosure_hw`.
6. CityJSON: East Street Road; district as LandUse `neighborhood`.
7. Docs + tests. No `pl` / Lean / MCP / MapLibre.

## Acceptance

```bash
uv run python demo/build_district.py
uv run python scripts/lint_spatial.py
uv run pytest tests/test_webgl_quality.py tests/test_spatial_structure.py tests/test_cityjson_export.py
# manual: District Openings — three blocks along Main; East Street visible
```

## Non-goals

- MapLibre city product surface (Layer 4).
- New catalog patterns or Topology check changes.

## Still true

Cite pattern numbers and names only.
