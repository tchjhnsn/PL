"""Load a project file and merge its parameter overrides."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from jsonschema import Draft202012Validator

from pattern_language.catalog import Pattern
from pattern_language.conditions.evidence import CheckError


@dataclass(frozen=True, slots=True)
class Project:
    id: str
    patterns: tuple[int, ...]
    start: int
    units: str
    latitude_deg: float | None
    by_pattern: Mapping[int, Mapping[str, Any]]


def load_project(path: Path, *, schema_path: Path | None = None) -> Project:
    """Validate ``path`` against the projects schema and return a Project.

    Raise CheckError when the file is missing, the schema rejects it,
    start is outside patterns, or a by_pattern key is outside patterns.
    """
    if not path.is_file():
        raise CheckError(f"cannot read {path}")
    schema_file = schema_path if schema_path is not None else _default_schema(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        schema = json.loads(schema_file.read_text(encoding="utf-8"))
    except OSError as exc:
        raise CheckError(f"cannot read {path}") from exc
    except json.JSONDecodeError as exc:
        raise CheckError(f"invalid JSON: {path}") from exc
    error = _first_error(payload, schema)
    if error is not None:
        raise CheckError(error)
    patterns = tuple(int(number) for number in payload["patterns"])
    pattern_set = set(patterns)
    start = int(payload["start"])
    if start not in pattern_set:
        raise CheckError(f"start is not in patterns: {start}")
    parameters = payload["parameters"]
    latitude = parameters.get("latitude_deg")
    by_pattern: dict[int, Mapping[str, Any]] = {}
    for key, value in parameters.get("by_pattern", {}).items():
        number = int(key)
        if number not in pattern_set:
            raise CheckError(f"by_pattern outside patterns: {number}")
        by_pattern[number] = MappingProxyType(dict(value))
    return Project(
        id=str(payload["id"]),
        patterns=patterns,
        start=start,
        units=str(parameters["units"]),
        latitude_deg=None if latitude is None else float(latitude),
        by_pattern=MappingProxyType(by_pattern),
    )


def params_for(pattern: Pattern, project: Project) -> Mapping[str, Any]:
    """Condition params, with project latitude and by_pattern overrides applied.

    Raise CheckError when an override names a key the condition does not have,
    or when the pattern does not have one condition.
    """
    if len(pattern.conditions) != 1:
        raise CheckError(f"pattern {pattern.number} has {len(pattern.conditions)} conditions")
    condition = pattern.conditions[0]
    merged: dict[str, Any] = {} if condition.params is None else dict(condition.params)
    if "latitude_deg" in merged and project.latitude_deg is not None:
        merged["latitude_deg"] = project.latitude_deg
    for key, value in project.by_pattern.get(pattern.number, {}).items():
        if key not in merged:
            raise CheckError(f"unknown param: {pattern.number} {key}")
        merged[key] = value
    return MappingProxyType(merged)


def _default_schema(path: Path) -> Path:
    parent = path.resolve().parent
    candidate = parent.parent / "schema" / "projects.schema.json"
    if parent.name == "projects" and candidate.is_file():
        return candidate
    raise CheckError("projects schema is missing")


def _first_error(instance: Any, schema: dict[str, Any]) -> str | None:
    errors = sorted(
        Draft202012Validator(schema).iter_errors(instance),
        key=lambda item: list(item.absolute_path),
    )
    if not errors:
        return None
    return errors[0].message
