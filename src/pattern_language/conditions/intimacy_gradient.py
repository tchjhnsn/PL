"""Public rooms are closer to the entrance than semi-private, then private."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from pattern_language.conditions.evidence import Evidence, make_evidence
from pattern_language.conditions.measure import (
    distances_from,
    door_graph,
    entrance,
    flag,
    spaces_under,
)
from pattern_language.topology import Topology

CHECK_ID = "intimacy-gradient"
_RANKS = {"public": 0, "semi-private": 1, "private": 2}


def check(topology: Topology, center: str, params: Mapping[str, Any]) -> Evidence:
    """Pass when all three ranks occur and a lower rank is always closer."""
    del params
    found = entrance(topology, center)
    if found is None:
        return make_evidence(CHECK_ID, passed=False, applicable=False)
    zones = spaces_under(topology, center)
    graph = door_graph(topology, {zone.name for zone in zones})
    distances = distances_from(graph, found.arrival)
    ranked: list[tuple[int, float]] = []
    subjects: list[str] = []
    doubled = False
    for zone in zones:
        present = [tag for tag in _RANKS if tag in zone.tags]
        if not present:
            continue
        subjects.append(zone.name)
        if len(present) > 1:
            doubled = True
            continue
        ranked.append((_RANKS[present[0]], float(distances.get(zone.name, math.inf))))
    passed = _ordered(ranked) and not doubled
    return make_evidence(
        CHECK_ID,
        passed=passed,
        applicable=True,
        subjects=subjects,
        measured=(("ordered", flag(passed)),),
    )


def _ordered(ranked: list[tuple[int, float]]) -> bool:
    ranks = {rank for rank, _distance in ranked}
    if ranks != {0, 1, 2}:
        return False
    for left_rank, left_distance in ranked:
        for right_rank, right_distance in ranked:
            if left_rank < right_rank and not left_distance < right_distance:
                return False
    return True
