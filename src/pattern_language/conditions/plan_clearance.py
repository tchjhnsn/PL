"""Plan-side clear-width comparison.

Not a CHECKS entry. ``six_foot_balcony.check`` remains the Topology reading.
This module does not open a file.
"""

from __future__ import annotations

from typing import Any

from pattern_language.spatial_structure import clear_width


def meets_clear_width(plan: dict[str, Any], place_id: str, minimum_m: float) -> bool | None:
    """True when the place's clear width is at least ``minimum_m``.

    None when the plan has no width or depth measure for ``place_id``.
    """
    span = clear_width(plan, place_id)
    if span is None:
        return None
    return span >= minimum_m
