# U6 candidate A — MCP server over the core

U6 adds an MCP server in `mcp/server.py` over the Python core.
It is done when a client test calls `patterns_search`, `pattern_get`, `language_sequence`, `model_check`, and `model_step` on the seed fixtures.
The server is an `MCPServer` from the official `mcp` package, speaking stdio, and each tool calls `load_catalog`, `sequence`, `run`, or `build_step`.
`patterns_search` and `pattern_get` read the twelve seed records.
`language_sequence` returns the ascending seed order.
`model_check` returns the check-report for one house.
`model_step` returns the step for two houses, and the pass house followed by the fail house has `preserved` false.
110 Main Entrance and 180 Window Place stay `needs_judgment` and stay out of `satisfied`.
A step with `preserved` false is still a successful tool result, carrying the step document.
No new schema, no Lean edit, no `pl` command, and no `bpy` import.

Cite pattern numbers and names only.

## Usage

From a checkout of the repo:

```bash
uv run python mcp/server.py
```

That process speaks MCP on stdin and stdout and blocks until the host closes the pipe. The unit check is the pytest client, which connects in memory and does not launch this process:

```bash
uv run pytest tests/test_mcp.py
```

`uv add "mcp>=2,<3"` adds the SDK to `[project.dependencies]` and rewrites `uv.lock`. The `mcp` CLI extra stays off. `anyio` arrives with the SDK, and its pytest plugin is what `@pytest.mark.anyio` uses.

Library the tools call:

```python
from pathlib import Path
from pattern_language.catalog import load_catalog
from pattern_language.checker import report_json, run
from pattern_language.parameters import load_project
from pattern_language.sequence import sequence
from pattern_language.step import build_step, step_json

root = Path(__file__).resolve().parent.parent
catalog = load_catalog(root)
project = load_project(
    root / "projects/seed-house.json",
    schema_path=root / "schema" / "projects.schema.json",
)
order = sequence(catalog, project)
report = run(
    catalog,
    project,
    root / "fixtures/pass-house.ifc",
    model_file="fixtures/pass-house.ifc",
    schema_path=root / "schema" / "check-report.schema.json",
)
step = build_step(
    catalog,
    project,
    root / "fixtures/pass-house.ifc",
    root / "fixtures/fail-house.ifc",
    pattern=105,
    before_file="fixtures/pass-house.ifc",
    after_file="fixtures/fail-house.ifc",
    schema_path=root / "schema" / "step.schema.json",
)
```

## Call sites

| Caller | What it does |
|---|---|
| `mcp/server.py` | Builds one `MCPServer` and registers the five tools. |
| `src/pattern_language/catalog.py` | `load_catalog`. Unchanged. |
| `src/pattern_language/sequence.py` | `sequence`. Unchanged. |
| `src/pattern_language/checker.py` | `run` and `report_json`. Unchanged. |
| `src/pattern_language/step.py` | `build_step` and `step_json`. Unchanged. |
| `src/pattern_language/cli.py` | `pl check`, `pl sequence`, and `pl step`. Unchanged. |
| `tests/test_mcp.py` | In-memory `Client` calls each tool on the fixtures. |

`pattern_language/__init__.py` stays on `load_catalog` and `scan`. The server imports the submodules by name. `[project.scripts]` stays `pl` alone, so `test_u4_pl_check_is_the_only_command` stays green.

The directory is named `mcp`, and the SDK's import name is `mcp`. `mcp/__init__.py` would make the checkout a regular package on pytest's path and hide the SDK. The directory stays a folder of `server.py`. The test loads that file with `importlib` under the module name `pattern_language_mcp`.

`server.py` imports `ifcopenshell` nowhere. `run` and `build_step` reach IFC through `read_ifc`, which already imports it inside the function. `bpy` stays out of the repository.

## Server

```python
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

mcp = MCPServer("pattern-language")

if __name__ == "__main__":
    mcp.run()
```

`run()` with no argument is stdio. The guard keeps an import, including the test's `importlib` load, from serving. Imports from the `mcp` package come before the assignment to the name `mcp`.

`ROOT` is `Path(__file__).resolve().parent.parent`. A relative tool argument opens under `ROOT`. An absolute argument opens as given. The string stored on a report or a step is the argument with backslashes flipped, unresolved, the same strings `pl check` and `pl step` store. Schema paths are `ROOT / "schema" / "<name>.schema.json"`, passed in, so the tools do not consult the current directory.

Each tool is a plain `def`. The SDK runs it on a thread. Each call loads the catalog again. The five tools carry `ToolAnnotations(read_only_hint=True, open_world_hint=False)`.

