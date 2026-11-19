"""Stdio MCP server. Five tools call the catalog, sequence, checker, and step."""

from __future__ import annotations

import asyncio
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from mcp.server import Server, ServerRequestContext
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequestParams,
    CallToolResult,
    ListToolsResult,
    PaginatedRequestParams,
    TextContent,
    Tool,
)

from pattern_language.catalog import (
    CatalogLoadError,
    get,
    load_catalog,
    pattern_record,
    search,
)
from pattern_language.checker import report_json, run
from pattern_language.conditions.evidence import CheckError
from pattern_language.parameters import load_project
from pattern_language.sequence import SequenceError, sequence
from pattern_language.step import build_step, step_json
from pattern_language.topology import TopologyError

_SCHEMA_FILES = (
    "catalog.schema.json",
    "check-report.schema.json",
    "step.schema.json",
)
_CAUGHT = (CatalogLoadError, SequenceError, CheckError, TopologyError, OSError)


def main() -> None:
    """Serve the five tools on stdio until the client closes stdin."""
    schemas = _read_schemas()
    if schemas is None:
        sys.stderr.write("schema is missing\n")
        raise SystemExit(2)
    asyncio.run(_serve(schemas))


def _array_of(record_schema: dict[str, Any]) -> dict[str, Any]:
    """An array schema whose items are one record schema.

    $defs move to the root so the record's #/$defs refs still resolve.
    properties, required, and additionalProperties are copied.
    """
    items = {
        "type": record_schema["type"],
        "additionalProperties": record_schema["additionalProperties"],
        "required": record_schema["required"],
        "properties": record_schema["properties"],
    }
    schema: dict[str, Any] = {"type": "array", "items": items}
    if "$schema" in record_schema:
        schema["$schema"] = record_schema["$schema"]
    if "$defs" in record_schema:
        schema["$defs"] = record_schema["$defs"]
    return schema


def _path(raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    return Path.cwd() / path


def _read_schemas() -> dict[str, dict[str, Any]] | None:
    loaded: dict[str, dict[str, Any]] = {}
    directory = Path.cwd() / "schema"
    for name in _SCHEMA_FILES:
        path = directory / name
        if not path.is_file():
            return None
        loaded[name] = json.loads(path.read_text(encoding="utf-8"))
    return loaded


def _tools(schemas: Mapping[str, dict[str, Any]]) -> list[Tool]:
    catalog = schemas["catalog.schema.json"]
    report = schemas["check-report.schema.json"]
    step = schemas["step.schema.json"]
    number = dict(catalog["$defs"]["patternNumber"])
    file_name = dict(report["properties"]["model"]["properties"]["file"])
    model_file = dict(step["$defs"]["modelRef"]["properties"]["file"])
    path_string = {"type": "string"}
    sequence_output = {
        "$schema": catalog["$schema"],
        "type": "array",
        "items": dict(catalog["$defs"]["patternNumber"]),
    }
    return [
        Tool(
            name="patterns_search",
            description="Return catalog records whose number, name, or scale match.",
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "number": dict(catalog["properties"]["number"]),
                    "name": dict(catalog["properties"]["name"]),
                    "scale": dict(catalog["properties"]["scale"]),
                },
                "$defs": {"patternNumber": number},
            },
            output_schema=_array_of(catalog),
        ),
        Tool(
            name="pattern_get",
            description="Return the catalog record for one pattern number.",
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["number"],
                "properties": {"number": number},
            },
            output_schema=catalog,
        ),
        Tool(
            name="language_sequence",
            description="Return the project pattern numbers in sequence order.",
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["project"],
                "properties": {"project": path_string},
            },
            output_schema=sequence_output,
        ),
        Tool(
            name="model_check",
            description="Return the check-report for one IFC model.",
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["model", "language"],
                "properties": {"model": file_name, "language": path_string},
            },
            output_schema=report,
        ),
        Tool(
            name="model_step",
            description="Return the step record for two IFC models.",
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["before", "after", "language", "pattern"],
                "properties": {
                    "before": model_file,
                    "after": model_file,
                    "language": path_string,
                    "pattern": dict(step["$defs"]["patternNumber"]),
                },
            },
            output_schema=step,
        ),
    ]


