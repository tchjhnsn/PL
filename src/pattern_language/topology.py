"""Read and write the two U3 houses as a BOT-shaped graph.

``read_ifc`` and ``write_ifc`` are the only functions that import
``ifcopenshell``. A window or door stores its host space in ``ObjectType``
because a window may sit on an edge shared with another space. Facing is the
outward normal of that host edge, not a stored property.
"""

from __future__ import annotations

import json
import math
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

Point = tuple[float, float]
ZoneKind = Literal["Site", "Building", "Storey", "Space"]
Cardinal = Literal["north", "south", "east", "west"]
OpeningKind = Literal["window", "door"]
AdjacencyKind = Literal["wall", "door"]

ALLOWED_TAGS = frozenset(
    {
        "outdoor",
        "street",
        "transition",
        "public",
        "semi-private",
        "private",
        "daytime",
        "corridor",
        "living",
        "room",
        "balcony",
        "occupied",
    }
)

_NORTH: Point = (0.0, 1.0)
_MIN_SEGMENT_M = 0.05
_GUID_NAMESPACE = uuid.UUID("c0ffee00-1111-4111-8111-000000000003")
_HEADER_STAMP = "2026-11-19T00:00:00"
_OWNER_STAMP = int(datetime(2026, 11, 19, tzinfo=timezone.utc).timestamp())


class TopologyError(Exception):
    """The IFC file is not this unit's graph, or a house table is inconsistent."""


@dataclass(frozen=True, slots=True)
class Zone:
    name: str
    kind: ZoneKind
    parent: str | None
    tags: frozenset[str]
    footprint: tuple[Point, ...]
    height_m: float | None


@dataclass(frozen=True, slots=True)
class Opening:
    name: str
    kind: OpeningKind
    orientation: Cardinal
    spaces: tuple[str, ...]
    at_m: Point


@dataclass(frozen=True, slots=True)
class Adjacency:
    a: str
    b: str
    kind: AdjacencyKind
    opening_id: str | None


@dataclass(frozen=True, slots=True)
class Boundary:
    space: str
    other: str | None
    start: Point
    end: Point
    external: bool


@dataclass(frozen=True, slots=True)
class Topology:
    north: Point
    zones: tuple[Zone, ...]
    adjacencies: tuple[Adjacency, ...]
    boundaries: tuple[Boundary, ...]
    openings: tuple[Opening, ...]


@dataclass(frozen=True, slots=True)
class _Space:
    name: str
    tags: frozenset[str]
    ring: tuple[Point, ...]
    height_m: float


@dataclass(frozen=True, slots=True)
class _Hole:
    name: str
    kind: OpeningKind
    host: str
    at_m: Point


def read_topology(path: Path) -> Topology:
    """Read one of these IFC houses. Same graph as ``read_ifc``."""
    return read_ifc(path)


def read_ifc(path: Path) -> Topology:
    """Read one IFC4 house into a frozen graph.

    Import ``ifcopenshell`` inside this function. Raise ``TopologyError``
    when the file is missing, is not this graph, uses a length unit other
    than metre, or a space has no extruded body.
    """
    import ifcopenshell

    try:
        ifc = ifcopenshell.open(str(path))
    except Exception as exc:
        raise TopologyError(f"cannot read {path}") from exc
    return _read_file(ifc)


def write_ifc(model: Topology, path: Path) -> None:
    """Write ``model`` to an IFC4 file, creating parent directories.

    Import ``ifcopenshell`` inside this function. Raise ``TopologyError``
    when a space edge is not axis-aligned.
    """
    _require_axis_aligned(model)
    import ifcopenshell.api.aggregate
    import ifcopenshell.api.context
    import ifcopenshell.api.project
    import ifcopenshell.api.root
    import ifcopenshell.api.unit
    import ifcopenshell.guid

    _write_file(
        model,
        path,
        create_file=ifcopenshell.api.project.create_file,
        create_entity=ifcopenshell.api.root.create_entity,
        assign_unit=ifcopenshell.api.unit.assign_unit,
        add_context=ifcopenshell.api.context.add_context,
        assign_object=ifcopenshell.api.aggregate.assign_object,
        compress=ifcopenshell.guid.compress,
    )


def write_fixtures(directory: Path) -> tuple[Path, Path]:
    """Overwrite ``pass-house.ifc`` and ``fail-house.ifc`` in ``directory``."""
    directory.mkdir(parents=True, exist_ok=True)
    houses = (("pass-house.ifc", _pass_house()), ("fail-house.ifc", _fail_house()))
    paths: list[Path] = []
    for filename, model in houses:
        path = directory / filename
        write_ifc(model, path)
        paths.append(path)
    return paths[0], paths[1]


