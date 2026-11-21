---
name: threejs-procedural-buildings-and-cities
description: Compile procedural buildings, cities, and semantic site assemblies for Three.js. Use for city-scale massing, block/street layout, plot series, LOD/batching guidance, and SpatialStructure → CityJSON urban seeds in this repo.
---

# Procedural Buildings and Cities (PL-adapted)

Upstream: [linegel/threejs-complete-set-of-skill](https://github.com/linegel/threejs-complete-set-of-skill/blob/main/skills/threejs-procedural-buildings-and-cities/SKILL.md).

**PL path:** CityJSON + SpatialStructure mid-layer first; WebGL Decided viewer second; MapLibre later for city map. Stay on `three@0.170` WebGL until an explicit upgrade unit.

## Process (mapped to this repo)

1. **Serializable plan before triangles** — author blocks, streets, lots, courts, gates, addresses in `demo/build_district.py` / SpatialStructure; lint with `scripts/lint_spatial.py`.
2. **Block morphology** — `block` places, street hierarchy (arterial / local / lane), junctions, plot series with frontage measures.
3. **Exposed street wall** — garden walls + gates on primary frontage; building line as named measure; every parcel meets the network (address node).
4. **Compile for draw cost** — shared materials, instanced vegetation, walls with opening gaps; district chunks when the seed grows past one screen.
5. **Verify** — screenshot Openings + District; flat material / grazing sun; lint + pytest green.

## Ownership

- Pattern catalog / `pl check` — building witnesses (IFC), not city mesh quality.
- SpatialStructure — places, network, measures, interfaces.
- CityJSON LoD0 — urban interchange export.
- `demo/webgl.js` — Decided-stage mesh emission only.