Return values are dicts. The SDK publishes that dict as `structured_content` and as JSON text in `content`. The test reads `structured_content`.

## Tools

`patterns_search(query: str = "") -> dict`. Loads the catalog. A pattern matches when `query` is empty or whitespace, when `query` is the decimal spelling of its number, or when `query` is a case-insensitive substring of its name. `"105"` matches 105 South Facing Outdoors and misses 110. `"entrance"` matches 110 Main Entrance, 112 Entrance Transition, and 130 Entrance Room. Hits are sorted by number. The dict is `{"patterns": [{"number", "name", "scale"}, ...]}`.

`pattern_get(number: int) -> dict`. Loads the catalog and returns the record for that number: `number`, `name`, `scale`, `confidence`, `larger`, `smaller`, `summary`, `forces`, `conditions`, `source`. Lists replace tuples. A condition includes `check` and `params` when it is computed, and `question` when it is judged. The loader's `path` stays off the dict. For each of the twelve, the dict equals `json.loads` of `catalog/<number>-<slug>.json`. A missing number raises `ToolError` with `missing pattern: <n>`.

`language_sequence(language: str) -> dict`. Loads the catalog and the project, calls `sequence`, and returns `{"project": project.id, "sequence": list(order)}`. On `projects/seed-house.json` the id is `seed-house` and the list is `105, 106, 107, 110, 112, 127, 128, 130, 159, 167, 180, 190`.

`model_check(model: str, language: str) -> dict`. Loads the catalog and the project, calls `run`, and returns `json.loads(report_json(report))`. On `fixtures/pass-house.ifc` with `projects/seed-house.json`, `satisfied` is `105, 106, 107, 112, 127, 128, 130, 159, 167, 190`, `project` is `seed-house`, and `model.file` is `fixtures/pass-house.ifc`. On `fixtures/fail-house.ifc`, `satisfied` is `[]`. 110 and 180 are `needs_judgment` with unanswered evidence on both houses. A report that fails the gate is still this dict, with `is_error` false. `pl check` keeps exiting 1 for that report.

`model_step(before: str, after: str, language: str, pattern: int) -> dict`. Loads the catalog and the project, calls `build_step`, and returns `json.loads(step_json(step))`. `pattern` is the step's `pattern` field, the same integer `pl step --pattern` requires. Pass house then fail house with `pattern` 105 yields `preserved` false, `satisfied_before` the ten computed numbers, and `satisfied_after` `[]`. The same house twice with `pattern` 105 yields `preserved` true and both lists equal to those ten numbers. `preserved` false is `is_error` false. `pl step` keeps exiting 1 for that step.

## Errors

A tool catches `CatalogLoadError`, `SequenceError`, `CheckError`, `TopologyError`, and `OSError`, and raises `ToolError` with the message joined onto one line, the line `_fail` already prints. The client sees `is_error` true, that line inside `content`, and `structured_content` none. The server log stays at info, without a traceback.

`pattern_get(200)` reports `missing pattern: 200`. A selected number absent from the catalog, a sequence `order_ok` rejects, and a `pattern` outside the project still use the messages `sequence` and `build_step` already raise. A missing model, a bad project, and a topology error still use the messages `run` and `load_project` already raise.

## Tests

`tests/test_mcp.py` loads `mcp/server.py` by file path and opens `Client(server, raise_exceptions=True)`. The anyio backend fixture returns `"asyncio"`. One test, marked `anyio`, holds that client for every call.

- `list_tools` names `patterns_search`, `pattern_get`, `language_sequence`, `model_check`, and `model_step`.
- `patterns_search` with `entrance` returns 110, 112, and 130, in that order, with those patterns' names and scale `building`.
- `patterns_search` with `105` returns one hit, number 105, name South Facing Outdoors.
- `pattern_get` of 105 equals the parsed `catalog/105-south-facing-outdoors.json`. `pattern_get` of 110 equals the parsed `catalog/110-main-entrance.json`.
- `pattern_get` of 200 has `is_error` true and `missing pattern: 200` in the text content.
- `language_sequence` of `projects/seed-house.json` returns project `seed-house` and the twelve-number list above.
- `model_check` of `fixtures/pass-house.ifc` equals `json.loads(report_json(run(...)))` for that house and `projects/seed-house.json`. The fail house does the same, and its `satisfied` list is empty. Both results have `is_error` false. The judged rows are 110 and 180.
- `model_step` from the pass house to the fail house with `pattern` 105 equals `json.loads(step_json(build_step(...)))`, `preserved` is false, and `is_error` is false. The pass house in both positions with `pattern` 105 has `preserved` true.

