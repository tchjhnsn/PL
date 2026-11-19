# U4 candidate A — registry, checker, pl check

U4 is the condition registry, the checker, and `pl check <model.ifc> --language <project.json>`.
It is done when each computed condition passes on pass-house and fails on fail-house, and the report validates against the check-report schema.
The registry is ten pure functions, `check(topology, center, params) -> Evidence`, with no file I/O and no IFC types.
The checker reads the model with `read_ifc`, runs the project language, and writes one check-report to stdout.
`pl check` is the only subcommand. `sequence` and `step` stay deferred.
110 Main Entrance and 180 Window Place come out as status `needs_judgment` and evidence kind `unanswered`.
They are absent from `satisfied`.
The pass house satisfies the ten computed patterns.
The fail house satisfies none.
One project file, `projects/seed-house.json`, selects all twelve seed patterns.

The ten functions live in one module. The registry maps each catalog `check` id to a function. Thresholds come from the merged params. Zone names in the houses are ids. Predicates read tags, opening kind, boundary geometry, and the center's parent chain.

Cite pattern numbers and names only. The report copies the catalog question strings we already store. It adds no book text.

## Usage

From the repo root:

```bash
uv run pl check fixtures/pass-house.ifc --language projects/seed-house.json
uv run pl check fixtures/fail-house.ifc --language projects/seed-house.json
```

Stdout is the check-report JSON, indented two spaces, keys sorted, one trailing newline. Stderr is empty. Exit 0 means the report was produced and validates. A violated pattern is still exit 0. Exit 1 is a model, catalog, project, or parameter error, with the message on stderr and no stdout. Exit 2 is usage: missing args, or any subcommand other than `check`.

```bash
uv run pl
uv run pl sequence projects/seed-house.json
```

Both exit 2. The usage line is `usage: pl check <model.ifc> --language <project.json>`.

Library:

```python
from pathlib import Path
from pattern_language.checker import check_model

report = check_model(
    Path("fixtures/pass-house.ifc"),
    Path("projects/seed-house.json"),
    Path("."),
)
```

`check_model` uses `root` as the catalog root. The CLI passes the current directory. Run it from the repo root.

## Call sites

| Caller | What it does |
|---|---|
| `src/pattern_language/cli.py` | Parses `pl check`. Calls `check_model`. Prints the report. |
| `src/pattern_language/checker.py` | Loads the catalog and the project, calls `read_ifc`, runs every selected pattern, validates the report. |
| `src/pattern_language/conditions/registry.py` | Maps the ten check ids to pure functions. |
| `src/pattern_language/conditions/checks.py` | The ten predicates and the geometry they share. |
| `tests/test_checker.py` | Pass house, fail house, schema validation, judged rows, parameter overrides. |
| U5 sequencer | Later caller of two reports. U4 does not add `sequence` or `step`. |

`pattern_language/__init__.py` stays on `load_catalog` and `scan`. Importing the package does not import the checker, so it does not load `ifcopenshell`. `read_ifc` and `write_ifc` remain the only functions that import it.

`scan` still walks `catalog/` and `projects/` only. A check-report is stdout. It is not a record, and it is not written under `fixtures/` or `projects/`.

## Project file

`projects/seed-house.json`:

```json
{
  "id": "seed-house",
  "patterns": [105, 106, 107, 110, 112, 127, 128, 130, 159, 167, 180, 190],
  "start": 105,
  "parameters": {
    "units": "si",
    "latitude_deg": 0
  }
}
```

`scan` then sees 13 records: the twelve catalog files and this one. `load_catalog` still returns the twelve patterns. `validate_catalog.py` prints `back-edges: 0` and `ok: 13 records`.

`start` must be a member of `patterns`. The checker runs every listed pattern. Order in the file does not matter. Instances are emitted in numeric order. Closure under `smaller` is U5. A project that lists only 190 is a legal input to `pl check`.

## Parameters

Catalog `params` are the base. The project overlays them.

