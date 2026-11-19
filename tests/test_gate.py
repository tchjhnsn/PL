"""Catalog gate behavior on empty trees and records."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pattern_language.gate import DirectorySchemaMap, scan

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


def _layout(root: Path) -> None:
    for name in ("schema", "catalog", "projects"):
        (root / name).mkdir()
        (root / name / ".gitkeep").write_text("\n", encoding="utf-8")


def test_empty_catalog_and_projects_pass(tmp_path: Path) -> None:
    _layout(tmp_path)
    result = scan(tmp_path)
    assert result.ok
    assert result.records == ()


def test_workspace_catalog_is_empty(repo_root: Path) -> None:
    result = scan(repo_root)
    assert result.ok
    assert result.records == ()


def test_record_without_schema_fails(tmp_path: Path) -> None:
    _layout(tmp_path)
    (tmp_path / "catalog" / "orphan.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "projects" / "orphan.json").write_text("{}\n", encoding="utf-8")
    result = scan(tmp_path)
    assert not result.ok
    assert "record without schema: catalog/orphan.json" in result.errors
    assert "record without schema: projects/orphan.json" in result.errors


def test_non_json_files_are_not_records(tmp_path: Path) -> None:
    _layout(tmp_path)
    (tmp_path / "catalog" / "notes.md").write_text("notes\n", encoding="utf-8")
    (tmp_path / "fixtures").mkdir()
    (tmp_path / "fixtures" / "sample.json").write_text("{}\n", encoding="utf-8")
    result = scan(tmp_path)
    assert result.ok
    assert result.records == ()


def test_record_matching_schema_passes(tmp_path: Path) -> None:
    _layout(tmp_path)
    schema = {"type": "object", "required": ["id"], "additionalProperties": False}
    schema["properties"] = {"id": {"type": "string"}}
    (tmp_path / "schema" / "catalog.schema.json").write_text(
        json.dumps(schema),
        encoding="utf-8",
    )
    (tmp_path / "catalog" / "one.json").write_text(
        json.dumps({"id": "one"}),
        encoding="utf-8",
    )
    result = scan(tmp_path)
    assert result.ok
    assert len(result.records) == 1


def test_record_that_breaks_schema_fails(tmp_path: Path) -> None:
    _layout(tmp_path)
    schema = {"type": "object", "required": ["id"], "properties": {"id": {"type": "string"}}}
    (tmp_path / "schema" / "projects.schema.json").write_text(
        json.dumps(schema),
        encoding="utf-8",
    )
    (tmp_path / "projects" / "bad.json").write_text(
        json.dumps({"id": 1}),
        encoding="utf-8",
    )
    result = scan(tmp_path)
    assert not result.ok
    assert any(error.startswith("schema: projects/bad.json:") for error in result.errors)


def test_directory_schema_map_uses_longest_prefix(tmp_path: Path) -> None:
    schema_dir = tmp_path / "schema"
    (schema_dir / "catalog").mkdir(parents=True)
    general = schema_dir / "catalog.schema.json"
    nested = schema_dir / "catalog" / "room.schema.json"
    general.write_text("{}\n", encoding="utf-8")
    nested.write_text("{}\n", encoding="utf-8")
    schema_map = DirectorySchemaMap.from_schema_dir(schema_dir)
    assert schema_map.schema_for("catalog") == general
    assert schema_map.schema_for("catalog/room") == nested
    assert schema_map.schema_for("projects") is None
