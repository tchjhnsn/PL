#!/usr/bin/env python3
"""Build seed-district plan-model (spatial structure) + CityJSON/GeoJSON exports."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "data"
SCHEMA = ROOT / "schema" / "spatial-structure.schema.json"

ORIGIN_LAT = 39.9522
ORIGIN_LON = -75.1636
M_PER_DEG_LAT = 111_320.0

NAMES = {
    105: "South Facing Outdoors",
    106: "Positive Outdoor Space",
    107: "Wings of Light",
    110: "Main Entrance",
    112: "Entrance Transition",
    127: "Intimacy Gradient",
    128: "Indoor Sunlight",
    130: "Entrance Room",
    159: "Light on Two Sides of Every Room",
    167: "Six-Foot Balcony",
    180: "Window Place",
    190: "Ceiling Height Variety",
}


def dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return round(math.hypot(b[0] - a[0], b[1] - a[1]), 3)


def m_to_lonlat(x: float, y: float) -> tuple[float, float]:
    lat = ORIGIN_LAT + y / M_PER_DEG_LAT
    lon = ORIGIN_LON + x / (M_PER_DEG_LAT * math.cos(math.radians(ORIGIN_LAT)))
    return (round(lon, 7), round(lat, 7))


def build_plan() -> dict:
    places = [
        {
            "id": "street-main",
            "label": "Main Street ROW",
            "component": "street",
            "kind": "void",
            "ring": [(0, 0), (90, 0), (90, 8), (0, 8)],
            "roles": ["street", "public", "row"],
            "patterns": [105, 106],
            "role": "Right-of-way: carriageway + north sidewalk (CityGML Section stand-in).",
            "parent": None,
            "enclosure_hw": 0.35,
            "stage": "land",
        },
        {
            "id": "carriageway-main",
            "label": "Main Carriageway",
            "component": "carriageway",
            "kind": "void",
            "ring": [(0, 0), (90, 0), (90, 5.5), (0, 5.5)],
            "roles": ["street", "carriageway", "vehicle"],
            "patterns": [105],
            "role": "TrafficArea driving surface — 5.5 m clear (granularity way).",
            "parent": "street-main",
            "enclosure_hw": 0.4,
            "stage": "land",
        },
        {
            "id": "sidewalk-main-n",
            "label": "Main Sidewalk N",
            "component": "sidewalk",
            "kind": "path",
            "ring": [(0, 5.5), (90, 5.5), (90, 8), (0, 8)],
            "roles": ["sidewalk", "pedestrian", "public"],
            "patterns": [105, 106, 112],
            "role": "North footway against the block — 2.5 m clear width.",
            "parent": "street-main",
            "stage": "land",
        },
        {
            "id": "street-lane",
            "label": "Side Lane",
            "component": "street",
            "kind": "void",
            "ring": [(0, 8), (8, 8), (8, 70), (0, 70)],
            "roles": ["street"],
            "patterns": [106],
            "role": "North–south service lane; quieter hierarchy than Main Street.",
            "parent": None,
            "enclosure_hw": 0.5,
            "stage": "land",
        },
        {
            "id": "green-shared",
            "label": "Shared Green",
            "component": "court",
            "kind": "void",
            "ring": [(28, 38), (58, 38), (58, 48), (28, 48)],
            "roles": ["outdoor", "public", "green", "grass"],
            "patterns": [105, 106],
            "role": "Block outdoor room — turf grass court between parcels (no lot overlap).",
            "parent": None,
            "enclosure_hw": 0.4,
            "stage": "land",
        },
        {
            "id": "cover-gravel",
            "label": "Gravel court edge",
            "component": "ground-cover",
            "kind": "land",
            "ring": [(26, 36), (60, 36), (60, 38), (26, 38)],
            "roles": ["ground-cover", "gravel"],
            "patterns": [106],
            "role": "Gravel strip south of the green.",
            "parent": None,
            "stage": "survey",
        },
        {
            "id": "pond-a",
            "label": "Garden pond",
            "component": "pond",
            "kind": "void",
            "ring": [(34, 40), (44, 40), (44, 46), (34, 46)],
            "roles": ["water", "pond", "outdoor"],
            "patterns": [105, 106],
            "role": "Authored garden pond on the green (greenfield design).",
            "parent": "green-shared",
            "height_m": 0.15,
            "stage": "survey",
        },
        {
            "id": "lot-a",
            "label": "Lot A",
            "component": "parcel",
            "kind": "land",
            "ring": [(16, 10), (46, 10), (46, 36), (16, 36)],
            "roles": ["lot", "parcel"],
            "patterns": [],
            "role": "Surveyed parcel for House A — land before footprint.",
            "parent": None,
            "stage": "land",
        },
        {
            "id": "lot-b",
            "label": "Lot B",
            "component": "parcel",
            "kind": "land",
            "ring": [(50, 10), (74, 10), (74, 32), (50, 32)],
            "roles": ["lot", "parcel"],
            "patterns": [],
            "role": "Surveyed parcel east of the green.",
            "parent": None,
            "stage": "land",
        },
        {
            "id": "lot-c",
            "label": "Lot C",
            "component": "parcel",
            "kind": "land",
            "ring": [(16, 50), (42, 50), (42, 68), (16, 68)],
            "roles": ["lot", "parcel"],
            "patterns": [],
            "role": "Surveyed parcel north of the green.",
            "parent": None,
            "stage": "land",
        },
        {
            "id": "lot-d",
            "label": "Lot D",
            "component": "parcel",
            "kind": "land",
            "ring": [(48, 52), (74, 52), (74, 70), (48, 70)],
            "roles": ["lot", "parcel"],
            "patterns": [],
            "role": "Surveyed NE corner parcel.",
            "parent": None,
            "stage": "land",
        },
        {
            "id": "lot-workshop",
            "label": "Workshop Lot",
            "component": "parcel",
            "kind": "land",
            "ring": [(8, 38), (20, 38), (20, 50), (8, 50)],
            "roles": ["lot", "parcel"],
            "patterns": [],
            "role": "Surveyed lane-side workshop parcel.",
            "parent": None,
            "stage": "land",
        },
        {
            "id": "found-a",
            "label": "Foundation A",
            "component": "pad",
            "kind": "foundation",
            "ring": [(18, 14), (42, 14), (42, 36), (18, 36)],
            "roles": ["foundation", "pad"],
            "patterns": [],
            "role": "Pad for House A — sits on Lot A.",
            "parent": "lot-a",
            "height_m": 0.35,
            "floor_elevation_m": 0,
            "stage": "foundation",
        },
        {
            "id": "found-b",
            "label": "Foundation B",
            "component": "pad",
            "kind": "foundation",
            "ring": [(52, 12), (72, 12), (72, 30), (52, 30)],
            "roles": ["foundation", "pad"],
            "patterns": [],
            "role": "Pad for neighbor massing B.",
            "parent": "lot-b",
            "height_m": 0.35,
            "stage": "foundation",
        },
        {
            "id": "found-c",
            "label": "Foundation C",
            "component": "pad",
            "kind": "foundation",
            "ring": [(18, 52), (40, 52), (40, 66), (18, 66)],
            "roles": ["foundation", "pad"],
            "patterns": [],
            "role": "Pad for neighbor massing C.",
            "parent": "lot-c",
            "height_m": 0.35,
            "stage": "foundation",
        },
        {
            "id": "found-d",
            "label": "Foundation D",
            "component": "pad",
            "kind": "foundation",
            "ring": [(50, 54), (72, 54), (72, 68), (50, 68)],
            "roles": ["foundation", "pad"],
            "patterns": [],
            "role": "Pad for neighbor massing D.",
            "parent": "lot-d",
            "height_m": 0.35,
            "stage": "foundation",
        },
        {
            "id": "found-workshop",
            "label": "Foundation Workshop",
            "component": "pad",
            "kind": "foundation",
            "ring": [(10, 40), (18, 40), (18, 50), (10, 50)],
            "roles": ["foundation", "pad"],
            "patterns": [],
            "role": "Pad for workshop massing.",
            "parent": "lot-workshop",
            "height_m": 0.35,
            "stage": "foundation",
        },
        {
            "id": "a-court",
            "label": "South Court",
            "component": "court",
            "kind": "void",
            "ring": [(18, 14), (42, 14), (42, 22), (18, 22)],
            "roles": ["outdoor", "transition"],
            "patterns": [105, 106, 112],
            "role": "Transition void between street and main door (8 m deep).",
            "parent": "house-a",
            "enclosure_hw": 0.45,
            "stage": "frame",
        },
        {
            "id": "path-approach",
            "label": "Approach Path",
            "component": "path",
            "kind": "path",
            "ring": [(26, 8), (34, 8), (32, 14), (28, 14)],
            "roles": ["transition"],
            "patterns": [110, 112],
            "role": "Pedestrian approach: street → court (2 m clear width).",
            "parent": None,
            "stage": "land",
        },
        {
            "id": "a-porch",
            "label": "Entrance Porch",
            "component": "porch",
            "kind": "void",
            "ring": [(21, 20), (27, 20), (27, 22), (21, 22)],
            "roles": ["outdoor", "transition", "porch"],
            "patterns": [110, 112, 130],
            "role": "Covered arrival between court and hall (2 m deep).",
            "parent": "house-a",
            "height_m": 2.4,
            "stage": "frame",
        },
        {
            "id": "a-hall",
            "label": "Hall",
            "component": "room",
            "kind": "room",
            "ring": [(18, 22), (28, 22), (28, 30), (18, 30)],
            "roles": ["room", "public", "occupied"],
            "patterns": [107, 110, 112, 130, 159],
            "role": "Entrance room — shallow wing.",
            "parent": "house-a",
            "height_m": 2.4,
            "stage": "frame",
        },
        {
            "id": "a-living",
            "label": "Living",
            "component": "room",
            "kind": "room",
            "ring": [(28, 22), (42, 22), (42, 30), (28, 30)],
            "roles": ["living", "semi-private", "occupied"],
            "patterns": [127, 128, 130, 159, 190],
            "role": "Day room; taller ceiling.",
            "parent": "house-a",
            "height_m": 3.0,
            "stage": "frame",
        },
        {
            "id": "a-bedroom",
            "label": "Bedroom",
            "component": "room",
            "kind": "room",
            "ring": [(28, 30), (42, 30), (42, 36), (28, 36)],
            "roles": ["room", "private", "occupied"],
            "patterns": [127, 159, 167],
            "role": "Private end of the intimacy gradient (upper storey).",
            "parent": "house-a",
            "height_m": 2.7,
            "floor_elevation_m": 3.0,
            "stage": "frame",
        },
        {
            "id": "a-balcony",
            "label": "Balcony",
            "component": "balcony",
            "kind": "void",
            "ring": [(42, 30), (48, 30), (48, 36), (42, 36)],
            "roles": ["balcony", "outdoor"],
            "patterns": [167],
            "role": "Elevated outdoor edge ≥1.83 m deep (upper storey).",
            "parent": "house-a",
            "height_m": 3.0,
            "floor_elevation_m": 3.0,
            "stage": "frame",
        },
        {
            "id": "house-b",
            "label": "Massing B",
            "component": "massing",
            "kind": "solid",
            "ring": [(52, 12), (72, 12), (72, 30), (52, 30)],
            "roles": ["building", "massing"],
            "patterns": [105, 106],
            "role": "Frame-stage massing on Foundation B — not a finished house.",
            "parent": "found-b",
            "height_m": 6.5,
            "stage": "frame",
        },
        {
            "id": "house-c",
            "label": "Massing C",
            "component": "massing",
            "kind": "solid",
            "ring": [(18, 52), (40, 52), (40, 66), (18, 66)],
            "roles": ["building", "massing"],
            "patterns": [105, 106],
            "role": "Frame-stage massing on Foundation C.",
            "parent": "found-c",
            "height_m": 6.0,
            "stage": "frame",
        },
        {
            "id": "house-d",
            "label": "Massing D",
            "component": "massing",
            "kind": "solid",
            "ring": [(50, 54), (72, 54), (72, 68), (50, 68)],
            "roles": ["building", "massing"],
            "patterns": [105, 106],
            "role": "Frame-stage massing on Foundation D.",
            "parent": "found-d",
            "height_m": 5.5,
            "stage": "frame",
        },
        {
            "id": "workshop",
            "label": "Workshop Massing",
            "component": "massing",
            "kind": "solid",
            "ring": [(10, 40), (18, 40), (18, 50), (10, 50)],
            "roles": ["building", "massing"],
            "patterns": [105, 106],
            "role": "Frame-stage workshop massing.",
            "parent": "found-workshop",
            "height_m": 4.0,
            "stage": "frame",
        },
    ]

    walls = [
        {"id": "w-court-s", "a": (18, 14), "b": (42, 14), "thickness": 0.2},
        {"id": "w-hall-s", "a": (18, 22), "b": (28, 22), "thickness": 0.35},
        {"id": "w-liv-s", "a": (28, 22), "b": (42, 22), "thickness": 0.35},
        {"id": "w-hall-w", "a": (18, 22), "b": (18, 30), "thickness": 0.35},
        {"id": "w-hall-liv", "a": (28, 22), "b": (28, 30), "thickness": 0.3},
        {"id": "w-hall-n", "a": (18, 30), "b": (28, 30), "thickness": 0.35},
        {"id": "w-liv-bed", "a": (28, 30), "b": (42, 30), "thickness": 0.3},
        {"id": "w-liv-e", "a": (42, 22), "b": (42, 30), "thickness": 0.35},
        {"id": "w-bed-e", "a": (42, 30), "b": (42, 36), "thickness": 0.25},
        {"id": "w-bed-n", "a": (28, 36), "b": (42, 36), "thickness": 0.35},
        {"id": "w-bed-w", "a": (28, 30), "b": (28, 36), "thickness": 0.35},
        {"id": "w-balc-n", "a": (42, 36), "b": (48, 36), "thickness": 0.15},
        {"id": "w-balc-e", "a": (48, 30), "b": (48, 36), "thickness": 0.15},
        {"id": "w-balc-s", "a": (42, 30), "b": (48, 30), "thickness": 0.15},
        {"id": "w-house-w", "a": (18, 14), "b": (18, 22), "thickness": 0.25},
        {"id": "w-house-e-court", "a": (42, 14), "b": (42, 22), "thickness": 0.25},
        {"id": "w-porch-w", "a": (21, 20), "b": (21, 22), "thickness": 0.25},
        {"id": "w-porch-e", "a": (27, 20), "b": (27, 22), "thickness": 0.25},
    ]
    # tuples → lists for JSON
    walls = [
        {"id": w["id"], "a": list(w["a"]), "b": list(w["b"]), "thickness": w["thickness"]}
        for w in walls
    ]

    openings = [
        {
            "id": "a-door-approach",
            "label": "Court Gate",
            "component": "door",
            "x": 30,
            "y": 14,
            "width": 1.2,
            "wall_angle": 0,
            "swing": "ccw",
            "patterns": [106, 112],
            "role": "Garden-wall threshold: path into the south court (gate in w-court-s).",
            "parent": "a-court",
        },
        {
            "id": "a-door-main",
            "label": "Main Door",
            "component": "door",
            "x": 24,
            "y": 22,
            "width": 1.0,
            "wall_angle": 0,
            "swing": "ccw",
            "patterns": [110, 112, 130],
            "role": "Court into the entrance hall — address point.",
            "parent": "a-hall",
        },
        {
            "id": "a-door-living",
            "label": "Hall–Living",
            "component": "door",
            "x": 28,
            "y": 26,
            "width": 0.9,
            "wall_angle": 90,
            "swing": "ccw",
            "patterns": [127, 130],
            "role": "Into the day room.",
            "parent": "a-living",
        },
        {
            "id": "a-door-bed",
            "label": "Living–Bedroom",
            "component": "door",
            "x": 35,
            "y": 30,
            "width": 0.9,
            "wall_angle": 0,
            "swing": "ccw",
            "patterns": [127],
            "role": "Toward the private wing.",
            "parent": "a-bedroom",
        },
        {
            "id": "a-door-balc",
            "label": "Balcony Door",
            "component": "door",
            "x": 42,
            "y": 33,
            "width": 0.9,
            "wall_angle": 90,
            "swing": "cw",
            "patterns": [167],
            "role": "Onto the balcony.",
            "parent": "a-balcony",
        },
        {
            "id": "a-win-hall-s",
            "label": "Hall S",
            "component": "window",
            "x": 21,
            "y": 22,
            "width": 1.4,
            "wall_angle": 0,
            "patterns": [107, 159],
            "role": "South light into the hall.",
            "parent": "a-hall",
            "facing": "south",
        },
        {
            "id": "a-win-hall-w",
            "label": "Hall W",
            "component": "window",
            "x": 18,
            "y": 26,
            "width": 1.2,
            "wall_angle": 90,
            "patterns": [107, 159],
            "role": "West light — second side.",
            "parent": "a-hall",
            "facing": "west",
        },
        {
            "id": "a-win-liv-s",
            "label": "Living S",
            "component": "window",
            "x": 35,
            "y": 22,
            "width": 1.8,
            "wall_angle": 0,
            "patterns": [128, 159, 180],
            "role": "Equator light into living.",
            "parent": "a-living",
            "facing": "south",
        },
        {
            "id": "a-win-liv-e",
            "label": "Living E",
            "component": "window",
            "x": 42,
            "y": 26,
            "width": 1.4,
            "wall_angle": 90,
            "patterns": [128, 159],
            "role": "East light — second side.",
            "parent": "a-living",
            "facing": "east",
        },
        {
            "id": "a-win-bed-n",
            "label": "Bedroom N",
            "component": "window",
            "x": 35,
            "y": 36,
            "width": 1.4,
            "wall_angle": 0,
            "patterns": [159],
            "role": "North light.",
            "parent": "a-bedroom",
            "facing": "north",
        },
        {
            "id": "a-win-bed-w",
            "label": "Bedroom W",
            "component": "window",
            "x": 28,
            "y": 33,
            "width": 1.2,
            "wall_angle": 90,
            "patterns": [159],
            "role": "West light — second side.",
            "parent": "a-bedroom",
            "facing": "west",
        },
    ]

    trees = [
        {"id": "tree-1", "label": "White pine", "component": "tree", "x": 30, "y": 42, "canopy": 3.5, "trunk": 0.35, "form": "evergreen", "species": "Pinus strobus", "patterns": [105, 106], "role": "Authored pine on the green."},
        {"id": "tree-2", "label": "White pine", "component": "tree", "x": 50, "y": 44, "canopy": 4.0, "trunk": 0.4, "form": "evergreen", "species": "Pinus strobus", "patterns": [105, 106], "role": "Authored pine on the green."},
        {"id": "tree-3", "label": "Oak", "component": "tree", "x": 40, "y": 47, "canopy": 4.5, "trunk": 0.45, "form": "deciduous", "species": "Quercus alba", "patterns": [105, 106], "role": "Shade tree north edge of green."},
        {"id": "tree-4", "label": "Maple", "component": "tree", "x": 22, "y": 20, "canopy": 3.2, "trunk": 0.3, "form": "deciduous", "species": "Acer rubrum", "patterns": [105, 106], "role": "Lot A yard tree."},
        {"id": "tree-5", "label": "White pine", "component": "tree", "x": 12, "y": 28, "canopy": 2.8, "trunk": 0.28, "form": "evergreen", "species": "Pinus strobus", "patterns": [105, 106], "role": "Lane shade pine."},
        {"id": "tree-6", "label": "Willow", "component": "tree", "x": 46, "y": 42, "canopy": 3.0, "trunk": 0.3, "form": "deciduous", "species": "Salix babylonica", "patterns": [105, 106], "role": "Pond-edge willow."},
    ]

    # Circulation network — makes street FLOW and approach sequence first-class
    nodes = [
        {"id": "n-w", "x": 2, "y": 2.75, "kind": "intersection", "label": "W"},
        {"id": "n-mid", "x": 30, "y": 2.75, "kind": "intersection", "label": "Main@Approach"},
        {"id": "n-e", "x": 88, "y": 2.75, "kind": "intersection", "label": "E"},
        {"id": "n-sw-w", "x": 2, "y": 6.75, "kind": "place", "place": "sidewalk-main-n", "label": "SW W"},
        {"id": "n-sw-mid", "x": 30, "y": 6.75, "kind": "place", "place": "sidewalk-main-n", "label": "SW@Path"},
        {"id": "n-sw-e", "x": 88, "y": 6.75, "kind": "place", "place": "sidewalk-main-n", "label": "SW E"},
        {"id": "n-lane-s", "x": 4, "y": 12, "kind": "intersection", "label": "Lane S"},
        {"id": "n-lane-n", "x": 4, "y": 60, "kind": "intersection", "label": "Lane N"},
        {"id": "n-path", "x": 30, "y": 11, "kind": "place", "place": "path-approach", "label": "Path"},
        {"id": "n-court", "x": 30, "y": 18, "kind": "place", "place": "a-court", "label": "Court"},
        {"id": "n-door", "x": 24, "y": 22, "kind": "address", "place": "a-hall", "label": "Main Door"},
        {"id": "n-hall", "x": 23, "y": 26, "kind": "place", "place": "a-hall", "label": "Hall"},
        {"id": "n-liv", "x": 35, "y": 26, "kind": "place", "place": "a-living", "label": "Living"},
        {"id": "n-bed", "x": 35, "y": 33, "kind": "place", "place": "a-bedroom", "label": "Bedroom"},
        {"id": "n-green", "x": 43, "y": 43, "kind": "place", "place": "green-shared", "label": "Green"},
    ]

    edges = [
        {
            "id": "e-main-1",
            "a": "n-w",
            "b": "n-mid",
            "mode": "vehicle",
            "hierarchy": "arterial",
            "width_m": 5.5,
            "directed": True,
            "label": "Carriageway →",
            "polyline": [[2, 2.75], [30, 2.75]],
        },
        {
            "id": "e-main-2",
            "a": "n-mid",
            "b": "n-e",
            "mode": "vehicle",
            "hierarchy": "arterial",
            "width_m": 5.5,
            "directed": True,
            "label": "Carriageway →",
            "polyline": [[30, 2.75], [88, 2.75]],
        },
        {
            "id": "e-sidewalk-1",
            "a": "n-sw-w",
            "b": "n-sw-mid",
            "mode": "pedestrian",
            "hierarchy": "path",
            "width_m": 2.5,
            "directed": False,
            "label": "Sidewalk N",
            "polyline": [[2, 6.75], [30, 6.75]],
        },
        {
            "id": "e-sidewalk-2",
            "a": "n-sw-mid",
            "b": "n-sw-e",
            "mode": "pedestrian",
            "hierarchy": "path",
            "width_m": 2.5,
            "directed": False,
            "label": "Sidewalk N",
            "polyline": [[30, 6.75], [88, 6.75]],
        },
        {
            "id": "e-lane",
            "a": "n-lane-s",
            "b": "n-lane-n",
            "mode": "shared",
            "hierarchy": "lane",
            "width_m": 6.0,
            "directed": False,
            "label": "Side Lane",
            "polyline": [[4, 12], [4, 60]],
        },
        {
            "id": "e-approach-1",
            "a": "n-sw-mid",
            "b": "n-path",
            "mode": "pedestrian",
            "hierarchy": "approach",
            "width_m": 2.0,
            "directed": True,
            "label": "1 Street→Path",
            "polyline": [[30, 4], [30, 11]],
        },
        {
            "id": "e-approach-2",
            "a": "n-path",
            "b": "n-court",
            "mode": "pedestrian",
            "hierarchy": "approach",
            "width_m": 2.0,
            "directed": True,
            "label": "2 Path→Court",
            "polyline": [[30, 11], [30, 18]],
        },
        {
            "id": "e-approach-3",
            "a": "n-court",
            "b": "n-door",
            "mode": "pedestrian",
            "hierarchy": "approach",
            "width_m": 1.2,
            "directed": True,
            "label": "3 Court→Door",
            "polyline": [[30, 18], [24, 22]],
        },
        {
            "id": "e-in-hall",
            "a": "n-door",
            "b": "n-hall",
            "mode": "pedestrian",
            "hierarchy": "path",
            "width_m": 1.0,
            "directed": True,
            "label": "Enter hall",
            "polyline": [[24, 22], [23, 26]],
        },
        {
            "id": "e-hall-liv",
            "a": "n-hall",
            "b": "n-liv",
            "mode": "pedestrian",
            "hierarchy": "path",
            "width_m": 0.9,
            "directed": True,
            "label": "Public→living",
            "polyline": [[23, 26], [35, 26]],
        },
        {
            "id": "e-liv-bed",
            "a": "n-liv",
            "b": "n-bed",
            "mode": "pedestrian",
            "hierarchy": "path",
            "width_m": 0.9,
            "directed": True,
            "label": "Living→private",
            "polyline": [[35, 26], [35, 33]],
        },
        {
            "id": "e-to-green",
            "a": "n-liv",
            "b": "n-green",
            "mode": "pedestrian",
            "hierarchy": "path",
            "width_m": 1.5,
            "directed": False,
            "label": "To shared green",
            "polyline": [[35, 26], [42, 30], [45, 38]],
        },
    ]

    measures = [
        {
            "id": "m-court-depth",
            "label": "Court depth",
            "a": [30, 14],
            "b": [30, 22],
            "value_m": 8.0,
            "kind": "depth",
            "of": "a-court",
            "patterns": [105, 106, 112],
        },
        {
            "id": "m-approach-width",
            "label": "Approach width",
            "a": [28, 11],
            "b": [32, 11],
            "value_m": 2.0,
            "kind": "width",
            "of": "path-approach",
            "patterns": [112],
        },
        {
            "id": "m-main-width",
            "label": "ROW width",
            "a": [40, 0],
            "b": [40, 8],
            "value_m": 8.0,
            "kind": "width",
            "of": "street-main",
            "patterns": [105],
        },
        {
            "id": "m-carriageway-width",
            "label": "Carriageway width",
            "a": [50, 0],
            "b": [50, 5.5],
            "value_m": 5.5,
            "kind": "width",
            "of": "carriageway-main",
            "patterns": [105],
        },
        {
            "id": "m-sidewalk-width",
            "label": "Sidewalk clear width",
            "a": [50, 5.5],
            "b": [50, 8],
            "value_m": 2.5,
            "kind": "width",
            "of": "sidewalk-main-n",
            "patterns": [112],
        },
        {
            "id": "m-setback-a",
            "label": "House A setback",
            "a": [30, 8],
            "b": [30, 14],
            "value_m": 6.0,
            "kind": "setback",
            "of": "a-court",
            "patterns": [112],
        },
        {
            "id": "m-porch-depth",
            "label": "Porch depth",
            "a": [24, 20],
            "b": [24, 22],
            "value_m": 2.0,
            "kind": "depth",
            "of": "a-porch",
            "patterns": [112, 130],
        },
        {
            "id": "m-balcony-depth",
            "label": "Balcony depth",
            "a": [42, 33],
            "b": [48, 33],
            "value_m": 6.0,
            "kind": "depth",
            "of": "a-balcony",
            "patterns": [167],
        },
        {
            "id": "m-hall-span",
            "label": "Hall width",
            "a": [18, 26],
            "b": [28, 26],
            "value_m": 10.0,
            "kind": "width",
            "of": "a-hall",
            "patterns": [107],
        },
        {
            "id": "m-gap-ab",
            "label": "Gap A–B",
            "a": [42, 21],
            "b": [52, 21],
            "value_m": dist((42, 21), (52, 21)),
            "kind": "spacing",
            "of": "house-b",
            "patterns": [105],
        },
        {
            "id": "m-green-frontage",
            "label": "Green S frontage",
            "a": [28, 38],
            "b": [58, 38],
            "value_m": 30.0,
            "kind": "frontage",
            "of": "green-shared",
            "patterns": [106],
        },
        {
            "id": "m-ceil-hall",
            "label": "Hall ceiling",
            "a": [20, 24],
            "b": [20, 26.4],
            "value_m": 2.4,
            "kind": "height",
            "of": "a-hall",
            "patterns": [190],
        },
        {
            "id": "m-ceil-liv",
            "label": "Living ceiling",
            "a": [38, 24],
            "b": [38, 27],
            "value_m": 3.0,
            "kind": "height",
            "of": "a-living",
            "patterns": [190],
        },
    ]

    interfaces = [
        {"id": "if-approach", "kind": "door", "between": ["street-main", "a-court"], "opening": "a-door-approach"},
        {"id": "if-main", "kind": "threshold", "between": ["a-porch", "a-hall"], "opening": "a-door-main"},
        {"id": "if-porch-court", "kind": "threshold", "between": ["a-court", "a-porch"]},
        {"id": "if-liv", "kind": "door", "between": ["a-hall", "a-living"], "opening": "a-door-living"},
        {"id": "if-bed", "kind": "door", "between": ["a-living", "a-bedroom"], "opening": "a-door-bed"},
        {"id": "if-balc", "kind": "door", "between": ["a-bedroom", "a-balcony"], "opening": "a-door-balc"},
        {"id": "if-front-a", "kind": "frontage", "between": ["a-court", "street-main"], "length_m": 24.0},
        {"id": "if-overlook-liv", "kind": "overlook", "between": ["a-living", "a-court"], "opening": "a-win-liv-s"},
    ]

    interactions = [
        {"id": "ix-found-a-lot", "kind": "sit-on", "a": "found-a", "b": "lot-a", "note": "Pad sits on surveyed Lot A"},
        {"id": "ix-found-b-lot", "kind": "sit-on", "a": "found-b", "b": "lot-b"},
        {"id": "ix-found-c-lot", "kind": "sit-on", "a": "found-c", "b": "lot-c"},
        {"id": "ix-found-d-lot", "kind": "sit-on", "a": "found-d", "b": "lot-d"},
        {"id": "ix-found-w-lot", "kind": "sit-on", "a": "found-workshop", "b": "lot-workshop"},
        {"id": "ix-hall-found", "kind": "sit-on", "a": "a-hall", "b": "found-a"},
        {"id": "ix-porch-found", "kind": "sit-on", "a": "a-porch", "b": "found-a"},
        {"id": "ix-liv-found", "kind": "sit-on", "a": "a-living", "b": "found-a"},
        {"id": "ix-bed-found", "kind": "sit-on", "a": "a-bedroom", "b": "found-a"},
        {"id": "ix-porch-court", "kind": "outdoor-adjacency", "a": "a-porch", "b": "a-court"},
        {"id": "ix-mass-b", "kind": "sit-on", "a": "house-b", "b": "found-b"},
        {"id": "ix-mass-c", "kind": "sit-on", "a": "house-c", "b": "found-c"},
        {"id": "ix-mass-d", "kind": "sit-on", "a": "house-d", "b": "found-d"},
        {"id": "ix-mass-w", "kind": "sit-on", "a": "workshop", "b": "found-workshop"},
        {"id": "ix-clear-ab", "kind": "clearance", "a": "found-a", "b": "found-b", "min_m": 4.0, "note": "Lot side clearance"},
        {"id": "ix-pond-green", "kind": "sit-on", "a": "pond-a", "b": "green-shared", "note": "Pond sits on shared green"},
        {"id": "ix-court-outdoor", "kind": "outdoor-adjacency", "a": "a-court", "b": "a-living"},
        {"id": "ix-wall-hall-liv", "kind": "shared-wall", "a": "a-hall", "b": "a-living"},
    ]

    patterns = []
    for number, look_for, feature_ids, diagram in [
        (105, "Open land south of occupied rooms — measure the court.", ["a-court", "green-shared", "street-main", "m-court-depth"], {"kind": "zone+arrow", "zones": ["a-court", "green-shared"], "arrows": [{"from": (30, 26), "to": (30, 18), "label": "south"}], "measures": ["m-court-depth"]}),
        (106, "Outdoor rooms with definite shape.", ["a-court", "green-shared", "m-green-frontage"], {"kind": "zone", "zones": ["a-court", "green-shared"], "measures": ["m-green-frontage"]}),
        (107, "Narrow wings — hall clear span.", ["a-hall", "a-win-hall-s", "a-win-hall-w", "m-hall-span"], {"kind": "zone+rays", "zones": ["a-hall"], "rays": [{"at": (21, 22), "dir": (0, -1)}, {"at": (18, 26), "dir": (-1, 0)}], "measures": ["m-hall-span"]}),
        (110, "Address on the movement network.", ["a-door-main", "a-porch", "path-approach", "e-approach-3", "n-door"], {"kind": "marker", "markers": [{"at": (24, 22), "label": "entrance"}], "zones": ["a-hall", "a-porch"], "edges": ["e-approach-3"]}),
        (112, "Street → path → gate → court → porch → door.", ["e-approach-1", "e-approach-2", "e-approach-3", "a-court", "a-porch", "m-setback-a", "m-porch-depth"], {"kind": "sequence", "arrows": [{"from": (30, 4), "to": (30, 11), "label": "1"}, {"from": (30, 11), "to": (30, 18), "label": "2"}, {"from": (30, 18), "to": (24, 21), "label": "3"}], "zones": ["a-court", "path-approach", "a-porch"], "edges": ["e-approach-1", "e-approach-2", "e-approach-3"], "measures": ["m-setback-a", "m-approach-width", "m-porch-depth"]}),
        (127, "Public before private along the graph.", ["e-hall-liv", "e-liv-bed", "a-hall", "a-living", "a-bedroom"], {"kind": "sequence", "arrows": [{"from": (23, 26), "to": (35, 26), "label": "public"}, {"from": (35, 26), "to": (35, 33), "label": "private"}], "zones": ["a-hall", "a-living", "a-bedroom"], "edges": ["e-hall-liv", "e-liv-bed"]}),
        (128, "Day rooms that see the sun.", ["a-living", "a-win-liv-s", "a-win-liv-e"], {"kind": "zone+rays", "zones": ["a-living"], "rays": [{"at": (35, 22), "dir": (0, -1)}, {"at": (42, 26), "dir": (1, 0)}]}),
        (130, "Arrival is a room.", ["a-hall", "a-porch", "a-door-main"], {"kind": "zone", "zones": ["a-hall", "a-porch"]}),
        (159, "Windows on two sides.", ["a-win-hall-s", "a-win-hall-w", "a-win-liv-s", "a-win-liv-e", "a-win-bed-n", "a-win-bed-w"], {"kind": "openings", "openings": ["a-win-hall-s", "a-win-hall-w", "a-win-liv-s", "a-win-liv-e", "a-win-bed-n", "a-win-bed-w"]}),
        (167, "Balcony depth ≥ ~1.83 m (shown 6.0 m clear).", ["a-balcony", "m-balcony-depth"], {"kind": "zone+dim", "zones": ["a-balcony"], "measures": ["m-balcony-depth"]}),
        (180, "Place by the window.", ["a-win-liv-s", "a-living"], {"kind": "marker", "markers": [{"at": (35, 24), "label": "window place"}], "zones": ["a-living"]}),
        (190, "Ceiling heights differ.", ["m-ceil-hall", "m-ceil-liv", "a-hall", "a-living", "a-bedroom"], {"kind": "heights", "labels": [{"at": (23, 26), "text": "2.4 m"}, {"at": (35, 26), "text": "3.0 m"}, {"at": (35, 33), "text": "2.7 m"}], "zones": ["a-hall", "a-living", "a-bedroom"], "measures": ["m-ceil-hall", "m-ceil-liv"]}),
    ]:
        patterns.append(
            {
                "number": number,
                "name": NAMES[number],
                "look_for": look_for,
                "feature_ids": feature_ids,
                "kind": "judgment" if number in (110, 180) else "computed",
                "diagram": diagram,
            }
        )

    for p in places:
        p["ring"] = [list(pt) for pt in p["ring"]]

    return {
        "id": "seed-district",
        "title": "Seed District",
        "owned_layer": "pattern-language.plan-symbology",
        "concept_graph": "docs/design/spatial-concept-graph.json",
        "frame": {
            "units": "m",
            "north": "up",
            "latitude_deg": 40,
            "origin_lon": ORIGIN_LON,
            "origin_lat": ORIGIN_LAT,
        },
        "extent": {"min_x": -2, "min_y": -2, "max_x": 94, "max_y": 72},
        "places": places,
        "walls": walls,
        "openings": openings,
        "trees": trees,
        "network": {"nodes": nodes, "edges": edges},
        "measures": measures,
        "interfaces": interfaces,
        "interactions": interactions,
        "patterns": patterns,
        "names": {str(k): v for k, v in NAMES.items()},
    }


def export_geojson(plan: dict) -> dict:
    feats = []
    for p in plan["places"]:
        ring = p["ring"]
        coords = [list(m_to_lonlat(x, y)) for x, y in ring]
        coords.append(coords[0][:])
        feats.append(
            {
                "type": "Feature",
                "id": p["id"],
                "properties": {
                    "id": p["id"],
                    "label": p["label"],
                    "component": p["component"],
                    "kind": p["kind"],
                    "role": p.get("role", ""),
                    "patterns": p.get("patterns", []),
                },
                "geometry": {"type": "Polygon", "coordinates": [coords]},
            }
        )
    for e in plan["network"]["edges"]:
        poly = e.get("polyline") or []
        if len(poly) < 2:
            continue
        feats.append(
            {
                "type": "Feature",
                "id": e["id"],
                "properties": {
                    "id": e["id"],
                    "label": e.get("label", e["id"]),
                    "component": "centerline",
                    "hierarchy": e["hierarchy"],
                    "mode": e["mode"],
                    "width_m": e["width_m"],
                    "directed": e["directed"],
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [list(m_to_lonlat(x, y)) for x, y in poly],
                },
            }
        )
    return {"type": "FeatureCollection", "name": "seed-district", "features": feats}


def export_cityjson(plan: dict) -> dict:
    """CityJSON 2.0 export: LoD0 footprints + Road/TrafficArea children (U11)."""
    scale = 0.01
    vertices: list[list[int]] = []
    objects: dict = {}
    by_id = {p["id"]: p for p in plan["places"]}

    def add_solid(ring: list, h: float) -> list:
        base, top = [], []
        for x, y in ring:
            base.append(len(vertices))
            vertices.append([int(round(x / scale)), int(round(y / scale)), 0])
            top.append(len(vertices))
            vertices.append([int(round(x / scale)), int(round(y / scale)), int(round(h / scale))])
        faces = [[base + [base[0]]], [list(reversed(top + [top[0]]))]]
        n = len(base)
        for i in range(n):
            j = (i + 1) % n
            faces.append([[base[i], base[j], top[j], top[i], base[i]]])
        return [faces]

    def add_surface(ring: list) -> list:
        idxs = []
        for x, y in list(ring) + [ring[0]]:
            idxs.append(len(vertices))
            vertices.append([int(round(x / scale)), int(round(y / scale)), 0])
        return [[idxs]]

    def lod0_surface(ring: list) -> dict:
        return {"type": "MultiSurface", "lod": "0", "boundaries": add_surface(ring)}

    def lod1_surface(ring: list) -> dict:
        return {"type": "MultiSurface", "lod": "1", "boundaries": add_surface(ring)}

    # House A composite footprint (court + rooms) as Building with LoD0 + LoD1.
    house_a_ring = [(18, 14), (42, 14), (42, 36), (18, 36)]
    objects["house-a"] = {
        "type": "Building",
        "attributes": {"name": "House A", "floorPlan": "plan-model"},
        "geometry": [
            lod0_surface(house_a_ring),
            {"type": "Solid", "lod": "1", "boundaries": add_solid(house_a_ring, 7.2)},
        ],
    }
    for p in plan["places"]:
        if p["kind"] != "solid":
            continue
        objects[p["id"]] = {
            "type": "Building",
            "attributes": {"name": p["label"], "massing": True},
            "geometry": [
                lod0_surface(p["ring"]),
                {"type": "Solid", "lod": "1", "boundaries": add_solid(p["ring"], p.get("height_m") or 6.0)},
            ],
        }

    # Main street Road with TrafficArea children (granularity way).
    street = by_id["street-main"]
    carriageway = by_id["carriageway-main"]
    sidewalk = by_id["sidewalk-main-n"]
    objects["street-main"] = {
        "type": "Road",
        "attributes": {
            "name": street["label"],
            "trafficDirection": "both",
            "class": "section",
            "granularity": "way",
        },
        "children": ["carriageway-main", "sidewalk-main-n"],
        "geometry": [lod0_surface(street["ring"]), lod1_surface(street["ring"])],
    }
    objects["carriageway-main"] = {
        "type": "TrafficArea",
        "parents": ["street-main"],
        "attributes": {
            "name": carriageway["label"],
            "function": "drivingLane",
            "granularity": "way",
            "surfaceMaterial": "asphalt",
        },
        "geometry": [lod0_surface(carriageway["ring"])],
    }
    objects["sidewalk-main-n"] = {
        "type": "TrafficArea",
        "parents": ["street-main"],
        "attributes": {
            "name": sidewalk["label"],
            "function": "footpath",
            "granularity": "way",
            "surfaceMaterial": "concrete",
        },
        "geometry": [lod0_surface(sidewalk["ring"])],
    }

    lane = by_id.get("street-lane")
    if lane:
        objects["street-lane"] = {
            "type": "Road",
            "attributes": {
                "name": lane["label"],
                "trafficDirection": "both",
                "class": "section",
                "hierarchy": "lane",
            },
            "geometry": [lod0_surface(lane["ring"])],
        }

    for p in plan["places"]:
        roles = set(p.get("roles") or [])
        if "lot" in roles or "parcel" in roles:
            objects[p["id"]] = {
                "type": "LandUse",
                "attributes": {"name": p["label"], "class": "parcel"},
                "geometry": [lod0_surface(p["ring"])],
            }
        elif p["id"] == "green-shared" or "green" in roles:
            objects[p["id"]] = {
                "type": "PlantCover",
                "attributes": {"name": p["label"], "cover": "grass"},
                "geometry": [lod0_surface(p["ring"]), lod1_surface(p["ring"])],
            }
        elif "pond" in roles or p.get("component") == "pond":
            objects[p["id"]] = {
                "type": "WaterBody",
                "attributes": {"name": p["label"], "class": "pond", "authored": True},
                "geometry": [lod0_surface(p["ring"])],
            }
        elif "gravel" in roles:
            objects[p["id"]] = {
                "type": "LandUse",
                "attributes": {"name": p["label"], "class": "gravel"},
                "geometry": [lod0_surface(p["ring"])],
            }

    for t in plan.get("trees") or []:
        # Point footprint as tiny LoD0 square around trunk.
        half = max(0.15, float(t.get("trunk") or 0.25))
        x, y = float(t["x"]), float(t["y"])
        ring = [(x - half, y - half), (x + half, y - half), (x + half, y + half), (x - half, y + half)]
        objects[t["id"]] = {
            "type": "SolitaryVegetationObject",
            "attributes": {
                "name": t.get("label") or t["id"],
                "species": t.get("species"),
                "form": t.get("form"),
                "canopy_m": t.get("canopy"),
            },
            "geometry": [lod0_surface(ring)],
        }

    return {
        "type": "CityJSON",
        "version": "2.0",
        "transform": {"scale": [scale, scale, scale], "translate": [0.0, 0.0, 0.0]},
        "metadata": {
            "title": "Seed District",
            "spatialStructure": "plan-model",
            "referenceSystem": "local-metres",
        },
        "CityObjects": objects,
        "vertices": vertices,
    }


def main() -> int:
    from pattern_language.spatial_lint import lint_plan

    OUT.mkdir(parents=True, exist_ok=True)
    plan = build_plan()
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(plan)
    lint_errors = lint_plan(plan)
    if lint_errors:
        for line in lint_errors:
            print(line, file=sys.stderr)
        raise SystemExit(f"spatial lint failed: {len(lint_errors)} errors")
    (OUT / "plan-model.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    (OUT / "district.geojson").write_text(json.dumps(export_geojson(plan), indent=2) + "\n", encoding="utf-8")
    (OUT / "district.city.json").write_text(json.dumps(export_cityjson(plan), indent=2) + "\n", encoding="utf-8")
    (OUT / "pattern-components.json").write_text(
        json.dumps({"patterns": plan["patterns"], "names": plan["names"]}, indent=2) + "\n",
        encoding="utf-8",
    )
    graph_src = ROOT / "docs" / "design" / "spatial-concept-graph.json"
    if graph_src.is_file():
        (OUT / "concept-graph.json").write_text(graph_src.read_text(encoding="utf-8"), encoding="utf-8")
    print(
        "plan-model ok:",
        f"{len(plan['places'])} places,",
        f"{len(plan['network']['edges'])} edges,",
        f"{len(plan['measures'])} measures,",
        f"{len(plan['interfaces'])} interfaces",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