async def _call(name: str, arguments: dict[str, Any], tools: Mapping[str, Tool]) -> CallToolResult:
    """Dispatch one tool name to one function and wrap the JSON.

    A known name that raises CatalogLoadError, SequenceError,
    CheckError, TopologyError, or OSError returns is_error true.
    preserved false returns is_error false.
    """
    tool = tools.get(name)
    if tool is None:
        return _error("unknown tool")
    errors = sorted(
        Draft202012Validator(tool.input_schema).iter_errors(arguments),
        key=lambda item: list(item.absolute_path),
    )
    if errors:
        return _error(errors[0].message)
    try:
        text = _dispatch(name, arguments)
    except _CAUGHT as exc:
        return _error(str(exc))
    payload = json.loads(text)
    rejected = sorted(
        Draft202012Validator(tool.output_schema or {}).iter_errors(payload),
        key=lambda item: list(item.absolute_path),
    )
    if rejected:
        return _error("schema rejected the result")
    return CallToolResult(
        content=[TextContent(type="text", text=text)],
        structured_content=payload,
        is_error=False,
    )


def _dispatch(name: str, arguments: dict[str, Any]) -> str:
    if name == "patterns_search":
        return _patterns_search(arguments)
    if name == "pattern_get":
        return _pattern_get(arguments)
    if name == "language_sequence":
        return _language_sequence(arguments)
    if name == "model_check":
        return _model_check(arguments)
    if name == "model_step":
        return _model_step(arguments)
    return ""


def _patterns_search(arguments: dict[str, Any]) -> str:
    catalog = load_catalog(_root())
    found = search(
        catalog,
        number=arguments.get("number"),
        name=arguments.get("name"),
        scale=arguments.get("scale"),
    )
    return _canonical([pattern_record(item) for item in found])


def _pattern_get(arguments: dict[str, Any]) -> str:
    catalog = load_catalog(_root())
    return _canonical(pattern_record(get(catalog, arguments["number"])))


def _language_sequence(arguments: dict[str, Any]) -> str:
    root = _root()
    catalog = load_catalog(root)
    project = load_project(_path(arguments["project"]), schema_path=_projects_schema(root))
    order = sequence(catalog, project)
    return json.dumps(list(order), indent=2) + "\n"


def _model_check(arguments: dict[str, Any]) -> str:
    root = _root()
    catalog = load_catalog(root)
    project = load_project(_path(arguments["language"]), schema_path=_projects_schema(root))
    report = run(
        catalog,
        project,
        _path(arguments["model"]),
        model_file=arguments["model"].replace("\\", "/"),
        schema_path=root / "schema" / "check-report.schema.json",
    )
    return report_json(report)


def _model_step(arguments: dict[str, Any]) -> str:
    root = _root()
    catalog = load_catalog(root)
    project = load_project(_path(arguments["language"]), schema_path=_projects_schema(root))
    step = build_step(
        catalog,
        project,
        _path(arguments["before"]),
        _path(arguments["after"]),
        pattern=arguments["pattern"],
        before_file=arguments["before"].replace("\\", "/"),
        after_file=arguments["after"].replace("\\", "/"),
        schema_path=root / "schema" / "step.schema.json",
    )
    return step_json(step)


def _root() -> Path:
    return Path.cwd().resolve()


def _projects_schema(root: Path) -> Path:
    return root / "schema" / "projects.schema.json"


def _canonical(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _error(text: str) -> CallToolResult:
    return CallToolResult(content=[TextContent(type="text", text=text)], is_error=True)


async def _serve(schemas: Mapping[str, dict[str, Any]]) -> None:
    tools = _tools(schemas)
    by_name = {tool.name: tool for tool in tools}

    async def on_list_tools(
        _ctx: ServerRequestContext[Any],
        _params: PaginatedRequestParams | None,
    ) -> ListToolsResult:
        return ListToolsResult(tools=tools)

    async def on_call_tool(
        _ctx: ServerRequestContext[Any],
        params: CallToolRequestParams,
    ) -> CallToolResult:
        return await _call(params.name, params.arguments or {}, by_name)

    server = Server(
        "pattern-language",
        version="0.0.0",
        on_list_tools=on_list_tools,
        on_call_tool=on_call_tool,
    )
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    main()
