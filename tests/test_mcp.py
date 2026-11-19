"""Stdio client calls the five MCP tools on the seed fixtures."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
from mcp import Client, StdioServerParameters
from mcp.types import CallToolResult, TextContent

from pattern_language.catalog import get, load_catalog, pattern_record
from pattern_language.checker import report_json, run
from pattern_language.parameters import load_project
from pattern_language.sequence import sequence
from pattern_language.step import build_step, step_json

_LANGUAGE = "projects/seed-house.json"
_PASS = "fixtures/pass-house.ifc"
_FAIL = "fixtures/fail-house.ifc"
_COMPUTED = [105, 106, 107, 112, 127, 128, 130, 159, 167, 190]


def _text(result: CallToolResult) -> str:
    assert len(result.content) == 1
    block = result.content[0]
    assert isinstance(block, TextContent)
    return block.text


def test_stdio_client_calls_each_tool(repo_root: Path) -> None:
    asyncio.run(_call_each(repo_root))


def test_missing_schema_exits_before_protocol(tmp_path: Path, repo_root: Path) -> None:
    completed = subprocess.run(
        [sys.executable, str(repo_root / "mcp" / "server.py")],
        check=False,
        cwd=tmp_path,
        capture_output=True,
        text=True,
        input="",
    )
    assert completed.returncode == 2
    assert completed.stderr == "schema is missing\n"
    assert completed.stdout == ""


async def _call_each(repo_root: Path) -> None:
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(repo_root / "mcp" / "server.py")],
        cwd=str(repo_root),
    )
    catalog = load_catalog(repo_root)
    project = load_project(
        repo_root / _LANGUAGE,
        schema_path=repo_root / "schema" / "projects.schema.json",
    )
    catalog_schema = json.loads((repo_root / "schema" / "catalog.schema.json").read_text())
    report_schema = json.loads((repo_root / "schema" / "check-report.schema.json").read_text())
    step_schema = json.loads((repo_root / "schema" / "step.schema.json").read_text())
    record_validator = Draft202012Validator(catalog_schema)

    async with Client(params) as client:
        listed = await client.list_tools()
        names = [tool.name for tool in listed.tools]
        assert names == [
            "patterns_search",
            "pattern_get",
            "language_sequence",
            "model_check",
            "model_step",
        ]
        by_name = {tool.name: tool for tool in listed.tools}
        assert by_name["pattern_get"].output_schema == catalog_schema
        assert by_name["model_check"].output_schema == report_schema
        assert by_name["model_step"].output_schema == step_schema

        found = await client.call_tool("patterns_search", {"name": "Entrance"})
        one = await client.call_tool("pattern_get", {"number": 105})
        order = await client.call_tool("language_sequence", {"project": _LANGUAGE})
        report = await client.call_tool(
            "model_check",
            {"model": _PASS, "language": _LANGUAGE},
        )
        failed = await client.call_tool(
            "model_check",
            {"model": _FAIL, "language": _LANGUAGE},
        )
        step = await client.call_tool(
            "model_step",
            {
                "before": _PASS,
                "after": _FAIL,
                "language": _LANGUAGE,
                "pattern": 112,
            },
        )
        same = await client.call_tool(
            "model_step",
            {
                "before": _PASS,
                "after": _PASS,
                "language": _LANGUAGE,
                "pattern": 105,
            },
        )
        missing = await client.call_tool("pattern_get", {"number": 200})
        outside = await client.call_tool(
            "model_step",
            {
                "before": _PASS,
                "after": _PASS,
                "language": _LANGUAGE,
                "pattern": 99,
            },
        )
        zero = await client.call_tool("pattern_get", {"number": 0})

    assert found.is_error is False
    records = json.loads(_text(found))
    assert [item["number"] for item in records] == [110, 112, 130]
    assert [item["name"] for item in records] == [
        "Main Entrance",
        "Entrance Transition",
        "Entrance Room",
    ]
    for item in records:
        record_validator.validate(item)

    assert one.is_error is False
    got = json.loads(_text(one))
    assert got == pattern_record(get(catalog, 105))
    assert got["name"] == "South Facing Outdoors"
    record_validator.validate(got)

    assert order.is_error is False
    assert _text(order) == json.dumps(list(sequence(catalog, project)), indent=2) + "\n"

    expected_report = report_json(
        run(
            catalog,
            project,
            repo_root / _PASS,
            model_file=_PASS,
            schema_path=repo_root / "schema" / "check-report.schema.json",
        )
    )
    assert report.is_error is False
    assert _text(report) == expected_report
    passed = json.loads(_text(report))
    assert passed["satisfied"] == _COMPUTED
    assert 110 not in passed["satisfied"]
    assert 180 not in passed["satisfied"]

    expected_fail = report_json(
        run(
            catalog,
            project,
            repo_root / _FAIL,
            model_file=_FAIL,
            schema_path=repo_root / "schema" / "check-report.schema.json",
        )
    )
    assert failed.is_error is False
    assert _text(failed) == expected_fail
    assert json.loads(_text(failed))["satisfied"] == []

    expected_step = step_json(
        build_step(
            catalog,
            project,
            repo_root / _PASS,
            repo_root / _FAIL,
            pattern=112,
            before_file=_PASS,
            after_file=_FAIL,
            schema_path=repo_root / "schema" / "step.schema.json",
        )
    )
    assert step.is_error is False
    assert _text(step) == expected_step
    stepped = json.loads(_text(step))
    assert stepped["preserved"] is False
    assert 105 in stepped["satisfied_before"]
    assert 105 not in stepped["satisfied_after"]

    expected_same = step_json(
        build_step(
            catalog,
            project,
            repo_root / _PASS,
            repo_root / _PASS,
            pattern=105,
            before_file=_PASS,
            after_file=_PASS,
            schema_path=repo_root / "schema" / "step.schema.json",
        )
    )
    assert same.is_error is False
    assert _text(same) == expected_same
    assert json.loads(_text(same))["preserved"] is True

    assert missing.is_error is True
    assert _text(missing) == "missing pattern: 200"
    assert outside.is_error is True
    assert _text(outside) == "pattern is not in language: 99"

    number_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["number"],
        "properties": {"number": catalog_schema["$defs"]["patternNumber"]},
    }
    schema_error = next(
        Draft202012Validator(number_schema).iter_errors({"number": 0})
    ).message
    assert zero.is_error is True
    assert _text(zero) == schema_error
    assert _text(zero) != "missing pattern: 0"
