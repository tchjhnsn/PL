# WebGL quality

Reference: [threejs-archviz.vercel.app](https://threejs-archviz.vercel.app) (Anderson Mancini, Seashore house). That page is the visual bar for light, ground, and camera. It is a Blender-optimized glTF (`beach-house8.glb`) under an EXR environment (`spruit_sunrise_1K.exr`), with midday/sunset sun controls. The page warns that its SSAO pass is expensive. Our viewer stays a Decided stage model. Blender + Bonsai remains the finished-house path (`WEBGL-ENTRY.md`).

## What reads as quality there

- Filmic color (ACES-style grading) and a real sky, not a flat clear color
- One sun plus image-based ambient light, with soft shadows
- PBR materials: grass and gravel underfoot, reflective water, glass that catches the sky
- Vegetation with volume, not a single lollipop sphere
- A low architectural camera and thin chrome (customize panel, vignette), not a CAD grid

## Adopted

In `demo/webgl.js` / `demo/index.html`, still on the demo's pinned `three@0.170`:

- `ACESFilmicToneMapping`, sRGB output, exposure, pixel-ratio cap (2 desktop, 1.5 on mobile)
- One shadow-casting directional sun and a dim hemisphere light. Ambient fill removed so shadows stay visible. The visible sky is the `Sky` shader (drawn on the far plane, fog off). Its PMREM, captured with tone mapping off, is the image-based light only — no downloaded HDR
- Look panel: sun time slider (midday → sunset) refreshes sky uniforms, PMREM, fog, sun color/intensity, and shadow maps. Soft bloom via `EffectComposer` + `UnrealBloomPass` + `OutputPass` (on by default on desktop; off on mobile)
- `PCFSoftShadowMap`, 2048 map (1024 on mobile), frustum fit to the site, `shadowMap.autoUpdate` off and refreshed when the stage rebuilds or the sun moves
- Seeded canvas maps for grass, gravel, asphalt, and plaster (repeat wrap, anisotropy). Shared maps, not a texture per place
- Site ground plane in grass. The dark void plane and the `GridHelper` are gone
- Pond places use `MeshPhysicalMaterial` (transmission / IOR) so they read as water. Facade windows and catalog openings use the same glass stack. Building shells tint a plaster map
- Authored trees only: instanced trunks, layered evergreen cones, faceted deciduous crowns, plus understory shrubs around trees and on green cover
- Default camera near eye height so the sky sits above the site. Orbit can drop to just above the horizon. Damping and a CSS vignette
- Decided strip unchanged: survey → land → foundation → frame → openings → patterns

## Deferred

- The reference house mesh, interior glass, and purchased-model detail
- An HDRI file (PMREM still comes from the procedural sky)
- SSAO and LUT grading. The reference flags SSAO as a GPU risk, and extruded massing does not have the surface detail that pass needs
- Cascaded shadows
- `web-ifc` meshes. Extrusions stay the semantic view

## Still true

Stages still hide later work. Pattern focus still recolors places. Satisfaction is still the check report, not the picture. 110 Main Entrance and 180 Window Place stay judgment items.