1. Copy the condition's `params`.
2. When that copy has `latitude_deg` and the project has `parameters.latitude_deg`, replace it.
3. Apply `parameters.by_pattern["<number>"]` last. Keys replace. The object is flat.

`latitude_deg` on the project reaches 105 and 128, the conditions that already have that key. It does not appear on 167. A `by_pattern` entry for 105 beats the project latitude. The committed project sets `latitude_deg` to 0, the same value as the catalog, so the fixture run takes the equator side the pass house was built for.

A threshold that is a bool, a string, or missing raises `CheckError`. JSON integers are accepted and read as floats. Unknown keys are ignored.

| Pattern | Check id | Param |
|---|---|---|
| 105 | `south-facing-outdoors` | `latitude_deg` 0 |
| 106 | `positive-outdoor-space` | `min_convexity_ratio` 0.75 |
| 107 | `wings-of-light` | `max_depth_m` 8 |
| 112 | `entrance-transition` | none |
| 127 | `intimacy-gradient` | none |
| 128 | `indoor-sunlight` | `latitude_deg` 0 |
| 130 | `entrance-room` | none |
| 159 | `light-on-two-sides` | `min_orientations` 2 |
| 167 | `six-foot-balcony` | `min_depth_m` 1.83 |
| 190 | `ceiling-height-variety` | `min_height_difference_m` 0.3 |

110 and 180 have no `check` and no `params`.

## Data shapes

```python
@dataclass(frozen=True, slots=True)
class Evidence:
    check: str
    passed: bool | None


@dataclass(frozen=True, slots=True)
class Project:
    id: str
    patterns: tuple[int, ...]
    start: int
    latitude_deg: float | None
    by_pattern: Mapping[str, Mapping[str, Any]]
```

`passed is True` becomes status `satisfied` and JSON `passed: true`. `passed is False` becomes `violated` and `passed: false`. `passed is None` becomes `not_applicable` and `passed: false`. The check-report schema requires a boolean there. The status is the distinction. `satisfied` in the report lists only `satisfied` patterns, sorted.

The registry binds the id:

```python
def _bind(check_id: str, fn: Callable[..., bool | None]) -> Check:
    def check(topology: Topology, center: str, params: Mapping[str, Any]) -> Evidence:
        return Evidence(check_id, fn(topology, center, params))
    return check
```

`Check` is that callable. The checker calls the bound function. A raw predicate returns `True`, `False`, or `None`.

Each selected pattern has one condition, as the seed does. The report has one evidence object per instance. A pattern with any other count raises `CheckError` and prints nothing.

The center is the unique zone of kind `Building`. Both houses name it `house`. `centers` is `["house"]`. A space belongs to that center when walking `parent` reaches it. `ground` sits under `house`, and every space sits under `ground`.

## Shared readings

Coordinates are the millimetre-rounded values already on the graph. Predicates use those numbers as stored.

**Polygon centroid.** The shoelace centroid, the same formula as the U3 witness helper: sum of `(x1*y2 - x2*y1)` is `twice`, and the centroid divides the weighted vertex sums by `3 * twice`. Rectangles land on their box center. The fail `court` lands on `(2.2, 17.6)`.

**Occupied reference.** The unweighted mean of the polygon centroids of spaces tagged `occupied`. On the pass house that mean is Y `7.333`. On the fail house the occupied spaces are `bedroom` `(6, 7)` and `dayroom` `(3, 13.5)`, so the mean is Y `10.25`.

**Equator side.** `latitude_deg >= 0` uses the opposite of `topology.north`. `latitude_deg < 0` uses `north`. Both houses store `north` as `(0, 1)`, so a non-negative latitude means south, the `-Y` direction. The magnitude is unused. A point is on the equator side of the reference when the dot product of `(point - reference)` with that direction is greater than 0. Zero and negative fail when both points exist.

**Subjects.**

| Word | Spaces |
|---|---|
| Main outdoor | The one space tagged `outdoor` and not `balcony`. None returns `None`. More than one returns `False`. |
| Outdoor | Every space tagged `outdoor`, balcony included. |
| Occupied | Every space tagged `occupied`. |
| Daytime | Every space tagged `daytime`. |
| Balcony | Every space tagged `balcony`. |
| Street | Every space tagged `street`. |

