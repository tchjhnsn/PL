"""The door path from the street passes through a transition space."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pattern_language.conditions.evidence import Evidence, make_evidence
from pattern_language.conditions.measure import entrance, flag, spaces_under
from pattern_language.topology import Topology

CHECK_ID = "entrance-transition"


def check(topology: Topology, center: str, params: Mapping[str, Any]) -> Evidence:
    """Pass when a strict intermediate node of the entrance path is tagged transition."""
    del params
    found = entrance(topology, center)
    if found is None:
        return make_evidence(CHECK_ID, passed=False, applicable=False)
    by_name = {zone.name: zone for zone in spaces_under(topology, center)}
    passed = any("transition" in by_name[name].tags for name in found.path[1:-1])
    return make_evidence(
        CHECK_ID,
        passed=passed,
        applicable=True,
        subjects=found.path,
        measured=(("transition", flag(passed)),),
    )
