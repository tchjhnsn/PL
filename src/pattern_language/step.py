"""Python twin of ``Preserving``.

``preserved`` is true when every selected pattern in ``satisfied_before`` is
in ``satisfied_after``. ``build_step`` runs the U4 checker on both models.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from pattern_language.catalog import Catalog
from pattern_language.checker import run
from pattern_language.conditions.evidence import CheckError
from pattern_language.parameters import Project
from pattern_language.sequence import SequenceError, sequence


def preserving(
    selection: Sequence[int],
    satisfied_before: Sequence[int],
    satisfied_after: Sequence[int],
) -> bool:
    """True when every selected pattern satisfied before is satisfied after.

    Matches Preserving with sat = membership in the satisfied list.
    A pattern outside selection is ignored. A pattern satisfied only
    after stays allowed.
    """
    held = set(satisfied_before)
    later = set(satisfied_after)
    return all(number in later for number in selection if number in held)


@dataclass(frozen=True, slots=True)
class Step:
    before_file: str
    before_sha256: str
    after_file: str
    after_sha256: str
    pattern: int
    satisfied_before: tuple[int, ...]
    satisfied_after: tuple[int, ...]
    preserved: bool


def build_step(
    catalog: Catalog,
    project: Project,
    before_path: Path,
    after_path: Path,
    *,
    pattern: int,
    before_file: str,
    after_file: str,
    schema_path: Path | None = None,
) -> Step:
    """Run the checker on both models and set preserved from preserving.

    sel is sequence(catalog, project). Raise SequenceError when that
    call does, or when pattern is outside project.patterns.
    Raise CheckError unchanged when a model, a report, or the step
    schema fails. schema_path defaults the way checker.run defaults
    the check-report schema, with schema/step.schema.json beside it.
    """
    selection = sequence(catalog, project)
    if pattern not in project.patterns:
        raise SequenceError(f"pattern is not in language: {pattern}")
    step_schema = _step_schema(schema_path)
    report_schema = step_schema.parent / "check-report.schema.json"
    before = run(
        catalog,
        project,
        before_path,
        model_file=before_file.replace("\\", "/"),
        schema_path=report_schema,
    )
    after = run(
        catalog,
        project,
        after_path,
        model_file=after_file.replace("\\", "/"),
        schema_path=report_schema,
    )
    step = Step(
        before_file=before.model_file,
        before_sha256=before.model_sha256,
        after_file=after.model_file,
        after_sha256=after.model_sha256,
        pattern=pattern,
        satisfied_before=before.satisfied,
        satisfied_after=after.satisfied,
        preserved=preserving(selection, before.satisfied, after.satisfied),
    )
    _validate(step, step_schema)
    return step


def step_json(step: Step) -> str:
    """Canonical step JSON, one trailing newline."""
    payload = {
        "after": {"file": step.after_file, "sha256": step.after_sha256},
        "before": {"file": step.before_file, "sha256": step.before_sha256},
        "pattern": step.pattern,
        "preserved": step.preserved,
        "satisfied_after": list(step.satisfied_after),
        "satisfied_before": list(step.satisfied_before),
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _step_schema(schema_path: Path | None) -> Path:
    if schema_path is not None:
        if not schema_path.is_file():
            raise CheckError("step schema is missing")
        return schema_path
    candidate = Path.cwd() / "schema" / "step.schema.json"
    if candidate.is_file():
        return candidate
    raise CheckError("step schema is missing")


def _validate(step: Step, schema_path: Path) -> None:
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CheckError(f"cannot read {schema_path}") from exc
    payload: Any = json.loads(step_json(step))
    errors = sorted(
        Draft202012Validator(schema).iter_errors(payload),
        key=lambda item: list(item.absolute_path),
    )
    if errors:
        raise CheckError(errors[0].message)