An empty subject returns `None` (`not_applicable`). A present subject that misses an exterior wall, a shared balcony edge, or a required tag returns `False`.

**Door graph.** Undirected edges from openings of kind `door`. Wall adjacencies are not edges. The pass house has a wall between `court` and `living`. A walk on all adjacencies can reach `living` as soon as it reaches `hall`. The door walk reaches `hall` first. Neighbors are visited in sorted name order.

**Entrance.** Multi-source breadth-first search on the door graph from every street space. A space is indoors when it has none of the tags `street`, `outdoor`, and `transition`. The first indoors space is the entrance room. The edge that reached it is the entrance door. The path is the parent chain back to a street space.

On the pass house the path is `street`, `court`, `hall`. `court` is outdoor and transition, so it stays outside the entrance room. `hall` is the entrance room. On the fail house the path is `street`, `corridor`. `corridor` is the entrance room. Opening names are not read.

No street space, or no indoors space, returns `None` for 112, 127, and 130.

**Intimacy.** `public` rank 0, `semi-private` rank 1, `private` rank 2. Distance is the door-hop count from the entrance room.

## The ten checks

Each row is the whole pattern. The pass house makes the predicate true. The fail house makes it false. 110 and 180 have no row.

**`south-facing-outdoors`.** No occupied spaces, or no main outdoor space, returns `None`. Two main outdoor spaces return `False`. Otherwise the main outdoor centroid is on the equator side of the occupied reference. Pass: `court` at Y `2` against occupied Y `7.333`. Fail: `court` at Y `17.6` against occupied Y `10.25`.

**`positive-outdoor-space`.** No outdoor space returns `None`. Each outdoor ring has shoelace area over its convex-hull area at least `min_convexity_ratio`. The hull is Andrew's monotone chain on the ring vertices. A zero area returns `False`. Pass: `court` and `balcony` are rectangles, ratio 1. Fail: `court` has area 20 and hull area 38, ratio under 0.75. The fail `balcony` stays a rectangle, and the pattern still fails because `court` fails.

**`wings-of-light`.** No occupied space returns `None`. For each occupied space, take the maximum over footprint vertices of the minimum distance to that space's exterior boundary segments (`external` true). The space passes when the maximum is at most `max_depth_m`. A space with no exterior segment fails. Pass: every occupied vertex is 4 m or closer. Fail: `bedroom` vertex `(6, 2)` is 10 m from the only exterior segment `(6, 12)–(8, 12)`.

**`entrance-transition`.** Some space strictly between the street space and the entrance room on the entrance path is tagged `transition`. Pass: `court`. Fail: the path has no space between `street` and `corridor`.

**`intimacy-gradient`.** From the entrance room, over door-reachable spaces. A space with two intimacy tags returns `False`. For every pair whose ranks differ, the lower rank has a strictly smaller hop count. Spaces with no intimacy tag are skipped. A graph with no tagged space returns `True`. Pass, from `hall`: public at 0, semi-private at 1, private at 2. Fail, from `corridor`: private at 1, public at 2. There is no semi-private space, and the missing rank is not itself a failure.

**`indoor-sunlight`.** No daytime space, or no occupied space, returns `None`. Every daytime centroid is on the equator side of the same occupied reference 105 uses. Pass: `living` at Y `6` against Y `7.333`. Fail: `dayroom` at Y `13.5` against Y `10.25`.

**`entrance-room`.** The entrance room is tagged `room`, and it is not tagged `corridor`, and it is not tagged `living`. Pass: `hall`. Fail: `corridor`.

**`light-on-two-sides`.** No occupied space returns `None`. Each occupied space has at least `min_orientations` distinct window orientations. A window counts when its kind is `window` and the space is in `spaces`. The orientation is `Opening.orientation`. Pass: `hall` south and west, `living` south and east, `bedroom` north and west. Fail: `bedroom` has north only. `dayroom` still has two, and the pattern fails because `bedroom` fails.

