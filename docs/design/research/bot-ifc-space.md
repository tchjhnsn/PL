# BOT and IFC space, mapped to places and interfaces

BOT names the containment ladder we already store. IFC is the file that ladder is read from. Three IFC words that look like “zone” are different objects, and only one of them is `bot:Zone`.

Sources: [Building Topology Ontology](https://w3c-lbd-cg.github.io/bot/), [IfcRelSpaceBoundary](https://standards.buildingsmart.org/IFC/RELEASE/IFC4/FINAL/HTML/schema/ifcproductextension/lexical/ifcrelspaceboundary.htm), [IfcZone](https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/schema/ifcproductextension/lexical/ifczone.htm), [IfcSpatialZone](https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/schema/ifcproductextension/lexical/ifcspatialzone.htm), [IfcExternalSpatialElement](https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/schema/ifcproductextension/lexical/ifcexternalspatialelement.htm), [IfcRelVoidsElement](https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/schema/ifcproductextension/lexical/ifcrelvoidselement.htm).

## BOT classes and properties

`bot:Zone` is anything with a location and a 3D extent. `bot:Site`, `bot:Building`, `bot:Storey`, and `bot:Space` are subclasses. A zone may contain zones, sit adjacent to zones, or intersect zones. It is disjoint from `bot:Element` and `bot:Interface`. [BOT Zone](https://w3c-lbd-cg.github.io/bot/)

| Property | OWL facts | Graph id |
|---|---|---|
| `bot:containsZone` | transitive; domain and range `bot:Zone` | `T.contains` |
| `bot:hasBuilding` | subproperty; range `bot:Building` | `T.has_building` |
| `bot:hasStorey` | subproperty; range `bot:Storey` | `T.has_storey` |
| `bot:hasSpace` | subproperty; range `bot:Space` | `T.has_space` |
| `bot:adjacentZone` | symmetric; zones share an interface and do not intersect | `T.adjacent` |
| `bot:intersectsZone` | symmetric; disjoint from adjacent. The spec’s example is a stairwell through storeys | `T.intersects` |
| `bot:hasElement` | superproperty; inferred from the three below | `T.has_element` |
| `bot:containsElement` | element inside the zone | `T.contains_element` |
| `bot:adjacentElement` | element bounding the zone | `T.adjacent_element` |
| `bot:intersectingElement` | element crossing the zone | `T.intersecting_element` |
| `bot:hasSubElement` | element hosts an element (a wall hosts a window) | `T.has_subelement` |
| `bot:Interface` | qualifies a relationship. The spec’s examples include a heat-transfer surface, a joint, and a door | `T.interface` |
| `bot:interfaceOf` | from the interface to a zone, an element, or another thing | `T.interface_of` |

`bot:has3DModel` and `bot:hasSimple3DModel` point at geometry. `bot:hasZeroPoint` points a site at a WGS84 point. BOT does not define metres, frontage, or a street graph. [BOT 3D model](https://w3c-lbd-cg.github.io/bot/)

## IFC classes that share the words

The aggregation tree is `IfcProject` → `IfcSite` → `IfcBuilding` → `IfcBuildingStorey` → `IfcSpace`, linked by `IfcRelAggregates`. That is `bot:containsZone`. Elements sit in a storey by `IfcRelContainedInSpatialStructure`, which is `bot:containsElement`, not containment of a zone.

| IFC | Definition we are using | Graph id |
|---|---|---|
| `IfcSpace` | A spatial structure element. `InteriorOrExteriorSpace` is internal or external | `T.space` |
| `IfcZone` | A group of spaces, partial spaces, or zones via `IfcRelAssignsToGroup`. One space may belong to many zones. An `IfcZone` has no shape of its own. IFC4 subtypes it from `IfcSystem` | `T.ifc_zone` |
| `IfcSpatialZone` | IFC4. A non-hierarchical, possibly overlapping decomposition (thermal, lighting, construction) that may have its own placement and shape. Related by `IfcRelReferencedInSpatialStructure` | `T.spatial_zone` |
| `IfcExternalSpatialElement` | IFC4. An external region at the site, logical (air around the building) or physical (ground against the envelope). `PredefinedType` plus `BoundedBy` → `IfcRelSpaceBoundary` | `T.external_space` |
| `IfcRelSpaceBoundary` | Space-to-element delimiter, seen from the space. `PhysicalOrVirtualBoundary`, `InternalOrExternalBoundary`, optional `ConnectionGeometry`. 1st level ignores changes of element; 2nd level splits them. Virtual boundaries point at `IfcVirtualElement` | `T.space_boundary`, `T.virtual_boundary` |
| `IfcOpeningElement` | A subtraction feature | `T.opening_element` |
| `IfcRelVoidsElement` | One-to-one: opening voids an element | `T.voids_element` |
| `IfcRelFillsElement` | Door or window fills that opening | `T.fills_element` |
| `Qto_SpaceBaseQuantities` | Net and gross floor area, height, finish ceiling height | `T.quantity` |

`IfcZone` is a group. `bot:Zone` is the containment supertype. `IfcSpatialZone` is a shaped, overlapping region. The graph keeps `T.zone`, `T.ifc_zone`, and `T.spatial_zone` as siblings so a loader cannot collapse them.

## Map onto SpatialStructure

`topology.py` already stores BOT kinds: `Zone.kind` is Site, Building, Storey, or Space. `Adjacency.kind` is `wall` or `door`. `Opening.kind` is `window` or `door`, with a cardinal `orientation`.

| Product field | BOT / IFC | Gap |
|---|---|---|
| `places[]` with `parent` | `bot:containsZone` / `IfcRelAggregates` | One parent. `bot:intersectsZone` and `IfcSpatialZone` need a space in more than one storey |
| `places[].kind` `room` | `IfcSpace` internal | — |
| `places[].kind` `void` | `IfcExternalSpatialElement`, or an external `IfcSpace` | The schema has no external-element type. `T.external_space` maps to a place and to `V2.ground` |
| `places[].kind` `solid` | `bot:Element` mass, not a zone | Figure, not a BOT zone |
| `places[].kind` `path` | no BOT or IFC class | CityGML road, not an `IfcSpace` |
| `places[].roles` | no BOT property. Loose match: `IfcZone.ObjectType`, space long name | Pattern tags (`P1.tags`) |
| `places[].height_m` | `Qto_SpaceBaseQuantities.Height` / finish ceiling height | `T.quantity` maps to `M8.measure` |
| `walls[]` | `IfcWall`, `bot:Element` | — |
| `openings[]` | `IfcDoor` / `IfcWindow` filling an `IfcOpeningElement` | We store the filler. The voiding relationship is `T.voids_element` |
| `openings[].swing` | drawing convention | IFC door operation types are a different enum |
| `openings[].facing` | derived from placement | IFC has no cardinal field |
| `interfaces[]` `door` / `window` | `bot:Interface` whose `interfaceOf` includes the two zones and the filler | `between` is two ids |
| `interfaces[]` `threshold` / `frontage` / `overlook` | no IFC entity | Ours. Frontage maps to `I13.ss_interface` |
| `network` | none in BOT or the IFC spatial structure | District movement is the CityGML note |
| `measures[]` | quantity sets, when present | Named spans (`setback`, `frontage`) are not IFC base quantities |

A physical `IfcRelSpaceBoundary` is our wall adjacency. A virtual one is `T.virtual_boundary`. A 2nd-level boundary that stops at an opening is the piece of wall beside a door, which we do not store; we store the opening.

## Gaps

- `places[].parent` is a tree. A stair that intersects several storeys (`bot:intersectsZone`) does not fit.
- `IfcZone` membership is many-to-many and has no geometry. Loading it as `parent` would invent a container.
- `IfcSpatialZone` may overlap and may carry its own footprint. We have no overlapping place.
- External air and external ground are one `IfcExternalSpatialElement` idea. Our voids are rings with roles.
- `Adjacency.kind` is `wall` or `door`. IFC also distinguishes physical/virtual and internal/external, and 1st-level vs 2nd-level boundaries.
- The host chain wall → `IfcRelVoidsElement` → opening → `IfcRelFillsElement` → door is flattened to an opening record. `T.has_subelement` is the BOT form of “wall hosts window.”
- Interface kinds `threshold`, `frontage`, and `overlook` have no BOT or IFC class. `bot:Interface` can qualify them later; it does not define them.
- Space quantities are not read into `measures[]`.
- `bot:hasZeroPoint` is a site pin. Our frame stores `origin_lon` / `origin_lat` and a project north. They are the same job only after we pick one geodetic point.

## Siblings added from this pass

`T.has_element`, `T.has_subelement`, `T.intersecting_element`, `T.space_boundary`, `T.virtual_boundary`, `T.external_space`, `T.ifc_zone`, `T.spatial_zone`, `T.opening_element`, `T.voids_element`, `T.fills_element`, `T.quantity`.

## Sources

- [Building Topology Ontology](https://w3c-lbd-cg.github.io/bot/)
- [BOT tutorial](https://w3c-lbd-cg.github.io/bot/tutorial/)
- [IfcRelSpaceBoundary (IFC4)](https://standards.buildingsmart.org/IFC/RELEASE/IFC4/FINAL/HTML/schema/ifcproductextension/lexical/ifcrelspaceboundary.htm)
- [IfcZone (IFC4 ADD2 TC1)](https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/schema/ifcproductextension/lexical/ifczone.htm)
- [IfcSpatialZone (IFC4 ADD2 TC1)](https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/schema/ifcproductextension/lexical/ifcspatialzone.htm)
- [IfcExternalSpatialElement (IFC4 ADD2 TC1)](https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/schema/ifcproductextension/lexical/ifcexternalspatialelement.htm)
- [IfcRelVoidsElement (IFC4 ADD2 TC1)](https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/schema/ifcproductextension/lexical/ifcrelvoidselement.htm)
