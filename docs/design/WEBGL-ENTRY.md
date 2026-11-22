# WebGL entry level

Blender + Bonsai remains a **complete** professional path for IFC authoring and the live e2e loop (`docs/design/E2E-BONSAI-EFFECT.md`). It is not required to start.

## Entry surface

`demo/` serves a **Three.js** Decided stage viewer as `http://127.0.0.1:8765/`:

- Stage strip: Survey → Land → Foundations → Frames → Openings → Patterns (default **Land**).
- Loads `data/seed-district-survey.json`, `data/process-stages.json`, and `data/plan-model.json`.
- Survey/land first: site ground, contours, north rose, sun sector, lots; then pads; then frames/openings.
- Light and materials: `docs/design/WEBGL-QUALITY.md`.
- Pattern focus and **measured** evidence only at the Patterns stage.
- SVG plan stays at `/plan.html`. Concept graph at `/concepts.html`.
- Process rules: `docs/design/DECIDED.md`. Satisfaction: `docs/design/SATISFACTION.md`.

```bash
python3 demo/serve.py
# open http://127.0.0.1:8765/
```

## Optional advanced path

Blender + Bonsai + PL add-on for IFC edit / export / `drive_run`. See `adapters/blender/README.md`.

## Out of scope (this slice)

- `web-ifc` mesh load of `fixtures/*.ifc` (next: optional IFC layer once plan extrusion is stable).
- Marketing / Naive dogfood (deferred).