**`six-foot-balcony`.** No balcony returns `None`. Depth is the maximum over footprint vertices of the minimum distance to that balcony's internal boundary segments (`other` set). No internal segment returns `False`. Depth is at least `min_depth_m`. Pass: 2.00 m off the shared edge `x = 8`. Fail: 1.00 m off the shared edge `x = 0`.

**`ceiling-height-variety`.** No occupied space returns `None`. A missing `height_m` returns `False`. `max(height) - min(height)` is at least `min_height_difference_m`. Pass: 2.4, 3.0, and 2.7. Fail: 2.4 and 2.4. Spaces without `occupied` are omitted. One occupied space differs by 0, so the seed threshold fails it.

## Judged patterns

110 and 180 do not call the registry. On both houses the instances are:

```json
{
  "pattern": 110,
  "centers": ["house"],
  "status": "needs_judgment",
  "evidence": {
    "kind": "unanswered",
    "question": "Is the entrance seen from the approach?"
  }
}
```

```json
{
  "pattern": 180,
  "centers": ["house"],
  "status": "needs_judgment",
  "evidence": {
    "kind": "unanswered",
    "question": "Does the main room have a window with a place to sit?"
  }
}
```

The question text is `Condition.question`. U4 writes no `answer`, no `reason`, and no `judged_by`. The judgment object already in the schema stays there for a later unit that has a person.

`schema/pattern-instance.schema.json` and the inlined `patternInstance` in `schema/check-report.schema.json` each gain:

```json
"unansweredEvidence": {
  "type": "object",
  "additionalProperties": false,
  "required": ["kind", "question"],
  "properties": {
    "kind": { "const": "unanswered" },
    "question": { "type": "string", "minLength": 1, "maxLength": 240 }
  }
}
```

`evidence.oneOf` gains `{ "$ref": "#/$defs/unansweredEvidence" }`. The two schemas stay self-contained. No cross-file `$ref`. `RECORD_ROOTS` stays `catalog` and `projects`.

An `unchecked` condition, none in the seed, becomes `not_applicable` with check evidence `passed: false` and `check` set to the condition id.

## Report

`model.file` is the model argument's POSIX string, unresolved. Longer than 240 characters raises `CheckError`. `model.sha256` is the hex sha256 of the file bytes.

`project` is the project `id`, `seed-house` for the committed file.

`instances` has one object per selected pattern, sorted by number. The seed file yields twelve.

`satisfied` on the pass house:

```json
[105, 106, 107, 112, 127, 128, 130, 159, 167, 190]
```

`satisfied` on the fail house is `[]`. Statuses on that report are `violated` for the ten and `needs_judgment` for 110 and 180.

A computed instance:

```json
{
  "pattern": 167,
  "centers": ["house"],
  "status": "satisfied",
  "evidence": {
    "kind": "check",
    "check": "six-foot-balcony",
    "passed": true
  }
}
```

The fail house uses `violated` and `passed: false` for that same check. Statuses `proposed` and `checking` are not emitted.

The checker validates the dict with `Draft202012Validator` against `schema/check-report.schema.json` before returning it. A report that misses the schema raises `CheckError`.

One failure does not skip the remaining patterns. A `CheckError`, a `TopologyError`, a failed project schema, or a missing pattern number aborts before stdout.

Stable stderr lines:

| Situation | Line |
|---|---|
| Pattern number absent from the catalog | `missing pattern: <n>` |
| `start` absent from `patterns` | `start is not in patterns: <n>` |
| Condition count other than 1 | `pattern <n> has <k> conditions` |
| Check id absent from the registry | `unknown check: <id>` |
| Bad or missing threshold | `bad param: <check> <key>` |
| Model path over 240 characters | `model path too long` |
| Building zones other than one | `building count: <n>` |

`TopologyError` and JSON Schema messages pass through. `CatalogLoadError` prints its errors and exits 1.

At the start of a run the checker requires the registry keys to equal the set of `check` ids on computed conditions in the catalog. The seed set is the ten ids in the table above.

