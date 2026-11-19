"""Occupied spaces stay within a set depth of an exterior wall."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pattern_language.conditions.evidence import Evidence, make_evidence
from pattern_language.conditions.measure import (
    boundaries_for,
    dec,
    require_number,
    room_depth,
    spaces_under,
)
from pattern_language.topology import Topology

CHECK_ID = "wings-of-light"


def check(topology: Topology, center: str, params: Mapping[str, Any]) -> Evidence:
    """Pass when every occupied depth is finite and within ``max_depth_m``."""
    limit = require_number(params, "max_depth_m", CHECK_ID)
    zones = [zone for zone in spaces_under(topology, center) if "occupied" in zone.tags]
    if not zones:
        return make_evidence(CHECK_ID, passed=False, applicable=False)
    depths = [
        room_depth(zone, boundaries_for(topology, zone.name, external=True)) for zone in zones
    ]
    worst = max(depths)
    return make_evidence(
        CHECK_ID,
        passed=all(depth <= limit for depth in depths),
        applicable=True,
        subjects=[zone.name for zone in zones],
        measured=(("max_depth_m", dec(worst)),),
    )
