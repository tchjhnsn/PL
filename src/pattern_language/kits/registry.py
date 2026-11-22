"""Component library registry — typology → kit entrypoints.

The formal catalog lives in schema/ontology/urban-typologies.json.
This module re-exports implemented kits for stampers.
"""

from __future__ import annotations

from typing import Any, Callable

from pattern_language.kits.city_fabric import generate_city_fabric
from pattern_language.kits.frontage_lot import FrontageLotSpec, stamp_frontage_lot
from pattern_language.kits.program_place import ProgramPlaceSpec, stamp_program_place
from pattern_language.urban_typology import get_component, implemented_kits, load_urban_typologies

KIT_CALLABLES: dict[str, Callable[..., Any]] = {
    "pattern_language.kits.frontage_lot.stamp_frontage_lot": stamp_frontage_lot,
    "pattern_language.kits.program_place.stamp_program_place": stamp_program_place,
    "pattern_language.kits.city_fabric.generate_city_fabric": generate_city_fabric,
}


def resolve_kit(comp_id: str) -> Callable[..., Any]:
    """Return the callable for an implemented component id (e.g. comp.frontage-lot)."""
    comp = get_component(comp_id)
    if comp["status"] != "implemented" or not comp.get("kit"):
        raise KeyError(f"{comp_id} is not an implemented kit ({comp['status']})")
    path = comp["kit"]
    if path not in KIT_CALLABLES:
        raise KeyError(f"no callable registered for {path}")
    return KIT_CALLABLES[path]


def library_summary() -> dict[str, Any]:
    doc = load_urban_typologies()
    return {
        "types": len(doc["types"]),
        "components": len(doc["components"]),
        "implemented": [c["id"] for c in implemented_kits(doc=doc)],
        "planned": [c["id"] for c in doc["components"] if c["status"] == "planned"],
    }


__all__ = [
    "FrontageLotSpec",
    "ProgramPlaceSpec",
    "KIT_CALLABLES",
    "generate_city_fabric",
    "library_summary",
    "resolve_kit",
    "stamp_frontage_lot",
    "stamp_program_place",
]
