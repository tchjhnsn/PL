"""Every elevated balcony is at least as deep as the threshold."""

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
    """Pass when every elevated balcony's shallowest off-wall depth meets ``min_depth_m``.

    A space tagged ``balcony`` must also sit at ``floor_elevation_m >= min_elevation_m``
    (default 2.4). Ground-level outdoor edges are not balconies; the check is then
    not applicable.
    """
    minimum = require_number(params, "min_depth_m", CHECK_ID)
    min_elev = float(params.get("min_elevation_m", 2.4))
    tagged = [zone for zone in spaces_under(topology, center) if "balcony" in zone.tags]
    balconies = [
        zone
        for zone in tagged
        if zone.floor_elevation_m is not None and zone.floor_elevation_m >= min_elev
    ]
    if not balconies:
        measured = (("min_elevation_m", dec(min_elev)),)
        if tagged:
            lowest = min(
                (zone.floor_elevation_m for zone in tagged if zone.floor_elevation_m is not None),
                default=0.0,
            )
            measured = (("floor_elevation_m", dec(lowest)), ("min_elevation_m", dec(min_elev)))
        return make_evidence(
            CHECK_ID,
            passed=False,
            applicable=False,
            subjects=[zone.name for zone in tagged],
            measured=measured,
        )
    depths = [
        balcony_depth(zone, boundaries_for(topology, zone.name, external=False)) for zone in balconies
    ]
    elevations = [
        0.0 if zone.floor_elevation_m is None else zone.floor_elevation_m for zone in balconies
    ]
    return make_evidence(
        CHECK_ID,
        passed=all(depth >= minimum for depth in depths),
        applicable=True,
        subjects=[zone.name for zone in balconies],
        measured=(
            ("floor_elevation_m", dec(min(elevations))),
            ("min_depth_m", dec(min(depths))),
            ("min_elevation_m", dec(min_elev)),
        ),
    )
