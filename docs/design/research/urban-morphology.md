# Urban morphology siblings of the spatial graph

Figure-ground, plot series, street hierarchy, enclosure, frontage, and permeability are already named in the inventory. The literature splits several of them into pairs our single nodes were collapsing. This note records the pairs and the graph ids that now hold them.

Pattern numbers below are catalog ids only.

## Figure and ground

A figure-ground drawing paints built mass and unbuilt void. Our `V1.figure` and `V2.ground` are that pair, and `V9.poché` is the solid fill the plan renderer uses (`symbology.figure_ground`).

Nolli’s 1748 map of Rome counts publicly accessible interior as void and private mass as figure. Our renderer paints building footprints as solid. Public rooms stay rooms. That second reading is `V14.nolli`, which specializes ground and depends on the public/private cut (`P3.domain`).

`V2.convex` is the convex outdoor void. 106 Positive Outdoor Space already depends on enclosure, ground, and this convexity check.

Trancik’s linkage is the circulation graph (`C1.graph`). His place is `P2.center`.

## Conzen’s form complexes

Conzen splits urban form into three complexes. The town plan (ground plan) is streets, plots, and the block-plans of buildings. Building fabric is the three-dimensional form. Land and building utilization changes fastest. Whitehand’s account of the Ludlow regions treats the ground plan as the part that fixes the larger units. [Whitehand, Urban Morphology 13(1)](https://journal.urbanform.org/index.php/jum/article/download/3945/3261/11563), [Whitehand, Conzenian urban morphology](http://spacesyntaxistanbul.itu.edu.tr/papers/invitedpapers/Jeremy_whitehand.pdf)

| Complex | Graph |
|---|---|
| Town plan: streets + plots + block-plans | `V6.town_plan`, `U.road`, `V6.parcel` |
| Plot series: plots in a row on one street, readable by width | `V6.plot_series`, `M14.frontage_grain`, `I3.frontage_rhythm` |
| Building fabric | `V6.building_fabric` (depends on figure and height) |
| Land utilization | `U.landuse` |
| Morphological region / plan unit | `V6.plan_unit` |
| Morphotope, the smallest ensemble | `V6.morphotope`, child of the plan unit |
| Fringe belt: larger plots, fewer crossings, formed against a fixation line | `V6.fringe_belt`, `V6.fixation_line` |

Whitehand, citing Conzen, describes a nested ladder: the old town, quarters fixed by the ground plan, street units and precincts, then morphotopes. `P6.district` maps to `V6.plan_unit`. [Whitehand 2009](https://journal.urbanform.org/index.php/jum/article/download/3945/3261/11563)

The burgage cycle (infill of a plot, then clearance) is a process through time. The spatial model has no time index for it, so it stays out of the graph. Plot width as a measured series is in; the historical cycle is not.

## Street hierarchy and the block

Our edge `hierarchy` is `arterial`, `local`, `lane`, `path`, or `approach` (`C3.hierarchy`). That is a design classification stored on the edge. It is not CityGML’s function code and not a count of driving lanes (`C20.lane`).

A block face is one side of a block between two junctions: the place where frontage, street wall, and intersection meet. The inventory asked for it. It is `V6.block_face`.

Three lines are easy to merge and should stay apart:

| Line | Id | Measure |
|---|---|---|
| Curb | `C13.curb` | — |
| Building line | `V12.building_line` | — |
| Distance between them | `M6.setback` | `kind: setback` |
| Street wall as a continuous vertical edge | `V4.street_wall` | breaks are `V3.edge_continuity` and `V8.dead_space` |

The street cross-section (`V13.cross_section`) is the sum of sidewalk, verge (`U.aux_area`), and carriageway. Enclosure uses that width. A single edge `width_m` is one strip, not the section.

## Enclosure as H:W and as D/H

`M5.hw_ratio` is height divided by street width. `places[].enclosure_hw` can store it. Ashihara’s townscape ratio is distance/height, the inverse. `M15.dh_ratio` is that reading and depends on the cross-section so the two numbers are not stored as if they were the same.

A review that follows Carmona treats height/width of about 1:1 as the strong enclosure, ratios under 1:2 as weakly enclosed, and 4:1 as the point where the section closes too hard. [Enclosure ratio and skyline](https://iconarp.ktun.edu.tr/index.php/iconarp/article/download/630/309) Those bands are perception summaries, not checks.

Ewing and Handy treat enclosure as street-wall continuity plus the amount of sky, not as a single ratio. [Same review, citing Ewing & Handy 2009](https://iconarp.ktun.edu.tr/index.php/iconarp/article/download/630/309) Sky fraction is `M16.sky_view`. `V3.enclosure` depends on it. We do not compute it.

## Frontage

`I3.frontage` is the length of solid facing a void (`M9.length_along`, measure `kind: frontage`). The siblings:

| Idea | Id |
|---|---|
| Doors and windows on that length | `I3.active_frontage` |
| The same length with neither | `I3.blank_frontage` |
| The street the parcel addresses | `I3.primary_frontage` |
| Repeated plot widths along the series | `I3.frontage_rhythm` |
| Open length / frontage length | `M17.active_frontage_ratio` |
| Plots per 100 m | `M14.frontage_grain` |

105 South Facing Outdoors depends on frontage onto an outdoor void. The active/blank split is what a street-wall check would still need.

## Permeability

Bentley’s permeability is the availability of routes through a place, with a visual twin: you can pass, or you can see. The graph keeps that split as `V11.permeability_phys` and `V11.permeability_vis`. Physical permeability depends on the graph. Visual permeability depends on frontage and overlook.

Space Syntax splits the same family again:

| Measure | Meaning | Id |
|---|---|---|
| Connectivity | How many lines a line touches | `C6.connectivity` |
| Integration | Closeness, to-movement | `C6.integration` |
| Choice | Betweenness, through-movement | `C6.choice` |
| Axial line | Longest straight line of sight and access | `C19.axial`, sibling of `C2.centerline` |
| Convex space | A void in which every point sees every other | `V2.convex` |
| Isovist | The field visible from a point | `I5.isovist` |

`C6.choice` used to stand for all of this. It is now the betweenness sibling only. Integration stays a placeholder until a check needs it. `C2.centerline` is a drawn axis with a width. An axial line is a syntactic object. They stay siblings so a loader does not copy one onto the other.

Cullen’s serial vision is the sequence of views along a walk. `C5.serial_vision` depends on the centerline and the isovist. `C5.approach` is the ordered places up to a door (112 Entrance Transition, 110 Main Entrance). One is visual, one is the entrance sequence.

Lynch’s path is the circulation edge. His edge is close to `V4.street_wall`. District is `P6.district`. Landmark is `P5.landmark` (a placeholder). The imageable node is not the same object as a traffic intersection (`U.intersection`).

## What we still do not store

- A time series, so the burgage cycle and fringe-belt growth stay as names (`V6.fringe_belt` is a placeholder).
- Sky view as a number. The place field is `enclosure_hw` only.
- Active-frontage ratio. Measure kinds are depth, width, setback, spacing, frontage, height, clearance.
- Block face as a place. It is a concept (`V6.block_face`) with no schema object.
- Integration and axial lines. Named, not computed.
- A Nolli switch on the renderer. `V14.nolli` records the reading; the poché pass still paints private mass.

## Siblings added from this pass

`M15.dh_ratio`, `M16.sky_view`, `M17.active_frontage_ratio`, `V2.convex`, `V6.block_face`, `V6.plan_unit`, `V6.morphotope`, `V6.fringe_belt`, `V6.fixation_line`, `V6.building_fabric`, `V12.building_line`, `V13.cross_section`, `V14.nolli`, `C6.connectivity`, `C6.integration`, `C19.axial`, `C5.serial_vision`, `I3.blank_frontage`, `I3.primary_frontage`, `I3.frontage_rhythm`, `P5.landmark`, `P6.district`.

## Sources

- [Whitehand, “The structure of urban landscapes,” Urban Morphology 13(1)](https://journal.urbanform.org/index.php/jum/article/download/3945/3261/11563)
- [Whitehand, Conzenian urban morphology and urban landscapes](http://spacesyntaxistanbul.itu.edu.tr/papers/invitedpapers/Jeremy_whitehand.pdf)
- [Diniz and Serra, morphological regions in GIS](https://strathprints.strath.ac.uk/80497/1/Diniz_Serra_ISUF_2021_Towards_a_quantitative_approach_to_morphological.pdf)
- [Enclosure ratio and skyline complexity](https://iconarp.ktun.edu.tr/index.php/iconarp/article/download/630/309)
