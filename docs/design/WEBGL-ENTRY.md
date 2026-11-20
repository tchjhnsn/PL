# WebGL entry level

Blender + Bonsai remains a **complete** professional path for IFC authoring and the live e2e loop (`docs/design/E2E-BONSAI-EFFECT.md`). It is not required to start.

## Entry surface

`demo/` serves a **Three.js** viewer as `http://127.0.0.1:8765/`:

- Loads `data/plan-model.json` (SpatialStructure rings → extruded volumes at `floor_elevation_m`).
- North indicator from `frame.north`; pattern focus dims unrelated volumes.
- Overlays check status and **measured** evidence from `data/pass-report.json`.
- District and House A modes; click a mesh for inspector detail (elevation + height).
- SVG plan stays at `/plan.html`. Concept graph at `/concepts.html`.
- Satisfaction rules: `docs/design/SATISFACTION.md`.

```bash
python3 demo/serve.py
# open http://127.0.0.1:8765/
```

## Optional advanced path

Blender + Bonsai + PL add-on for IFC edit / export / `drive_run`. See `adapters/blender/README.md`.

## Out of scope (this slice)

- `web-ifc` mesh load of `fixtures/*.ifc` (next: optional IFC layer once plan extrusion is stable).
- Marketing / Naive dogfood (deferred).
