"""Object library kits stamp frontage lots and city fabric."""

from __future__ import annotations

from pattern_language.kits import (
    FrontageLotSpec,
    generate_city_fabric,
    stamp_frontage_lot,
)


def test_frontage_lot_kit_ids() -> None:
    kit = stamp_frontage_lot(
        FrontageLotSpec(
            key="z",
            label="Z",
            block_id="block-test",
            street_id="street-main",
            lot_ring=((0, 0), (10, 0), (10, 20), (0, 20)),
            found_ring=((1, 6), (9, 6), (9, 18), (1, 18)),
            court_ring=((1, 0), (9, 0), (9, 6), (1, 6)),
            mass_ring=((1, 6), (9, 6), (9, 18), (1, 18)),
            gate_xy=(5, 0),
            path_ring=((4, -2), (6, -2), (6, 0), (4, 0)),
        )
    )
    ids = {p["id"] for p in kit["places"]}
    assert ids >= {"lot-z", "found-z", "z-court", "house-z", "path-approach-z"}
    assert any(o["id"] == "z-door-approach" for o in kit["openings"])
    assert any(n["kind"] == "address" for n in kit["nodes"])
    assert any(m["kind"] == "frontage" for m in kit["measures"])


def test_city_fabric_has_fingers_and_civic() -> None:
    fabric = generate_city_fabric(origin_x=0, origin_y=0, cols=8, rows=6)
    roles = {r for p in fabric["places"] for r in (p.get("roles") or [])}
    assert "park" in roles
    assert "school" in roles
    assert "shop" in roles or "grocery" in roles
    assert any(p["id"] == "district-metro" for p in fabric["places"])
    assert any("finger" in p["id"] for p in fabric["places"])
    width = next(m for m in fabric["measures"] if m["id"] == "m-metro-width")
    assert width["value_m"] >= 400
