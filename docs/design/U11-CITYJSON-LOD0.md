# U11 — CityJSON LoD0 + TrafficArea parity

Contract. Expand `demo/build_district.py` → `district.city.json` so interchange matches the SpatialStructure seed: LoD0 footprints, Road children as TrafficArea (carriageway / sidewalk), land / water / vegetation. SpatialStructure remains the owned mid-layer; CityJSON stays export.

## In scope

1. `Road` for ROW places; child `TrafficArea` objects for carriageway (`function: drivingLane`) and sidewalk (`function: footpath`), granularity `way`.
2. LoD0 `MultiSurface` footprints for buildings, roads, lots (`LandUse`), green (`PlantCover`), pond (`WaterBody`).
3. LoD1 solids kept for building massing where already present.
4. `SolitaryVegetationObject` for plan trees (optional attributes: species, form).
5. Pytest: required CityObject ids and parent/child links; LoD0 present on TrafficAreas.

## Non-goals

- Full CityGML 3 Section/Intersection types (CityJSON encodes as attributes).
- Lane-level granularity.
- New `pl` command, MCP tool, Lean, or Blender change.

## Acceptance

```bash
uv run python demo/build_district.py
uv run pytest tests/test_cityjson_export.py
uv run python scripts/lint_spatial.py
```

## Exit

Draft PR titled `U11 CityJSON LoD0 TrafficArea`. Agents do not merge.
