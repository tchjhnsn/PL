# U23 — Real city fabric

## Goal

Grow past the seed neighborhood into a multi-neighborhood city quarter with
civic and commercial program, green fingers, and stampable kits — so the demo
reads as a city, not a single house plot series.

## Contract

- `generate_city_fabric` stamps a grid of blocks (~84 m pitch) with:
  - **3 City Country Fingers** — north–south park columns every fourth block
  - **Identifiable Neighborhood** / **Neighborhood Boundary** — street grid + blocks
  - **Shopfront Schools**, **Connected Play** — school + playground pairs
  - **Corner Grocery**, **Market of Many Shops**, **Shopping Street**, **Web of Shopping**
  - **Local Town Hall**, police, bank, **Health Center**
  - **Industrial Ribbon** utilities on the metro edge
  - Residential **frontage_lot** stamps elsewhere
- Kits: `program_place`, `city_fabric` (plus existing `frontage_lot`)
- Plan cites town-scale pattern **numbers and names only** (no book text)
- No new `pl` command, Lean edit, MCP tool, or catalog records in this unit
- Spatial lint must pass on the merged plan

## Commands

```bash
uv run python demo/build_district.py
uv run python scripts/lint_spatial.py
uv run pytest tests/test_kits.py tests/test_spatial_structure.py tests/test_webgl_quality.py tests/test_cityjson_export.py tests/test_maplibre_city.py
```

## Out of scope

Catalog / Lean town-pattern records; measure conditions for civic program;
Blender.
