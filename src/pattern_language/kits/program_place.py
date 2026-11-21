"""Program place kit — school, shop, park, civic, utility massings for city fabric.

Patterns are cited by number/name only (draft urban language). Our own wording.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProgramPlaceSpec:
    key: str
    label: str
    program: str  # school | grocery | shop | park | playground | town_hall | police | bank | utility | market | clinic
    ring: tuple[tuple[float, float], ...]
    mass_ring: tuple[tuple[float, float], ...] | None = None
    height_m: float = 6.0
    parent: str | None = None
    patterns: tuple[int, ...] = ()


_PROGRAM = {
    "school": {
        "component": "school",
        "roles": ["civic", "school", "public"],
        "patterns": (85, 14),  # Shopfront Schools, Identifiable Neighborhood
        "kind_mass": "solid",
        "height": 8.0,
    },
    "grocery": {
        "component": "shop",
        "roles": ["shop", "grocery", "public", "work"],
        "patterns": (89, 87, 19),  # Corner Grocery, Individually Owned Shops, Web of Shopping
        "kind_mass": "solid",
        "height": 5.0,
    },
    "shop": {
        "component": "shop",
        "roles": ["shop", "public", "work"],
        "patterns": (87, 32, 19),  # Individually Owned Shops, Shopping Street, Web of Shopping
        "kind_mass": "solid",
        "height": 5.5,
    },
    "market": {
        "component": "market",
        "roles": ["market", "shop", "public"],
        "patterns": (46, 30),  # Market of Many Shops, Activity Nodes
        "kind_mass": "solid",
        "height": 6.0,
    },
    "park": {
        "component": "park",
        "roles": ["park", "green", "grass", "outdoor", "public"],
        "patterns": (3, 60, 67),  # City Country Fingers, Accessible Green, Common Land
        "kind_mass": None,
        "height": 0.0,
    },
    "playground": {
        "component": "playground",
        "roles": ["playground", "outdoor", "public", "play"],
        "patterns": (68, 57),  # Connected Play, Children in the City
        "kind_mass": None,
        "height": 0.0,
    },
    "town_hall": {
        "component": "civic",
        "roles": ["civic", "government", "public", "town-hall"],
        "patterns": (44, 30),  # Local Town Hall, Activity Nodes
        "kind_mass": "solid",
        "height": 10.0,
    },
    "police": {
        "component": "civic",
        "roles": ["civic", "government", "public", "safety"],
        "patterns": (44, 81),  # Local Town Hall orbit, Small Services Without Red Tape
        "kind_mass": "solid",
        "height": 7.0,
    },
    "bank": {
        "component": "civic",
        "roles": ["civic", "work", "public", "bank"],
        "patterns": (41, 30),  # Work Community, Activity Nodes
        "kind_mass": "solid",
        "height": 8.0,
    },
    "utility": {
        "component": "utility",
        "roles": ["utility", "work", "service"],
        "patterns": (42,),  # Industrial Ribbon (edge services)
        "kind_mass": "solid",
        "height": 4.5,
    },
    "clinic": {
        "component": "clinic",
        "roles": ["civic", "health", "public"],
        "patterns": (47,),  # Health Center
        "kind_mass": "solid",
        "height": 7.0,
    },
}


def stamp_program_place(spec: ProgramPlaceSpec) -> dict[str, Any]:
    meta = _PROGRAM[spec.program]
    pats = list(spec.patterns) if spec.patterns else list(meta["patterns"])
    places: list[dict[str, Any]] = [
        {
            "id": f"lot-{spec.key}",
            "label": spec.label,
            "component": "parcel",
            "kind": "land",
            "ring": [list(p) for p in spec.ring],
            "roles": ["lot", "parcel", *meta["roles"][:2]],
            "patterns": pats,
            "role": f"{spec.program.replace('_', ' ').title()} parcel — {spec.label}.",
            "parent": spec.parent,
            "stage": "land",
        }
    ]
    mass_ring = spec.mass_ring
    if meta["kind_mass"] and mass_ring:
        places.append(
            {
                "id": f"found-{spec.key}",
                "label": f"{spec.label} pad",
                "component": "pad",
                "kind": "foundation",
                "ring": [list(p) for p in mass_ring],
                "roles": ["foundation", "pad"],
                "patterns": [],
                "role": f"Pad for {spec.label}.",
                "parent": f"lot-{spec.key}",
                "height_m": 0.35,
                "stage": "foundation",
            }
        )
        places.append(
            {
                "id": f"bldg-{spec.key}",
                "label": spec.label,
                "component": meta["component"],
                "kind": "solid",
                "ring": [list(p) for p in mass_ring],
                "roles": ["building", "massing", *meta["roles"]],
                "patterns": pats,
                "role": f"{spec.program.replace('_', ' ').title()} massing.",
                "parent": f"found-{spec.key}",
                "height_m": spec.height_m or meta["height"],
                "stage": "frame",
            }
        )
    elif "park" in meta["roles"] or "playground" in meta["roles"] or spec.program in {"park", "playground"}:
        places[0]["component"] = meta["component"]
        places[0]["kind"] = "void"
        places[0]["roles"] = list(meta["roles"])
        places[0]["stage"] = "land"

    xs = [p[0] for p in spec.ring]
    ys = [p[1] for p in spec.ring]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    nodes = [
        {
            "id": f"n-addr-{spec.key}",
            "x": cx,
            "y": cy,
            "kind": "address",
            "place": f"bldg-{spec.key}" if meta["kind_mass"] and mass_ring else f"lot-{spec.key}",
            "label": spec.label,
        }
    ]
    interactions = []
    if meta["kind_mass"] and mass_ring:
        interactions = [
            {"id": f"ix-found-{spec.key}", "kind": "sit-on", "a": f"found-{spec.key}", "b": f"lot-{spec.key}"},
            {"id": f"ix-bldg-{spec.key}", "kind": "sit-on", "a": f"bldg-{spec.key}", "b": f"found-{spec.key}"},
        ]
    return {
        "places": places,
        "walls": [],
        "openings": [],
        "nodes": nodes,
        "edges": [],
        "measures": [],
        "interfaces": [],
        "interactions": interactions,
    }
