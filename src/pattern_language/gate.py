"""Validate catalog and project records against directory schemas.

An empty ``catalog/`` and ``projects/`` tree is valid. A JSON record whose
directory has no schema is an error.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

RECORD_ROOTS = ("catalog", "projects")
SCHEMA_SUFFIX = ".schema.json"


@dataclass(frozen=True)
class DirectorySchemaMap:
    """Record directory, relative to the repo root, mapped to a schema file.

    ``schema/catalog.schema.json`` covers ``catalog/``. A nested file
    ``schema/catalog/room.schema.json`` covers ``catalog/room/``.
    """

    entries: tuple[tuple[str, Path], ...]
    duplicate_directories: tuple[str, ...] = ()

    @classmethod
    def from_schema_dir(cls, schema_dir: Path) -> DirectorySchemaMap:
        """Build a map from ``*.schema.json`` files under ``schema_dir``."""
        if not schema_dir.is_dir():
            return cls(())
        found: dict[str, Path] = {}
        duplicates: list[str] = []
        for path in sorted(schema_dir.rglob(f"*{SCHEMA_SUFFIX}")):
            key = _schema_key(schema_dir, path)
            if key in found:
                duplicates.append(key)
                continue
            found[key] = path
        entries = tuple(sorted(found.items()))
        return cls(entries, tuple(sorted(set(duplicates))))

    def schema_for(self, directory: str) -> Path | None:
        """Return the schema for the longest matching directory prefix."""
        matches = [
            (key, path)
            for key, path in self.entries
            if directory == key or directory.startswith(f"{key}/")
        ]
        if not matches:
            return None
        matches.sort(key=lambda item: len(item[0]), reverse=True)
        return matches[0][1]


@dataclass(frozen=True)
class CatalogScan:
    """Immutable result of scanning a catalog root."""

    root: Path
    records: tuple[Path, ...]
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


def scan(root: Path, schema_map: DirectorySchemaMap | None = None) -> CatalogScan:
    """Scan ``catalog/`` and ``projects/`` under ``root``.

    Missing record directories and records without a schema are errors.
    JSON records with a schema are checked against draft 2020-12.
    """
    root = root.resolve()
    if schema_map is None:
        schema_map = DirectorySchemaMap.from_schema_dir(root / "schema")
    errors = list(_missing_roots(root))
    errors.extend(
        f"duplicate schema for directory: {directory}"
        for directory in schema_map.duplicate_directories
    )
    records = _iter_records(root)
    validators: dict[Path, Draft202012Validator] = {}
    for record in records:
        errors.extend(_check_record(root, record, schema_map, validators))
    return CatalogScan(root=root, records=tuple(records), errors=tuple(errors))


def _schema_key(schema_dir: Path, path: Path) -> str:
    relative = path.relative_to(schema_dir)
    stem = path.name[: -len(SCHEMA_SUFFIX)]
    if relative.parent == Path("."):
        return stem
    return f"{relative.parent.as_posix()}/{stem}"


def _missing_roots(root: Path) -> tuple[str, ...]:
    return tuple(
        f"missing record directory: {name}"
        for name in RECORD_ROOTS
        if not (root / name).is_dir()
    )


def _iter_records(root: Path) -> list[Path]:
    records: list[Path] = []
    for name in RECORD_ROOTS:
        base = root / name
        if not base.is_dir():
            continue
        records.extend(path for path in sorted(base.rglob("*.json")) if _is_record(path))
    return records


def _is_record(path: Path) -> bool:
    return path.is_file() and path.suffix == ".json" and not path.name.startswith(".")


def _check_record(
    root: Path,
    record: Path,
    schema_map: DirectorySchemaMap,
    validators: dict[Path, Draft202012Validator],
) -> list[str]:
    relative = record.relative_to(root).as_posix()
    directory = record.relative_to(root).parent.as_posix()
    schema_path = schema_map.schema_for(directory)
    if schema_path is None:
        return [f"record without schema: {relative}"]
    try:
        instance = json.loads(record.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"invalid JSON: {relative}: {exc.msg}"]
    validator = _validator(schema_path, validators)
    if isinstance(validator, str):
        return [validator]
    return [
        f"schema: {relative}: {_error_location(error)}: {error.message}"
        for error in validator.iter_errors(instance)
    ]


def _validator(
    schema_path: Path,
    validators: dict[Path, Draft202012Validator],
) -> Draft202012Validator | str:
    cached = validators.get(schema_path)
    if cached is not None:
        return cached
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
    except (OSError, json.JSONDecodeError, SchemaError) as exc:
        return f"unreadable schema: {schema_path}: {exc}"
    validator = Draft202012Validator(schema)
    validators[schema_path] = validator
    return validator


def _error_location(error: object) -> str:
    path = getattr(error, "absolute_path", ())
    parts = [str(part) for part in path]
    return "/".join(parts) if parts else "<root>"
