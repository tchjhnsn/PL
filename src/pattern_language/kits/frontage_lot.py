"""Frontage lot kit: lot + pad + front court + garden walls + gate + massing + address.

Stamp this kit instead of hand-authoring neighbor parcels. Variations are
parameters (rings, heights, street id), not forks of the schema.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FrontageLotSpec:
    """One street-facing parcel with court gate and massing (plot-series cell)."""

    key: str  # short id fragment: "e", "g", …
    label: str  # "E", "G", …
    block_id: str
    street_id: str  # street the court fronts
    lot_ring: tuple[tuple[float, float], ...]
    found_ring: tuple[tuple[float, float], ...]
    court_ring: tuple[tuple[float, float], ...]
    mass_ring: tuple[tuple[float, float], ...]
    gate_xy: tuple[float, float]
    gate_swing: str = "ccw"
    path_ring: tuple[tuple[float, float], ...] | None = None
    mass_height_m: float = 6.0
    land_use: str = "living"  # living | work | civic
    wall_thickness: float = 0.2
    patterns: tuple[int, ...] = (105, 106, 112)


def stamp_frontage_lot(spec: FrontageLotSpec) -> dict[str, Any]:
    """Return partial plan fragments to merge into a SpatialStructure document."""
    k = spec.key
    lot_id = f"lot-{k}"
    found_id = f"found-{k}"
    court_id = f"{k}-court"
    house_id = f"house-{k}"
    door_id = f"{k}-door-approach"
    path_id = f"path-approach-{k}" if spec.path_ring else None

    places: list[dict[str, Any]] = [
        {
            "id": lot_id,
            "label": f"Lot {spec.label}",
            "component": "parcel",
            "kind": "land",
            "ring": [list(p) for p in spec.lot_ring],
            "roles": ["lot", "parcel", spec.land_use],
            "patterns": [],
            "role": f"Parcel on {spec.block_id} facing {spec.street_id}.",
            "parent": spec.block_id,
            "stage": "land",
        },
        {
            "id": found_id,
            "label": f"Foundation {spec.label}",
            "component": "pad",
            "kind": "foundation",
            "ring": [list(p) for p in spec.found_ring],
            "roles": ["foundation", "pad"],
            "patterns": [],
            "role": f"Pad for massing {spec.label}.",
            "parent": lot_id,
            "height_m": 0.35,
            "stage": "foundation",
        },
        {
            "id": court_id,
            "label": f"Front Court {spec.label}",
            "component": "court",
            "kind": "void",
            "ring": [list(p) for p in spec.court_ring],
            "roles": ["outdoor", "transition", "frontage"],
            "patterns": list(spec.patterns),
            "role": f"Street front court on Lot {spec.label}.",
            "parent": lot_id,
            "enclosure_hw": 0.4,
            "stage": "frame",
        },
        {
            "id": house_id,
            "label": f"Massing {spec.label}",
            "component": "massing",
            "kind": "solid",
            "ring": [list(p) for p in spec.mass_ring],
            "roles": ["building", "massing"],
            "patterns": [105, 106],
            "role": f"Frame-stage massing on Foundation {spec.label}.",
            "parent": found_id,
            "height_m": spec.mass_height_m,
            "stage": "frame",
        },
    ]
    if spec.path_ring:
        places.append(
            {
                "id": path_id,
                "label": f"Approach Path {spec.label}",
                "component": "path",
                "kind": "path",
                "ring": [list(p) for p in spec.path_ring],
                "roles": ["transition", "frontage"],
                "patterns": [110, 112],
                "role": f"Stub into Court {spec.label}.",
                "parent": None,
                "stage": "land",
            }
        )

    # Garden walls on court south edge + returns (axis-aligned AABB courts).
    xs = [p[0] for p in spec.court_ring]
    ys = [p[1] for p in spec.court_ring]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    walls = [
        {"id": f"w-{k}-court-s", "a": [x0, y0], "b": [x1, y0], "thickness": spec.wall_thickness},
        {"id": f"w-{k}-court-w", "a": [x0, y0], "b": [x0, y1], "thickness": spec.wall_thickness},
        {"id": f"w-{k}-court-e", "a": [x1, y0], "b": [x1, y1], "thickness": spec.wall_thickness},
    ]

    openings = [
        {
            "id": door_id,
            "label": f"Court Gate {spec.label}",
            "component": "door",
            "x": spec.gate_xy[0],
            "y": spec.gate_xy[1],
            "width": 1.2,
            "wall_angle": 0,
            "swing": spec.gate_swing,
            "patterns": list(spec.patterns),
            "role": f"Garden-wall gate into Front Court {spec.label}.",
            "parent": court_id,
        }
    ]

    gx, _gy = spec.gate_xy
    addr_y = y1  # massing front
    on_main = "main" in spec.street_id
    sw_place = "sidewalk-main-n" if on_main else "sidewalk-cross-n"
    sw_y = 6.75 if on_main else 51.25
    path_y = (sw_y + y0) / 2
    court_y = (y0 + y1) / 2
    nodes = [
        {
            "id": f"n-sw-{k}",
            "x": gx,
            "y": sw_y,
            "kind": "place",
            "place": sw_place,
            "label": f"SW@{spec.label}",
        },
        {"id": f"n-court-{k}", "x": gx, "y": court_y, "kind": "place", "place": court_id, "label": f"Court {spec.label}"},
        {"id": f"n-addr-{k}", "x": gx, "y": addr_y, "kind": "address", "place": house_id, "label": f"Address {spec.label}"},
    ]
    if path_id:
        nodes.insert(
            1,
            {
                "id": f"n-path-{k}",
                "x": gx,
                "y": path_y,
                "kind": "place",
                "place": path_id,
                "label": f"Path {spec.label}",
            },
        )

    # Approach edges: sidewalk → (path) → court → address
    sw = f"n-sw-{k}"
    court_n = f"n-court-{k}"
    addr = f"n-addr-{k}"
    edges: list[dict[str, Any]] = []
    if path_id:
        path_n = f"n-path-{k}"
        edges.append(
            {
                "id": f"e-approach-{k}-1",
                "a": sw,
                "b": path_n,
                "mode": "pedestrian",
                "hierarchy": "approach",
                "width_m": 2.0,
                "directed": True,
                "label": f"Sidewalk→Path {spec.label}",
                "polyline": [[gx, sw_y], [gx, path_y]],
            }
        )
        edges.append(
            {
                "id": f"e-approach-{k}-2",
                "a": path_n,
                "b": court_n,
                "mode": "pedestrian",
                "hierarchy": "approach",
                "width_m": 1.2,
                "directed": True,
                "label": f"Path→Court {spec.label}",
                "polyline": [[gx, path_y], [gx, court_y]],
            }
        )
        edges.append(
            {
                "id": f"e-approach-{k}-3",
                "a": court_n,
                "b": addr,
                "mode": "pedestrian",
                "hierarchy": "approach",
                "width_m": 1.2,
                "directed": True,
                "label": f"Court→Address {spec.label}",
                "polyline": [[gx, court_y], [gx, addr_y]],
            }
        )
    else:
        edges.append(
            {
                "id": f"e-approach-{k}-1",
                "a": sw,
                "b": court_n,
                "mode": "pedestrian",
                "hierarchy": "approach",
                "width_m": 1.5,
                "directed": True,
                "label": f"Sidewalk→Court {spec.label}",
                "polyline": [[gx, sw_y], [gx, court_y]],
            }
        )
        edges.append(
            {
                "id": f"e-approach-{k}-2",
                "a": court_n,
                "b": addr,
                "mode": "pedestrian",
                "hierarchy": "approach",
                "width_m": 1.2,
                "directed": True,
                "label": f"Court→Address {spec.label}",
                "polyline": [[gx, court_y], [gx, addr_y]],
            }
        )

    frontage_m = round(x1 - x0, 3)
    measures = [
        {
            "id": f"m-frontage-{k}",
            "label": f"Lot {spec.label} frontage",
            "a": [x0, y0],
            "b": [x1, y0],
            "value_m": frontage_m,
            "kind": "frontage",
            "of": court_id,
            "patterns": [105, 106],
        }
    ]

    interfaces = [
        {"id": f"if-approach-{k}", "kind": "door", "between": [spec.street_id, court_id], "opening": door_id},
        {"id": f"if-front-{k}", "kind": "frontage", "between": [court_id, spec.street_id], "length_m": frontage_m},
    ]

    interactions = [
        {"id": f"ix-found-{k}-lot", "kind": "sit-on", "a": found_id, "b": lot_id},
        {"id": f"ix-mass-{k}", "kind": "sit-on", "a": house_id, "b": found_id},
        {"id": f"ix-{k}-court-mass", "kind": "outdoor-adjacency", "a": court_id, "b": house_id},
    ]

    return {
        "places": places,
        "walls": walls,
        "openings": openings,
        "nodes": nodes,
        "edges": edges,
        "measures": measures,
        "interfaces": interfaces,
        "interactions": interactions,
    }


def merge_kit(plan_parts: dict[str, list], kit: dict[str, Any]) -> None:
    """Append kit fragments into mutable plan part lists."""
    for key in ("places", "walls", "openings", "nodes", "edges", "measures", "interfaces", "interactions"):
        plan_parts.setdefault(key, []).extend(kit.get(key) or [])