def to_json(model: Topology) -> str:
    """Canonical JSON for a topology graph, with one trailing newline."""
    payload = {
        "adjacencies": [_plain_adjacency(item) for item in model.adjacencies],
        "boundaries": [_plain_boundary(item) for item in model.boundaries],
        "north": [_num(item) for item in model.north],
        "openings": [_plain_opening(item) for item in model.openings],
        "zones": [_plain_zone(item) for item in model.zones],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def from_json(text: str) -> Topology:
    """Parse a topology report written by ``to_json``."""
    try:
        payload = json.loads(text)
        north = _as_point(payload["north"])
        zones = tuple(_zone_from(item) for item in payload["zones"])
        adjacencies = tuple(_adjacency_from(item) for item in payload["adjacencies"])
        boundaries = tuple(_boundary_from(item) for item in payload["boundaries"])
        openings = tuple(_opening_from(item) for item in payload["openings"])
    except (KeyError, TypeError, ValueError) as exc:
        raise TopologyError("topology JSON is unreadable") from exc
    return Topology(north, zones, adjacencies, boundaries, openings)


def _pass_house() -> Topology:
    return _assemble(
        (
            _Space("street", frozenset({"street"}), ((0, -2), (8, -2), (8, 0), (0, 0)), 3.0),
            _Space("court", frozenset({"outdoor", "transition"}), ((0, 0), (8, 0), (8, 4), (0, 4)), 3.0),
            _Space("hall", frozenset({"room", "public", "occupied"}), ((0, 4), (4, 4), (4, 8), (0, 8)), 2.4),
            _Space(
                "living",
                frozenset({"living", "semi-private", "daytime", "occupied"}),
                ((4, 4), (8, 4), (8, 8), (4, 8)),
                3.0,
            ),
            _Space("bedroom", frozenset({"room", "private", "occupied"}), ((4, 8), (8, 8), (8, 12), (4, 12)), 2.7),
            _Space("balcony", frozenset({"balcony", "outdoor"}), ((8, 8), (10, 8), (10, 12), (8, 12)), 3.0),
        ),
        (
            _Hole("approach-door", "door", "court", (4, 0)),
            _Hole("main-door", "door", "hall", (3, 4)),
            _Hole("hall-living", "door", "hall", (4, 6)),
            _Hole("living-bedroom", "door", "living", (6, 8)),
            _Hole("bedroom-balcony", "door", "bedroom", (8, 10)),
            _Hole("hall-south", "window", "hall", (1, 4)),
            _Hole("hall-west", "window", "hall", (0, 6)),
            _Hole("living-south", "window", "living", (6, 4)),
            _Hole("living-east", "window", "living", (8, 6)),
            _Hole("bedroom-north", "window", "bedroom", (6, 12)),
            _Hole("bedroom-west", "window", "bedroom", (4, 10)),
        ),
    )


def _fail_house() -> Topology:
    return _assemble(
        (
            _Space("street", frozenset({"street"}), ((0, -2), (8, -2), (8, 0), (0, 0)), 2.4),
            _Space("corridor", frozenset({"corridor"}), ((0, 0), (8, 0), (8, 2), (0, 2)), 2.4),
            _Space("west-flank", frozenset(), ((0, 2), (4, 2), (4, 12), (0, 12)), 2.4),
            _Space("bedroom", frozenset({"room", "private", "occupied"}), ((4, 2), (8, 2), (8, 12), (4, 12)), 2.4),
            _Space("east-flank", frozenset(), ((8, 2), (11, 2), (11, 12), (8, 12)), 2.4),
            _Space(
                "dayroom",
                frozenset({"public", "daytime", "occupied"}),
                ((0, 12), (6, 12), (6, 15), (0, 15)),
                2.4,
            ),
            _Space("balcony", frozenset({"balcony", "outdoor"}), ((-1, 12), (0, 12), (0, 15), (-1, 15)), 2.4),
            _Space(
                "court",
                frozenset({"outdoor"}),
                ((0, 15), (8, 15), (8, 16), (2, 16), (2, 22), (0, 22)),
                3.0,
            ),
        ),
        (
            _Hole("main-door", "door", "corridor", (4, 0)),
            _Hole("corridor-bedroom", "door", "corridor", (6, 2)),
            _Hole("bedroom-dayroom", "door", "bedroom", (5, 12)),
            _Hole("dayroom-balcony", "door", "dayroom", (0, 13)),
            _Hole("bedroom-north", "window", "bedroom", (7, 12)),
            _Hole("dayroom-north", "window", "dayroom", (3, 15)),
            _Hole("dayroom-west", "window", "dayroom", (0, 14)),
        ),
    )


def _assemble(spaces: tuple[_Space, ...], holes: tuple[_Hole, ...]) -> Topology:
    for space in spaces:
        _reject_unknown_tags(space.tags)
        if space.name in {"site", "house", "ground"}:
            raise TopologyError("duplicate zone name")
    if len({space.name for space in spaces}) != len(spaces):
        raise TopologyError("duplicate zone name")
    if len({hole.name for hole in holes}) != len(holes):
        raise TopologyError("duplicate opening name")
    rings = {space.name: _normalize_ring(space.ring) for space in spaces}
    boundaries = _boundaries_from(rings)
    openings: list[Opening] = []
    for hole in holes:
        at = _point(*hole.at_m)
        start, end = _nearest_edge(rings[hole.host], at)
        orientation = _outward(start, end)
        if hole.kind == "window":
            hosts = (hole.host,)
        else:
            boundary = _boundary_at(boundaries, hole.host, at)
            if boundary.other is None:
                raise TopologyError(f"{hole.name} is not on a shared wall")
            hosts = tuple(sorted((hole.host, boundary.other)))
        openings.append(Opening(hole.name, hole.kind, orientation, hosts, at))
    opening_tuple = tuple(sorted(openings, key=lambda item: item.name))
    zones: list[Zone] = [
        Zone("site", "Site", None, frozenset(), (), None),
        Zone("house", "Building", "site", frozenset(), (), None),
        Zone("ground", "Storey", "house", frozenset(), (), None),
    ]
    for space in spaces:
        zones.append(
            Zone(
                space.name,
                "Space",
                "ground",
                space.tags,
                rings[space.name],
                _num(space.height_m),
            )
        )
    return Topology(
        _NORTH,
        tuple(sorted(zones, key=lambda item: item.name)),
        _adjacencies(boundaries, opening_tuple),
        boundaries,
        opening_tuple,
    )


def _require_axis_aligned(model: Topology) -> None:
    for zone in model.zones:
        _reject_unknown_tags(zone.tags)
        if zone.kind != "Space":
            continue
        if len(zone.footprint) < 3:
            raise TopologyError(f"{zone.name} has no extruded body")
        for start, end in _edges(zone.footprint):
            if not (_is_horizontal(start, end) or _is_vertical(start, end)):
                raise TopologyError(f"{zone.name} edge is not axis-aligned")


def _reject_unknown_tags(tags: frozenset[str]) -> None:
    unknown = tags - ALLOWED_TAGS
    if unknown:
        raise TopologyError(f"unknown tag: {sorted(unknown)[0]}")


def _num(value: float) -> float:
    return float(round(float(value), 3))


def _point(x: float, y: float) -> Point:
    return (_num(x), _num(y))


def _as_point(value: Any) -> Point:
    if len(value) != 2:
        raise TypeError("point")
    return _point(value[0], value[1])


def _edges(ring: tuple[Point, ...]) -> tuple[tuple[Point, Point], ...]:
    return tuple((ring[index], ring[(index + 1) % len(ring)]) for index in range(len(ring)))


def _is_horizontal(start: Point, end: Point) -> bool:
    return start[1] == end[1] and start[0] != end[0]


def _is_vertical(start: Point, end: Point) -> bool:
    return start[0] == end[0] and start[1] != end[1]


def _shoelace(ring: tuple[Point, ...]) -> float:
    total = 0.0
    for start, end in _edges(ring):
        total += start[0] * end[1] - end[0] * start[1]
    return total / 2.0


def _normalize_ring(points: tuple[Point, ...]) -> tuple[Point, ...]:
    ring = [_point(x, y) for x, y in points]
    if len(ring) >= 2 and ring[0] == ring[-1]:
        ring = ring[:-1]
    if len(ring) < 3:
        raise TopologyError("space ring has fewer than 3 points")
    if abs(_shoelace(tuple(ring))) <= _MIN_SEGMENT_M:
        raise TopologyError("space ring has no area")
    if _shoelace(tuple(ring)) < 0:
        ring.reverse()
    start = min(range(len(ring)), key=lambda index: ring[index])
    ring = ring[start:] + ring[:start]
    for edge_start, edge_end in _edges(tuple(ring)):
        if not (_is_horizontal(edge_start, edge_end) or _is_vertical(edge_start, edge_end)):
            raise TopologyError("space edge is not axis-aligned")
    return tuple(ring)


def _outward(start: Point, end: Point) -> Cardinal:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    nx, ny = dy, -dx
    if abs(abs(nx) - abs(ny)) <= 1e-9:
        raise TopologyError("facing is not cardinal")
    if abs(nx) > abs(ny):
        return "east" if nx > 0 else "west"
    return "north" if ny > 0 else "south"


def _distance_to_segment(point: Point, start: Point, end: Point) -> float:
    px, py = point
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        return math.hypot(px - start[0], py - start[1])
    ratio = ((px - start[0]) * dx + (py - start[1]) * dy) / length_sq
    ratio = max(0.0, min(1.0, ratio))
    return math.hypot(px - (start[0] + ratio * dx), py - (start[1] + ratio * dy))


def _nearest_edge(ring: tuple[Point, ...], point: Point) -> tuple[Point, Point]:
    ranked: list[tuple[float, tuple[Point, Point]]] = []
    for start, end in _edges(ring):
        ranked.append((_distance_to_segment(point, start, end), (start, end)))
    ranked.sort(key=lambda item: item[0])
    if not ranked or ranked[0][0] > _MIN_SEGMENT_M:
        raise TopologyError("opening is not on one footprint edge")
    if len(ranked) > 1 and abs(ranked[0][0] - ranked[1][0]) <= 1e-4:
        raise TopologyError("opening is not on one footprint edge")
    return ranked[0][1]


def _overlap_interval(
    start: Point,
    end: Point,
    other_start: Point,
    other_end: Point,
) -> tuple[float, float] | None:
    if _is_horizontal(start, end) and _is_horizontal(other_start, other_end):
        if start[1] != other_start[1]:
            return None
        lo = max(min(start[0], end[0]), min(other_start[0], other_end[0]))
        hi = min(max(start[0], end[0]), max(other_start[0], other_end[0]))
        if hi - lo <= _MIN_SEGMENT_M:
            return None
        distances = sorted((abs(lo - start[0]), abs(hi - start[0])))
        return distances[0], distances[1]
    if _is_vertical(start, end) and _is_vertical(other_start, other_end):
        if start[0] != other_start[0]:
            return None
        lo = max(min(start[1], end[1]), min(other_start[1], other_end[1]))
        hi = min(max(start[1], end[1]), max(other_start[1], other_end[1]))
        if hi - lo <= _MIN_SEGMENT_M:
            return None
        distances = sorted((abs(lo - start[1]), abs(hi - start[1])))
        return distances[0], distances[1]
    return None


def _point_along(start: Point, end: Point, distance: float) -> Point:
    length = math.hypot(end[0] - start[0], end[1] - start[1])
    if length == 0:
        raise TopologyError("space edge has no length")
    ratio = distance / length
    return _point(start[0] + (end[0] - start[0]) * ratio, start[1] + (end[1] - start[1]) * ratio)


def _split_edge(
    space: str,
    start: Point,
    end: Point,
    rings: dict[str, tuple[Point, ...]],
) -> list[Boundary]:
    length = round(math.hypot(end[0] - start[0], end[1] - start[1]), 3)
    overlaps: list[tuple[float, float, str]] = []
    cuts = {0.0, length}
    for other, ring in rings.items():
        if other == space:
            continue
        for other_start, other_end in _edges(ring):
            interval = _overlap_interval(start, end, other_start, other_end)
            if interval is None:
                continue
            d0, d1 = round(interval[0], 3), round(interval[1], 3)
            if d1 - d0 <= _MIN_SEGMENT_M:
                continue
            overlaps.append((d0, d1, other))
            cuts.add(d0)
            cuts.add(d1)
    segments: list[Boundary] = []
    ordered = sorted(cuts)
    for left, right in zip(ordered, ordered[1:]):
        if right - left <= _MIN_SEGMENT_M:
            continue
        mid = (left + right) / 2.0
        owners = [name for d0, d1, name in overlaps if d0 <= mid <= d1]
        if len(set(owners)) > 1:
            raise TopologyError(f"{space} edge overlaps more than one space")
        other = owners[0] if owners else None
        segments.append(
            Boundary(
                space=space,
                other=other,
                start=_point_along(start, end, left),
                end=_point_along(start, end, right),
                external=other is None,
            )
        )
    if not segments:
        raise TopologyError(f"{space} edge produced no boundary")
    return segments


def _boundaries_from(rings: dict[str, tuple[Point, ...]]) -> tuple[Boundary, ...]:
    found: list[Boundary] = []
    for space, ring in rings.items():
        for start, end in _edges(ring):
            if not (_is_horizontal(start, end) or _is_vertical(start, end)):
                raise TopologyError(f"{space} edge is not axis-aligned")
            found.extend(_split_edge(space, start, end, rings))
    return tuple(sorted(found, key=lambda item: (item.space, item.start, item.end)))


def _boundary_at(boundaries: tuple[Boundary, ...], space: str, point: Point) -> Boundary:
    hits: list[tuple[float, Boundary]] = []
    for boundary in boundaries:
        if boundary.space != space:
            continue
        distance = _distance_to_segment(point, boundary.start, boundary.end)
        if distance <= _MIN_SEGMENT_M:
            hits.append((distance, boundary))
    if not hits:
        raise TopologyError("opening is not on one footprint edge")
    hits.sort(key=lambda item: item[0])
    if len(hits) > 1 and abs(hits[0][0] - hits[1][0]) <= 1e-4:
        raise TopologyError("opening is not on one footprint edge")
    return hits[0][1]


def _adjacencies(
    boundaries: tuple[Boundary, ...],
    openings: tuple[Opening, ...],
) -> tuple[Adjacency, ...]:
    pairs = sorted({tuple(sorted((item.space, item.other))) for item in boundaries if item.other})
    doors: dict[tuple[str, str], list[str]] = {}
    for opening in openings:
        if opening.kind != "door":
            continue
        if len(opening.spaces) != 2:
            raise TopologyError(f"{opening.name} does not join two spaces")
        doors.setdefault(tuple(sorted(opening.spaces)), []).append(opening.name)
    pair_set = set(pairs)
    for pair in doors:
        if pair not in pair_set:
            raise TopologyError(f"door does not fill a shared wall: {pair[0]} {pair[1]}")
    result: list[Adjacency] = []
    for pair in pairs:
        names = doors.get(pair, [])
        if len(names) > 1:
            raise TopologyError(f"multiple doors between {pair[0]} and {pair[1]}")
        if names:
            result.append(Adjacency(pair[0], pair[1], "door", names[0]))
        else:
            result.append(Adjacency(pair[0], pair[1], "wall", None))
    return tuple(result)


def _plain_zone(zone: Zone) -> dict[str, Any]:
    return {
        "footprint": [[_num(x), _num(y)] for x, y in zone.footprint],
        "height_m": None if zone.height_m is None else _num(zone.height_m),
        "kind": zone.kind,
        "name": zone.name,
        "parent": zone.parent,
        "tags": sorted(zone.tags),
    }


def _plain_opening(opening: Opening) -> dict[str, Any]:
    return {
        "at_m": [_num(opening.at_m[0]), _num(opening.at_m[1])],
        "kind": opening.kind,
        "name": opening.name,
        "orientation": opening.orientation,
        "spaces": list(opening.spaces),
    }


def _plain_adjacency(adjacency: Adjacency) -> dict[str, Any]:
    return {
        "a": adjacency.a,
        "b": adjacency.b,
        "kind": adjacency.kind,
        "opening_id": adjacency.opening_id,
    }


def _plain_boundary(boundary: Boundary) -> dict[str, Any]:
    return {
        "end": [_num(boundary.end[0]), _num(boundary.end[1])],
        "external": boundary.external,
        "other": boundary.other,
        "space": boundary.space,
        "start": [_num(boundary.start[0]), _num(boundary.start[1])],
    }


def _tags_from(value: Any) -> frozenset[str]:
    if not isinstance(value, list):
        raise TypeError("tags")
    tags = frozenset(str(item) for item in value)
    _reject_unknown_tags(tags)
    return tags


def _zone_from(value: dict[str, Any]) -> Zone:
    kind = value["kind"]
    if kind not in {"Site", "Building", "Storey", "Space"}:
        raise ValueError("kind")
    height = value["height_m"]
    return Zone(
        str(value["name"]),
        kind,
        None if value["parent"] is None else str(value["parent"]),
        _tags_from(value["tags"]),
        tuple(_as_point(point) for point in value["footprint"]),
        None if height is None else _num(height),
    )


def _opening_from(value: dict[str, Any]) -> Opening:
    kind = value["kind"]
    orientation = value["orientation"]
    if kind not in {"window", "door"} or orientation not in {"north", "south", "east", "west"}:
        raise ValueError("opening")
    return Opening(
        str(value["name"]),
        kind,
        orientation,
        tuple(str(space) for space in value["spaces"]),
        _as_point(value["at_m"]),
    )


def _adjacency_from(value: dict[str, Any]) -> Adjacency:
    kind = value["kind"]
    if kind not in {"wall", "door"}:
        raise ValueError("adjacency")
    opening_id = value["opening_id"]
    return Adjacency(
        str(value["a"]),
        str(value["b"]),
        kind,
        None if opening_id is None else str(opening_id),
    )


def _boundary_from(value: dict[str, Any]) -> Boundary:
    other = value["other"]
    return Boundary(
        str(value["space"]),
        None if other is None else str(other),
        _as_point(value["start"]),
        _as_point(value["end"]),
        bool(value["external"]),
    )


def _read_file(ifc: Any) -> Topology:
    _require_metre(ifc)
    north = _read_north(ifc)
    site, building, storey = _spatial_roots(ifc)
    spaces = _spaces_on_storey(ifc, storey)
    zones = [
        Zone(site.Name, "Site", None, _description_tags(site), (), None),
        Zone(building.Name, "Building", site.Name, _description_tags(building), (), None),
        Zone(storey.Name, "Storey", building.Name, _description_tags(storey), (), None),
    ]
    rings: dict[str, tuple[Point, ...]] = {}
    for space in spaces:
        ring, height = _space_body(space)
        rings[space.Name] = ring
        zones.append(Zone(space.Name, "Space", storey.Name, _description_tags(space), ring, height))
    names = [zone.name for zone in zones]
    if len(names) != len(set(names)):
        raise TopologyError("duplicate zone name")
    boundaries = _read_boundaries(ifc)
    openings = _read_openings(ifc, rings)
    return Topology(
        north,
        tuple(sorted(zones, key=lambda item: item.name)),
        _adjacencies(boundaries, openings),
        boundaries,
        openings,
    )


def _require_metre(ifc: Any) -> None:
    projects = ifc.by_type("IfcProject")
    if len(projects) != 1 or not projects[0].UnitsInContext:
        raise TopologyError("length unit other than metre")
    length_units = [
        unit for unit in projects[0].UnitsInContext.Units if getattr(unit, "UnitType", None) == "LENGTHUNIT"
    ]
    if len(length_units) != 1:
        raise TopologyError("length unit other than metre")
    unit = length_units[0]
    if not unit.is_a("IfcSIUnit") or unit.Name != "METRE" or unit.Prefix:
        raise TopologyError("length unit other than metre")


def _read_north(ifc: Any) -> Point:
    contexts = [
        ctx
        for ctx in ifc.by_type("IfcGeometricRepresentationContext")
        if ctx.ContextType == "Model" and not ctx.is_a("IfcGeometricRepresentationSubContext")
    ]
    if len(contexts) != 1:
        raise TopologyError("model context is missing")
    true_north = contexts[0].TrueNorth
    if true_north is None:
        return _NORTH
    ratios = [float(value) for value in true_north.DirectionRatios]
    if len(ratios) < 2:
        raise TopologyError("true north is missing")
    north = _point(ratios[0], ratios[1])
    if north == (0.0, 0.0):
        raise TopologyError("true north is missing")
    return north


def _aggregate_children(element: Any) -> list[Any]:
    children: list[Any] = []
    for rel in element.IsDecomposedBy:
        if rel.is_a("IfcRelAggregates"):
            children.extend(rel.RelatedObjects)
    return children


def _spatial_roots(ifc: Any) -> tuple[Any, Any, Any]:
    sites = ifc.by_type("IfcSite")
    buildings = ifc.by_type("IfcBuilding")
    storeys = ifc.by_type("IfcBuildingStorey")
    if len(sites) != 1 or len(buildings) != 1 or len(storeys) != 1:
        raise TopologyError("expected one site, one building, and one storey")
    site, building, storey = sites[0], buildings[0], storeys[0]
    if building not in _aggregate_children(site) or storey not in _aggregate_children(building):
        raise TopologyError("site, building, and storey are not aggregated")
    return site, building, storey


def _spaces_on_storey(ifc: Any, storey: Any) -> list[Any]:
    contained: list[Any] = []
    for rel in storey.ContainsElements:
        contained.extend(element for element in rel.RelatedElements if element.is_a("IfcSpace"))
    spaces = ifc.by_type("IfcSpace")
    if sorted(element.id() for element in contained) != sorted(element.id() for element in spaces):
        raise TopologyError("space is not on the storey")
    if not spaces:
        raise TopologyError("house has no spaces")
    return spaces


def _description_tags(element: Any) -> frozenset[str]:
    description = getattr(element, "Description", None)
    if description is None or not str(description).strip():
        return frozenset()
    tags = frozenset(str(description).split())
    _reject_unknown_tags(tags)
    return tags


def _world_translation(placement: Any) -> tuple[float, float, float]:
    if placement is None:
        return (0.0, 0.0, 0.0)
    parent = _world_translation(placement.PlacementRelTo)
    relative = placement.RelativePlacement
    axis = relative.Axis
    ref = relative.RefDirection
    if axis is not None and not _is_direction(axis, (0.0, 0.0, 1.0)):
        raise TopologyError("placement is rotated")
    if ref is not None and not _is_direction(ref, (1.0, 0.0, 0.0)):
        raise TopologyError("placement is rotated")
    coords = [float(value) for value in relative.Location.Coordinates]
    x = coords[0]
    y = coords[1] if len(coords) > 1 else 0.0
    z = coords[2] if len(coords) > 2 else 0.0
    return (parent[0] + x, parent[1] + y, parent[2] + z)


def _is_direction(direction: Any, expected: tuple[float, float, float]) -> bool:
    ratios = [float(value) for value in direction.DirectionRatios]
    if len(ratios) < 3:
        return False
    return all(abs(ratios[index] - expected[index]) <= 1e-6 for index in range(3))


def _space_body(space: Any) -> tuple[tuple[Point, ...], float]:
    solids = [
        item
        for representation in (space.Representation.Representations if space.Representation else [])
        for item in representation.Items
        if item.is_a("IfcExtrudedAreaSolid")
    ]
    if len(solids) != 1:
        raise TopologyError(f"{space.Name} has no extruded body")
    solid = solids[0]
    if not _is_direction(solid.ExtrudedDirection, (0.0, 0.0, 1.0)):
        raise TopologyError(f"{space.Name} extrusion is not +Z")
    if solid.Position and solid.Position.Axis and not _is_direction(solid.Position.Axis, (0.0, 0.0, 1.0)):
        raise TopologyError(f"{space.Name} extrusion is not +Z")
    profile = solid.SweptArea
    if not profile.is_a("IfcArbitraryClosedProfileDef") or not profile.OuterCurve.is_a("IfcPolyline"):
        raise TopologyError(f"{space.Name} profile is not a closed polyline")
    origin = _world_translation(space.ObjectPlacement)
    solid_origin = solid.Position.Location.Coordinates if solid.Position else (0.0, 0.0, 0.0)
    points = []
    for point in profile.OuterCurve.Points:
        coords = [float(value) for value in point.Coordinates]
        points.append(
            (
                coords[0] + origin[0] + float(solid_origin[0]),
                coords[1] + origin[1] + float(solid_origin[1]),
            )
        )
    return _normalize_ring(tuple(points)), _num(solid.Depth)


def _read_boundaries(ifc: Any) -> tuple[Boundary, ...]:
    grouped: dict[int, list[Any]] = {}
    for rel in ifc.by_type("IfcRelSpaceBoundary"):
        if rel.RelatedBuildingElement is None or not rel.RelatingSpace.is_a("IfcSpace"):
            raise TopologyError("space boundary has no wall")
        grouped.setdefault(rel.RelatedBuildingElement.id(), []).append(rel)
    found: list[Boundary] = []
    for rels in grouped.values():
        for rel in rels:
            flag = rel.InternalOrExternalBoundary
            if flag == "EXTERNAL":
                external = True
            elif flag == "INTERNAL":
                external = False
            else:
                raise TopologyError("boundary is not internal or external")
            partners = [item for item in rels if item.id() != rel.id()]
            if external and partners:
                raise TopologyError("exterior boundary is paired")
            if not external and len(partners) != 1:
                raise TopologyError("internal boundary has no neighbor")
            other = None if external else partners[0].RelatingSpace.Name
            start, end = _boundary_points(rel)
            found.append(Boundary(rel.RelatingSpace.Name, other, start, end, external))
    return tuple(sorted(found, key=lambda item: (item.space, item.start, item.end)))


def _boundary_points(rel: Any) -> tuple[Point, Point]:
    geometry = rel.ConnectionGeometry
    if geometry is None or not geometry.is_a("IfcConnectionCurveGeometry"):
        raise TopologyError("space boundary has no curve")
    curve = geometry.CurveOnRelatingElement
    if not curve.is_a("IfcPolyline") or len(curve.Points) != 2:
        raise TopologyError("space boundary has no curve")
    start = curve.Points[0].Coordinates
    end = curve.Points[1].Coordinates
    return _point(float(start[0]), float(start[1])), _point(float(end[0]), float(end[1]))


def _read_openings(ifc: Any, rings: dict[str, tuple[Point, ...]]) -> tuple[Opening, ...]:
    openings: list[Opening] = []
    for element in [*ifc.by_type("IfcWindow"), *ifc.by_type("IfcDoor")]:
        kind: OpeningKind = "window" if element.is_a("IfcWindow") else "door"
        host_name = element.ObjectType
        if not host_name or host_name not in rings:
            raise TopologyError(f"{element.Name} has no host space")
        at = _point(*_world_translation(element.ObjectPlacement)[:2])
        if kind == "window":
            spaces = (host_name,)
        else:
            spaces = _door_spaces(element)
            if host_name not in spaces:
                raise TopologyError(f"{element.Name} host is not on its wall")
        start, end = _nearest_edge(rings[host_name], at)
        openings.append(Opening(element.Name, kind, _outward(start, end), spaces, at))
    names = [opening.name for opening in openings]
    if any(name is None for name in names) or len(names) != len(set(names)):
        raise TopologyError("duplicate opening name")
    return tuple(sorted(openings, key=lambda item: item.name))


def _door_spaces(element: Any) -> tuple[str, ...]:
    wall = _filled_wall(element)
    spaces: list[str] = []
    for rel in element.file.by_type("IfcRelSpaceBoundary"):
        if rel.RelatedBuildingElement and rel.RelatedBuildingElement.id() == wall.id():
            spaces.append(rel.RelatingSpace.Name)
    unique = tuple(sorted(set(spaces)))
    if len(unique) != 2:
        raise TopologyError(f"{element.Name} does not join two spaces")
    return unique


def _filled_wall(element: Any) -> Any:
    opening = None
    for rel in element.file.by_type("IfcRelFillsElement"):
        if rel.RelatedBuildingElement.id() == element.id():
            opening = rel.RelatingOpeningElement
            break
    if opening is None:
        raise TopologyError(f"{element.Name} does not fill a wall")
    for rel in element.file.by_type("IfcRelVoidsElement"):
        if rel.RelatedOpeningElement.id() == opening.id():
            return rel.RelatingBuildingElement
    raise TopologyError(f"{element.Name} does not fill a wall")


def _write_file(
    model: Topology,
    path: Path,
    *,
    create_file: Any,
    create_entity: Any,
    assign_unit: Any,
    add_context: Any,
    assign_object: Any,
    compress: Any,
) -> None:
    house = path.stem
    ifc = create_file(version="IFC4")
    project = create_entity(ifc, ifc_class="IfcProject", name=house)
    assign_unit(
        ifc,
        length={"is_metric": True, "raw": "METRE"},
        area={"is_metric": True, "raw": "METRE"},
        volume={"is_metric": True, "raw": "METRE"},
    )
    model_context = add_context(ifc, context_type="Model")
    body = add_context(
        ifc,
        context_type="Model",
        context_identifier="Body",
        target_view="MODEL_VIEW",
        parent=model_context,
    )
    model_context.TrueNorth = ifc.create_entity("IfcDirection", DirectionRatios=(0.0, 1.0, 0.0))
    site = create_entity(ifc, ifc_class="IfcSite", name="site")
    building = create_entity(ifc, ifc_class="IfcBuilding", name="house")
    storey = create_entity(ifc, ifc_class="IfcBuildingStorey", name="ground")
    storey.Elevation = 0.0
    assign_object(ifc, products=[site], relating_object=project)
    assign_object(ifc, products=[building], relating_object=site)
    assign_object(ifc, products=[storey], relating_object=building)
    site.ObjectPlacement = _placement(ifc, None, (0.0, 0.0))
    building.ObjectPlacement = _placement(ifc, site.ObjectPlacement, (0.0, 0.0))
    storey.ObjectPlacement = _placement(ifc, building.ObjectPlacement, (0.0, 0.0))
    for rel in ifc.by_type("IfcRelAggregates"):
        rel.Name = f"agg-{rel.RelatingObject.Name}"
    zones = {zone.name: zone for zone in model.zones if zone.kind == "Space"}
    space_elements: dict[str, Any] = {}
    for name in sorted(zones):
        zone = zones[name]
        if zone.height_m is None:
            raise TopologyError(f"{name} has no extruded body")
        element = create_entity(ifc, ifc_class="IfcSpace", name=name, predefined_type="SPACE")
        element.Description = " ".join(sorted(zone.tags)) if zone.tags else None
        element.ObjectPlacement = _placement(ifc, storey.ObjectPlacement, (0.0, 0.0))
        _assign_body(ifc, element, zone.footprint, zone.height_m, body)
        space_elements[name] = element
    walls = _write_walls(ifc, model, storey, create_entity)
    _write_boundaries(ifc, model, space_elements, walls, house, compress)
    elements = _write_openings(ifc, model, walls, storey, house, compress, create_entity)
    ifc.create_entity(
        "IfcRelContainedInSpatialStructure",
        GlobalId=_guid(compress, house, "contain-ground"),
        OwnerHistory=None,
        Name="contain-ground",
        Description=None,
        RelatedElements=[*space_elements.values(), *walls.values(), *elements],
        RelatingStructure=storey,
    )
    _stamp_named_roots(ifc, house, compress)
    path.parent.mkdir(parents=True, exist_ok=True)
    ifc.header.file_name.name = path.name
    ifc.header.file_name.time_stamp = _HEADER_STAMP
    ifc.write(str(path))


def _owner_history(ifc: Any) -> Any:
    person = ifc.create_entity(
        "IfcPerson",
        Identification="pattern-language",
        FamilyName="Catalog",
        GivenName="Pattern",
    )
    organisation = ifc.create_entity(
        "IfcOrganization",
        Identification="pattern-language",
        Name="Pattern Language",
    )
    user = ifc.create_entity(
        "IfcPersonAndOrganization",
        ThePerson=person,
        TheOrganization=organisation,
    )
    application = ifc.create_entity(
        "IfcApplication",
        ApplicationDeveloper=organisation,
        Version="0.0.0",
        ApplicationFullName="pattern-language",
        ApplicationIdentifier="pattern-language",
    )
    return ifc.create_entity(
        "IfcOwnerHistory",
        OwningUser=user,
        OwningApplication=application,
        State=None,
        ChangeAction="ADDED",
        LastModifiedDate=_OWNER_STAMP,
        LastModifyingUser=user,
        LastModifyingApplication=application,
        CreationDate=_OWNER_STAMP,
    )


def _guid(compress: Any, house: str, name: str) -> str:
    return compress(uuid.uuid5(_GUID_NAMESPACE, f"{house}/{name}").hex)


def _stamp_named_roots(ifc: Any, house: str, compress: Any) -> None:
    """Assign one owner history after the API calls, so they do not stamp the clock."""
    owner = _owner_history(ifc)
    names: list[str] = []
    for entity in ifc:
        if not entity.is_a("IfcRoot"):
            continue
        if not entity.Name:
            raise TopologyError(f"unnamed {entity.is_a()}")
        names.append(entity.Name)
        entity.OwnerHistory = owner
        entity.GlobalId = _guid(compress, house, entity.Name)
    if len(names) != len(set(names)):
        raise TopologyError("duplicate IFC name")
    owner.CreationDate = _OWNER_STAMP
    owner.LastModifiedDate = _OWNER_STAMP
    for history in list(ifc.by_type("IfcOwnerHistory")):
        if history != owner:
            ifc.remove(history)


def _placement(ifc: Any, relative: Any, xy: Point) -> Any:
    point = ifc.create_entity("IfcCartesianPoint", Coordinates=(float(xy[0]), float(xy[1]), 0.0))
    axis = ifc.create_entity("IfcAxis2Placement3D", Location=point, Axis=None, RefDirection=None)
    return ifc.create_entity("IfcLocalPlacement", PlacementRelTo=relative, RelativePlacement=axis)


def _assign_body(ifc: Any, element: Any, ring: tuple[Point, ...], height: float, body: Any) -> None:
    points = [
        ifc.create_entity("IfcCartesianPoint", Coordinates=(float(x), float(y))) for x, y in (*ring, ring[0])
    ]
    polyline = ifc.create_entity("IfcPolyline", Points=points)
    profile = ifc.create_entity(
        "IfcArbitraryClosedProfileDef",
        ProfileType="AREA",
        ProfileName=None,
        OuterCurve=polyline,
    )
    origin = ifc.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0))
    position = ifc.create_entity(
        "IfcAxis2Placement3D",
        Location=origin,
        Axis=ifc.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0)),
        RefDirection=ifc.create_entity("IfcDirection", DirectionRatios=(1.0, 0.0, 0.0)),
    )
    solid = ifc.create_entity(
        "IfcExtrudedAreaSolid",
        SweptArea=profile,
        Position=position,
        ExtrudedDirection=ifc.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0)),
        Depth=float(height),
    )
    shape = ifc.create_entity(
        "IfcShapeRepresentation",
        ContextOfItems=body,
        RepresentationIdentifier="Body",
        RepresentationType="SweptSolid",
        Items=[solid],
    )
    element.Representation = ifc.create_entity(
        "IfcProductDefinitionShape",
        Name=None,
        Description=None,
        Representations=[shape],
    )


