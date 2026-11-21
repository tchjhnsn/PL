"""Object library kits stamp valid frontage lots."""

from __future__ import annotations

from pattern_language.kits import FrontageLotSpec, stamp_frontage_lot


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
