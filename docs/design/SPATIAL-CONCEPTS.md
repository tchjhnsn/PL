# Spatial concepts we must codify

The plan demo failed a second test: even with door swings and trees, it still reads as a **blob of components**. You cannot see street flow, distances, or how pieces interact. That is not a CSS problem. **Symbology draws types; spatial concepts explain structure.**

Alexander’s solutions are “fields of spatial relationships,” not object catalogs ([DESIGN.full.md](DESIGN.full.md) §1.1). Our system already checks some relationships. Most of what makes a district legible is **not yet in the model**.

This document is the inventory: what exists, what is missing, and what we must make first-class (geometry-aware, metric, relational).

**Complete knowledge graph:** [`spatial-concept-graph.json`](spatial-concept-graph.json) — regenerate with `python3 scripts/build_spatial_graph.py`.  
**199 nodes / 579 edges** (foundations, metric, morphology, BOT/IFC, CityGML transport, circulation, interaction, climate, place roles, language, owned symbology, twelve seed pattern hooks).  
Nodes carry `depends_on` / `parent_of` / `sibling_of` / `maps_to` / `specializes` / `renders_as` edges, status (`have`|`partial`|`todo`|`placeholder`), and sources (BOT, CityGML, IFC, HABS, Conzen/Morpho, seed patterns).  
Browse: `demo/concepts.html` (via `demo/serve.py`). Research folds: [`research/`](research/).

**Schema:** [`schema/spatial-structure.schema.json`](../../schema/spatial-structure.schema.json) — places, directed `network`, named `measures`, `interfaces`. Not part of the catalog gate.

---

## Diagnosis

| What humans need to see | What we have today | Gap |
|---|---|---|
| How movement flows | Door adjacency + one entrance-path check (112, 127) | No district circulation network; no street direction; no path widths |
| How far things are | Coordinates exist; few metric predicates (167 depth, 107 depth) | No dimension layer; no setbacks; no spacing between buildings |
| How things interact | `Adjacency` wall/door; BOT-shaped containment | No overlook, enclosure ratio as *street* quality, frontage, approach cone |
| What is figure vs ground | Drawn as fills | Not a typed solid/void structure in data |
| Street as a thing that *goes* | Polygon labeled “street” | No centerline, hierarchy, one-way/two-way, block face |

**Decision:** the core must be aware of **geometry and spacing**, not only typed footprints. The owned symbology layer (`pattern-language.plan-symbology`) renders concepts that the **spatial model** must already hold.

---

## What we already codify (keep)

From topology + seed checks (our wording):

| Concept | In model today | Used by |
|---|---|---|
| Zone containment | Site → Building → Storey → Space | BOT-shaped graph |
| Footprint polygon | `Zone.footprint` | all geometry |
| Shared-wall / door adjacency | `Adjacency` | circulation seeds |
| Opening + cardinal facing | `Opening.orientation` | 105, 128, 159 |
| Ceiling height | `height_m` | 190 |
| Outdoor convexity | check | 106 |
| Wing depth | check | 107 |
| Street→transition→door path | check | 112 |
| Public→private order on graph | check | 127 |
| Balcony depth | check | 167 |
| Latitude / equator side | project param | 105, 128 |

This is a **building-topology** slice. It is not a **district spatial structure**.

---

## Concepts to codify (exhaustive inventory)

Grouped so we can assign owners and schemas. Each item is a candidate record or derived graph — not a drawing trick.

### A. Metric space (geometry & spacing)

| ID | Concept | Meaning | Why patterns / readers need it |
|---|---|---|---|
| M1 | Coordinate frame | CRS or local metres + north | All distances and facing |
| M2 | Length / distance | Metres between points, edges, fronts | “How far”; setbacks; balcony depth |
| M3 | Area | m² of zones and voids | Density, grain |
| M4 | Clear width / depth | Usable dimension of a space or path | 167; corridor vs room; sidewalk |
| M5 | Height / section | Vertical measure; height-to-width | 190; street enclosure |
| M6 | Setback | Building face to street / lot line | Street wall; dead space |
| M7 | Spacing / gap | Distance between buildings or masses | Grain; light; privacy |
| M8 | Dimension annotation | Named measured spans as data | Readable plans; check evidence |

### B. Solid / void structure (morphology)

