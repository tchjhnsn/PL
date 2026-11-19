"""Every balcony is at least as deep as the threshold."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pattern_language.conditions.evidence import Evidence, make_evidence
from pattern_language.conditions.measure import (
    balcony_depth,
    boundaries_for,
    dec,
    require_number,
    spaces_under,
)
from pattern_language.topology import Topology

CHECK_ID = "six-foot-balcony"


def check(topology: Topology, center: str, params: Mapping[str, Any]) -> Evidence:
    """Pass when every balcony's shallowest off-wall depth meets ``min_depth_m``."""
    minimum = require_number(params, "min_depth_m", CHECK_ID)
    zones = [zone for zone in spaces_under(topology, center) if "balcony" in zone.tags]
    if not zones:
        return make_evidence(CHECK_ID, passed=False, applicable=False)
    depths = [
        balcony_depth(zone, boundaries_for(topology, zone.name, external=False)) for zone in zones
    ]
    return make_evidence(
        CHECK_ID,
        passed=all(depth >= minimum for depth in depths),
        applicable=True,
        subjects=[zone.name for zone in zones],
        measured=(("min_depth_m", dec(min(depths))),),
    )
