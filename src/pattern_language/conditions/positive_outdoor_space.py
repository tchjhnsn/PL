"""Each outdoor space is mostly convex."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pattern_language.conditions.evidence import CheckError, Evidence, make_evidence
from pattern_language.conditions.measure import dec, hull_area, polygon_area, require_number, spaces_under
from pattern_language.topology import Topology

CHECK_ID = "positive-outdoor-space"


def check(topology: Topology, center: str, params: Mapping[str, Any]) -> Evidence:
    """Pass when every outdoor footprint area over hull area meets the ratio."""
    threshold = require_number(params, "min_convexity_ratio", CHECK_ID)
    zones = [zone for zone in spaces_under(topology, center) if "outdoor" in zone.tags]
    if not zones:
        return make_evidence(CHECK_ID, passed=False, applicable=False)
    ratios: list[float] = []
    for zone in zones:
        hull = hull_area(zone.footprint)
        if hull == 0:
            raise CheckError("hull area is 0")
        ratios.append(polygon_area(zone.footprint) / hull)
    return make_evidence(
        CHECK_ID,
        passed=all(ratio >= threshold for ratio in ratios),
        applicable=True,
        subjects=[zone.name for zone in zones],
        measured=(("min_ratio", dec(min(ratios))),),
    )