def _segment_key(start: Point, end: Point) -> tuple[Point, Point]:
    return tuple(sorted((start, end)))


def _wall_name(group: list[Boundary]) -> str:
    spaces = sorted({item.space for item in group} | {item.other for item in group if item.other})
    start, end = _segment_key(group[0].start, group[0].end)
    label = "-".join(spaces)
    return f"wall-{label}-{start[0]:.3f}-{start[1]:.3f}-{end[0]:.3f}-{end[1]:.3f}"


def _write_walls(
    ifc: Any,
    model: Topology,
    storey: Any,
    create_entity: Any,
) -> dict[tuple[Point, Point], Any]:
    groups: dict[tuple[Point, Point], list[Boundary]] = {}
    for boundary in model.boundaries:
        groups.setdefault(_segment_key(boundary.start, boundary.end), []).append(boundary)
    walls: dict[tuple[Point, Point], Any] = {}
    for key, group in groups.items():
        _require_boundary_group(group)
        wall = create_entity(ifc, ifc_class="IfcWall", name=_wall_name(group))
        wall.ObjectPlacement = _placement(ifc, storey.ObjectPlacement, (0.0, 0.0))
        walls[key] = wall
    return walls


def _require_boundary_group(group: list[Boundary]) -> None:
    if len(group) == 1:
        boundary = group[0]
        if boundary.other is not None or not boundary.external:
            raise TopologyError("exterior boundary is paired")
        return
    if len(group) == 2:
        first, second = group
        paired = first.other == second.space and second.other == first.space
        if not paired or first.external or second.external:
            raise TopologyError("internal boundary pair does not match")
        return
    raise TopologyError("boundary segment has more than two sides")


