# Research notes — Three.js viewer + site inventory (2026-11-20)

## Diagnosis of colliding Land view

Seed parcels and `green-shared` previously **area-overlapped** in plan. Coplanar transparent meshes then z-fought in WebGL. Fix: non-overlapping lots + green; opaque land/cover; slight Y bias; `scripts/lint_spatial.py` gates rebuild.

## Three.js practices applied

- Prefer opaque geometry for land/cover; translucent only for street voids (`depthWrite: false`).
- Dispose geometries/materials on rebuild; cap DPR at 2.
- Semantic trees as simple meshes (cylinder + cone/sphere), not photoreal.
- Sources: Three.js transparency manual; `emalorenzo/three-agent-skills` (`three-best-practices`); `cesartevisual/threejs-skills` (`threejs-spatial-data`, `threejs-testing`).

## Site survey inventory (landscape practice)

Survey is not only cadastral. Inventory includes ground cover, vegetation (species/form/canopy), and water. Greenfield authoring may plant trees and dig ponds. Refs: MSU landscape plan; NC State vegetation map; municipal landscaping checklists (Cheshire East, Knox, Fontana).

## Spatial lint pattern

Topology QA: must-not-overlap peers, covered_by for sit-on, buffered clearance. Implemented as AABB lint (seed rings are axis-aligned). Broader polygon SAT / Shapely can wait until concave rings appear.

## Skills installed in-repo

`.agents/skills/three-best-practices`, `threejs-spatial-data`, `threejs-testing`.