## Module map

```text
src/pattern_language/conditions/__init__.py    exports registry and Evidence
src/pattern_language/conditions/registry.py    the ten bindings
src/pattern_language/conditions/checks.py      predicates and geometry
src/pattern_language/checker.py                Project, check_model, evaluate
src/pattern_language/cli.py                    pl check
projects/seed-house.json                       the twelve-pattern language
schema/pattern-instance.schema.json            unanswered evidence
schema/check-report.schema.json                the same evidence, inlined
tests/test_checker.py                          the unit check
pyproject.toml                                 [project.scripts] pl
README.md                                      U4 paragraph and the command
AGENTS.md                                      checker row, pl check, 13 records
docs/design/DESIGN.md                          short U4 pointer after U3
```

`topology.py`, the twelve catalog files, the IFC fixtures, `lean/`, and `uv.lock` stay. No new dependency. `shapely` and `networkx` stay out. The hull, the distances, and the door walk are a few dozen lines over rings that are already in hand.

`pyproject.toml`:

```toml
[project.scripts]
pl = "pattern_language.cli:main"
```

Docs the implementer updates, in place:

- `README.md` — `pl check`, the seed project path, and the pass and fail results. The U1 sentence that `projects/` has no records becomes the seed project. The sample gate output becomes `ok: 13 records`.
- `AGENTS.md` — `conditions/` holds the registry. `checker.py` writes a check-report. `pl check` is the only subcommand. `projects/seed-house.json` selects the twelve patterns. The U1 empty-projects sentence becomes history.
- `docs/design/DESIGN.md` — a U4 section after U3: ten pure checks, reports validated against the check-report schema, 110 and 180 left `needs_judgment` with unanswered evidence.

## Signatures

`src/pattern_language/conditions/registry.py`:

```python
def registry() -> Mapping[str, Check]: ...
```

The mapping is a `MappingProxyType`. Keys are the ten check ids.

`src/pattern_language/checker.py`:

```python
def evaluate(
    topology: Topology,
    catalog: Catalog,
    project: Project,
    *,
    model_file: str,
    model_sha256: str,
) -> dict[str, Any]: ...

def check_model(model: Path, language: Path, root: Path) -> dict[str, Any]: ...
```

`check_model` reads the project JSON, validates it against `schema/projects.schema.json`, loads the catalog, hashes the model, calls `read_ifc`, and calls `evaluate`. `evaluate` is the in-memory path tests use for `not_applicable`.

`src/pattern_language/cli.py`:

```python
def main(argv: list[str] | None = None) -> int: ...
```

`cli.py` holds argparse and the exit codes. Geometry stays in `checks.py`.

## Tests

`tests/test_checker.py`:

- Registry keys equal the ten catalog check ids.
- On `read_ifc` of the pass house, each bound check with the seed params and center `house` returns `passed is True`. On the fail house, `passed is False`.
- `check_model` on the pass house: schema-valid, `project == "seed-house"`, `model.file == "fixtures/pass-house.ifc"`, sha256 matches the file bytes, `satisfied` is the ten numbers, 110 and 180 are `needs_judgment` with kind `unanswered` and the catalog questions.
- `check_model` on the fail house: schema-valid, `satisfied == []`, the ten are `violated` with `passed: false` and the right `check` id, judged rows match the pass house.
- One unanswered instance validates against `schema/pattern-instance.schema.json`, and one check instance does too.
- A temp project with `latitude_deg: -45` makes the pass house violate 105 and 128 and satisfy the other eight.
- A temp project with `by_pattern` `{"167": {"min_depth_m": 3}}` makes the pass house violate 167 only.
- A temp project with `latitude_deg: -45` and `by_pattern` `{"105": {"latitude_deg": 0}}` satisfies 105 and violates 128.
- `evaluate` on a `Topology` whose only space is an occupied room, project patterns `[167]`, returns `not_applicable` for 167, evidence `passed: false`, `satisfied` empty.
- `main(["check", "fixtures/pass-house.ifc", "--language", "projects/seed-house.json"])` from the repo root returns 0 and prints JSON that matches `check_model`.
- `main([])` and `main(["sequence"])` and `main(["step"])` return 2 with empty stdout.

