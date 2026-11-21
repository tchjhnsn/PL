---
name: threejs-procedural-architecture
description: Build authored procedural buildings and architectural kits in Three.js. Use for massing grammars, exposed-edge analysis, façade bays, roofs, material-slot mesh compilation, and Decided/SpatialStructure-driven house visuals in this repo.
---

# Procedural Architecture (PL-adapted)

Upstream: [scottstts/Threejs-Awesome-Graphics-Agent-Skills](https://github.com/scottstts/Threejs-Awesome-Graphics-Agent-Skills/blob/main/skills/threejs-procedural-architecture/SKILL.md).

**This repo pins `three@0.170` WebGL** in `demo/`. Do not switch to WebGPU/TSL unless a unit explicitly upgrades the import map. Prefer SpatialStructure plan → mesh emission over inventing geometry that is not in the plan.

## Required architecture

```text
SpatialStructure / building plan
  → mass grammar (footprint, stack, court)
  → exposed-surface graph
  → façade / roof / opening placements
  → material-slot mesh writer (demo/webgl.js)
  → geometries
```

## Rules

- Massing, façade rhythm, and detail modules are separate layers.
- Resolve exposed edges before façade placement. Do not decorate hidden internal faces.
- Upper storeys sit on `floor_elevation_m`; never extrude an elevated room from grade through the roof below.
- Outdoor decks (balcony, porch) are thin slabs + posts/rails — not storey-tall void boxes.
- Compile by material slot / shared maps to cut draw calls (`InstancedMesh` for trees, shared plaster/grass maps).
- Preserve real metres for floor height, bay width, balcony depth, and texture density.
- Randomness may select among valid designs; it must not repair invalid geometry.
- Self-verify with screenshots (`__plWebgl.setCamera` / `setStage` / `setMode`) before claiming a house “works.”

## Acceptance

Survives: silhouette-only view; flat untextured material; grazing light; close inspection of corners, roofs, and openings; no door onto a roof that is not a deck; seed variation without floating ornament.
