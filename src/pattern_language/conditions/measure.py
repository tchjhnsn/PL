"""Shared readings for pure checks.

Area, hull, depth, and door distance are arithmetic on the frozen graph.
This module names no check id and no pattern number.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from pattern_language.conditions.evidence import CheckError
from pattern_language.topology import Boundary, Point, Topology, Zone

_ON_SEGMENT_M = 0.001


@dataclass(frozen=True, slots=True)
class Entrance:
    street: str
    path: tuple[str, ...]
    arrival: str


def require_number(params: Mapping[str, Any], key: str, check: str) -> float:
    """Read one numeric param. Raise CheckError when it is missing or not a number."""
    if key not in params or isinstance(params[key], bool) or not isinstance(params[key], (int, float)):
        raise CheckError(f"bad param: {check} {key}")
    return float(params[key])


def dec(value: float) -> str:
    """Render a measurement. Infinity stays the token ``inf``."""
    if math.isinf(value):
        return "inf"
    return format(value, ".3f")


def flag(value: bool) -> str:
    """Render a boolean outcome as ``1.000`` or ``0.000``."""
    return "1.000" if value else "0.000"


def building_center(topology: Topology) -> str:
    """Name of the unique zone of kind Building. Raise CheckError otherwise."""
    names = [zone.name for zone in topology.zones if zone.kind == "Building"]
    if len(names) != 1:
        raise CheckError(f"building count: {len(names)}")
    return names[0]


def spaces_under(topology: Topology, center: str) -> tuple[Zone, ...]:
    """Space zones whose parent chain reaches ``center``."""
    by_name = {zone.name: zone for zone in topology.zones}

    def reaches(zone: Zone) -> bool:
        seen: set[str] = set()
        current = zone
        while current.parent is not None:
            if current.parent == center:
                return True
            if current.parent in seen:
                return False
            seen.add(current.parent)
            parent = by_name.get(current.parent)
            if parent is None:
                return False
            current = parent
        return False

    return tuple(zone for zone in topology.zones if zone.kind == "Space" and reaches(zone))


def equator_direction(
    north: tuple[float, float],
    latitude_deg: float,
) -> tuple[float, float] | None:
    """Unit vector toward the equator. None when latitude_deg is 0."""
    if latitude_deg == 0:
        return None
    length = math.hypot(north[0], north[1])
    if length == 0:
        raise CheckError("north has no direction")
    sign = -1.0 if latitude_deg > 0 else 1.0
    return (north[0] / length * sign, north[1] / length * sign)


def direction_dot(point: Point, reference: Point, direction: Point) -> float:
    """Dot product of ``point - reference`` with ``direction``."""
    return (point[0] - reference[0]) * direction[0] + (point[1] - reference[1]) * direction[1]


def polygon_area(ring: Sequence[Point]) -> float:
    """Absolute shoelace area of a ring."""
    return abs(_shoelace_twice(ring)) / 2.0


def polygon_centroid(ring: Sequence[Point]) -> Point:
    """Shoelace centroid of a ring."""
    twice = _shoelace_twice(ring)
    if twice == 0:
        raise CheckError("ring has no area")
    cx = 0.0
    cy = 0.0
    count = len(ring)
    for index in range(count):
        x1, y1 = ring[index]
        x2, y2 = ring[(index + 1) % count]
        cross = x1 * y2 - x2 * y1
        cx += (x1 + x2) * cross
        cy += (y1 + y2) * cross
    return (cx / (3.0 * twice), cy / (3.0 * twice))


def mean_centroid(zones: Sequence[Zone]) -> Point:
    """Unweighted mean of footprint centroids."""
    centroids = [polygon_centroid(zone.footprint) for zone in zones]
    count = float(len(centroids))
    return (
        sum(item[0] for item in centroids) / count,
        sum(item[1] for item in centroids) / count,
    )


def hull_area(points: Sequence[Point]) -> float:
    """Area of the convex hull. Zero when the hull has no area."""
    hull = _convex_hull(points)
    if len(hull) < 3:
        return 0.0
    return polygon_area(hull)


def boundaries_for(topology: Topology, space: str, *, external: bool) -> tuple[Boundary, ...]:
    """Boundary segments of ``space`` with the requested external flag."""
    return tuple(
        item
        for item in topology.boundaries
        if item.space == space and item.external is external
    )


def room_depth(zone: Zone, segments: Sequence[Boundary]) -> float:
    """Maximum, over footprint vertices, of the minimum distance to ``segments``.

    No segment means infinite depth.
    """
    if not segments:
        return math.inf
    worst = 0.0
    for vertex in zone.footprint:
        nearest = min(_distance_to_segment(vertex, segment.start, segment.end) for segment in segments)
        if nearest > worst:
            worst = nearest
    return worst


def balcony_depth(zone: Zone, segments: Sequence[Boundary]) -> float:
    """Shallowest footprint vertex that does not lie on an internal segment.

    No internal segment, or no off-segment vertex, means depth 0.
    """
    if not segments:
        return 0.0
    off_segment: list[float] = []
    for vertex in zone.footprint:
        nearest = min(_distance_to_segment(vertex, segment.start, segment.end) for segment in segments)
        if nearest < _ON_SEGMENT_M:
            continue
        off_segment.append(nearest)
    if not off_segment:
        return 0.0
    return min(off_segment)


def door_graph(topology: Topology, names: set[str]) -> dict[str, tuple[str, ...]]:
    """Undirected door graph. An edge is a door opening whose spaces both exist."""
    linked: dict[str, set[str]] = {name: set() for name in names}
    for opening in topology.openings:
        if opening.kind != "door" or len(opening.spaces) != 2:
            continue
        left, right = opening.spaces
        if left in linked and right in linked and left != right:
            linked[left].add(right)
            linked[right].add(left)
    return {name: tuple(sorted(neighbors)) for name, neighbors in linked.items()}


def distances_from(graph: Mapping[str, tuple[str, ...]], origin: str) -> dict[str, int]:
    """Breadth-first door distances from ``origin``."""
    if origin not in graph:
        return {}
    distances = {origin: 0}
    queue = [origin]
    while queue:
        node = queue.pop(0)
        for neighbor in graph[node]:
            if neighbor in distances:
                continue
            distances[neighbor] = distances[node] + 1
            queue.append(neighbor)
    return distances


def entrance(topology: Topology, center: str | None = None) -> Entrance | None:
    """Shortest door-graph path from a street space to an arrival.

    A space tagged street, transition, or outdoor is not an arrival.
    Ties break by arrival name, then by the path tuple.
    """
    if center is None:
        center = building_center(topology)
    zones = spaces_under(topology, center)
    by_name = {zone.name: zone for zone in zones}
    graph = door_graph(topology, set(by_name))
    streets = sorted(name for name, zone in by_name.items() if "street" in zone.tags)
    if not streets:
        return None
    parent: dict[str, str | None] = {name: None for name in streets}
    queue = list(streets)
    while queue:
        node = queue.pop(0)
        for neighbor in graph.get(node, ()):
            if neighbor in parent:
                continue
            parent[neighbor] = node
            queue.append(neighbor)
    found: list[tuple[int, str, tuple[str, ...]]] = []
    for name in parent:
        tags = by_name[name].tags
        if {"street", "transition", "outdoor"} & set(tags):
            continue
        path = _path_from(name, parent)
        found.append((len(path), name, path))
    if not found:
        return None
    found.sort()
    _length, arrival, path = found[0]
    return Entrance(street=path[0], path=path, arrival=arrival)


def _shoelace_twice(ring: Sequence[Point]) -> float:
    total = 0.0
    count = len(ring)
    for index in range(count):
        x1, y1 = ring[index]
        x2, y2 = ring[(index + 1) % count]
        total += x1 * y2 - x2 * y1
    return total


def _convex_hull(points: Sequence[Point]) -> tuple[Point, ...]:
    """Andrew's monotone chain. Collinear points stay off the hull."""
    unique = sorted(set(points))
    if len(unique) <= 1:
        return tuple(unique)

    def cross(origin: Point, left: Point, right: Point) -> float:
        return (left[0] - origin[0]) * (right[1] - origin[1]) - (left[1] - origin[1]) * (
            right[0] - origin[0]
        )

    lower: list[Point] = []
    for point in unique:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)
    upper: list[Point] = []
    for point in reversed(unique):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    return tuple(lower[:-1] + upper[:-1])


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


def _path_from(name: str, parent: Mapping[str, str | None]) -> tuple[str, ...]:
    nodes: list[str] = []
    current: str | None = name
    while current is not None:
        nodes.append(current)
        current = parent[current]
    nodes.reverse()
    return tuple(nodes)
