"""Each occupied space has windows on enough distinct orientations."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pattern_language.conditions.evidence import Evidence, make_evidence
from pattern_language.conditions.measure import dec, require_number, spaces_under
from pattern_language.topology import Topology

CHECK_ID = "light-on-two-sides"


def check(topology: Topology, center: str, params: Mapping[str, Any]) -> Evidence:
    """Pass when every occupied space has at least ``min_orientations`` window sides."""
    minimum = require_number(params, "min_orientations", CHECK_ID)
    zones = [zone for zone in spaces_under(topology, center) if "occupied" in zone.tags]
    if not zones:
        return make_evidence(CHECK_ID, passed=False, applicable=False)
    counts: list[int] = []
    for zone in zones:
        orientations = {
            opening.orientation
            for opening in topology.openings
            if opening.kind == "window" and zone.name in opening.spaces
        }
        counts.append(len(orientations))
    smallest = min(counts)
    return make_evidence(
        CHECK_ID,
        passed=all(count >= minimum for count in counts),
        applicable=True,
        subjects=[zone.name for zone in zones],
        measured=(("min_orientations", dec(float(smallest))),),
    )
