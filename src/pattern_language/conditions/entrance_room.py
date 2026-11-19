"""The entrance arrival is a room, and neither a corridor nor a living room."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pattern_language.conditions.evidence import Evidence, make_evidence
from pattern_language.conditions.measure import entrance, flag, spaces_under
from pattern_language.topology import Topology

CHECK_ID = "entrance-room"


def check(topology: Topology, center: str, params: Mapping[str, Any]) -> Evidence:
    """Pass when the arrival is tagged room and is tagged neither corridor nor living."""
    del params
    found = entrance(topology, center)
    if found is None:
        return make_evidence(CHECK_ID, passed=False, applicable=False)
    tags = next(zone.tags for zone in spaces_under(topology, center) if zone.name == found.arrival)
    passed = "room" in tags and "corridor" not in tags and "living" not in tags
    return make_evidence(
        CHECK_ID,
        passed=passed,
        applicable=True,
        subjects=(found.arrival,),
        measured=(("room", flag(passed)),),
    )
