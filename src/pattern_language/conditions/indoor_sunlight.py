"""Daytime rooms lie equator-ward of the other occupied rooms."""

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

CHECK_ID = "indoor-sunlight"


def check(topology: Topology, center: str, params: Mapping[str, Any]) -> Evidence:
    """Pass when every daytime centroid is equator-ward of the non-daytime occupied set."""
    latitude = require_number(params, "latitude_deg", CHECK_ID)
    zones = spaces_under(topology, center)
    daytime = [zone for zone in zones if "daytime" in zone.tags]
    reference_zones = [
        zone for zone in zones if "occupied" in zone.tags and "daytime" not in zone.tags
    ]
    if not daytime or not reference_zones:
        return make_evidence(
            CHECK_ID,
            passed=False,
            applicable=False,
            subjects=[zone.name for zone in daytime],
        )
    direction = equator_direction(topology.north, latitude)
    reference = mean_centroid(reference_zones)
    if direction is None:
        dot = 0.0
        passed = False
    else:
        dots = [
            direction_dot(polygon_centroid(zone.footprint), reference, direction) for zone in daytime
        ]
        dot = min(dots)
        passed = all(item > 0 for item in dots)
    return make_evidence(
        CHECK_ID,
        passed=passed,
        applicable=True,
        subjects=[zone.name for zone in daytime],
        measured=(("dot", dec(dot)),),
    )
