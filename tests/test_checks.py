"""Computed checks against the two U3 houses."""

from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path
from types import MappingProxyType

import pytest
from jsonschema import Draft202012Validator

from pattern_language.catalog import load_catalog
from pattern_language.checker import CheckReport, evaluate, report_json, run
from pattern_language.conditions.evidence import CheckError
from pattern_language.conditions.indoor_sunlight import check as indoor_sunlight_check
from pattern_language.conditions.registry import CHECKS
from pattern_language.conditions.south_facing_outdoors import check as south_facing_check
from pattern_language.parameters import Project, load_project, params_for
from pattern_language.topology import Topology, Zone, read_topology

FORBIDDEN_NUMBERS = frozenset(
    {105, 106, 107, 110, 112, 127, 128, 130, 159, 167, 180, 190}
)
COMPUTED = (
    105,
    106,
    107,
    112,
    127,
    128,
    130,
    159,
    167,
    190,
)
MEASURED = {
    "south-facing-outdoors": ("dot", "5.333", "-7.350"),
    "positive-outdoor-space": ("min_ratio", "1.000", "0.526"),
    "wings-of-light": ("max_depth_m", "4.000", "10.198"),
    "entrance-transition": ("transition", "1.000", "0.000"),
    "intimacy-gradient": ("ordered", "1.000", "0.000"),
    "indoor-sunlight": ("dot", "2.000", "-6.500"),
    "entrance-room": ("room", "1.000", "0.000"),
    "light-on-two-sides": ("min_orientations", "2.000", "1.000"),
    "six-foot-balcony": ("min_depth_m", "2.000", "1.000"),
    "ceiling-height-variety": ("difference_m", "0.600", "0.000"),
}


@pytest.fixture(scope="module")
def houses(repo_root: Path) -> tuple[Topology, Topology]:
    return (
        read_topology(repo_root / "fixtures" / "pass-house.ifc"),
        read_topology(repo_root / "fixtures" / "fail-house.ifc"),
    )


@pytest.fixture(scope="module")
def seed_project(repo_root: Path) -> Project:
    return load_project(repo_root / "projects" / "seed-house.json")


def test_registry_matches_computed_checks(repo_root: Path) -> None:
    catalog = load_catalog(repo_root)
    computed = {
        condition.check
        for pattern in catalog.patterns
        for condition in pattern.conditions
        if condition.kind == "computed"
    }
    assert set(CHECKS) == computed
    assert len(CHECKS) == 10
    for key, function in CHECKS.items():
        module = sys.modules[function.__module__]
        assert module.CHECK_ID == key
        assert function.__module__ == "pattern_language.conditions." + key.replace("-", "_")
    for number in (110, 180):
        condition = catalog.by_number[number].conditions[0]
        assert condition.kind == "judged"
        assert condition.check is None


@pytest.mark.parametrize("check_id", sorted(MEASURED))
def test_check_passes_and_fails_on_the_houses(
    check_id: str,
    houses: tuple[Topology, Topology],
    seed_project: Project,
    repo_root: Path,
) -> None:
    catalog = load_catalog(repo_root)
    pattern = next(
        item
        for item in catalog.patterns
        if item.conditions[0].check == check_id
    )
    params = params_for(pattern, seed_project)
    key, passed, failed = MEASURED[check_id]
    pass_evidence = CHECKS[check_id](houses[0], "house", params)
    fail_evidence = CHECKS[check_id](houses[1], "house", params)
    assert pass_evidence.check == check_id
    assert pass_evidence.applicable is True
    assert pass_evidence.passed is True
    assert fail_evidence.applicable is True
    assert fail_evidence.passed is False
    assert dict(pass_evidence.measured)[key] == passed
    assert dict(fail_evidence.measured)[key] == failed


def test_latitude_zero_fails_equator_checks(
    houses: tuple[Topology, Topology],
) -> None:
    params = {"latitude_deg": 0}
    for function in (south_facing_check, indoor_sunlight_check):
        evidence = function(houses[0], "house", params)
        assert evidence.applicable is True
        assert evidence.passed is False


def test_pass_house_report_satisfies_computed_patterns(
    repo_root: Path,
    seed_project: Project,
) -> None:
    report = _run(repo_root, seed_project, "pass-house.ifc")
    _assert_schema(repo_root, report)
    digest = hashlib.sha256((repo_root / "fixtures" / "pass-house.ifc").read_bytes()).hexdigest()
    assert report.project == "seed-house"
    assert report.model_file == "fixtures/pass-house.ifc"
    assert report.model_sha256 == digest
    assert report.satisfied == COMPUTED
    assert len(report.instances) == 12
    by_status = {item.pattern: item for item in report.instances}
    for number in COMPUTED:
        assert by_status[number].status == "satisfied"
        assert by_status[number].centers == ("house",)
        assert by_status[number].passed is True
    _assert_judged(repo_root, report)


def test_fail_house_report_satisfies_nothing(repo_root: Path, seed_project: Project) -> None:
    report = _run(repo_root, seed_project, "fail-house.ifc")
    _assert_schema(repo_root, report)
    assert report.satisfied == ()
    by_status = {item.pattern: item for item in report.instances}
    for number in COMPUTED:
        assert by_status[number].status == "violated"
        assert by_status[number].passed is False
        assert by_status[number].centers == ("house",)
    _assert_judged(repo_root, report)