`tests/test_boundaries.py`:

- `projects/` contains `projects/seed-house.json` and no other JSON.
- The gate CLI expects `back-edges: 0` and `ok: 13 records`.
- `test_u0_has_no_pl_command` becomes the assertion that `[project.scripts]` names `pl` and only `pl`.
- The IfcOpenShell and `bpy` import scan stays. New modules add no `ifcopenshell` import.

`tests/test_gate.py` `test_workspace_catalog_has_twelve_records` expects 13 records, twelve under `catalog/`, and `projects/seed-house.json`.

`test_importing_gate_does_not_load_forbidden_modules` stays. `catalog_to_lean.py --check` stays green because the generator reads patterns, and the project file is outside that render.

## Rationale

- §2.2 asks for a registry of pure `check(topology, center, params) -> Evidence` functions, and a checker that writes a check-report. One module of functions plus a dict is that registry. Ten files would repeat the same geometry for the entrance walk, the centroid, and the hull.
- §3.3 is one pass and one fail per computed condition. The U3 houses already separate the ten. This unit applies the predicates. It does not add a house.
- The entrance walk skips `street`, `outdoor`, and `transition`, and it walks doors. That is what makes `hall` the pass entrance room and `corridor` the fail entrance room. The pass wall between `court` and `living` is why the walk is the door graph.
- Equator-facing is the sign of `latitude_deg` against `topology.north`. Zero uses the same side as a positive latitude, which is the side the pass house gives `court` and `living`. The degree magnitude is a later climate reading.
- The report schema can already say `needs_judgment`. It cannot say that nobody has answered: judgment evidence requires `answer`, `reason`, and `judged_by`. `unanswered` is the evidence object that carries the question and validates. Both schema files gain it because the instance object is inlined.
- `not_applicable` keeps `passed: false` because check evidence requires a boolean. The status carries the case. The two fixture reports do not use it. The balcony-free `evaluate` test does.
- Stdout is the report. A committed check-report would pin the IFC sha256, and U3 already treats STEP bytes as unstable across a writer change. Tests hash the committed files at runtime.
- `pl` is a console script with one subcommand. `sequence` and `step` are U5. The package root does not import the checker.
- The checker does not prove preservation and does not call Lean. Geometry stays on the fixture tests, which is the split in §2.6.

## CI impact

`.github/workflows/ci.yml` gains no step. `uv run pytest` runs the checker. `uv sync --frozen` already installs the project, and the lockfile stays put because no dependency is added.

| Check | U4 result |
|---|---|
| `uv run pytest` | Both houses produce schema-valid reports. The ten checks pass on one and fail on the other. 110 and 180 are `needs_judgment` / `unanswered`. |
| `pl check` on the pass house | Exit 0. `satisfied` is the ten computed numbers. |
| `pl check` on the fail house | Exit 0. `satisfied` is empty. |
| `validate_catalog.py` | `back-edges: 0` and `ok: 13 records`. |
| `catalog_to_lean.py --check` | Unchanged. |
| `lake build` | Unchanged. |
| Import boundary | `ifcopenshell` still appears only inside `read_ifc` and `write_ifc`. `bpy` appears nowhere. |

## What this unit leaves

U5 adds `pl sequence` and `pl step`, the preservation diff, and the requirement that a project language be down-closed. U4 stores `start` and does not order the patterns.

A person answering 110 or 180 is a later write of judgment evidence. This unit has no answers flag.

The occupied rooms in these houses are rectangles, so the vertex-to-segment maximum is the depth of the room. A concave occupied room is outside the fixture set. The outdoor convexity check already handles the fail `court`, which is the concave ring in the two files.

Town scale, CityJSON, Blender, and the MCP server stay later units. `adapters/blender/` and `mcp/` stay empty. Nothing imports `bpy`.
