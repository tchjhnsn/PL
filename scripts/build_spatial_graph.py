#!/usr/bin/env python3
"""Emit the exhaustive spatial-concept knowledge graph."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "design" / "spatial-concept-graph.json"

# node: id, name, kind, layer, status (have|partial|todo|placeholder), sources[]
# edge: from, to, rel in depends_on | parent_of | sibling_of | maps_to | specializes | renders_as

NODES: list[dict] = []
EDGES: list[dict] = []


def N(id: str, name: str, kind: str, layer: str, status: str, sources: list[str], note: str = "") -> None:
    NODES.append(
        {
            "id": id,
            "name": name,
            "kind": kind,
            "layer": layer,
            "status": status,
            "sources": sources,
            "note": note,
        }
    )


def E(frm: str, to: str, rel: str) -> None:
    EDGES.append({"from": frm, "to": to, "rel": rel})


def siblings(*ids: str) -> None:
    for i, a in enumerate(ids):
        for b in ids[i + 1 :]:
            E(a, b, "sibling_of")
            E(b, a, "sibling_of")


def main() -> int:
    # —— Foundations (primitives everything depends on) ——
    N("prim.point", "Point", "primitive", "foundation", "have", ["ISO 19107", "internal"], "2D/3D location")
    N("prim.segment", "Segment", "primitive", "foundation", "have", ["ISO 19107"], "Edge between two points")
    N("prim.ring", "Ring / Polygon", "primitive", "foundation", "have", ["ISO 19107", "topology.py"], "Closed footprint")
    N("prim.curve", "Curve / Polyline", "primitive", "foundation", "have", ["ISO 19107", "CityGML LoD0", "plan-model network"], "Centerlines")
    N("prim.frame", "Coordinate frame", "primitive", "foundation", "have", ["EPSG", "plan-model"], "North + units + optional CRS")
    N("prim.north", "True / project north", "primitive", "foundation", "have", ["topology north"], "")
    N("prim.metre", "Metric measure", "primitive", "foundation", "have", ["SI"], "Length unit")
    N("prim.angle", "Bearing / angle", "primitive", "foundation", "have", ["cardinal", "wall_angle"], "")
    N("prim.time", "Time / season", "primitive", "foundation", "placeholder", ["climate"], "For solar schedules later")

    E("prim.segment", "prim.point", "depends_on")
    E("prim.ring", "prim.segment", "depends_on")
    E("prim.curve", "prim.point", "depends_on")
    E("prim.frame", "prim.north", "depends_on")
    E("prim.frame", "prim.metre", "depends_on")
    siblings("prim.point", "prim.segment", "prim.ring", "prim.curve")

    # —— Metric space ——
    N("M1.frame", "Spatial frame", "metric", "metric", "partial", ["plan-model"], "Alias of prim.frame in product")
    N("M2.distance", "Distance", "metric", "metric", "have", ["plan-model measures"], "Between points/edges/fronts")
    N("M3.area", "Area", "metric", "metric", "todo", [], "m² of places/voids")
    N("M4.clear_width", "Clear width / depth", "metric", "metric", "have", ["167", "107", "measures"], "Usable span")
    N("M5.height", "Height / section", "metric", "metric", "have", ["Zone.height_m", "190"], "")
    N("M5.hw_ratio", "Height-to-width ratio", "metric", "metric", "partial", ["enclosure lit.", "places.enclosure_hw"], "Street section")
    N("M6.setback", "Setback", "metric", "metric", "todo", ["site plans"], "Face to ROW/lot line")
    N("M7.spacing", "Spacing / gap", "metric", "metric", "have", ["m-gap-ab"], "Between solids")
    N("M8.measure", "Named measure", "metric", "metric", "have", ["plan-model measures", "schema"], "First-class dimension record")
    N("M9.length_along", "Length along curve", "metric", "metric", "partial", ["centerline", "frontage"], "Stationing")
    N("M10.offset", "Offset / buffer", "metric", "metric", "todo", ["sidewalk from curb"], "")
    N("M11.coverage", "Building coverage ratio", "metric", "metric", "todo", ["Morpho", "FSI sibling"], "Footprint / parcel")
    N("M12.fsi", "Floor space index", "metric", "metric", "todo", ["Morpho"], "GFA / parcel")
    N("M13.plot_density", "Plot density", "metric", "metric", "todo", ["Morpho plots/block"], "")
    N("M14.frontage_grain", "Frontage grain", "metric", "metric", "todo", ["plots per 100m"], "")
    N("M15.dh_ratio", "Distance-to-height ratio", "metric", "metric", "todo", ["Ashihara D/H"], "Inverse reading of H:W")
    N("M16.sky_view", "Sky view", "metric", "metric", "todo", ["Ewing enclosure"], "Sky fraction in a street section")
    N("M17.active_frontage_ratio", "Active frontage ratio", "metric", "metric", "todo", ["active frontage"], "Open length / frontage length")

    for m in [
        "M2.distance",
        "M3.area",
        "M4.clear_width",
        "M5.height",
        "M6.setback",
        "M7.spacing",
        "M8.measure",
        "M9.length_along",
        "M10.offset",
        "M11.coverage",
        "M12.fsi",
        "M13.plot_density",
        "M14.frontage_grain",
    ]:
        E(m, "prim.metre", "depends_on")
        E(m, "prim.frame", "depends_on")
    E("M5.hw_ratio", "M5.height", "depends_on")
    E("M5.hw_ratio", "M4.clear_width", "depends_on")
    E("M6.setback", "M2.distance", "depends_on")
    E("M7.spacing", "M2.distance", "depends_on")
    E("M8.measure", "M2.distance", "specializes")
    E("M11.coverage", "M3.area", "depends_on")
    E("M11.coverage", "V6.parcel", "depends_on")
    E("M12.fsi", "M11.coverage", "sibling_of")
    E("M11.coverage", "M12.fsi", "sibling_of")
    E("M13.plot_density", "V6.block", "depends_on")
    E("M13.plot_density", "V6.parcel", "depends_on")
    E("M14.frontage_grain", "I3.frontage", "depends_on")
    E("M14.frontage_grain", "V5.grain", "depends_on")
    E("M15.dh_ratio", "M5.height", "depends_on")
    E("M15.dh_ratio", "M2.distance", "depends_on")
    E("M15.dh_ratio", "V13.cross_section", "depends_on")
    E("M15.dh_ratio", "M5.hw_ratio", "sibling_of")
    E("M5.hw_ratio", "M15.dh_ratio", "sibling_of")
    E("M16.sky_view", "M5.height", "depends_on")
    E("M16.sky_view", "V13.cross_section", "depends_on")
    E("V3.enclosure", "M16.sky_view", "depends_on")
    E("M17.active_frontage_ratio", "I3.active_frontage", "depends_on")
    E("M17.active_frontage_ratio", "M9.length_along", "depends_on")
    E("M1.frame", "prim.frame", "maps_to")
    siblings("M2.distance", "M3.area", "M4.clear_width", "M5.height", "M6.setback", "M7.spacing")
    siblings("M11.coverage", "M12.fsi", "M13.plot_density", "M14.frontage_grain")

    # —— Morphology solid/void ——
    N("V1.figure", "Figure (solid mass)", "morphology", "morphology", "partial", ["Nolli", "figure-ground"], "Buildings as solid")
    N("V2.ground", "Ground (void)", "morphology", "morphology", "partial", ["Nolli"], "Streets, courts, parks")
    N("V3.enclosure", "Enclosure", "morphology", "morphology", "partial", ["Alexander positive outdoor", "Ewing", "places"], "Outdoor room definition")
    N("V3.edge_continuity", "Edge continuity", "morphology", "morphology", "todo", ["street wall", "Morpho alignment"], "Breaks = dead space")
    N("V4.street_wall", "Street wall / frontage wall", "morphology", "morphology", "todo", ["urban design"], "")
    N("V5.grain", "Urban grain", "morphology", "morphology", "todo", ["UDC", "Conzen"], "Plot/block fineness")
    N("V6.parcel", "Lot / parcel", "morphology", "morphology", "todo", ["LandInfra", "cadastre", "Conzen"], "")
    N("V6.block", "Block", "morphology", "morphology", "todo", ["UDC grid", "Morpho"], "Assembly of parcels")
    N("V6.plot_series", "Plot series", "morphology", "morphology", "todo", ["Conzen town plan"], "Plots along one street frontage")
    N("V6.town_plan", "Town plan", "morphology", "morphology", "todo", ["Conzen"], "Ground plan: streets, plots, building block-plans")
    N("V7.soft_edge", "Soft edge", "morphology", "morphology", "todo", ["Alexander"], "Porous building edge")
    N("V8.dead_space", "Dead space", "morphology", "morphology", "todo", ["Ewing"], "Inactive setback/gap")
    N("V9.poché", "Poché", "morphology", "morphology", "partial", ["Beaux-Arts", "figure-ground", "mass-fill"], "Graphic solid fill")
    N("V10.alignment", "Building alignment", "morphology", "morphology", "todo", ["Morpho"], "Face to street consistency")
    N("V11.permeability_vis", "Visual permeability", "morphology", "morphology", "todo", ["Bentley"], "See-through at the edge")
    N("V11.permeability_phys", "Physical permeability", "morphology", "morphology", "todo", ["Bentley"], "Alternative routes through the plan")
    N("V2.convex", "Convex space", "morphology", "morphology", "partial", ["Hillier", "106"], "Outdoor convexity already checked")
    N("V6.block_face", "Block face", "morphology", "morphology", "todo", ["street wall"], "One side of a block between junctions")
    N("V6.plan_unit", "Morphological region", "morphology", "morphology", "todo", ["Conzen", "Whitehand"], "Nested plan unit")
    N("V6.morphotope", "Morphotope", "morphology", "morphology", "todo", ["Conzen"], "Smallest form ensemble")
    N("V6.fringe_belt", "Fringe belt", "morphology", "morphology", "placeholder", ["Louis", "Conzen"], "Large plots, fewer crossings")
    N("V6.fixation_line", "Fixation line", "morphology", "morphology", "placeholder", ["Conzen"], "Edge that holds a fringe belt")
    N("V6.building_fabric", "Building fabric", "morphology", "morphology", "todo", ["Conzen"], "3D form complex, beside the ground plan")
    N("V12.building_line", "Building line", "morphology", "morphology", "todo", ["site plans"], "Face line; setback offsets it from the curb")
    N("V13.cross_section", "Street cross-section", "morphology", "morphology", "todo", ["UDC"], "Sidewalk + verge + carriageway")
    N("V14.nolli", "Nolli public void", "morphology", "morphology", "todo", ["Nolli map"], "Public interiors join the ground")

    E("V1.figure", "prim.ring", "depends_on")
    E("V2.ground", "prim.ring", "depends_on")
    E("V3.enclosure", "M5.hw_ratio", "depends_on")
    E("V3.enclosure", "V3.edge_continuity", "depends_on")
    E("V3.enclosure", "V2.ground", "depends_on")
    E("V4.street_wall", "V1.figure", "depends_on")
    E("V4.street_wall", "V3.edge_continuity", "depends_on")
    E("V5.grain", "V6.parcel", "depends_on")
    E("V5.grain", "V6.block", "depends_on")
    E("V6.block", "V6.parcel", "parent_of")
    E("V6.plot_series", "V6.parcel", "depends_on")
    E("V6.plot_series", "U.road", "depends_on")
    E("V6.town_plan", "U.road", "depends_on")
    E("V6.town_plan", "V6.parcel", "depends_on")
    E("V6.town_plan", "V1.figure", "depends_on")
    E("V6.town_plan", "V6.plot_series", "parent_of")
    E("V8.dead_space", "M6.setback", "depends_on")
    E("V8.dead_space", "V3.edge_continuity", "depends_on")
    E("V9.poché", "V1.figure", "renders_as")
    E("V7.soft_edge", "V4.street_wall", "specializes")
    E("V7.soft_edge", "I3.active_frontage", "depends_on")
    E("V10.alignment", "V4.street_wall", "depends_on")
    E("V10.alignment", "V6.parcel", "depends_on")
    E("V11.permeability_vis", "I3.frontage", "depends_on")
    E("V11.permeability_vis", "I5.overlook", "depends_on")
    E("V11.permeability_phys", "C6.connectivity", "depends_on")
    E("V11.permeability_phys", "C6.choice", "depends_on")
    E("V2.convex", "V2.ground", "specializes")
    E("V2.convex", "prim.ring", "depends_on")
    E("V6.block_face", "V6.block", "depends_on")
    E("V6.block_face", "U.intersection", "depends_on")
    E("V6.block_face", "I3.frontage", "depends_on")
    E("V6.plan_unit", "V6.town_plan", "depends_on")
    E("V6.plan_unit", "V6.morphotope", "parent_of")
    E("V6.morphotope", "V1.figure", "depends_on")
    E("V6.fringe_belt", "V6.parcel", "depends_on")
    E("V6.fringe_belt", "V6.fixation_line", "depends_on")
    E("V6.fringe_belt", "V11.permeability_phys", "depends_on")
    E("V6.fixation_line", "U.road", "sibling_of")
    E("U.road", "V6.fixation_line", "sibling_of")
    E("V6.building_fabric", "V1.figure", "depends_on")
    E("V6.building_fabric", "M5.height", "depends_on")
    E("V6.town_plan", "V6.building_fabric", "sibling_of")
    E("V6.building_fabric", "V6.town_plan", "sibling_of")
    E("V6.building_fabric", "U.landuse", "sibling_of")
    E("U.landuse", "V6.building_fabric", "sibling_of")
    E("V12.building_line", "V4.street_wall", "depends_on")
    E("V12.building_line", "M6.setback", "depends_on")
    E("V12.building_line", "C13.curb", "depends_on")
    E("V13.cross_section", "C9.sidewalk", "depends_on")
    E("V13.cross_section", "C10.carriageway", "depends_on")
    E("V13.cross_section", "U.aux_area", "depends_on")
    E("V13.cross_section", "M5.hw_ratio", "depends_on")
    E("V14.nolli", "V2.ground", "specializes")
    E("V14.nolli", "P3.domain", "depends_on")
    siblings("V1.figure", "V2.ground")
    siblings("V6.parcel", "V6.block", "V6.plot_series")
    siblings("V6.plan_unit", "V6.fringe_belt", "V6.block_face")
    siblings("V12.building_line", "C13.curb", "V4.street_wall")
    siblings("V11.permeability_vis", "V11.permeability_phys")
    siblings("V7.soft_edge", "V4.street_wall")

    # —— Topology / BOT / IFC ——
    N("T.site", "Site", "topology", "topology", "have", ["BOT Site", "IfcSite"], "")
    N("T.building", "Building", "topology", "topology", "have", ["BOT Building", "IfcBuilding"], "")
    N("T.storey", "Storey", "topology", "topology", "have", ["BOT Storey", "IfcBuildingStorey"], "")
    N("T.space", "Space", "topology", "topology", "have", ["BOT Space", "IfcSpace"], "")
    N("T.zone", "Zone", "topology", "topology", "have", ["BOT Zone"], "Supertype")
    N("T.element", "Element", "topology", "topology", "partial", ["BOT Element", "IfcElement"], "Walls etc.")
    N("T.contains", "Containment", "topology", "topology", "have", ["bot:containsZone"], "")
    N("T.adjacent", "Adjacency", "topology", "topology", "have", ["Adjacency", "bot:adjacentZone"], "")
    N("T.boundary", "Boundary segment", "topology", "topology", "have", ["Boundary"], "")
    N("T.interface", "Interface", "topology", "topology", "have", ["bot:Interface", "plan-model interfaces"], "Shared face / opening")
    N("T.opening.door", "Door", "topology", "topology", "have", ["IfcDoor", "Opening"], "")
    N("T.opening.window", "Window", "topology", "topology", "have", ["IfcWindow", "Opening"], "")
    N("T.facing", "Cardinal facing", "topology", "topology", "have", ["Opening.orientation"], "")
    N("T.intersects", "Intersection of zones", "topology", "topology", "todo", ["bot:intersectsZone"], "Stairwell across storeys")
    N("T.has_building", "hasBuilding", "topology", "topology", "have", ["bot:hasBuilding"], "⊑ containsZone")
    N("T.has_storey", "hasStorey", "topology", "topology", "have", ["bot:hasStorey"], "⊑ containsZone")
    N("T.has_space", "hasSpace", "topology", "topology", "have", ["bot:hasSpace"], "⊑ containsZone")
    N("T.adjacent_element", "adjacentElement", "topology", "topology", "partial", ["bot:adjacentElement"], "Zone↔Element")
    N("T.contains_element", "containsElement", "topology", "topology", "todo", ["bot:containsElement"], "")
    N("T.interface_of", "interfaceOf", "topology", "topology", "partial", ["bot:interfaceOf", "interfaces"], "Qualifies adjacency")
    N("T.has_element", "hasElement", "topology", "topology", "partial", ["bot:hasElement"], "Superproperty of contain and adjacent element")
    N("T.has_subelement", "hasSubElement", "topology", "topology", "todo", ["bot:hasSubElement"], "Wall hosts an opening")
    N("T.intersecting_element", "intersectingElement", "topology", "topology", "todo", ["bot:intersectingElement"], "Element crosses a zone")
    N("T.space_boundary", "Space boundary", "topology", "topology", "partial", ["IfcRelSpaceBoundary"], "Space-to-element delimiter")
    N("T.virtual_boundary", "Virtual boundary", "topology", "topology", "todo", ["IfcPhysicalOrVirtualEnum"], "Delimited by IfcVirtualElement")
    N("T.external_space", "External spatial element", "topology", "topology", "todo", ["IfcExternalSpatialElement"], "Site exterior with its own boundary")
    N("T.ifc_zone", "IfcZone group", "topology", "topology", "todo", ["IfcZone"], "Groups spaces; own geometry is forbidden")
    N("T.spatial_zone", "Overlapping spatial zone", "topology", "topology", "todo", ["IfcSpatialZone"], "Thermal or fire zone may overlap")
    N("T.opening_element", "Opening element", "topology", "topology", "partial", ["IfcOpeningElement"], "Void cut into a host")
    N("T.voids_element", "Voids element", "topology", "topology", "todo", ["IfcRelVoidsElement"], "Opening subtracts from a wall")
    N("T.fills_element", "Fills element", "topology", "topology", "partial", ["IfcRelFillsElement"], "Door or window fills the void")
    N("T.quantity", "Space quantities", "topology", "topology", "todo", ["Qto_SpaceBaseQuantities"], "IFC area and height")

    E("T.site", "T.zone", "specializes")
    E("T.building", "T.zone", "specializes")
    E("T.storey", "T.zone", "specializes")
    E("T.space", "T.zone", "specializes")
    E("T.contains", "T.zone", "depends_on")
    E("T.has_building", "T.contains", "specializes")
    E("T.has_storey", "T.contains", "specializes")
    E("T.has_space", "T.contains", "specializes")
    E("T.adjacent", "T.space", "depends_on")
    E("T.intersects", "T.zone", "depends_on")
    E("T.boundary", "prim.segment", "depends_on")
    E("T.interface", "T.adjacent", "depends_on")
    E("T.interface_of", "T.interface", "depends_on")
    E("T.adjacent_element", "T.element", "depends_on")
    E("T.adjacent_element", "T.zone", "depends_on")
    E("T.contains_element", "T.element", "depends_on")
    E("T.contains_element", "T.zone", "depends_on")
    E("T.opening.door", "T.interface", "specializes")
    E("T.opening.window", "T.interface", "specializes")
    E("T.facing", "prim.angle", "depends_on")
    E("T.building", "T.site", "depends_on")
    E("T.storey", "T.building", "depends_on")
    E("T.space", "T.storey", "depends_on")
    E("T.contains_element", "T.has_element", "specializes")
    E("T.adjacent_element", "T.has_element", "specializes")
    E("T.intersecting_element", "T.has_element", "specializes")
    E("T.has_subelement", "T.element", "depends_on")
    E("T.opening.door", "T.has_subelement", "depends_on")
    E("T.opening.window", "T.has_subelement", "depends_on")
    E("T.space_boundary", "T.boundary", "maps_to")
    E("T.space_boundary", "T.element", "depends_on")
    E("T.space_boundary", "T.space", "depends_on")
    E("T.virtual_boundary", "T.space_boundary", "specializes")
    E("T.external_space", "I10.place", "maps_to")
    E("T.external_space", "V2.ground", "maps_to")
    E("T.external_space", "T.space", "sibling_of")
    E("T.space", "T.external_space", "sibling_of")
    E("T.ifc_zone", "T.space", "depends_on")
    E("T.ifc_zone", "T.zone", "sibling_of")
    E("T.zone", "T.ifc_zone", "sibling_of")
    E("T.spatial_zone", "T.intersects", "depends_on")
    E("T.spatial_zone", "T.ifc_zone", "sibling_of")
    E("T.ifc_zone", "T.spatial_zone", "sibling_of")
    E("T.opening_element", "T.element", "specializes")
    E("T.voids_element", "T.opening_element", "depends_on")
    E("T.voids_element", "T.element", "depends_on")
    E("T.fills_element", "T.opening_element", "depends_on")
    E("T.opening.door", "T.fills_element", "depends_on")
    E("T.opening.window", "T.fills_element", "depends_on")
    E("T.quantity", "M8.measure", "maps_to")
    E("T.quantity", "T.space", "depends_on")
    siblings("T.opening.door", "T.opening.window")
    siblings("T.site", "T.building", "T.storey", "T.space")
    siblings("T.adjacent", "T.intersects", "T.contains")
    siblings("T.adjacent_element", "T.intersecting_element", "T.contains_element")

    # —— City / transportation (CityGML) ——
    N("U.road", "Road", "urban", "citygml", "partial", ["CityGML Road"], "District street")
    N("U.square", "Square", "urban", "citygml", "todo", ["CityGML Square"], "")
    N("U.track", "Track", "urban", "citygml", "placeholder", ["CityGML Track"], "")
    N("U.railway", "Railway", "urban", "citygml", "placeholder", ["CityGML Railway"], "")
    N("U.waterway", "Waterway", "urban", "citygml", "placeholder", ["CityGML Waterway"], "")
    N("U.complex", "TransportationComplex", "urban", "citygml", "todo", ["CityGML 2"], "2.0 name; 3.0 superclass is AbstractTransportationSpace")
    N("U.abstract_space", "AbstractTransportationSpace", "urban", "citygml", "todo", ["CityGML 3.0"], "Network geometry and surface geometry may both be stored")
    N("U.section", "Transportation section", "urban", "citygml", "todo", ["CityGML 3 Section"], "")
    N("U.intersection", "Intersection", "urban", "citygml", "todo", ["CityGML 3"], "")
    N("U.granularity", "Transport granularity", "urban", "citygml", "todo", ["lane", "way"], "XSD enum is lane|way")
    N("U.granularity_way", "Granularity way", "urban", "citygml", "todo", ["GranularityValueType"], "One object per surface function")
    N("U.granularity_lane", "Granularity lane", "urban", "citygml", "todo", ["GranularityValueType"], "One object per lane")
    N("U.granularity_area", "Granularity area", "urban", "citygml", "todo", ["TUM road2citygml3"], "Whole section width; absent from the XSD enum")
    N("U.traffic_space", "Traffic space", "urban", "citygml", "todo", ["CityGML TrafficSpace"], "Lane/way volume")
    N("U.traffic_area", "Traffic area", "urban", "citygml", "todo", ["CityGML TrafficArea"], "Carriageway, sidewalk")
    N("U.aux_space", "Auxiliary traffic space", "urban", "citygml", "todo", ["CityGML"], "Non-traffic volume")
    N("U.aux_area", "Auxiliary traffic area", "urban", "citygml", "todo", ["CityGML"], "Median, verge")
    N("U.clearance", "Clearance space", "urban", "citygml", "placeholder", ["TrafficSpace clearance"], "")
    N("U.pred_succ", "Predecessor/successor", "urban", "citygml", "partial", ["TrafficSpace"], "Property of TrafficSpace, not of Section")
    N("U.traffic_function", "Traffic-area function", "urban", "citygml", "todo", ["driving_lane", "footpath", "cyclepath"], "Codelist on the surface")
    N("U.marking", "Traffic marking", "urban", "citygml", "placeholder", ["CityGML Marking", "CityJSON TransportationMarking"], "Painted restriction")
    N("U.hole", "Transportation hole", "urban", "citygml", "placeholder", ["CityGML Hole", "CityJSON TransportationHole"], "Manhole or break in the surface")
    N("U.traffic_dir", "Traffic direction", "urban", "citygml", "have", ["TrafficDirection", "edge.directed"], "")
    N("U.plant_cover", "Plant cover", "urban", "citygml", "partial", ["PlantCover"], "Shared green")
    N("U.tree", "Solitary vegetation", "urban", "citygml", "have", ["SolitaryVegetationObject", "trees"], "Canopy tree")
    N("U.landuse", "Land use", "urban", "citygml", "todo", ["LandUse"], "")
    N("U.relief", "Relief / terrain", "urban", "citygml", "placeholder", ["Relief"], "")
    N("U.city_furniture", "City furniture", "urban", "citygml", "placeholder", ["CityFurniture"], "")
    N("U.bridge", "Bridge", "urban", "citygml", "placeholder", ["CityGML Bridge"], "")
    N("U.tunnel", "Tunnel", "urban", "citygml", "placeholder", ["CityGML Tunnel"], "")

    E("U.road", "V2.ground", "specializes")
    E("U.road", "U.complex", "specializes")
    E("U.square", "U.complex", "specializes")
    E("U.track", "U.complex", "specializes")
    E("U.railway", "U.complex", "specializes")
    E("U.waterway", "U.complex", "specializes")
    E("U.section", "U.road", "depends_on")
    E("U.intersection", "U.road", "depends_on")
    E("U.traffic_area", "U.section", "depends_on")
    E("U.traffic_space", "U.traffic_area", "depends_on")
    E("U.traffic_space", "U.granularity", "depends_on")
    E("U.aux_area", "U.section", "depends_on")
    E("U.aux_space", "U.aux_area", "depends_on")
    E("U.clearance", "U.traffic_space", "depends_on")
    E("U.clearance", "M8.measure", "maps_to")
    E("U.complex", "U.abstract_space", "maps_to")
    E("U.granularity_way", "U.granularity", "specializes")
    E("U.granularity_lane", "U.granularity", "specializes")
    E("U.granularity_area", "U.section", "depends_on")
    E("U.traffic_function", "U.traffic_area", "depends_on")
    E("U.marking", "U.traffic_area", "depends_on")
    E("U.hole", "U.road", "depends_on")
    E("U.pred_succ", "U.traffic_space", "depends_on")
    E("U.traffic_dir", "U.pred_succ", "depends_on")
    E("U.plant_cover", "V2.ground", "specializes")
    E("U.tree", "prim.point", "depends_on")
    E("U.landuse", "V6.parcel", "depends_on")
    E("U.relief", "prim.frame", "depends_on")
    E("U.city_furniture", "U.road", "depends_on")
    siblings("U.road", "U.square", "U.track", "U.railway", "U.waterway")
    siblings("U.traffic_area", "U.aux_area")
    siblings("U.traffic_space", "U.aux_space")
    siblings("U.section", "U.intersection")
    siblings("U.bridge", "U.tunnel")
    siblings("U.granularity_way", "U.granularity_lane", "U.granularity_area")
    siblings("U.marking", "U.hole")
    siblings("U.landuse", "U.plant_cover", "U.relief")
    siblings("U.city_furniture", "U.tree")

    # —— Circulation / linkage ——
    N("C1.graph", "Circulation graph", "circulation", "circulation", "have", ["112", "127", "plan-model network"], "Nodes+edges")
    N("C1.node", "Circulation node", "circulation", "circulation", "have", ["network.nodes"], "Place or intersection")
    N("C1.edge", "Circulation edge", "circulation", "circulation", "have", ["network.edges"], "Traversable link")
    N("C2.centerline", "Centerline", "circulation", "circulation", "have", ["CityGML LoD0", "edge.polyline"], "Directed axis")
    N("C3.hierarchy", "Route hierarchy", "circulation", "circulation", "have", ["UDC", "edge.hierarchy"], "Arterial…path")
    N("C4.mode", "Movement mode", "circulation", "circulation", "have", ["ped/bike/veh", "edge.mode"], "")
    N("C4.shared_surface", "Shared surface", "circulation", "circulation", "placeholder", ["woonerf"], "")
    N("C5.approach", "Approach sequence", "circulation", "circulation", "have", ["112", "network"], "Ordered places to door")
    N("C6.choice", "Choice / permeability", "circulation", "circulation", "todo", ["Space Syntax choice"], "Betweenness / through-movement")
    N("C6.connectivity", "Connectivity", "circulation", "circulation", "todo", ["Space Syntax"], "Degree of a line or node")
    N("C6.integration", "Integration", "circulation", "circulation", "placeholder", ["Space Syntax"], "Closeness / to-movement")
    N("C7.address", "Front door / address point", "circulation", "circulation", "have", ["110", "112", "door"], "")
    N("C8.direction", "Flow direction", "circulation", "circulation", "have", ["TrafficDirection", "directed"], "Boolean directed; CityGML enumerates forwards, backwards, both")
    N("C5.serial_vision", "Serial vision", "circulation", "circulation", "todo", ["Cullen"], "Sequence of views along a path")
    N("C9.sidewalk", "Sidewalk / footway", "circulation", "circulation", "have", ["TrafficArea", "sidewalk-main-n"], "")
    N("C10.carriageway", "Carriageway", "circulation", "circulation", "have", ["TrafficArea", "carriageway-main"], "")
    N("C11.crossing", "Crossing", "circulation", "circulation", "todo", [], "")
    N("C12.row", "Right-of-way", "circulation", "circulation", "have", ["street-main", "site plans"], "")
    N("C13.curb", "Curb line", "circulation", "circulation", "partial", ["sidewalk/carriageway split"], "")
    N("C14.bike_lane", "Bicycle lane", "circulation", "circulation", "todo", ["TrafficArea function"], "")
    N("C15.parking_bay", "Parking bay", "circulation", "circulation", "todo", ["TrafficArea"], "")
    N("C16.lod0", "LoD0 network geometry", "circulation", "circulation", "partial", ["CityJSON LoD0"], "Linear transport")
    N("C17.lod1", "LoD1 mass / section", "circulation", "circulation", "partial", ["CityJSON LoD1"], "Extruded solids")
    N("C18.lod2", "LoD2 traffic surfaces", "circulation", "circulation", "todo", ["CityJSON", "PLATEAU"], "TrafficArea surfaces; CityGML 3 splits LoD from granularity")
    N("C19.axial", "Axial line", "circulation", "circulation", "placeholder", ["Space Syntax"], "Longest line of sight and access")
    N("C20.lane", "Traffic lane", "circulation", "circulation", "todo", ["granularity lane"], "Subdivision of a carriageway")

    E("C1.graph", "C1.node", "depends_on")
    E("C1.graph", "C1.edge", "depends_on")
    E("C1.edge", "C1.node", "depends_on")
    E("C1.edge", "C2.centerline", "depends_on")
    E("C2.centerline", "prim.curve", "depends_on")
    E("C2.centerline", "C8.direction", "depends_on")
    E("C3.hierarchy", "C1.edge", "depends_on")
    E("C4.mode", "C1.edge", "depends_on")
    E("C5.approach", "C1.graph", "depends_on")
    E("C5.approach", "I6.threshold", "depends_on")
    E("C5.approach", "C7.address", "depends_on")
    E("C6.choice", "C1.graph", "depends_on")
    E("C6.connectivity", "C1.graph", "depends_on")
    E("C6.integration", "C1.graph", "depends_on")
    E("C5.serial_vision", "C2.centerline", "depends_on")
    E("C5.serial_vision", "I5.isovist", "depends_on")
    E("C7.address", "T.opening.door", "depends_on")
    E("C7.address", "C1.graph", "depends_on")
    E("C9.sidewalk", "U.traffic_area", "maps_to")
    E("C10.carriageway", "U.traffic_area", "maps_to")
    E("C9.sidewalk", "C1.edge", "specializes")
    E("C10.carriageway", "C1.edge", "specializes")
    E("C12.row", "U.road", "depends_on")
    E("C13.curb", "C12.row", "depends_on")
    E("C4.shared_surface", "C9.sidewalk", "depends_on")
    E("C4.shared_surface", "C10.carriageway", "depends_on")
    E("C4.shared_surface", "C4.mode", "depends_on")
    E("C14.bike_lane", "U.traffic_area", "maps_to")
    E("C15.parking_bay", "U.aux_area", "maps_to")
    E("C14.bike_lane", "C1.edge", "specializes")
    E("C16.lod0", "C2.centerline", "depends_on")
    E("C17.lod1", "V1.figure", "depends_on")
    E("C18.lod2", "U.traffic_area", "depends_on")
    E("C9.sidewalk", "U.granularity_way", "depends_on")
    E("C9.sidewalk", "U.traffic_function", "depends_on")
    E("C10.carriageway", "U.granularity_way", "depends_on")
    E("C10.carriageway", "U.traffic_function", "depends_on")
    E("C11.crossing", "U.traffic_function", "depends_on")
    E("C14.bike_lane", "U.traffic_function", "depends_on")
    E("C15.parking_bay", "U.traffic_function", "depends_on")
    E("C19.axial", "C2.centerline", "sibling_of")
    E("C2.centerline", "C19.axial", "sibling_of")
    E("C20.lane", "C10.carriageway", "specializes")
    E("C20.lane", "U.granularity_lane", "depends_on")
    siblings("C9.sidewalk", "C10.carriageway", "C11.crossing", "C14.bike_lane", "C15.parking_bay", "C4.shared_surface")
    siblings("C3.hierarchy", "C4.mode", "C8.direction")
    siblings("C6.choice", "C6.connectivity", "C6.integration")
    siblings("C5.approach", "C5.serial_vision")
    siblings("C16.lod0", "C17.lod1", "C18.lod2")

    # —— Interaction ——
    N("I1.adjacency", "Adjacency", "interaction", "interaction", "have", ["Adjacency"], "maps T.adjacent")
    N("I2.interface", "Interface relation", "interaction", "interaction", "partial", ["Opening"], "")
    N("I3.frontage", "Frontage", "interaction", "interaction", "partial", ["active frontage", "m-green-frontage"], "Metres of face on a void")
    N("I3.active_frontage", "Active frontage", "interaction", "interaction", "todo", ["UD"], "Doors/windows onto street")
    N("I3.blank_frontage", "Blank frontage", "interaction", "interaction", "todo", ["street wall"], "Frontage length without openings")
    N("I3.primary_frontage", "Primary frontage", "interaction", "interaction", "todo", ["plot address"], "The street a parcel faces")
    N("I3.frontage_rhythm", "Frontage rhythm", "interaction", "interaction", "todo", ["Conzen plot series"], "Repeated plot widths along one street")
    N("I4.access", "Access / reachability", "interaction", "interaction", "partial", ["graph walk", "network"], "")
    N("I5.overlook", "Overlook / exposure", "interaction", "interaction", "todo", ["isovist"], "Sees relation")
    N("I5.isovist", "Isovist / visibility field", "interaction", "interaction", "placeholder", ["Space Syntax"], "")
    N("I5.prospect_refuge", "Prospect–refuge", "interaction", "interaction", "placeholder", ["Appleton"], "")
    N("I6.threshold", "Threshold", "interaction", "interaction", "have", ["112", "130", "interfaces"], "Thickened transition")
    N("I7.containment", "Containment", "interaction", "interaction", "have", ["BOT"], "")
    N("I8.shared_outdoor", "Shared outdoor address", "interaction", "interaction", "partial", ["shared green", "interfaces"], "Many solids face one void")
    N("I9.intimacy_field", "Intimacy gradient field", "interaction", "interaction", "partial", ["127"], "Public→private along path")
    N("I10.place", "SpatialStructure place", "interaction", "owned", "have", ["schema places"], "Product mid-layer zone")
    N("I11.ss_network", "SpatialStructure network", "interaction", "owned", "have", ["schema network"], "")
    N("I12.ss_measure", "SpatialStructure measure", "interaction", "owned", "have", ["schema measures"], "")
    N("I13.ss_interface", "SpatialStructure interface", "interaction", "owned", "have", ["schema interfaces"], "")

    E("I1.adjacency", "T.adjacent", "maps_to")
    E("I2.interface", "T.interface", "maps_to")
    E("I3.frontage", "V1.figure", "depends_on")
    E("I3.frontage", "V2.ground", "depends_on")
    E("I3.frontage", "M9.length_along", "depends_on")
    E("I3.frontage", "I13.ss_interface", "maps_to")
    E("I3.active_frontage", "I3.frontage", "specializes")
    E("I3.active_frontage", "T.opening.door", "depends_on")
    E("I3.blank_frontage", "I3.frontage", "specializes")
    E("I3.blank_frontage", "V8.dead_space", "depends_on")
    E("I3.primary_frontage", "I3.frontage", "specializes")
    E("I3.primary_frontage", "V6.parcel", "depends_on")
    E("I3.primary_frontage", "U.road", "depends_on")
    E("I3.frontage_rhythm", "V6.plot_series", "depends_on")
    E("I3.frontage_rhythm", "M14.frontage_grain", "depends_on")
    E("I4.access", "C1.graph", "depends_on")
    E("I5.overlook", "T.opening.window", "depends_on")
    E("I5.overlook", "V2.ground", "depends_on")
    E("I5.isovist", "prim.ring", "depends_on")
    E("I5.prospect_refuge", "I5.isovist", "depends_on")
    E("I6.threshold", "I2.interface", "depends_on")
    E("I6.threshold", "C5.approach", "depends_on")
    E("I7.containment", "T.contains", "maps_to")
    E("I8.shared_outdoor", "V2.ground", "depends_on")
    E("I8.shared_outdoor", "I3.frontage", "depends_on")
    E("I9.intimacy_field", "C1.graph", "depends_on")
    E("I9.intimacy_field", "P3.domain", "depends_on")
    E("I10.place", "T.zone", "maps_to")
    E("I10.place", "prim.ring", "depends_on")
    E("I11.ss_network", "C1.graph", "maps_to")
    E("I12.ss_measure", "M8.measure", "maps_to")
    E("I13.ss_interface", "T.interface", "maps_to")
    siblings("I3.active_frontage", "I3.blank_frontage", "I3.primary_frontage")
    siblings("I5.overlook", "I5.isovist", "I5.prospect_refuge")
    siblings("I10.place", "I11.ss_network", "I12.ss_measure", "I13.ss_interface")

    # —— Orientation / climate ——
    N("O1.cardinal", "Cardinal frame", "climate", "climate", "have", ["north"], "")
    N("O2.equator_side", "Equator-facing side", "climate", "climate", "have", ["105", "128", "latitude"], "")
    N("O3.solar_access", "Solar access", "climate", "climate", "todo", [], "Time-aware sun on places")
    N("O3.daylight", "Daylight (qualitative)", "climate", "climate", "partial", ["159", "107"], "")
    N("O4.approach_dir", "Prevailing approach direction", "climate", "climate", "todo", ["110"], "")
    N("O5.wind", "Wind / comfort", "climate", "climate", "placeholder", [], "Out of scope physics")

    E("O1.cardinal", "prim.north", "depends_on")
    E("O2.equator_side", "O1.cardinal", "depends_on")
    E("O2.equator_side", "prim.frame", "depends_on")
    E("O3.solar_access", "O2.equator_side", "depends_on")
    E("O3.solar_access", "prim.time", "depends_on")
    E("O3.daylight", "T.opening.window", "depends_on")
    E("O4.approach_dir", "C5.approach", "depends_on")
    siblings("O3.solar_access", "O3.daylight", "O5.wind")

    # —— Place roles ——
    N("P1.tags", "Role tags", "place", "place", "have", ["ALLOWED_TAGS"], "street, outdoor, private…")
    N("P2.center", "Center", "place", "place", "partial", ["Alexander", "DESIGN"], "Coherent region")
    N("P3.domain", "Public–private domain", "place", "place", "partial", ["127"], "")
    N("P4.room_kind", "Room kind", "place", "place", "partial", ["living", "hall"], "")
    N("P5.landmark", "Landmark", "place", "place", "placeholder", ["Lynch"], "Imageable object")
    N("P6.district", "District", "place", "place", "todo", ["Lynch", "Conzen region"], "Named area of common character")

    E("P2.center", "T.zone", "depends_on")
    E("P3.domain", "P1.tags", "depends_on")
    E("P4.room_kind", "P1.tags", "specializes")
    E("P4.room_kind", "T.space", "depends_on")
    E("P5.landmark", "V1.figure", "depends_on")
    E("P6.district", "V6.plan_unit", "maps_to")
    E("P6.district", "P2.center", "sibling_of")
    E("P2.center", "P6.district", "sibling_of")

    # —— Pattern language field ——
    N("L1.condition", "Spatial condition", "language", "language", "have", ["conditions/"], "Predicate over model")
    N("L2.diagram", "Pattern diagram schema", "language", "language", "partial", ["plan-model diagrams"], "")
    N("L3.preserve", "Structure preservation", "language", "language", "have", ["Preserving", "step"], "")
    N("L4.sequence", "Pattern sequence", "language", "language", "have", ["sequence.py"], "")
    N("L5.project", "Project language", "language", "language", "have", ["seed-house"], "")

    E("L1.condition", "C1.graph", "depends_on")
    E("L1.condition", "M2.distance", "depends_on")
    E("L2.diagram", "L1.condition", "depends_on")
    E("L2.diagram", "symbology.profile", "depends_on")
    E("L3.preserve", "L1.condition", "depends_on")
    E("L4.sequence", "L5.project", "depends_on")

    # —— Owned symbology (product layer) ——
    N("symbology.profile", "Plan symbology profile", "symbology", "owned", "partial", ["VISUAL-LANGUAGE"], "pattern-language.plan-symbology")
    N("symbology.door_swing", "Door swing glyph", "symbology", "owned", "have", ["HABS"], "")
    N("symbology.window_tick", "Window tick glyph", "symbology", "owned", "have", ["HABS"], "")
    N("symbology.tree_canopy", "Tree canopy glyph", "symbology", "owned", "have", ["HABS"], "")
    N("symbology.flow_arrow", "Flow arrow glyph", "symbology", "owned", "have", ["plan.js centerline"], "Needs C2")
    N("symbology.dimension", "Dimension string glyph", "symbology", "owned", "have", ["plan.js measures"], "Needs M8")
    N("symbology.figure_ground", "Figure–ground render", "symbology", "owned", "partial", ["Nolli"], "")
    N("symbology.legend", "Legend / north / scale", "symbology", "owned", "have", ["site plans", "demo legend"], "")
    N("symbology.hierarchy_weight", "Hierarchy stroke weight", "symbology", "owned", "have", ["HIER_WIDTH"], "")
    N("symbology.diagram_overlay", "Pattern diagram overlay", "symbology", "owned", "have", ["plan.js diagrams"], "")

    E("symbology.door_swing", "T.opening.door", "renders_as")
    E("symbology.window_tick", "T.opening.window", "renders_as")
    E("symbology.tree_canopy", "U.tree", "renders_as")
    E("symbology.flow_arrow", "C2.centerline", "renders_as")
    E("symbology.dimension", "M8.measure", "renders_as")
    E("symbology.figure_ground", "V1.figure", "renders_as")
    E("symbology.figure_ground", "V2.ground", "renders_as")
    E("symbology.hierarchy_weight", "C3.hierarchy", "renders_as")
    E("symbology.diagram_overlay", "L2.diagram", "renders_as")
    E("symbology.profile", "symbology.door_swing", "parent_of")
    E("symbology.profile", "symbology.window_tick", "parent_of")
    E("symbology.profile", "symbology.tree_canopy", "parent_of")
    E("symbology.profile", "symbology.flow_arrow", "parent_of")
    E("symbology.profile", "symbology.dimension", "parent_of")
    E("symbology.profile", "symbology.hierarchy_weight", "parent_of")
    E("symbology.profile", "symbology.diagram_overlay", "parent_of")
    E("symbology.profile", "symbology.legend", "parent_of")

    # —— Seed pattern hooks (cite numbers only) ——
    for num, name, deps in [
        (105, "South Facing Outdoors", ["O2.equator_side", "V2.ground", "I3.frontage"]),
        (106, "Positive Outdoor Space", ["V3.enclosure", "V2.ground", "V2.convex", "prim.ring"]),
        (107, "Wings of Light", ["M4.clear_width", "T.space", "O3.daylight"]),
        (110, "Main Entrance", ["C7.address", "C5.approach", "O4.approach_dir"]),
        (112, "Entrance Transition", ["C5.approach", "I6.threshold", "C1.graph"]),
        (127, "Intimacy Gradient", ["I9.intimacy_field", "C1.graph", "P3.domain"]),
        (128, "Indoor Sunlight", ["O2.equator_side", "T.space", "P4.room_kind"]),
        (130, "Entrance Room", ["C7.address", "T.space", "I6.threshold"]),
        (159, "Light on Two Sides", ["T.opening.window", "T.facing", "T.space"]),
        (167, "Six-Foot Balcony", ["M4.clear_width", "M8.measure"]),
        (180, "Window Place", ["T.opening.window", "I5.overlook", "P4.room_kind"]),
        (190, "Ceiling Height Variety", ["M5.height", "T.space"]),
    ]:
        pid = f"pat.{num}"
        N(pid, f"{num} {name}", "pattern", "catalog", "have", [f"catalog/{num}"], "Seed pattern")
        for d in deps:
            E(pid, d, "depends_on")
        E(pid, "L1.condition", "depends_on")

    graph = {
        "id": "pattern-language.spatial-concept-graph",
        "title": "Spatial concept knowledge graph",
        "version": 1,
        "description": (
            "Exhaustive graph of spatial concepts for the pattern-language workbench: "
            "foundations, metric space, morphology, topology, city transportation, "
            "circulation, interaction, climate, place roles, language, and owned symbology. "
            "Edges: depends_on, parent_of, sibling_of, maps_to, specializes, renders_as."
        ),
        "status_legend": {
            "have": "In topology/checks/demo today",
            "partial": "Present but incomplete",
            "todo": "Must codify next",
            "placeholder": "Named; out of scope or thin",
        },
        "nodes": NODES,
        "edges": EDGES,
    }

    # stats
    by_status: dict[str, int] = {}
    for n in NODES:
        by_status[n["status"]] = by_status.get(n["status"], 0) + 1
    graph["stats"] = {
        "nodes": len(NODES),
        "edges": len(EDGES),
        "by_status": by_status,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(NODES)} nodes, {len(EDGES)} edges, {by_status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
