"""Evaluate a project language against one topology and write a check-report."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from pattern_language.catalog import Catalog
from pattern_language.conditions.evidence import CheckError
from pattern_language.conditions.measure import building_center
from pattern_language.conditions.registry import CHECKS
from pattern_language.parameters import Project, params_for
from pattern_language.topology import Topology, read_topology

_STATUS_FAILS = frozenset({"violated", "not_applicable"})


@dataclass(frozen=True, slots=True)
class PatternInstance:
    pattern: int
    centers: tuple[str, ...]
    status: str
    check: str | None = None
    passed: bool | None = None
    question: str | None = None
    measured: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class CheckReport:
    model_file: str
    model_sha256: str
    project: str
    instances: tuple[PatternInstance, ...]
    satisfied: tuple[int, ...]


def run(
    catalog: Catalog,
    project: Project,
    model_path: Path,
    *,
    model_file: str,
    schema_path: Path | None = None,
) -> CheckReport:
    """Read the IFC, evaluate each selected pattern, and validate the report."""
    model_file = model_file.replace("\\", "/")
    if len(model_file) > 240:
        raise CheckError("model path too long")
    try:
        digest = hashlib.sha256(model_path.read_bytes()).hexdigest()
    except OSError as exc:
        raise CheckError(f"cannot read {model_path}") from exc
    topology = read_topology(model_path)
    report = evaluate(
        topology,
        catalog,
        project,
        model_file=model_file,
        model_sha256=digest,
    )
    _validate(report, _schema_path(schema_path))
    return report


def evaluate(
    topology: Topology,
    catalog: Catalog,
    project: Project,
    *,
    model_file: str,
    model_sha256: str,
) -> CheckReport:
    """Evaluate ``project`` on an in-memory topology. Does not read a file."""
    _require_registry(catalog)
    center = building_center(topology)
    instances: list[PatternInstance] = []
    for number in sorted(project.patterns):
        pattern = catalog.by_number.get(number)
        if pattern is None:
            raise CheckError(f"missing pattern: {number}")
        if len(pattern.conditions) != 1:
            raise CheckError(f"pattern {number} has {len(pattern.conditions)} conditions")
        condition = pattern.conditions[0]
        if condition.kind == "judged":
            if not condition.question:
                raise CheckError(f"pattern {number} has no question")
            instances.append(
                PatternInstance(
                    pattern=number,
                    centers=(center,),
                    status="needs_judgment",
                    question=condition.question,
                )
            )
            continue
        if condition.kind == "unchecked":
            instances.append(
                PatternInstance(
                    pattern=number,
                    centers=(),
                    status="not_applicable",
                    check=condition.id,
                    passed=False,
                )
            )
            continue
        if condition.kind != "computed":
            raise CheckError(f"unknown condition kind: {condition.kind}")
        check_id = condition.check or ""
        if check_id not in CHECKS:
            raise CheckError(f"unknown check: {check_id}")
        evidence = CHECKS[check_id](topology, center, params_for(pattern, project))
        if evidence.applicable and evidence.passed:
            status = "satisfied"
            centers: tuple[str, ...] = (center,)
        elif evidence.applicable:
            status = "violated"
            centers = (center,)
        else:
            status = "not_applicable"
            centers = ()
        instances.append(
            PatternInstance(
                pattern=number,
                centers=centers,
                status=status,
                check=evidence.check,
                passed=evidence.passed,
                measured=evidence.measured,
            )
        )
    ordered = tuple(instances)
    satisfied = tuple(item.pattern for item in ordered if item.status == "satisfied")
    return CheckReport(
        model_file=model_file.replace("\\", "/"),
        model_sha256=model_sha256,
        project=project.id,
        instances=ordered,
        satisfied=satisfied,
    )


def report_json(report: CheckReport) -> str:
    """Canonical check-report JSON, one trailing newline."""
    payload = {
        "instances": [_instance_json(item) for item in report.instances],
        "model": {"file": report.model_file, "sha256": report.model_sha256},
        "project": report.project,
        "satisfied": list(report.satisfied),
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def fails_gate(report: CheckReport) -> bool:
    """True when a computed instance is violated or not applicable."""
    return any(item.status in _STATUS_FAILS for item in report.instances)


def _instance_json(item: PatternInstance) -> dict[str, Any]:
    if item.status == "needs_judgment":
        evidence: dict[str, Any] = {"kind": "unanswered", "question": item.question}
    else:
        evidence = {"kind": "check", "check": item.check, "passed": item.passed}
        if item.measured:
            evidence["measured"] = [
                {"name": name, "value": value} for name, value in item.measured
            ]
    return {
        "centers": list(item.centers),
        "evidence": evidence,
        "pattern": item.pattern,
        "status": item.status,
    }


def _require_registry(catalog: Catalog) -> None:
    expected = {
        condition.check
        for pattern in catalog.patterns
        for condition in pattern.conditions
        if condition.kind == "computed" and condition.check
    }
    if expected != set(CHECKS):
        raise CheckError("registry does not match catalog")


def _schema_path(schema_path: Path | None) -> Path:
    if schema_path is not None:
        return schema_path
    candidate = Path.cwd() / "schema" / "check-report.schema.json"
    if candidate.is_file():
        return candidate
    raise CheckError("check-report schema is missing")


def _validate(report: CheckReport, schema_path: Path) -> None:
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CheckError(f"cannot read {schema_path}") from exc
    payload = json.loads(report_json(report))
    errors = sorted(
        Draft202012Validator(schema).iter_errors(payload),
        key=lambda item: list(item.absolute_path),
    )
    if errors:
        raise CheckError(errors[0].message)
