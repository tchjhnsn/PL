"""Urban typology ontology validates and binds to the kit library."""

from __future__ import annotations

from pattern_language.kits.registry import KIT_CALLABLES, library_summary, resolve_kit
from pattern_language.urban_typology import (
    components_for_type,
    get_type,
    load_urban_typologies,
    match_place_roles,
    types_in_layer,
)


def test_ontology_loads_and_has_core_layers() -> None:
    doc = load_urban_typologies()
    assert doc["id"] == "pattern-language.urban-typology"
    layer_ids = {layer["id"] for layer in doc["layers"]}
    assert layer_ids >= {
        "fabric",
        "transect",
        "street",
        "block",
        "plot",
        "building",
        "open_space",
        "program",
    }
    assert len(doc["types"]) >= 20
    assert len(doc["components"]) >= 5


def test_conzen_street_plot_building_present() -> None:
    streets = types_in_layer("street")
    plots = types_in_layer("plot")
    buildings = types_in_layer("building")
    assert any(t["id"] == "ut.street.local" for t in streets)
    assert any(t["id"] == "ut.plot.frontage" for t in plots)
    assert any(t["id"] == "ut.building.block-edge" for t in buildings)


def test_green_finger_patterns() -> None:
    finger = get_type("ut.open.green-finger")
    assert finger["patterns"] == [3, 60, 67]
    comps = components_for_type("ut.open.green-finger")
    assert any(c["id"] == "comp.program-place" for c in comps)


def test_implemented_kits_resolve() -> None:
    summary = library_summary()
    assert "comp.frontage-lot" in summary["implemented"]
    assert "comp.street-section" in summary["planned"]
    stamp = resolve_kit("comp.frontage-lot")
    assert stamp is KIT_CALLABLES["pattern_language.kits.frontage_lot.stamp_frontage_lot"]


def test_match_place_roles_park() -> None:
    hits = match_place_roles(["park", "green"], component="park")
    ids = {t["id"] for t in hits}
    assert "ut.open.green-finger" in ids or "ut.open.country-fringe" in ids
