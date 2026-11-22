# Where this project sits

Public and private both need the same spine: we are not a physics engine and not a general GIS. We are a **pattern language** — semantic rules over place — that must sit cleanly among existing AEC/urban formalisms.

## What we are

| We own | Meaning |
|---|---|
| Pattern catalog | Application ontology: numbered patterns, links, conditions, draft prose |
| Project language | A selection of patterns + parameters (e.g. `latitude_deg`) |
| Checks / sequence / preservation | Whether a model satisfies patterns and whether a step undoes earlier ones |
| Lean laws | Language-level theorems (sequence, preserving), not building physics |

That is closest to **semantic city/building models + classifications/dictionaries**: what a place *means* and which named patterns apply — not CFD, structural FEA, or traffic microsimulation.

## What we deliberately use from the world

| Concern | Use | Do not use as our core |
|---|---|---|
| Urban / city semantics | **CityGML 3.0 model** via **CityJSON** files | CityGML-XML as day-to-day authoring |
| Building product detail | **IFC** (ISO 16739) import/export | Revit/DWG as the public spine |
| Topology vocabulary | **BOT**-shaped zones (Site/Building/Storey/Space) | Full ifcOWL graph as required runtime |
| Real geography | CRS, terrain/context as **inputs** to checks | Owning a global basemap stack |
| Light / sun | Solar geometry from lat/long/time (as today) | Full radiosity / climate engines |
| Classifications | bSDD / Uniclass/OmniClass **when labeling** | Replacing pattern numbers with those codes |
| Statutory zoning | XPlan / INSPIRE PLU **later**, as a facet | Treating PL as a legal plan format |
| Ops / handover | COBie / Brick **out of scope** for now | |

**Geography and light are first-class planning inputs**, not “nice visuals.” A pattern such as 105 South Facing Outdoors or 128 Indoor Sunlight is meaningless without north, latitude, and openings. That is still **semantic + geometric solar**, not material physics.

## What we are not

- Not a real-world physics simulator (structures, fluids, acoustic FEM).
- Not a replacement for CityGML/IFC — we **consume and annotate** them.
- Not only an architectural CAD plugin — Alexander’s language is multi-scale; the seed house was a witness, not the ceiling.

## Stack (adopted)

```text
┌─────────────────────────────────────────────────────────┐
│  Pattern Language (ours)                                │
│  catalog · project · check · step · Lean · MCP          │
├─────────────────────────────────────────────────────────┤
│  Place model                                            │
│  CityJSON (city/urban)  ·  IFC (building detail)        │
│  BOT-shaped topology (internal graph)                   │
├─────────────────────────────────────────────────────────┤
│  Context                                                │
│  CRS · site georegistration · solar params              │
├─────────────────────────────────────────────────────────┤
│  Optional later facets                                  │
│  LandInfra · XPlan/INSPIRE · bSDD labels · 3D Tiles viz │
└─────────────────────────────────────────────────────────┘
```

**SpatialStructure** ([`schema/spatial-structure.schema.json`](../../schema/spatial-structure.schema.json)) is the mid-layer between CityJSON/IFC and plan-symbology. CityJSON and IFC remain the interchange documents. SpatialStructure holds the places, the directed circulation network, and the named measures that `demo/plan.js` draws as centerlines, width bands, and dimension strings. Unit note: [U8-SPATIAL-STRUCTURE.md](U8-SPATIAL-STRUCTURE.md).

**When / where / how / why / whether** (working rules):

- **CityJSON** — public spatial document for districts, blocks, massing, urban PL work; why: matches city developers; whether: default for new urban seeds.
- **IFC** — building interiors, openings, storeys; why: BIM interchange we already check; whether: keep for building witnesses and Blender/Bonsai.
- **BOT** — shared names for containment/adjacency; why: already matches `topology.py`; whether: vocabulary, not a second file format we must ship.
- **Our JSON Schema catalog** — the pattern dictionary; why: no CityGML class is “127 Intimacy Gradient”; whether: always.
- **GeoPackage / GeoJSON** — 2D planning overlays and light web maps; why: planners live here; whether: derived views, not the semantic source of truth.
- **Cesium / full digital-twin clients** — only if a stakeholder requires globe-scale streaming; whether: **not** the default workbench.

## Software pick (authoring vs viewing)

Heavy client rendering on CityGML/Cesium demos is a product smell for *our* loop. We need readable place + pattern status, not a GPU twin by default.

| Role | Pick | Why |
|---|---|---|
| Pattern / check core | This repo (Python + Lean + MCP) | Already proven U0–U7 |
| City model files | **CityJSON** (+ `cjio` for validate/convert) | Standard, JSON-native, subset of CityGML 3.0 |
| Building files | **IFC** (+ IfcOpenShell / Bonsai) | Already integrated |
| Default **web UI** | **MapLibre GL** + extruded footprints (fill-extrusion) / MVT | Lightest credible map UX; strong 2D cartography; avoid loading a second 3D engine until needed ([MapLibre vs Cesium feature/benchmark notes](https://www.ortho-earth.com/docs/story-features)) |
| Optional rich 3D | CityJSON → glTF / 3D Tiles, or [ninja](https://github.com/cityjson/ninja/) behind a toggle | Keep off the critical path; Cesium only for globe/streaming cases |
| Desktop GIS | QGIS + GeoPackage | Planner-native inspection, not our runtime |
| Blender | Existing adapter (gated live path) | Design app, not the public web surface |

**Decision:** build the public/local explorer on **MapLibre-first** (map + height extrusions + pattern overlays). Store place as **CityJSON** (and IFC where building-detailed). Do not make Cesium or full WebGL city twins the default — derive heavier viz only when a dataset needs it.

## Demo posture

`demo/` ships an **owned plan-symbology** renderer (`pattern-language.plan-symbology`): SVG floor/site plan with flow centerlines, dimension strings, door swings, windows, canopy trees, figure–ground, and pattern diagrams. CityJSON remains interchange. SpatialStructure is the mid-layer those drawings read. See `docs/design/VISUAL-LANGUAGE.md` and [U8-SPATIAL-STRUCTURE.md](U8-SPATIAL-STRUCTURE.md). Marketing/Naive dogfood is deferred.

## Urban typologies (U24)

Street / plot / building / fabric / transect / program types live in
[`schema/ontology/urban-typologies.json`](../../schema/ontology/urban-typologies.json).
See [URBAN-TYPOLOGY.md](URBAN-TYPOLOGY.md). That ontology binds to the kit
component library (`pattern_language.kits.registry`) without replacing CityGML or IFC.

## Next formalization pass

Catalog existing formalisms (CityGML modules, IFC domains, LandInfra, BOT, bSDD, planning models) into a single **inventory** with adopt / adapt / ignore / later. This file is the adopt-map for *our* product; the inventory is the wider shelf we will sort next.
