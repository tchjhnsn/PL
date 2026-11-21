# U23 — Scale ladder UX (research → product)

## Mistake we keep making

Jumping to “City” and deleting or renaming away the **neighborhood**. The seed block is the detailed core. The metro is an **outer scale**, not a replacement.

## Research (applied)

- **Progressive disclosure by scale** — landmarks/districts first; street and building detail as you come in ([Layerpin zoom visibility](https://www.layerpin.com/docs/zoom-visibility), [map UX principles](https://www.maplibrary.org/9568/7-map-based-user-experience-design-principles/)).
- **City → District → Street → Property** as one model, many views ([Spatial](https://mukoko.studio/spatial), [3DGeoCity](https://3dgeo.city/platform.html), ArcGIS Urban).
- **Map/canvas first, slim chrome** — the 3D place is the product; the rail is a light HUD ([Oxagon digital twin](https://kunal-soni.com/oxagon)).
- **Anchor the focus** — orbit around the active scale so the reader doesn’t lose the place ([Zillow SkyTour](https://www.zillow.com/news/designing-an-immersive-3d-experience-for-home-exteriors-skytour/)).

## Product rule

| Scale | Shows | Default? |
|---|---|---|
| House A | Seed house detail | no |
| Neighborhood | Seed streets, courts, House A… (no metro fabric) | **yes** |
| City | Seed + metro quarters (fingers, shops, civic) | no |

HUD: plain words only (`Neighborhood · Buildings · drag to look`). Never `unlocks survey.complete`.

## Verify

Hard-refresh `/` — Scale shows House A / Neighborhood / City; Neighborhood is active; seed courts still there; City adds green fingers south/east.
