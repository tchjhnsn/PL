---
name: threejs-architecture-effects
description: Architectural construction sequencing and procedural PBR materials for Three.js. Use when refining roofs, eaves, joints, assembly stages, or miniature lighting — adapted here for Decided WebGL houses, not Chinese pavilion scaffolding.
---

# Architecture Effects (PL-adapted)

Upstream: [lhlGitHub/threejs-architecture-effects](https://github.com/lhlGitHub/threejs-architecture-effects).

Use the **method**, not the pavilion starter, unless someone asks for that typology.

## Method that transfers

1. Stable silhouette first; adjoining parts share dimensions — no floating upper storeys.
2. Assembly order matches Decided stages: survey → land → foundation → frame → openings.
3. Author materials separately (plaster, asphalt, grass, gravel, glass); do not hide crude joints with fog or bloom.
4. Rhythm and repeating bays over random ornament.
5. Self-verify with orbit + close-up cameras (`__plWebgl.setCamera`).

## Out of scope for this repo

Do not scaffold a new Vite/React app over `demo/`. Stay on `three@0.170` in `demo/webgl.js`. City morphology lives in SpatialStructure / CityJSON first.
