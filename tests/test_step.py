"""Preserving on tuples, then the two houses."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from pattern_language.catalog import load_catalog
from pattern_language.parameters import load_project
from pattern_language.sequence import sequence
from pattern_language.step import build_step, preserving, step_json

_COMPUTED = (105, 106, 107, 112, 127, 128, 130, 159, 167, 190)


def test_preserving_quantifier(repo_root: Path) -> None:
    catalog = load_catalog(repo_root)
    project = load_project(
        repo_root / "projects" / "seed-house.json",
        schema_path=repo_root / "schema" / "projects.schema.json",
    )
    order = sequence(catalog, project)
    assert preserving((105, 106, 190), (105, 106), (106,)) is False
    assert preserving((105, 106), (105,), (105, 190)) is True
    assert preserving((106,), (105,), ()) is True
    assert preserving(order, (), ()) is True


def test_pass_house_twice_preserves(repo_root: Path) -> None:
    kept = _build(repo_root, "pass-house.ifc", "pass-house.ifc", pattern=105)
    assert kept.preserved is True
    assert kept.before_sha256 == kept.after_sha256
    assert kept.satisfied_before == _COMPUTED
    assert kept.satisfied_after == _COMPUTED


def test_judged_pattern_on_the_pass_house_stays_outside_satisfied(repo_root: Path) -> None:
    step = _build(repo_root, "pass-house.ifc", "pass-house.ifc", pattern=110)
    assert step.preserved is True
    assert 110 not in step.satisfied_before
    assert 110 not in step.satisfied_after


def test_pass_then_fail_drops_an_earlier_pattern(repo_root: Path) -> None:
    broken = _build(repo_root, "pass-house.ifc", "fail-house.ifc", pattern=112)
    assert broken.preserved is False
    assert broken.pattern == 112
    assert 105 in broken.satisfied_before
    assert 105 not in broken.satisfied_after
    assert broken.satisfied_before == _COMPUTED
    assert broken.satisfied_after == ()
    schema = json.loads(
        (repo_root / "schema" / "step.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(schema).validate(json.loads(step_json(broken)))


def _build(repo_root: Path, before: str, after: str, *, pattern: int):
    catalog = load_catalog(repo_root)
    project = load_project(
        repo_root / "projects" / "seed-house.json",
        schema_path=repo_root / "schema" / "projects.schema.json",
    )
    return build_step(
        catalog,
        project,
        repo_root / "fixtures" / before,
        repo_root / "fixtures" / after,
        pattern=pattern,
        before_file=f"fixtures/{before}",
        after_file=f"fixtures/{after}",
        schema_path=repo_root / "schema" / "step.schema.json",
    )
