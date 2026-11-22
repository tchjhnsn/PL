from __future__ import annotations

from pathlib import Path

from pattern_language.conditions.plan_clearance import meets_clear_width
from pattern_language.conditions.registry import CHECKS
from pattern_language.conditions.six_foot_balcony import check as six_foot_balcony_check
from pattern_language.spatial_structure import (
    clear_width,
    edge_width,
    load_spatial,
    measure_value,
    places_with_role,
)

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "demo" / "data" / "plan-model.json"


def test_load_and_widths() -> None:
    plan = load_spatial(PLAN)
    assert clear_width(plan, "sidewalk-main-n") == 2.5
    assert clear_width(plan, "a-balcony") == 6.0
    assert clear_width(plan, "carriageway-main") == 5.5
    assert measure_value(plan, "m-sidewalk-width") == 2.5
    assert measure_value(plan, "m-balcony-depth") == 6.0
    assert edge_width(plan, "e-main-1") == 5.5
    assert edge_width(plan, "e-sidewalk-1") == 2.5
    assert len(plan["network"]["edges"]) >= 10


def test_roles() -> None:
    plan = load_spatial(PLAN, validate=False)
    sidewalks = places_with_role(plan, "sidewalk")
    assert any(p["id"] == "sidewalk-main-n" for p in sidewalks)
    assert any(p["id"] == "carriageway-main" for p in places_with_role(plan, "carriageway"))
    assert any("row" in (p.get("roles") or []) for p in plan["places"])
    assert any(p["id"] == "block-south" for p in places_with_role(plan, "block"))
    assert any(p["id"] == "block-east" for p in places_with_role(plan, "block"))
    assert any(p["id"] == "block-northeast" for p in places_with_role(plan, "block"))
    assert any(p["id"] == "street-cross" for p in plan["places"])
    assert any(p["id"] == "street-north" for p in plan["places"])
    assert any(p["id"] == "district-seed" for p in places_with_role(plan, "district"))
    assert any(p["id"] == "lot-workshop" for p in places_with_role(plan, "work"))
    addr = [n for n in plan["network"]["nodes"] if n.get("kind") == "address"]
    assert {n["id"] for n in addr} >= {
        "n-door",
        "n-addr-b",
        "n-addr-c",
        "n-addr-d",
        "n-addr-w",
        "n-addr-e",
        "n-addr-f",
        "n-addr-g",
        "n-addr-h",
    }
    assert measure_value(plan, "m-frontage-rhythm-main") == 54.0
    assert measure_value(plan, "m-cross-width") == 4.0
    assert measure_value(plan, "m-enclosure-main") == 0.35
    assert measure_value(plan, "m-city-span-x") == 150.0
    assert len(places_with_role(plan, "block")) >= 5
    assert any(p["id"] == "lot-i" for p in plan["places"])
    assert any(p["id"] == "lot-j" for p in plan["places"])
    assert any(p["id"] == "district-metro" for p in places_with_role(plan, "district"))
    assert any(p["id"] == "district-metro-east" for p in places_with_role(plan, "district"))
    assert any("park" in (p.get("roles") or []) for p in plan["places"])
    assert any("school" in (p.get("roles") or []) for p in plan["places"])
    assert measure_value(plan, "m-metro-width") >= 400.0
    assert len(plan["places"]) >= 500


def test_balcony_clear_width_meets_threshold() -> None:
    plan = load_spatial(PLAN)
    assert meets_clear_width(plan, "a-balcony", 1.83) is True
    assert meets_clear_width(plan, "no-such-place", 1.83) is None
    shallow = {
        "measures": [
            {"id": "m", "of": "a-balcony", "kind": "depth", "value_m": 1.0},
        ]
    }
    assert meets_clear_width(shallow, "a-balcony", 1.83) is False


def test_plan_helper_stays_out_of_checks() -> None:
    modules = {function.__module__ for function in CHECKS.values()}
    assert "pattern_language.conditions.plan_clearance" not in modules
    assert len(CHECKS) == 10
    assert CHECKS["six-foot-balcony"] is six_foot_balcony_check
