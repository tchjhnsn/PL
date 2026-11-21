"""Readback of the two U3 houses and one witness per computed pattern."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from pattern_language.catalog import load_catalog
from pattern_language.topology import (
    Adjacency,
    Boundary,
    Opening,
    Topology,
    TopologyError,
    Zone,
    from_json,
    read_topology,
    to_json,
    write_fixtures,
    write_ifc,
)

COMPUTED = (105, 106, 107, 112, 127, 128, 130, 159, 167, 190)
PASS_RINGS = {
    "street": ((0.0, -2.0), (8.0, -2.0), (8.0, 0.0), (0.0, 0.0)),
    "court": ((0.0, 0.0), (8.0, 0.0), (8.0, 4.0), (0.0, 4.0)),
    "hall": ((0.0, 4.0), (4.0, 4.0), (4.0, 8.0), (0.0, 8.0)),
    "living": ((4.0, 4.0), (8.0, 4.0), (8.0, 8.0), (4.0, 8.0)),
    "bedroom": ((4.0, 8.0), (8.0, 8.0), (8.0, 12.0), (4.0, 12.0)),
    "balcony": ((8.0, 8.0), (10.0, 8.0), (10.0, 12.0), (8.0, 12.0)),
}
FAIL_RINGS = {
    "street": ((0.0, -2.0), (8.0, -2.0), (8.0, 0.0), (0.0, 0.0)),
    "corridor": ((0.0, 0.0), (8.0, 0.0), (8.0, 2.0), (0.0, 2.0)),
    "west-flank": ((0.0, 2.0), (4.0, 2.0), (4.0, 12.0), (0.0, 12.0)),
    "bedroom": ((4.0, 2.0), (8.0, 2.0), (8.0, 12.0), (4.0, 12.0)),
    "east-flank": ((8.0, 2.0), (11.0, 2.0), (11.0, 12.0), (8.0, 12.0)),
    "dayroom": ((0.0, 12.0), (6.0, 12.0), (6.0, 15.0), (0.0, 15.0)),
    "balcony": ((-1.0, 12.0), (0.0, 12.0), (0.0, 15.0), (-1.0, 15.0)),
    "court": ((0.0, 15.0), (8.0, 15.0), (8.0, 16.0), (2.0, 16.0), (2.0, 22.0), (0.0, 22.0)),
}


def _space(
    name: str,
    tags: set[str],
    ring: tuple[tuple[float, float], ...],
    height: float,
    *,
    storey: str = "ground",
    floor_elevation_m: float = 0.0,
) -> Zone:
    return Zone(name, "Space", storey, frozenset(tags), ring, height, floor_elevation_m)


def _boundary(
    space: str,
    other: str | None,
    start: tuple[float, float],
    end: tuple[float, float],
) -> Boundary:
    return Boundary(space, other, start, end, other is None)


def _topology(
    zones: list[Zone],
    adjacencies: list[Adjacency],
    boundaries: list[Boundary],
    openings: list[Opening],
) -> Topology:
    return Topology(
        (0.0, 1.0),
        tuple(sorted(zones, key=lambda zone: zone.name)),
        tuple(sorted(adjacencies, key=lambda item: (item.a, item.b, item.opening_id or ""))),
        tuple(sorted(boundaries, key=lambda item: (item.space, item.start, item.end))),
        tuple(sorted(openings, key=lambda item: item.name)),
    )


def _structural(*storeys: tuple[str, float]) -> list[Zone]:
    zones = [
        Zone("site", "Site", None, frozenset(), (), None, None),
        Zone("house", "Building", "site", frozenset(), (), None, None),
    ]
    levels = storeys or (("ground", 0.0),)
    for name, elev in levels:
        zones.append(Zone(name, "Storey", "house", frozenset(), (), None, elev))
    return zones


def expected_pass() -> Topology:
    zones = _structural(("ground", 0.0), ("upper", 3.0)) + [
        _space("street", {"street"}, PASS_RINGS["street"], 3.0),
        _space("court", {"outdoor", "transition"}, PASS_RINGS["court"], 3.0),
        _space("hall", {"room", "public", "occupied"}, PASS_RINGS["hall"], 2.4),
        _space("living", {"living", "semi-private", "daytime", "occupied"}, PASS_RINGS["living"], 3.0),
        _space(
            "bedroom",
            {"room", "private", "occupied"},
            PASS_RINGS["bedroom"],
            2.7,
            storey="upper",
            floor_elevation_m=3.0,
        ),
        _space(
            "balcony",
            {"balcony", "outdoor"},
            PASS_RINGS["balcony"],
            3.0,
            storey="upper",
            floor_elevation_m=3.0,
        ),
    ]
    adjacencies = [
        Adjacency("balcony", "bedroom", "door", "bedroom-balcony"),
        Adjacency("bedroom", "living", "door", "living-bedroom"),
        Adjacency("court", "hall", "door", "main-door"),
        Adjacency("court", "living", "wall", None),
        Adjacency("court", "street", "door", "approach-door"),
        Adjacency("hall", "living", "door", "hall-living"),
    ]
    boundaries = [
        _boundary("street", None, (0.0, -2.0), (8.0, -2.0)),
        _boundary("street", None, (8.0, -2.0), (8.0, 0.0)),
        _boundary("street", "court", (8.0, 0.0), (0.0, 0.0)),
        _boundary("street", None, (0.0, 0.0), (0.0, -2.0)),
        _boundary("court", "street", (0.0, 0.0), (8.0, 0.0)),
        _boundary("court", None, (8.0, 0.0), (8.0, 4.0)),
        _boundary("court", "living", (8.0, 4.0), (4.0, 4.0)),
        _boundary("court", "hall", (4.0, 4.0), (0.0, 4.0)),
        _boundary("court", None, (0.0, 4.0), (0.0, 0.0)),
        _boundary("hall", "court", (0.0, 4.0), (4.0, 4.0)),
        _boundary("hall", "living", (4.0, 4.0), (4.0, 8.0)),
        _boundary("hall", None, (4.0, 8.0), (0.0, 8.0)),
        _boundary("hall", None, (0.0, 8.0), (0.0, 4.0)),
        _boundary("living", "court", (4.0, 4.0), (8.0, 4.0)),
        _boundary("living", None, (8.0, 4.0), (8.0, 8.0)),
        _boundary("living", "bedroom", (8.0, 8.0), (4.0, 8.0)),
        _boundary("living", "hall", (4.0, 8.0), (4.0, 4.0)),
        _boundary("bedroom", "living", (4.0, 8.0), (8.0, 8.0)),
        _boundary("bedroom", "balcony", (8.0, 8.0), (8.0, 12.0)),
        _boundary("bedroom", None, (8.0, 12.0), (4.0, 12.0)),
        _boundary("bedroom", None, (4.0, 12.0), (4.0, 8.0)),
        _boundary("balcony", None, (8.0, 8.0), (10.0, 8.0)),
        _boundary("balcony", None, (10.0, 8.0), (10.0, 12.0)),
        _boundary("balcony", None, (10.0, 12.0), (8.0, 12.0)),
        _boundary("balcony", "bedroom", (8.0, 12.0), (8.0, 8.0)),
    ]
    openings = [
        Opening("approach-door", "door", "south", ("court", "street"), (4.0, 0.0)),
        Opening("main-door", "door", "south", ("court", "hall"), (3.0, 4.0)),
        Opening("hall-living", "door", "east", ("hall", "living"), (4.0, 6.0)),
        Opening("living-bedroom", "door", "north", ("bedroom", "living"), (6.0, 8.0)),
        Opening("bedroom-balcony", "door", "east", ("balcony", "bedroom"), (8.0, 10.0)),
        Opening("hall-south", "window", "south", ("hall",), (1.0, 4.0)),
        Opening("hall-west", "window", "west", ("hall",), (0.0, 6.0)),
        Opening("living-south", "window", "south", ("living",), (6.0, 4.0)),
        Opening("living-east", "window", "east", ("living",), (8.0, 6.0)),
        Opening("bedroom-north", "window", "north", ("bedroom",), (6.0, 12.0)),
        Opening("bedroom-west", "window", "west", ("bedroom",), (4.0, 10.0)),
    ]
    return _topology(zones, adjacencies, boundaries, openings)


def expected_fail() -> Topology:
    zones = _structural(("ground", 0.0), ("upper", 3.0)) + [
        _space("street", {"street"}, FAIL_RINGS["street"], 2.4),
        _space("corridor", {"corridor"}, FAIL_RINGS["corridor"], 2.4),
        _space("west-flank", set(), FAIL_RINGS["west-flank"], 2.4),
        _space("bedroom", {"room", "private", "occupied"}, FAIL_RINGS["bedroom"], 2.4),
        _space("east-flank", set(), FAIL_RINGS["east-flank"], 2.4),
        _space("dayroom", {"public", "daytime", "occupied"}, FAIL_RINGS["dayroom"], 2.4),
        _space(
            "balcony",
            {"balcony", "outdoor"},
            FAIL_RINGS["balcony"],
            2.4,
            storey="upper",
            floor_elevation_m=3.0,
        ),
        _space("court", {"outdoor"}, FAIL_RINGS["court"], 3.0),
    ]
    adjacencies = [
        Adjacency("balcony", "dayroom", "door", "dayroom-balcony"),
        Adjacency("bedroom", "corridor", "door", "corridor-bedroom"),
        Adjacency("bedroom", "dayroom", "door", "bedroom-dayroom"),
        Adjacency("bedroom", "east-flank", "wall", None),
        Adjacency("bedroom", "west-flank", "wall", None),
        Adjacency("corridor", "street", "door", "main-door"),
        Adjacency("corridor", "west-flank", "wall", None),
        Adjacency("court", "dayroom", "wall", None),
        Adjacency("dayroom", "west-flank", "wall", None),
    ]
    boundaries = [
        _boundary("street", None, (0.0, -2.0), (8.0, -2.0)),
        _boundary("street", None, (8.0, -2.0), (8.0, 0.0)),
        _boundary("street", "corridor", (8.0, 0.0), (0.0, 0.0)),
        _boundary("street", None, (0.0, 0.0), (0.0, -2.0)),
        _boundary("corridor", "street", (0.0, 0.0), (8.0, 0.0)),
        _boundary("corridor", None, (8.0, 0.0), (8.0, 2.0)),
        _boundary("corridor", "bedroom", (8.0, 2.0), (4.0, 2.0)),
        _boundary("corridor", "west-flank", (4.0, 2.0), (0.0, 2.0)),
        _boundary("corridor", None, (0.0, 2.0), (0.0, 0.0)),
        _boundary("west-flank", "corridor", (0.0, 2.0), (4.0, 2.0)),
        _boundary("west-flank", "bedroom", (4.0, 2.0), (4.0, 12.0)),
        _boundary("west-flank", "dayroom", (4.0, 12.0), (0.0, 12.0)),
        _boundary("west-flank", None, (0.0, 12.0), (0.0, 2.0)),
        _boundary("bedroom", "corridor", (4.0, 2.0), (8.0, 2.0)),
        _boundary("bedroom", "east-flank", (8.0, 2.0), (8.0, 12.0)),
        _boundary("bedroom", None, (8.0, 12.0), (6.0, 12.0)),
        _boundary("bedroom", "dayroom", (6.0, 12.0), (4.0, 12.0)),
        _boundary("bedroom", "west-flank", (4.0, 12.0), (4.0, 2.0)),
        _boundary("east-flank", None, (8.0, 2.0), (11.0, 2.0)),
        _boundary("east-flank", None, (11.0, 2.0), (11.0, 12.0)),
        _boundary("east-flank", None, (11.0, 12.0), (8.0, 12.0)),
        _boundary("east-flank", "bedroom", (8.0, 12.0), (8.0, 2.0)),
        _boundary("dayroom", "west-flank", (0.0, 12.0), (4.0, 12.0)),
        _boundary("dayroom", "bedroom", (4.0, 12.0), (6.0, 12.0)),
        _boundary("dayroom", None, (6.0, 12.0), (6.0, 15.0)),
        _boundary("dayroom", "court", (6.0, 15.0), (0.0, 15.0)),
        _boundary("dayroom", "balcony", (0.0, 15.0), (0.0, 12.0)),
        _boundary("balcony", None, (-1.0, 12.0), (0.0, 12.0)),
        _boundary("balcony", "dayroom", (0.0, 12.0), (0.0, 15.0)),
        _boundary("balcony", None, (0.0, 15.0), (-1.0, 15.0)),
        _boundary("balcony", None, (-1.0, 15.0), (-1.0, 12.0)),
        _boundary("court", "dayroom", (0.0, 15.0), (6.0, 15.0)),
        _boundary("court", None, (6.0, 15.0), (8.0, 15.0)),
        _boundary("court", None, (8.0, 15.0), (8.0, 16.0)),
        _boundary("court", None, (8.0, 16.0), (2.0, 16.0)),
        _boundary("court", None, (2.0, 16.0), (2.0, 22.0)),
        _boundary("court", None, (2.0, 22.0), (0.0, 22.0)),
        _boundary("court", None, (0.0, 22.0), (0.0, 15.0)),
    ]
    openings = [
        Opening("main-door", "door", "south", ("corridor", "street"), (4.0, 0.0)),
        Opening("corridor-bedroom", "door", "north", ("bedroom", "corridor"), (6.0, 2.0)),
        Opening("bedroom-dayroom", "door", "north", ("bedroom", "dayroom"), (5.0, 12.0)),
        Opening("dayroom-balcony", "door", "west", ("balcony", "dayroom"), (0.0, 13.0)),
        Opening("bedroom-north", "window", "north", ("bedroom",), (7.0, 12.0)),
        Opening("dayroom-north", "window", "north", ("dayroom",), (3.0, 15.0)),
        Opening("dayroom-west", "window", "west", ("dayroom",), (0.0, 14.0)),
    ]
    return _topology(zones, adjacencies, boundaries, openings)


def _zone(graph: Topology, name: str) -> Zone:
    found = [zone for zone in graph.zones if zone.name == name]
    assert len(found) == 1
    return found[0]


def _opening(graph: Topology, name: str) -> Opening:
    found = [opening for opening in graph.openings if opening.name == name]
    assert len(found) == 1
    return found[0]


def _centroid(ring: tuple[tuple[float, float], ...]) -> tuple[float, float]:
    twice = 0.0
    cx = 0.0
    cy = 0.0
    for start, end in zip(ring, ring[1:] + ring[:1]):
        cross = start[0] * end[1] - end[0] * start[1]
        twice += cross
        cx += (start[0] + end[0]) * cross
        cy += (start[1] + end[1]) * cross
    return cx / (3.0 * twice), cy / (3.0 * twice)


def _distances(pairs: list[tuple[str, str]], start: str) -> dict[str, int]:
    neighbors: dict[str, set[str]] = {}
    for left, right in pairs:
        neighbors.setdefault(left, set()).add(right)
        neighbors.setdefault(right, set()).add(left)
    dist = {start: 0}
    queue = [start]
    while queue:
        current = queue.pop(0)
        for nxt in neighbors.get(current, ()):
            if nxt not in dist:
                dist[nxt] = dist[current] + 1
                queue.append(nxt)
    return dist


def _door_pairs(graph: Topology) -> list[tuple[str, str]]:
    return [opening.spaces for opening in graph.openings if opening.kind == "door"]


def _adjacent_pairs(graph: Topology) -> list[tuple[str, str]]:
    return [(item.a, item.b) for item in graph.adjacencies]


def _is_rectangle(ring: tuple[tuple[float, float], ...]) -> bool:
    xs = {point[0] for point in ring}
    ys = {point[1] for point in ring}
    return len(ring) == 4 and len(xs) == 2 and len(ys) == 2


def _span(ring: tuple[tuple[float, float], ...]) -> tuple[float, float]:
    xs = [point[0] for point in ring]
    ys = [point[1] for point in ring]
    return max(xs) - min(xs), max(ys) - min(ys)


def _full_exterior_side(graph: Topology, name: str) -> bool:
    ring = _zone(graph, name).footprint
    edges = set(zip(ring, ring[1:] + ring[:1]))
    exterior = {
        (item.start, item.end) for item in graph.boundaries if item.space == name and item.external
    }
    return bool(edges & exterior)


def _window_facings(graph: Topology, name: str) -> set[str]:
    return {
        opening.orientation
        for opening in graph.openings
        if opening.kind == "window" and opening.spaces == (name,)
    }


def _occupied_heights(graph: Topology) -> dict[str, float]:
    return {
        zone.name: zone.height_m
        for zone in graph.zones
        if zone.height_m is not None and "occupied" in zone.tags
    }


@pytest.fixture(scope="module")
def pass_graph(repo_root: Path) -> Topology:
    return read_topology(repo_root / "fixtures" / "pass-house.ifc")


@pytest.fixture(scope="module")
def fail_graph(repo_root: Path) -> Topology:
    return read_topology(repo_root / "fixtures" / "fail-house.ifc")


def test_pass_house_readback(pass_graph: Topology) -> None:
    assert pass_graph == expected_pass()
    assert pass_graph.north == (0.0, 1.0)
    _assert_containment(pass_graph)


def test_fail_house_readback(fail_graph: Topology) -> None:
    assert fail_graph == expected_fail()
    assert fail_graph.north == (0.0, 1.0)
    _assert_containment(fail_graph)


def _assert_containment(graph: Topology) -> None:
    by_name = {zone.name: zone for zone in graph.zones}
    assert by_name["site"].parent is None
    assert by_name["house"].parent == "site"
    storeys = {zone.name for zone in graph.zones if zone.kind == "Storey"}
    assert storeys
    assert all(by_name[name].parent == "house" for name in storeys)
    spaces = [zone for zone in graph.zones if zone.kind == "Space"]
    assert spaces
    assert all(zone.parent in storeys for zone in spaces)


def test_two_openings_share_an_edge(pass_graph: Topology, fail_graph: Topology) -> None:
    hall_south = _opening(pass_graph, "hall-south")
    main_door = _opening(pass_graph, "main-door")
    assert hall_south.at_m[1] == main_door.at_m[1] == 4.0
    assert {hall_south.at_m[0], main_door.at_m[0]} == {1.0, 3.0}
    bedroom_window = _opening(fail_graph, "bedroom-north")
    bedroom_door = _opening(fail_graph, "bedroom-dayroom")
    assert bedroom_window.at_m[1] == bedroom_door.at_m[1] == 12.0
    assert bedroom_window.orientation == bedroom_door.orientation == "north"


def test_graph_values_are_not_ifc_objects(pass_graph: Topology) -> None:
    assert type(pass_graph).__module__ == "pattern_language.topology"

    def walk(value: object) -> list[object]:
        if isinstance(value, tuple | frozenset):
            found: list[object] = []
            for item in value:
                found.extend(walk(item))
            return found
        return [value]

    modules = {type(value).__module__ for value in walk(pass_graph)}
    assert all(not module.startswith("ifcopenshell") for module in modules)


def test_fixture_directory_has_two_houses(repo_root: Path) -> None:
    fixtures = repo_root / "fixtures"
    assert sorted(path.name for path in fixtures.glob("*.ifc")) == [
        "fail-house.ifc",
        "pass-house.ifc",
    ]
    assert sorted(path.name for path in fixtures.glob("*.expected.json")) == [
        "fail-house.expected.json",
        "pass-house.expected.json",
    ]


def test_expected_json_matches_graph(repo_root: Path, pass_graph: Topology, fail_graph: Topology) -> None:
    for name, graph in (("pass-house", pass_graph), ("fail-house", fail_graph)):
        text = (repo_root / "fixtures" / f"{name}.expected.json").read_text(encoding="utf-8")
        assert text == to_json(graph)
        assert from_json(text) == graph


def test_committed_fixtures_match_writer(tmp_path: Path, repo_root: Path) -> None:
    write_fixtures(tmp_path)
    for name in ("pass-house.ifc", "fail-house.ifc"):
        assert read_topology(tmp_path / name) == read_topology(repo_root / "fixtures" / name)


def test_make_fixtures_check(repo_root: Path) -> None:
    completed = subprocess.run(
        [sys.executable, str(repo_root / "scripts" / "make_fixtures.py"), "--check"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert completed.stdout == "fresh: 2 houses\n"
    assert completed.stderr == ""


def test_write_ifc_rejects_a_diagonal(tmp_path: Path) -> None:
    triangle = Zone(
        "room",
        "Space",
        "ground",
        frozenset(),
        ((0.0, 0.0), (2.0, 0.0), (1.0, 1.0)),
        2.4,
        0.0,
    )
    model = Topology((0.0, 1.0), (triangle,), (), (), ())
    with pytest.raises(TopologyError, match="not axis-aligned"):
        write_ifc(model, tmp_path / "triangle.ifc")
    assert not (tmp_path / "triangle.ifc").exists()


def test_read_topology_rejects_unreadable_file(tmp_path: Path) -> None:
    path = tmp_path / "notes.txt"
    path.write_text("not an ifc file\n", encoding="utf-8")
    with pytest.raises(TopologyError):
        read_topology(path)


def test_judged_patterns_have_no_house(repo_root: Path) -> None:
    catalog = load_catalog(repo_root)
    computed = tuple(
        sorted(
            pattern.number
            for pattern in catalog.patterns
            if any(condition.kind == "computed" for condition in pattern.conditions)
        )
    )
    judged = tuple(
        sorted(
            pattern.number
            for pattern in catalog.patterns
            if any(condition.kind == "judged" for condition in pattern.conditions)
        )
    )
    assert computed == COMPUTED
    assert judged == (110, 180)
    names = " ".join(path.name for path in (repo_root / "fixtures").iterdir())
    assert "110" not in names
    assert "180" not in names


@pytest.mark.parametrize("number", COMPUTED, ids=[str(number) for number in COMPUTED])
def test_witness(number: int, pass_graph: Topology, fail_graph: Topology) -> None:
    _WITNESSES[number](pass_graph, fail_graph)


def _witness_105(passed: Topology, failed: Topology) -> None:
    court_y = _centroid(_zone(passed, "court").footprint)[1]
    occupied = [zone for zone in passed.zones if "occupied" in zone.tags]
    occupied_y = sum(_centroid(zone.footprint)[1] for zone in occupied) / len(occupied)
    assert round(court_y, 3) == 2.0
    assert round(occupied_y, 3) == 7.333
    assert court_y < occupied_y
    fail_court_y = _centroid(_zone(failed, "court").footprint)[1]
    assert round(fail_court_y, 3) == 17.6
    occupied_fail = [zone for zone in failed.zones if "occupied" in zone.tags]
    assert occupied_fail
    for zone in occupied_fail:
        assert fail_court_y > max(point[1] for point in zone.footprint)


def _witness_106(passed: Topology, failed: Topology) -> None:
    assert _is_rectangle(_zone(passed, "court").footprint)
    assert _is_rectangle(_zone(passed, "balcony").footprint)
    assert _zone(failed, "court").footprint == FAIL_RINGS["court"]
    assert _is_rectangle(_zone(failed, "balcony").footprint)


def _witness_107(passed: Topology, failed: Topology) -> None:
    occupied = [zone for zone in passed.zones if "occupied" in zone.tags]
    assert {zone.name for zone in occupied} == {"hall", "living", "bedroom"}
    for zone in occupied:
        assert _span(zone.footprint) == (4.0, 4.0)
        assert _full_exterior_side(passed, zone.name)
    bedroom = _zone(failed, "bedroom")
    assert _span(bedroom.footprint) == (4.0, 10.0)
    exterior = [
        tuple(sorted((item.start, item.end)))
        for item in failed.boundaries
        if item.space == "bedroom" and item.external
    ]
    assert exterior == [((6.0, 12.0), (8.0, 12.0))]


def _witness_112(passed: Topology, failed: Topology) -> None:
    assert set(_opening(passed, "approach-door").spaces) == {"court", "street"}
    assert set(_opening(passed, "main-door").spaces) == {"court", "hall"}
    assert "transition" in _zone(passed, "court").tags
    assert set(_opening(failed, "main-door").spaces) == {"corridor", "street"}
    assert all("transition" not in zone.tags for zone in failed.zones)


def _witness_127(passed: Topology, failed: Topology) -> None:
    passed_doors = _distances(_door_pairs(passed), "hall")
    assert passed_doors["hall"] == 0
    assert passed_doors["living"] == 1
    assert passed_doors["bedroom"] == 2
    assert "public" in _zone(passed, "hall").tags
    assert "semi-private" in _zone(passed, "living").tags
    assert "private" in _zone(passed, "bedroom").tags
    assert not any({item.a, item.b} == {"hall", "bedroom"} for item in passed.adjacencies)
    failed_doors = _distances(_door_pairs(failed), "corridor")
    failed_adjacent = _distances(_adjacent_pairs(failed), "corridor")
    assert failed_doors["bedroom"] == 1
    assert failed_doors["dayroom"] == 2
    assert failed_adjacent["bedroom"] == 1
    assert failed_adjacent["dayroom"] == 2
    assert "private" in _zone(failed, "bedroom").tags
    assert "public" in _zone(failed, "dayroom").tags
    assert all("semi-private" not in zone.tags for zone in failed.zones)


def _witness_128(passed: Topology, failed: Topology) -> None:
    daytime = [zone for zone in passed.zones if "daytime" in zone.tags]
    assert [zone.name for zone in daytime] == ["living"]
    assert round(_centroid(daytime[0].footprint)[1], 3) == 6.0
    fail_daytime = [zone for zone in failed.zones if "daytime" in zone.tags]
    assert [zone.name for zone in fail_daytime] == ["dayroom"]
    assert round(_centroid(fail_daytime[0].footprint)[1], 3) == 13.5


def _witness_130(passed: Topology, failed: Topology) -> None:
    assert set(_opening(passed, "main-door").spaces) == {"court", "hall"}
    hall = _zone(passed, "hall")
    assert "room" in hall.tags
    assert "corridor" not in hall.tags
    assert "living" not in hall.tags
    assert set(_opening(failed, "main-door").spaces) == {"corridor", "street"}
    assert "corridor" in _zone(failed, "corridor").tags


def _witness_159(passed: Topology, failed: Topology) -> None:
    assert _window_facings(passed, "hall") == {"south", "west"}
    assert _window_facings(passed, "living") == {"south", "east"}
    assert _window_facings(passed, "bedroom") == {"north", "west"}
    assert _window_facings(failed, "bedroom") == {"north"}
    assert _window_facings(failed, "dayroom") == {"north", "west"}


def _witness_167(passed: Topology, failed: Topology) -> None:
    assert _zone(passed, "balcony").footprint == PASS_RINGS["balcony"]
    assert max(point[0] for point in PASS_RINGS["balcony"]) - 8.0 == 2.0
    assert _zone(failed, "balcony").footprint == FAIL_RINGS["balcony"]
    assert 0.0 - min(point[0] for point in FAIL_RINGS["balcony"]) == 1.0


def _witness_190(passed: Topology, failed: Topology) -> None:
    assert _occupied_heights(passed) == {"hall": 2.4, "living": 3.0, "bedroom": 2.7}
    assert _occupied_heights(failed) == {"bedroom": 2.4, "dayroom": 2.4}


_WITNESSES = {
    105: _witness_105,
    106: _witness_106,
    107: _witness_107,
    112: _witness_112,
    127: _witness_127,
    128: _witness_128,
    130: _witness_130,
    159: _witness_159,
    167: _witness_167,
    190: _witness_190,
}
