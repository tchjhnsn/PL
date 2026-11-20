"""Spatial geometry lint for the seed district plan."""

from __future__ import annotations

import json
from pathlib import Path

from pattern_language.spatial_lint import lint_plan, overlaps, separation_m


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "demo" / "data" / "plan-model.json"


def test_seed_plan_passes_spatial_lint() -> None:
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    assert lint_plan(plan) == []


def test_overlap_and_clearance_helpers() -> None:
    a = [(0, 0), (10, 0), (10, 10), (0, 10)]
    b = [(10, 0), (20, 0), (20, 10), (10, 10)]  # touch only
    c = [(5, 5), (15, 5), (15, 15), (5, 15)]  # area overlap
    assert not overlaps(a, b)
    assert overlaps(a, c)
    assert separation_m(a, [(14, 0), (24, 0), (24, 10), (14, 10)]) == 4.0


def test_deliberate_lot_overlap_is_caught() -> None:
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    broken = json.loads(json.dumps(plan))
    for p in broken["places"]:
        if p["id"] == "lot-b":
            p["ring"] = [[30, 10], [74, 10], [74, 32], [30, 32]]
            break
    errors = lint_plan(broken)
    assert any("overlap: lots" in e for e in errors)
