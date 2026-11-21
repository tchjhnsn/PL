"""Object library kits stamp valid frontage lots and city fabric."""

from __future__ import annotations

from pattern_language.kits import (
    FrontageLotSpec,
    ProgramPlaceSpec,
    generate_city_fabric,
    stamp_frontage_lot,
    stamp_program_place,
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


def test_program_place_school() -> None:
    kit = stamp_program_place(
        ProgramPlaceSpec(
            key="sch-test",
            label="Test school",
            program="school",
            ring=((0, 0), (40, 0), (40, 40), (0, 40)),
            mass_ring=((6, 6), (34, 6), (34, 34), (6, 34)),
        )
    )
    ids = {p["id"] for p in kit["places"]}
    assert "lot-sch-test" in ids
    assert "bldg-sch-test" in ids
    assert 85 in kit["places"][0]["patterns"]


def test_city_fabric_has_civic_and_fingers() -> None:
    fabric = generate_city_fabric(origin_x=0, origin_y=0, cols=8, rows=6)
    roles = {r for p in fabric["places"] for r in (p.get("roles") or [])}
    assert "park" in roles
    assert "school" in roles
    assert "grocery" in roles or "shop" in roles
    assert any(p["id"] == "district-metro" for p in fabric["places"])
    comps = {p.get("component") for p in fabric["places"]}
    assert "civic" in comps or any("town" in (p.get("label") or "").lower() for p in fabric["places"])
    assert any(m["id"] == "m-metro-width" for m in fabric["measures"])
    assert m_metro_width_ge_400(fabric)


def m_metro_width_ge_400(fabric: dict) -> bool:
    m = next(x for x in fabric["measures"] if x["id"] == "m-metro-width")
    return m["value_m"] >= 400