def _write_boundaries(
    ifc: Any,
    model: Topology,
    spaces: dict[str, Any],
    walls: dict[tuple[Point, Point], Any],
    house: str,
    compress: Any,
) -> None:
    for index, boundary in enumerate(model.boundaries):
        name = f"boundary-{boundary.space}-{index}"
        start = ifc.create_entity(
            "IfcCartesianPoint",
            Coordinates=(float(boundary.start[0]), float(boundary.start[1]), 0.0),
        )
        end = ifc.create_entity(
            "IfcCartesianPoint",
            Coordinates=(float(boundary.end[0]), float(boundary.end[1]), 0.0),
        )
        curve = ifc.create_entity("IfcPolyline", Points=[start, end])
        geometry = ifc.create_entity(
            "IfcConnectionCurveGeometry",
            CurveOnRelatingElement=curve,
            CurveOnRelatedElement=None,
        )
        ifc.create_entity(
            "IfcRelSpaceBoundary",
            GlobalId=_guid(compress, house, name),
            OwnerHistory=None,
            Name=name,
            Description=None,
            RelatingSpace=spaces[boundary.space],
            RelatedBuildingElement=walls[_segment_key(boundary.start, boundary.end)],
            ConnectionGeometry=geometry,
            PhysicalOrVirtualBoundary="PHYSICAL",
            InternalOrExternalBoundary="EXTERNAL" if boundary.external else "INTERNAL",
        )


