"""Table from each catalog check id to one function."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from types import MappingProxyType
from typing import Any

from pattern_language.conditions import ceiling_height_variety
from pattern_language.conditions import entrance_room
from pattern_language.conditions import entrance_transition
from pattern_language.conditions import indoor_sunlight
from pattern_language.conditions import intimacy_gradient
from pattern_language.conditions import light_on_two_sides
from pattern_language.conditions import positive_outdoor_space
from pattern_language.conditions import six_foot_balcony
from pattern_language.conditions import south_facing_outdoors
from pattern_language.conditions import wings_of_light
from pattern_language.conditions.evidence import Evidence
from pattern_language.topology import Topology

CheckFn = Callable[[Topology, str, Mapping[str, Any]], Evidence]

CHECKS: Mapping[str, CheckFn] = MappingProxyType(
    {
        ceiling_height_variety.CHECK_ID: ceiling_height_variety.check,
        entrance_room.CHECK_ID: entrance_room.check,
        entrance_transition.CHECK_ID: entrance_transition.check,
        indoor_sunlight.CHECK_ID: indoor_sunlight.check,
        intimacy_gradient.CHECK_ID: intimacy_gradient.check,
        light_on_two_sides.CHECK_ID: light_on_two_sides.check,
        positive_outdoor_space.CHECK_ID: positive_outdoor_space.check,
        six_foot_balcony.CHECK_ID: six_foot_balcony.check,
        south_facing_outdoors.CHECK_ID: south_facing_outdoors.check,
        wings_of_light.CHECK_ID: wings_of_light.check,
    }
)