| ID | Concept | Meaning | Why |
|---|---|---|---|
| V1 | Figure (solid) | Built mass | Figure–ground ([urban morphology](https://en.wikipedia.org/wiki/Urban_morphology)) |
| V2 | Ground (void) | Unbuilt outdoor continuum | Positive outdoor space; streets |
| V3 | Enclosure | How vertical edges define a void (H:W) | Outdoor “rooms” ([enclosure qualities](https://ddc.downtowndevelopment.com/wp-content/uploads/2017/02/pedestrian_and_transit_oriented_desgin_intro.pdf)) |
| V4 | Edge / street wall | Continuous vertical definition along a path | Frontage; dead gaps |
| V5 | Grain | Typical block/plot size and subdivision | Urban scale patterns |
| V6 | Lot / parcel | Ownership/development cell | District sequencing |

### C. Movement & linkage (flow)

Trancik’s **linkage** theory: lines that connect parts of the city ([figure-ground / linkage / place](https://en.wikipedia.org/wiki/Urban_morphology)).

| ID | Concept | Meaning | Why |
|---|---|---|---|
| C1 | Circulation graph | Nodes = places; edges = allowable moves | 112, 127; district flow |
| C2 | Centerline | Axis of a street or path with direction | “Which way the street flows” |
| C3 | Hierarchy | Arterial / local / lane / path | Choice and character ([Urban Design Compendium](https://www.ipswich.gov.uk/sites/ipswich/files/m-files/ncd37_-_urban_design_compendium_1_-_urban_design_principles.pdf)) |
| C4 | Mode | Pedestrian, bike, vehicle, shared | Different networks |
| C5 | Approach sequence | Ordered places from far to threshold | Entrance transition; Main Entrance |
| C6 | Choice / connectivity | Alternative routes between A and B | Permeability |
| C7 | Front door / address | Where a building meets the movement network | 110, 112 |
| C8 | Flow direction | Directed or bidirectional edges | One-way sense; approach vs exit |

### D. Interaction between components

| ID | Concept | Meaning | Why |
|---|---|---|---|
| I1 | Adjacency | Share a boundary | Already have wall/door |
| I2 | Interface | Opening or permeable edge between two places | Door/window as relation, not only object |
| I3 | Frontage | Which void a solid faces and for how many metres | Street life; south outdoors |
| I4 | Access | Can move from A to B without leaving the graph | Reachability |
| I5 | Overlook / exposure | Visual relation (window sees court) | Judgment patterns; privacy |
| I6 | Threshold | Thickened transition between domains | 112, 130 |
| I7 | Containment | Zone inside zone | BOT |
| I8 | Shared outdoor | Void that several solids address | Shared green |

### E. Orientation & climate geometry

| ID | Concept | Meaning | Why |
|---|---|---|---|
| O1 | Cardinal / true north | Bearing frame | Already partial |
| O2 | Equator-facing side | Derived from latitude | 105, 128 |
| O3 | Solar access / shade | Which places receive sun when | Light patterns (deeper than binary south) |
| O4 | Prevailing approach direction | From which side people arrive | 110 |

### F. Place roles (semantic tags on space — already started)

| ID | Concept | Meaning | Why |
|---|---|---|---|
| P1 | Role tags | street, outdoor, public, private, living, … | Checks filter centers |
| P2 | Center | Coherent region a pattern acts on | Alexander term; DESIGN §1.2 |
| P3 | Domain boundary | Public / semi-private / private cut | 127 |

### G. Pattern-field relations (language side)

| ID | Concept | Meaning | Why |
|---|---|---|---|
| L1 | Spatial relation in a condition | Predicate over geometry/graph | Computed checks |
| L2 | Diagram schema | How a pattern’s field is drawn (arrow, zone, dim) | Owned symbology consumes this |
| L3 | Structure preservation | Satisfied set not undone | Already `preserving` |

---

## Minimum spatial model (proposed)

Beyond today’s `Topology`, introduce an explicit **SpatialStructure** (name TBD) that the checker and the plan renderer both read:

```text
SpatialStructure
  frame: north + units + optional CRS
  solids[] / voids[]          # figure–ground typed
  places[]                    # zones with metric footprint + roles
  network:                    # C1–C8
    nodes[]  (place or intersection)
    edges[]  (centerline, width, mode, direction, hierarchy)
  measures[]                  # M2–M8 named dimensions
  interfaces[]                # I2–I6 openings as relations
  fields[]                    # optional solar / overlook layers
```

Footprints stay. **Centerlines, widths, directed edges, and named measures** are what make flow and distance first-class.

CityJSON/IFC remain interchange. This structure is our **geometry-aware mid-layer** (sibling to BOT topology, not a replacement for CityGML).

---

## What the UI must show (once concepts exist)

| Concept family | Visual obligation |
|---|---|
| Metric (M*) | Scale bar that matches; dimension strings from `measures[]` |
| Void / solid (V*) | True figure–ground; voids continuous |
| Circulation (C*) | Centerline arrows; hierarchy by line weight; approach path emphasized |
| Interaction (I*) | Interfaces marked; frontage lengths optional |
| Pattern field (L2) | Diagram drawn from schema over the same geometry |

Until `network` and `measures` exist in data, no amount of SVG polish will show “which way the street flows” or “how far.”

---

## Codification order

1. **Freeze this inventory** (this file) — amend as we discover gaps.  
2. **Schema sketch** for `SpatialStructure` / circulation edges / measures (JSON Schema).  
3. **Seed district rebuild** so Main Street has a directed centerline, path widths, and named dimensions (court depth, balcony depth, setbacks).  
4. **Lift checks** that already imply geometry (112, 127, 167, 107) onto the shared structure.  
5. **Renderer** consumes network + measures (arrows, dims) — symbology follows model.  
6. Later: overlook/solar fields; town-scale grain; Space Syntax–class metrics only if needed.

---

## Non-goals (for now)

- Full physics / CFD  
- Photoreal digital twins  
- Replacing IFC or CityJSON  
- Marketing pages / Naive dogfood (still deferred)

---

## Relation to owned layers

| Layer | Owns |
|---|---|
| Catalog + Lean | Pattern language laws |
| IFC / CityJSON | Industry interchange geometry |
| **Spatial concepts (this doc)** | Metric relations, circulation, enclosure, interaction |
| `pattern-language.plan-symbology` | How those concepts are drawn |

Symbology without spatial concepts = labeled blob.  
Spatial concepts without symbology = invisible structure.  
We need both; **codify concepts first.**
