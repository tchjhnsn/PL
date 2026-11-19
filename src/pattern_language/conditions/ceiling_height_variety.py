"""Occupied ceiling heights span at least a set difference."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pattern_language.conditions.evidence import Evidence, make_evidence
from pattern_language.conditions.measure import dec, require_number, spaces_under
from pattern_language.topology import Topology, Zone

CHECK_ID = "ceiling-height-variety"


def check(topology: Topology, center: str, params: Mapping[str, Any]) -> Evidence:
    """Pass when the tallest and shortest occupied heights differ by the threshold."""
    minimum = require_number(params, "min_height_difference_m", CHECK_ID)
    zones = [zone for zone in spaces_under(topology, center) if _occupied_height(zone)]
    if len(zones) < 2:
        return make_evidence(
            CHECK_ID,
            passed=False,
            applicable=False,
            subjects=[zone.name for zone in zones],
        )
    heights = [float(zone.height_m) for zone in zones if zone.height_m is not None]
    difference = max(heights) - min(heights)
    return make_evidence(
        CHECK_ID,
        passed=difference >= minimum,
        applicable=True,
        subjects=[zone.name for zone in zones],
        measured=(("difference_m", dec(difference)),),
    )


def _occupied_height(zone: Zone) -> bool:
    return "occupied" in zone.tags and isinstance(zone.height_m, (int, float)) and not isinstance(
        zone.height_m, bool
    )