def _host_space(opening: Opening, zones: dict[str, Zone]) -> str:
    matches: list[str] = []
    for name in opening.spaces:
        start, end = _nearest_edge(zones[name].footprint, opening.at_m)
        if _outward(start, end) == opening.orientation:
            matches.append(name)
    if len(matches) != 1:
        raise TopologyError(f"{opening.name} host is ambiguous")
    return matches[0]


def _write_openings(
    ifc: Any,
    model: Topology,
    walls: dict[tuple[Point, Point], Any],
    storey: Any,
    house: str,
    compress: Any,
    create_entity: Any,
) -> list[Any]:
    zones = {zone.name: zone for zone in model.zones if zone.kind == "Space"}
    written: list[Any] = []
    for opening in model.openings:
        host = _host_space(opening, zones)
        boundary = _boundary_at(model.boundaries, host, opening.at_m)
        if opening.kind == "door":
            if boundary.other is None or tuple(sorted((host, boundary.other))) != tuple(sorted(opening.spaces)):
                raise TopologyError(f"{opening.name} does not join two spaces")
        elif opening.spaces != (host,):
            raise TopologyError(f"{opening.name} has no host space")
        ifc_class = "IfcWindow" if opening.kind == "window" else "IfcDoor"
        element = create_entity(ifc, ifc_class=ifc_class, name=opening.name)
        element.ObjectType = host
        element.ObjectPlacement = _placement(ifc, storey.ObjectPlacement, opening.at_m)
        wall = walls[_segment_key(boundary.start, boundary.end)]
        opening_name = f"opening-{opening.name}"
        feature = create_entity(ifc, ifc_class="IfcOpeningElement", name=opening_name)
        feature.ObjectPlacement = _placement(ifc, storey.ObjectPlacement, opening.at_m)
        void_name = f"void-{opening.name}"
        ifc.create_entity(
            "IfcRelVoidsElement",
            GlobalId=_guid(compress, house, void_name),
            OwnerHistory=None,
            Name=void_name,
            Description=None,
            RelatingBuildingElement=wall,
            RelatedOpeningElement=feature,
        )
        fill_name = f"fill-{opening.name}"
        ifc.create_entity(
            "IfcRelFillsElement",
            GlobalId=_guid(compress, house, fill_name),
            OwnerHistory=None,
            Name=fill_name,
            Description=None,
            RelatingOpeningElement=feature,
            RelatedBuildingElement=element,
        )
        written.append(element)
    return written