The test builds its expected reports and steps by calling `run` and `build_step` with `ROOT` and the schema paths, so the assertion is that the tool returns the core's document.

`tests/test_boundaries.py` keeps the import scan. `mcp/server.py` adds no `ifcopenshell` and no `bpy` import. The subprocess checks that import `pattern_language`, `sequence`, and `step` stay as they are. `schema/` stays the five documents. `catalog_to_lean.py --check` stays green. The two houses stay.

## Module map

```text
mcp/server.py                         MCPServer and the five tools
tests/test_mcp.py                     the client calls each tool
pyproject.toml                        mcp>=2,<3
uv.lock                               the lock uv add writes
README.md                             U6 paragraph and the stdio command
AGENTS.md                             mcp row, U6 section
docs/design/DESIGN.md                 short U6 section after U5
```

Unchanged: `cli.py`, `catalog.py`, `checker.py`, `sequence.py`, `step.py`, `conditions/`, `topology.py`, the twelve catalog files, `projects/seed-house.json`, both IFC fixtures, `schema/`, `lean/`, `[project.scripts]`. `mcp/.gitkeep` goes away once `server.py` is the file in that directory. `adapters/blender/` stays empty.

Docs the implementer updates, in place:

- `README.md` — a U6 section: `mcp/server.py` serves the five tools on stdio, and `uv run pytest` is the client check against the two houses.
- `AGENTS.md` — `mcp/` holds the server. The five tool names and the done-when client test. The U5 sentence that the MCP server stays later becomes history. The command block gains `uv run python mcp/server.py`.
- `docs/design/DESIGN.md` — a U6 section after U5: one stdio server, five tools over `load_catalog`, `sequence`, `run`, and `build_step`, the client test on the fixtures. The adapters paragraph keeps `adapters/blender/` reserved and names `mcp/server.py` as the server.

## Rationale

- §2.2 gives `mcp` one job: an MCP server over the core. The tools call `load_catalog`, `sequence`, `run`, and `build_step`. The checker still owns reports. `step.py` still owns the step. The server owns the protocol.
- §3.1 names the official MCP Python SDK. That package is `mcp` 2.x, and the server type is `MCPServer`. §3.2 puts the file at `mcp/server.py`. §3.3 is done when a client calls each of the five tools on fixtures. `tests/test_mcp.py` is that client, on `projects/seed-house.json`, `fixtures/pass-house.ifc`, and `fixtures/fail-house.ifc`.
- §2.3 is how an agent walks a language: it looks up patterns, takes the sequence, checks a model, and reads whether the step preserved. The five tools are those reads. 110 and 180 stay unanswered, so this unit has no judgment tool.
- `pl check` and `pl step` use exit 1 when the document is real and the gate or the preservation fails. An agent needs that document. The tool returns it with `is_error` false. The CLI exits stay on the CLI.
- The checkout directory and the SDK share the name `mcp`. Leaving out `__init__.py` keeps `from mcp.server import MCPServer` bound to the SDK when pytest puts the repo root on the path.
- Stdio is the transport a host launches. The test uses `Client(server)` so CI does not hold a process open and does not listen on a port. U7 is the Blender adapter. This server does not import `bpy`.

## CI impact

`.github/workflows/ci.yml` gains no step. `uv run pytest` runs the client. `uv sync --frozen` installs `mcp` from the updated lock.

| Check | U6 result |
|---|---|
| `uv run pytest` | The client calls all five tools. Pass and fail reports match `run`. Pass then fail has `preserved` false. |
| `pl check` on the pass house | Unchanged, exit 0. |
| `pl sequence` on the seed | Unchanged, exit 0. |
| `validate_catalog.py` | `back-edges: 0` and `ok: 13 records`. |
| `catalog_to_lean.py --check` | Unchanged. |
| `lake build` | Unchanged. |
| Import boundary | `ifcopenshell` still appears only inside `read_ifc` and `write_ifc`. `bpy` appears nowhere. |

## What this unit leaves

U7 is the Blender adapter: a panel, an export through Bonsai, and an agent bridge. `adapters/blender/` stays empty.

The server has tools and no resources, prompts, or HTTP transport. A host that wants a port can wait for a later unit.

Judgment evidence for 110 Main Entrance and 180 Window Place stays unanswered. This unit has no tool that writes an answer.

`Selection` and `DownClosed` stay where U5 left them. `language_sequence` returns whatever `sequence` returns for the project file.
