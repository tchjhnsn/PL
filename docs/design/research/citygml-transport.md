# CityGML 3.0 Transportation and our network edges

CityGML 3.0 transportation is a space model with an optional linear network. Our `SpatialStructure.network` is the linear reading: nodes and directed edges with one mode, one hierarchy, and one width. Carriageway and sidewalk are separate edges. In CityGML they are surfaces inside one road section, and the movement graph hangs off `TrafficSpace`, not off the section.

Sources: [CityGML 3.0 transportation schema](https://opengeospatial.github.io/CityGML-3.0Encodings/xsd-doc/3.0/transportation/), [TUM road2citygml3](https://tum-gis.github.io/road2citygml3/guideline/guideline.html), [CityJSON Community Standard](https://docs.ogc.org/cs/20-072r5/20-072r5.html), [PLATEAU road LoD table](https://www.mlit.go.jp/plateaudocument02/tocD/tocD_02/tocD_02_01/).

## Classes and properties

`AbstractTransportationSpace` is the CityGML 3 superclass of `Road`, `Track`, `Railway`, `Waterway`, and `Square`. Each may carry `trafficDirection`, `occupancy`, `trafficSpace`, `auxiliaryTrafficSpace`, `hole`, and `marking`. `Road`, `Railway`, `Track`, and `Waterway` also decompose into `section` and `intersection`. [Schema](https://opengeospatial.github.io/CityGML-3.0Encodings/xsd-doc/3.0/transportation/)

| Class | What it is | Graph id |
|---|---|---|
| `AbstractTransportationSpace` | Superclass; network geometry and surface geometry may both be stored | `U.abstract_space` |
| `TransportationComplex` | CityGML 2 name for that parent | `U.complex` maps to `U.abstract_space` |
| `Road`, `Square`, `Track`, `Railway`, `Waterway` | Named transportation spaces | `U.road`, `U.square`, `U.track`, `U.railway`, `U.waterway` |
| `Section` | A segment of a road, railway, track, or waterway | `U.section` |
| `Intersection` | A shared segment of two or more of those objects | `U.intersection` |
| `TrafficSpace` | Volume in which traffic moves. Subclass of `AbstractUnoccupiedSpace` | `U.traffic_space` |
| `AuxiliaryTrafficSpace` | Volume inside the transportation space that is not for traffic | `U.aux_space` |
| `TrafficArea` | Ground surface of a `TrafficSpace`. Thematic surface | `U.traffic_area` |
| `AuxiliaryTrafficArea` | Ground of an auxiliary space: kerb, median, verge | `U.aux_area` |
| `ClearanceSpace` | Free volume above a traffic area | `U.clearance` |
| `Marking` | Visible pattern that structures or restricts traffic | `U.marking` |
| `Hole` | Opening in the surface (manhole, damage) | `U.hole` |

Properties that matter for edges:

- `TrafficSpace.granularity` is required. The XSD enum is `lane` or `way` only. [GranularityValueType](https://opengeospatial.github.io/CityGML-3.0Encodings/xsd-doc/3.0/transportation/)
- The TUM guideline adds a third modelling level, `area`: one object for the whole width of a section or intersection. That word is not in the XSD enum. [road2citygml3, three levels](https://tum-gis.github.io/road2citygml3/guideline/guideline.html)
- `way` is one object per surface function (one carriageway, one sidewalk, one cycle path). `lane` is one object per driving lane.
- `trafficDirection` on the space is `forwards`, `backwards`, or `both`. [TrafficDirectionValueType](https://opengeospatial.github.io/CityGML-3.0Encodings/xsd-doc/3.0/transportation/)
- `predecessor` and `successor` are references on `TrafficSpace`, not on `Section`. [TrafficSpace](https://opengeospatial.github.io/CityGML-3.0Encodings/xsd-doc/3.0/transportation/)
- `TrafficArea.function`, `usage`, `class`, and `surfaceMaterial` are codelists. TUM’s recommended functions include `driving_lane`, `footpath`, `cyclepath`, and `crosswalk`. A crossing may carry more than one function. [road2citygml3, Table 2](https://tum-gis.github.io/road2citygml3/guideline/guideline.html)
- `ClearanceSpace` is the free space above a traffic area. The same guideline cites 4.5 m over driving lanes and 2.5 m over sidewalks as a German example, not as our rule.

CityGML 3 stores LoD on geometries, and a feature may hold several LoDs at once. LoD is no longer the switch for semantic depth; granularity is. [road2citygml3, Levels of Detail](https://tum-gis.github.io/road2citygml3/guideline/guideline.html)

CityJSON keeps four transportation city objects: `Road`, `Railway`, `Waterway`, `TransportSquare`. It drops `Section`, `Intersection`, and `Track` as types and expects attributes plus parent/child (`class: "section"`). `TrafficArea`, `AuxiliaryTrafficArea`, `TransportationMarking`, and `TransportationHole` are semantic surfaces on a `MultiSurface` or `CompositeSurface`. The geometry `lod` string may be `"2"` or a refined `"2.2"`. [CityJSON §8.12](https://docs.ogc.org/cs/20-072r5/20-072r5.html)

PLATEAU’s road profile is stricter than CityGML 3: LoD0 is a network line (`lod0Network`), LoD1 is an undifferentiated road surface, and `TrafficArea` / `AuxiliaryTrafficArea` start at LoD2. [PLATEAU D.2.1](https://www.mlit.go.jp/plateaudocument02/tocD/tocD_02/tocD_02_01/)

## Map onto SpatialStructure

| CityGML | `places` | `network` | `measures` | `interfaces` |
|---|---|---|---|---|
| `Road` / `Square` footprint | place `kind: path` or `void` | — | — | — |
| LoD0 centerline, granularity `area` | the street place | one edge, `polyline` | `width_m` if known | — |
| `TrafficArea` function `footpath`, granularity `way` | sidewalk ring, still missing as its own place | `C9.sidewalk`, `mode: pedestrian` | edge `width_m`; measure `kind: width` | — |
| `TrafficArea` function `driving_lane`, granularity `way` | carriageway ring, same gap | `C10.carriageway`, `mode: vehicle` | `width_m` | — |
| granularity `lane` | — | `C20.lane` specializes the carriageway | per-lane width | — |
| `cyclepath` | — | `C14.bike_lane` | `width_m` | — |
| `crosswalk` (often two functions) | — | `C11.crossing`; node `kind: crossing` | — | — |
| `Intersection` | — | node `kind: intersection` | — | — |
| `predecessor` / `successor` | — | edge endpoints `a`/`b`. A split is several edges on one node | — | — |
| `trafficDirection: both` | — | `directed: false` (`C8.direction`) | — | — |
| `forwards` or `backwards` | — | `directed: true`. The boolean does not store which way | — | — |
| `AuxiliaryTrafficArea` | verge / median place, not in the schema’s place kinds | not an edge | `kind: spacing` when it is a gap | — |
| `ClearanceSpace` | — | — | measure `kind: clearance` (`U.clearance` maps to `M8.measure`) | — |
| `class` / `function` as arterial | — | `hierarchy` is ours (`arterial`, `local`, `lane`, `path`, `approach`), not a CityGML code | — | — |
| `Marking`, `Hole` | — | — | — | — |

`edge.hierarchy` and `edge.mode` are the product fields. CityGML’s function codelist is `U.traffic_function`. Sidewalk, carriageway, crossing, and bike lane depend on it. Our carriageway edge is granularity `way` (`U.granularity_way`). Lane-level geometry is `U.granularity_lane` and `C20.lane`.

## Gaps

- No place kind for a sidewalk polygon distinct from the street void. Edges carry the split; surfaces do not.
- `directed` is a boolean. CityGML’s `forwards` / `backwards` / `both` is an enum.
- One `mode` per edge. A CityGML crossing may list `driving_lane` and `footpath` on the same surface.
- No lane edges in the schema enum. `hierarchy: lane` means a minor street, not a driving lane.
- Auxiliary surfaces (kerb, median, verge) have no place and no interface.
- `ClearanceSpace` is a volume. The measure kind `clearance` is a length.
- `Marking` and `Hole` are named and out of the product schema.
- CityJSON will not round-trip `Section` and `Intersection` as types. We would encode them as attributes on `Road` children.
- PLATEAU shows `TrafficArea` at LoD2 (`C18.lod2`). CityGML 3 allows that decomposition at any LoD. A converter must not assume LoD2 means “has sidewalks.”
- `U.bridge` and `U.tunnel` are separate CityGML modules. They stay placeholders.

## Siblings added from this pass

`U.abstract_space`, `U.granularity_way`, `U.granularity_lane`, `U.granularity_area`, `U.traffic_function`, `U.marking`, `U.hole`, `C18.lod2`, `C20.lane`.

## Sources

- [CityGML 3.0 transportation schema documentation](https://opengeospatial.github.io/CityGML-3.0Encodings/xsd-doc/3.0/transportation/)
- [road2citygml3 guideline](https://tum-gis.github.io/road2citygml3/guideline/guideline.html)
- [OGC CityJSON Community Standard](https://docs.ogc.org/cs/20-072r5/20-072r5.html)
- [PLATEAU D.2.1 road feature types and LoD](https://www.mlit.go.jp/plateaudocument02/tocD/tocD_02/tocD_02_01/)