def test_instances_validate_against_pattern_instance_schema(
    repo_root: Path,
    seed_project: Project,
) -> None:
    report = _run(repo_root, seed_project, "pass-house.ifc")
    schema = json.loads(
        (repo_root / "schema" / "pattern-instance.schema.json").read_text(encoding="utf-8")
    )
    validator = Draft202012Validator(schema)
    payload = json.loads(report_json(report))
    satisfied = next(item for item in payload["instances"] if item["status"] == "satisfied")
    judged = next(item for item in payload["instances"] if item["status"] == "needs_judgment")
    validator.validate(satisfied)
    validator.validate(judged)
    assert judged["evidence"]["kind"] == "unanswered"
    assert satisfied["evidence"]["kind"] == "check"


def test_missing_subjects_are_not_applicable(repo_root: Path) -> None:
    room = Zone(
        "room",
        "Space",
        "house",
        frozenset({"occupied", "room"}),
        ((0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (0.0, 4.0)),
        2.4,
    )
    house = Zone("house", "Building", None, frozenset(), (), None)
    topology = Topology((0.0, 1.0), (house, room), (), (), ())
    project = Project(
        id="bare",
        patterns=(105, 106, 112, 127, 128, 130, 167, 190),
        start=105,
        units="si",
        latitude_deg=40.0,
        by_pattern=MappingProxyType({}),
    )
    report = evaluate(
        topology,
        load_catalog(repo_root),
        project,
        model_file="bare.ifc",
        model_sha256="ab" * 32,
    )
    assert tuple(item.pattern for item in report.instances) == project.patterns
    assert report.satisfied == ()
    assert all(item.status == "not_applicable" for item in report.instances)
    assert all(item.centers == () and item.passed is False for item in report.instances)
    _assert_schema(repo_root, report)


def test_by_pattern_depth_violates_only_the_balcony(repo_root: Path, tmp_path: Path) -> None:
    project = _project(
        repo_root,
        tmp_path,
        latitude_deg=40,
        by_pattern={"167": {"min_depth_m": 3}},
    )
    report = _run(repo_root, project, "pass-house.ifc")
    statuses = {item.pattern: item.status for item in report.instances}
    assert statuses[167] == "violated"
    for number in COMPUTED:
        if number == 167:
            continue
        assert statuses[number] == "satisfied"


def test_pattern_override_beats_project_latitude(repo_root: Path, tmp_path: Path) -> None:
    project = _project(
        repo_root,
        tmp_path,
        latitude_deg=-45,
        by_pattern={"105": {"latitude_deg": 40}},
    )
    report = _run(repo_root, project, "pass-house.ifc")
    statuses = {item.pattern: item.status for item in report.instances}
    assert statuses[105] == "satisfied"
    assert statuses[128] == "violated"


def test_unknown_override_is_a_check_error(repo_root: Path, tmp_path: Path) -> None:
    project = _project(
        repo_root,
        tmp_path,
        latitude_deg=40,
        by_pattern={"167": {"depth": 3}},
    )
    with pytest.raises(CheckError, match="unknown param: 167 depth"):
        _run(repo_root, project, "pass-house.ifc")


def test_check_modules_do_not_literalize_pattern_numbers(repo_root: Path) -> None:
    roots = [
        repo_root / "src" / "pattern_language" / "checker.py",
        repo_root / "src" / "pattern_language" / "cli.py",
        repo_root / "src" / "pattern_language" / "parameters.py",
    ]
    roots.extend((repo_root / "src" / "pattern_language" / "conditions").rglob("*.py"))
    found: list[str] = []
    for path in roots:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and type(node.value) is int and node.value in FORBIDDEN_NUMBERS:
                relative = path.relative_to(repo_root).as_posix()
                found.append(f"{relative}:{node.value}")
    assert found == []


def _run(repo_root: Path, project: Project, house: str) -> CheckReport:
    return run(
        load_catalog(repo_root),
        project,
        repo_root / "fixtures" / house,
        model_file=f"fixtures/{house}",
        schema_path=repo_root / "schema" / "check-report.schema.json",
    )


def _assert_schema(repo_root: Path, report: CheckReport) -> None:
    schema = json.loads(
        (repo_root / "schema" / "check-report.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(schema).validate(json.loads(report_json(report)))


def _assert_judged(repo_root: Path, report: CheckReport) -> None:
    catalog = load_catalog(repo_root)
    by_pattern = {item.pattern: item for item in report.instances}
    for number in (110, 180):
        instance = by_pattern[number]
        question = catalog.by_number[number].conditions[0].question
        assert instance.status == "needs_judgment"
        assert instance.centers == ("house",)
        assert instance.question == question
        assert number not in report.satisfied


def _project(
    repo_root: Path,
    tmp_path: Path,
    *,
    latitude_deg: float,
    by_pattern: dict[str, dict[str, float]],
) -> Project:
    payload = {
        "id": "override",
        "patterns": [105, 106, 107, 110, 112, 127, 128, 130, 159, 167, 180, 190],
        "start": 105,
        "parameters": {
            "units": "si",
            "latitude_deg": latitude_deg,
            "by_pattern": by_pattern,
        },
    }
    path = tmp_path / "override.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return load_project(path, schema_path=repo_root / "schema" / "projects.schema.json")
