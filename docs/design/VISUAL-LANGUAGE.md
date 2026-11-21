# Visual language — how place must be readable

The MapLibre district with colored polygons and dots is a **data probe**, not what city developers or pattern readers look at. If you cannot tell a door from a tree at a glance, the representation has failed.

`demo/plan.js` draws flow, distance, and the place glyphs from geometry: centerlines, dimension strings, door swings, window ticks, canopies, figure–ground masses, and pattern diagrams. The concepts those marks stand for are in [SPATIAL-CONCEPTS.md](SPATIAL-CONCEPTS.md). The sheet reads a SpatialStructure document ([`schema/spatial-structure.schema.json`](../../schema/spatial-structure.schema.json)).

This note separates three things people conflate:

1. **Semantic type** — what the object *is* (CityGML / IFC / our components)
2. **Drafting symbology** — how professionals *draw* it so humans recognize it
3. **Pattern diagram** — how *A Pattern Language* shows a solution as a labeled sketch

We need all three. CityJSON alone only gives (1).

## What Pattern Language itself renders

Each pattern in the book uses the same graphic habit ([Alexandrian form](https://kidneybone.com/c2/wiki/AlexandrianForm), [pattern illustrating research](https://hillside.net/plop/2014/papers/Social_Related/harasawa_2.pdf)):

| Piece | Role |
|---|---|
| Archetype **picture** | Feeling / example of the pattern in the world |
| **Diagram** after the solution | Labeled drawing of the physical relationships |
| Labels on parts | Name the centers (entrance, path, court…) |

Those diagrams are **plans, maps, and compositional sketches** — not GIS feature collections. They make structure obvious: what sits where, what opens onto what. Our UI must eventually speak that diagram language (our own drawings; never paste book art).

## What city developers and planners actually look at

| Drawing | What you see immediately | Standard / habit |
|---|---|---|
| **Figure–ground (Nolli / Schwarzplan)** | Buildings = solid mass; streets & courts = void | Classic urban morphology tool ([Morphocode](https://morphocode.com/figure-ground-diagram/), [UCL figure-ground](https://www.ucl.ac.uk/bartlett/sites/bartlett/files/1.4_techniques_handouts_illustrator-figure-ground.pdf)) |
| **Site plan** | ROW, curb, sidewalk, building footprint, entrances, trees with trunk + canopy, legend, north, scale | Municipal site-plan requirements ([e.g. San Bernardino](https://www.sanbernardino.gov/DocumentCenter/View/2262/Architectural-Plans-PDF)); survey tree conventions |
| **Architectural floor plan** | Walls poché’d; **doors with swing arcs**; **windows as breaks/ticks** in wall; rooms named | Measured-drawing practice ([HABS guidelines](https://www.nps.gov/subjects/heritagedocumentation/upload/HABS-Guidelines-Measured-Drawings_508.pdf)): doors swing 90°, casements 45° |
| **CADD symbol libraries** | Standardized blocks for doors, windows, trees, furniture | e.g. [PSPC National CADD Standard — symbols](https://publications.gc.ca/collections/collection_2024/spac-pspc/P26-4-2024-2-eng.pdf) |

**Immediate recognition comes from symbology + contrast + legend**, not from a hover tooltip on a dot.

## What digital city standards actually specify

[CityGML / CityJSON](https://www.cityjson.org/about/) define **thematic classes** and **levels of detail**, not a mandatory pretty renderer:

| Class (examples) | Meaning |
|---|---|
| `Building`, `BuildingPart`, `Door`, `Window` | Construction semantics |
| `Road`, `Transportation` | Streets / squares as networks or surfaces |
| `SolitaryVegetationObject` / `PlantCover` | Trees and planting |
| `CityFurniture` | Benches, lights, signs |
| `LandUse`, `Relief` | Use and terrain |

**LoD ladder** (buildings) ([CityGML overview](https://3d.bk.tudelft.de/hledoux/pdfs/18_bimbook_citygml.pdf), [CityGML wiki](https://www.citygmlwiki.org/index.php/Basic_Information)):

| LoD | What it looks like |
|---|---|
| 0 | Footprint / roof edge (2.5D map) |
| 1 | Extruded block (what our demo mostly was) |
| 2 | Roof shape + themed surfaces |
| 3 | Façade detail — **doors and windows as geometry** |
| 4 | Interior rooms, stairs, furniture |

**Appearance** module = materials/textures attached to surfaces — still not “draw a door swing.”  
**IFC** similarly stores `IfcDoor` / `IfcWindow` / `IfcSpace`; Bonsai/Blender or plan exporters choose the glyphs.

So: **standards exist for *what* the object is and at what detail; the glance-readable *drawing* is a separate layer** (drafting symbology + urban diagram grammar + our pattern diagrams).

## How each kind of thing should render (target)

| Object | Digital type (CityGML/IFC) | Human glyph (what we must draw) |
|---|---|---|
| Street | `Road` / transportation surface | Continuous pavement band, curb line, name; hierarchy by width |
| Circulation edge | SpatialStructure `network.edges` | Centerline, hierarchy stroke weight, directed arrowhead, width band |
| Measure | SpatialStructure `measures` | Dimension string: offset line, end ticks, value label |
| Court / green | `PlantCover` / land use / courtyard void | Soft fill or stipple; not the same hatch as street |
| Building mass | `Building` LoD1–2 | Figure–ground solid *or* light massing — never anonymous beige soup |
| Room | `Building` LoD4 / `IfcSpace` | Named compartment; wall thickness; poché on cut walls |
| Entrance / door | `Door` / `IfcDoor` | **Opening in wall + swing arc + threshold mark** |
| Window | `Window` / `IfcWindow` | **Gap or sill ticks in wall**, not a floating point |
| Tree | `SolitaryVegetationObject` | **Trunk circle + irregular canopy** (HABS); deciduous vs conifer if needed |
| Path | Road/track or our component | Narrow line with material difference from carriageway |
| Pattern | *Ours* | Labeled diagram overlay: arrows, zones, “look here” marks — Alexandrian habit |

## Geometry-aware symbology (`demo/plan.js`)

`demo/plan.js` renders `pattern-language.plan-symbology` from `demo/data/plan-model.json`. Each glyph is a `symbology.*` node in [`spatial-concept-graph.json`](spatial-concept-graph.json). Historic American Buildings Survey measured drawings are the source class for door, window, and tree marks (the [HABS guidelines](https://www.nps.gov/subjects/heritagedocumentation/upload/HABS-Guidelines-Measured-Drawings_508.pdf) linked above).

### Flow

`drawEdge` strokes each `network.edges` record as a centerline (`symbology.flow_arrow`) along `polyline`, or as the straight segment between the edge nodes. Stroke weight follows hierarchy (`symbology.hierarchy_weight`, sheet units in `HIER_WIDTH`):

| Hierarchy | Stroke weight |
|---|---|
| arterial | 0.55 |
| local | 0.40 |
| lane | 0.32 |
| approach | 0.28 |
| path | 0.22 |

When `directed` is true, the centerline ends in the `#flowhead` arrowhead. A second stroke, class `centerline-band`, draws the width band at `max(width_m × 0.15, 0.4)`. The edge label prints the name and the width in metres.

### Measures

`drawMeasure` draws each `measures` record as a dimension string (`symbology.dimension`): a dashed offset line parallel to the segment, a tick at each end, and a label with the measure name and the value in metres.

### Place marks on the same sheet

| Mark | Drawer | Graph node |
|---|---|---|
| Door: opening in the wall, swing arc from `swing` (`ccw` or `cw`), leaf | `drawDoor` | `symbology.door_swing` |
| Window: glass line with a tick at each jamb | `drawWindow` | `symbology.window_tick` |
| Tree: lobed canopy from `canopy`, trunk circle from `trunk` | `drawTree` | `symbology.tree_canopy` |
| Building solids as figure–ground mass (`kind: solid`, class `mass-fill`) | place loop | `symbology.figure_ground` |
| Pattern diagram: zones, labeled arrows (`#arrowhead`), rays, markers, opening rings | `drawDiagram` | `symbology.diagram_overlay` |

The profile node is `symbology.profile` (`pattern-language.plan-symbology`).

### Legend

The sheet legend in `demo/plan.html` (`symbology.legend`) includes **Flow** (centerline and arrowhead) and **Measure** (dimension line with end ticks), with Street, Outdoor, Building, Door, Window, and Tree. North and the scale sit in the sheet header.

## Owned layer (productizable)

CityGML/IFC/CityJSON do **not** own glance-readable glyphs. We do.

| Layer | Owner | Ship as |
|---|---|---|
| Semantic place types | CityJSON / IFC / BOT-shaped graph | interchange files |
| **Plan symbology + pattern diagrams** | **Pattern Language (`pattern-language.plan-symbology`)** | renderer + profile — **ours to productize** |
| Photoreal / heavy twins | Optional later consumers | not our default |

Acknowledging this on future marketing pages matters: *we turn formal place models into drawings humans can read the way they read a floor plan* — doors swing, trees have canopies, patterns draw as diagrams. That is a product surface, not a side effect of MapLibre.

**Marketing / Naive dogfood:** deferred on purpose. Do not split focus onto a marketing agent until this workbench is legible and the owned layer is stable.

## Adopted direction

1. **Keep CityJSON/IFC** as semantic store (types + geometry).  
2. **Own the rendering profile** `pattern-language.plan-symbology` — SVG plan engine in `demo/`.  
3. **Two coupled views**  
   - District: figure–ground massing + streets + canopy trees + flow centerlines + district measures + House A fabric  
   - House A: walls, door swings, window ticks, room names, approach flow, interior measures  
4. **Pattern mode**: diagram overlays (zones, arrows, rays, markers) on the same sheet as the dimension strings.  
5. Do **not** treat Cesium photorealism as the fix; legibility ≠ rendering weight.

## Demo

```bash
python3 demo/build_district.py
python3 demo/serve.py   # http://127.0.0.1:8765/
```

Source of truth for the sheet: `demo/data/plan-model.json` (`owned_layer` field), drawn by `demo/plan.js`. CityJSON/GeoJSON remain interchange/export siblings. Glyph nodes: [`spatial-concept-graph.json`](spatial-concept-graph.json) (`symbology.*`). Schema: [`schema/spatial-structure.schema.json`](../../schema/spatial-structure.schema.json).
