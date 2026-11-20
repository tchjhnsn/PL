"""Decided process-stage and survey artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator


def test_process_stages_and_survey_validate(repo_root: Path) -> None:
    stages_schema = json.loads(
        (repo_root / "schema" / "process-stage.schema.json").read_text(encoding="utf-8")
    )
    survey_schema = json.loads(
        (repo_root / "schema" / "survey.schema.json").read_text(encoding="utf-8")
    )
    stages = json.loads(
        (repo_root / "demo" / "data" / "process-stages.json").read_text(encoding="utf-8")
    )
    survey = json.loads(
        (repo_root / "demo" / "data" / "seed-district-survey.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(stages_schema)
    Draft202012Validator.check_schema(survey_schema)
    Draft202012Validator(stages_schema).validate(stages)
    Draft202012Validator(survey_schema).validate(survey)
    assert survey["status"] == "complete"
    assert survey["orientation"]["latitude_deg"] == 40
    ids = [item["id"] for item in stages["stages"]]
    assert ids == ["survey", "land", "foundation", "frame", "openings", "patterns"]


def test_plan_model_has_land_foundations_and_sit_on(repo_root: Path) -> None:
    plan = json.loads(
        (repo_root / "demo" / "data" / "plan-model.json").read_text(encoding="utf-8")
    )
    schema = json.loads(
        (repo_root / "schema" / "spatial-structure.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(schema).validate(plan)
    kinds = {p["kind"] for p in plan["places"]}
    assert "land" in kinds
    assert "foundation" in kinds
    sit = [ix for ix in plan["interactions"] if ix["kind"] == "sit-on"]
    assert any(ix["a"] == "found-a" and ix["b"] == "lot-a" for ix in sit)
    assert any(ix["a"] == "a-hall" and ix["b"] == "found-a" for ix in sit)
