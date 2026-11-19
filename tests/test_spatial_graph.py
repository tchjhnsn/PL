"""Spatial concept graph integrity (not part of catalog gate)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_spatial_graph_integrity() -> None:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_spatial_graph.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_plan_model_validates() -> None:
    from jsonschema import Draft202012Validator

    plan = json.loads((ROOT / "demo" / "data" / "plan-model.json").read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "schema" / "spatial-structure.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(plan)
    assert plan["network"]["edges"]
    assert plan["measures"]
    assert "places" in plan


def test_concept_graph_copied_for_demo() -> None:
    demo = ROOT / "demo" / "data" / "concept-graph.json"
    src = ROOT / "docs" / "design" / "spatial-concept-graph.json"
    assert demo.is_file()
    assert json.loads(demo.read_text())["stats"]["nodes"] == json.loads(src.read_text())["stats"]["nodes"]
