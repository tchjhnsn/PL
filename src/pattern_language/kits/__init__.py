"""Stampable SpatialStructure kits — the object library for city composition."""

from pattern_language.kits.city_fabric import generate_city_fabric
from pattern_language.kits.frontage_lot import FrontageLotSpec, stamp_frontage_lot
from pattern_language.kits.program_place import ProgramPlaceSpec, stamp_program_place

__all__ = [
    "FrontageLotSpec",
    "ProgramPlaceSpec",
    "generate_city_fabric",
    "stamp_frontage_lot",
    "stamp_program_place",
]
