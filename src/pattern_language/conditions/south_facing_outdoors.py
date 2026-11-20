"""The main outdoor space lies equator-ward of the occupied rooms."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pattern_language.conditions.evidence import Evidence, make_evidence
from pattern_language.conditions.measure import (
    dec,
    direction_dot,
    equator_direction,
    mean_centroid,
    polygon_centroid,
    require_number,
    spaces_under,
)
from pattern_language.topology import Topology

CHECK_ID = "south-facing-outdoors"


def check(topology: Topology, center: str, params: Mapping[str, Any]) -> Evidence:
    """Pass when the one main outdoor centroid is equator-ward of occupied rooms."""
    latitude = require_number(params, "latitude_deg", CHECK_ID)
    zones = spaces_under(topology, center)
    outdoors = [zone for zone in zones if "outdoor" in zone.tags and "balcony" not in zone.tags]
    occupied = [zone for zone in zones if "occupied" in zone.tags]
    subjects = [zone.name for zone in outdoors]
    frame = (
        ("latitude_deg", dec(latitude)),
        ("north_x", dec(topology.north[0])),
        ("north_y", dec(topology.north[1])),
    )
    if len(outdoors) != 1 or not occupied:
        return make_evidence(
            CHECK_ID,
            passed=False,
            applicable=False,
            subjects=subjects,
            measured=frame,
        )
    direction = equator_direction(topology.north, latitude)
    dot = 0.0
    if direction is not None:
        dot = direction_dot(polygon_centroid(outdoors[0].footprint), mean_centroid(occupied), direction)
    return make_evidence(
        CHECK_ID,
        passed=direction is not None and dot > 0,
        applicable=True,
        subjects=subjects,
        measured=(*frame, ("dot", dec(dot))),
    )
