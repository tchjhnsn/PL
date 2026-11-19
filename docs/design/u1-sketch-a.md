# U1 candidate A — minimal fit to the live gate

U1 adds five JSON Schemas, a catalog loader, and twelve seed pattern records. It is done when every record validates, every stored link target exists, and back-edges are reported.

`scan` in `src/pattern_language/gate.py` stays as it is. It walks `catalog/` and `projects/`, loads `schema/<directory>.schema.json`, and checks records with JSON Schema draft 2020-12. Empty record directories stay valid. This candidate adds files the gate already knows how to read, plus one module that reads the link graph after validation.

Cite pattern numbers and names only. Summaries, forces, and judged questions are our wording. `summary` and every force carry `"draft": true`.

## Usage

Library:

```python
from pathlib import Path
from pattern_language import load_catalog

catalog = load_catalog(Path("."))
south = catalog.by_number[105]
catalog.missing_targets   # () on the seed
catalog.back_edges        # () on the seed
catalog.ok                # True when missing_targets is empty
```

`load_catalog` raises `CatalogLoadError` when `scan` reports errors or two catalog files share a number. A missing link target is returned on the catalog. A back-edge is returned on the catalog. Neither is dropped to make `ok` true.

Command, from the repo root:

```bash
uv run python scripts/validate_catalog.py
```

Seed stdout:

```text
back-edges: 0
ok: 12 records
```

A downward smaller-link prints before the count, on success and on a missing-target failure:

```text
back-edge: 20 10
back-edges: 1
ok: 2 records
```

Missing targets go to stderr and the process exits 1:

```text
missing target: 105 smaller 104
```

Schema errors stay the gate's lines (`schema: …`, `invalid JSON: …`, `record without schema: …`) and exit 1 before the link report.

## Call sites

| Caller | What it does |
|---|---|
| `scripts/validate_catalog.py` | Runs `scan`. On a clean scan, calls `load_catalog`. Prints each back-edge, then `back-edges: N`, then `ok: N records`. Exits 1 when `missing_targets` is non-empty or `CatalogLoadError` is raised. |
| `src/pattern_language/__init__.py` | Re-exports `load_catalog`, `Catalog`, and `CatalogLoadError` beside the existing gate names. |
| `tests/test_catalog.py` | Loads the repo seed. Asserts the twelve numbers, empty `missing_targets`, empty `back_edges`, draft flags, filenames, and the forward link list. A `tmp_path` catalog asserts a downward smaller-link appears in `back_edges`, and a dangling number appears only in `missing_targets`. |
| `tests/test_gate.py` | Workspace scan expects 12 records and `ok`. Empty-tree cases stay on `tmp_path`. |
| `tests/test_boundaries.py` | Replaces the empty-tree ship check with the five schema paths and twelve catalog files. The CLI check expects `back-edges: 0` and `ok: 12 records`. |

U2's `scripts/catalog_to_lean.py` is the next caller of `load_catalog`. U1 does not add it. U1 does not add a `pl` command, `cli.py`, or a project JSON file.

`load_catalog` calls `scan(root)` itself, so a library caller gets schema failures without going through the script. The script also calls `scan` first and skips the loader when the scan has errors. The second scan on a clean tree is the whole seed.

## Data shapes

### How the five schemas meet the gate

`DirectorySchemaMap` keys a schema by the path under `schema/` with `.schema.json` removed. `scan` asks for a schema only for the parent directory of a file under `catalog/` or `projects/`.

| File | Map key | U1 records |
|---|---|---|
| `schema/catalog.schema.json` | `catalog` | the twelve `catalog/*.json` files |
| `schema/projects.schema.json` | `projects` | none; `projects/` stays an empty record root |
| `schema/pattern-instance.schema.json` | `pattern-instance` | none |
| `schema/check-report.schema.json` | `check-report` | none |
| `schema/step.schema.json` | `step` | none |

The last three are built into `DirectorySchemaMap.entries` at startup. No record parent is `pattern-instance`, `check-report`, or `step`, so `schema_for` is never asked for those keys. They take effect when a later unit adds that directory name to `RECORD_ROOTS` and puts `*.json` files there. The filenames already match the directory keys, so that unit does not rename them.

They stay top-level schema files. A path such as `schema/catalog/pattern-instance.schema.json` would be the longest prefix for `catalog/pattern-instance/` and would steal those records from the pattern schema.

Cross-file `$ref` is out of U1. `Draft202012Validator(schema)` is constructed with no retrieval function. Each schema file is self-contained. `check-report` repeats the pattern-instance object under `$defs`. `step` repeats its model hash object under `$defs`.

Every schema sets `"$schema": "https://json-schema.org/draft/2020-12/schema"`, `"type": "object"`, and `"additionalProperties": false`.

### Pattern record (`schema/catalog.schema.json`)

Closed object. Required: `number`, `name`, `scale`, `confidence`, `larger`, `smaller`, `summary`, `forces`, `conditions`, `source`.

| Field | Shape |
|---|---|
| `number` | integer, 1–253 |
| `name` | string, 1–80 characters |
| `scale` | `town`, `building`, or `construction` |
| `confidence` | integer, 0–2 (asterisk count) |
| `larger`, `smaller` | arrays of unique integers, 1–253, minimum length 0 |
| `summary` | `{ "text": string (1–240), "draft": boolean }` |
| `forces` | array of `{ "name": string (1–80), "draft": boolean }` |
| `conditions` | array of condition objects, minimum length 1 on the seed |
| `source` | `{ "book": "A Pattern Language", "number": integer 1–253 }` |

Condition (`$defs/condition`), closed:

| Field | When |
|---|---|
| `id` | always; kebab-case string |
| `kind` | `computed`, `judged`, or `unchecked` |
| `check` | required string when `kind` is `computed`; property schema `false` otherwise |
| `params` | required object when `kind` is `computed`; values are number, string, or boolean; property schema `false` otherwise |
| `question` | required string, 1–240 characters, when `kind` is `judged`; property schema `false` otherwise |

`if` / `then` on `kind` expresses that split. Draft 2020-12 allows `"question": false` inside `properties` to reject the field.

There is no `problem` or `solution` property. A pasted book paragraph has nowhere to land, and `summary.text` stops at 240 characters.

`summary.draft` is a boolean, so a later confirmation can set `false` without a schema change. Every seed file sets `true` on the summary and on every force.

### Project language (`schema/projects.schema.json`)

Closed object. Required: `id`, `patterns`, `start`, `parameters`.

| Field | Shape |
|---|---|
| `id` | kebab-case string |
| `patterns` | array of unique integers, 1–253, minimum length 1 |
| `start` | integer, 1–253 |
| `parameters.units` | required, const `si` |
| `parameters.climate` | optional string |
| `parameters.latitude_deg` | optional number, −90 to 90 |
| `parameters.by_pattern` | optional object; keys are decimal pattern numbers; values are flat objects of number, string, or boolean |

U1 writes no file under `projects/`. `start` belonging to `patterns` is left for the unit that writes a project. The directory schema is what makes a future project file validate instead of failing as `record without schema`.

### Pattern instance (`schema/pattern-instance.schema.json`)

Closed object. Required: `pattern`, `centers`, `status`, `evidence`.

| Field | Shape |
|---|---|
| `pattern` | integer, 1–253 |
| `centers` | array of strings, zone ids, minimum length 0 |
| `status` | `proposed`, `not_applicable`, `checking`, `satisfied`, `violated`, `needs_judgment` |
| `evidence` | one of the two closed objects below |

Check evidence: `kind` const `check`, `check` string, `passed` boolean.

Judgment evidence: `kind` const `judgment`, `answer` boolean, `reason` string (1–240), `judged_by` string (1–80).

Status names are the statechart states in `DESIGN.full.md` §2.4, written in snake_case. The inner `Computed` substate is the check evidence, so it is not a status.

### Check report (`schema/check-report.schema.json`)

Closed object. Required: `model`, `project`, `instances`, `satisfied`.

| Field | Shape |
|---|---|
| `model.file` | string, 1–240 |
| `model.sha256` | 64 lowercase hex characters |
| `project` | string, the project-language id |
| `instances` | array of the pattern-instance object, copied under `$defs/patternInstance` |
| `satisfied` | array of integers, 1–253 |

U4 is what checks that the instances cover each pattern and center. The U1 schema is the field list.

### Step (`schema/step.schema.json`)

Closed object. Required: `before`, `after`, `pattern`, `satisfied_before`, `satisfied_after`, `preserved`.

| Field | Shape |
|---|---|
| `before`, `after` | `{ "file": string, "sha256": 64 lowercase hex }` under `$defs/modelRef` |
| `pattern` | integer, 1–253 |
| `satisfied_before`, `satisfied_after` | arrays of integers, 1–253 |
| `preserved` | boolean |

### Loader values

Built only from files `scan` accepted under `catalog/`. Project files stay in the scan count and stay out of `Catalog`.

| Type | Fields |
|---|---|
| `DraftText` | `text: str`, `draft: bool` |
| `Force` | `name: str`, `draft: bool` |
| `Condition` | `id`, `kind`, `check: str \| None`, `params: Mapping \| None`, `question: str \| None` |
| `Source` | `book: str`, `number: int` |
| `Pattern` | the schema fields, with `larger` and `smaller` as `tuple[int, ...]`, plus `path: str` (repo-relative POSIX, `catalog/105-south-facing-outdoors.json`) |
| `LinkRef` | `source: int`, `field: "larger" \| "smaller"`, `target: int` |
| `BackEdge` | `source: int`, `target: int` |
| `Catalog` | `patterns`, `by_number`, `missing_targets`, `back_edges`; `ok` is true when `missing_targets` is empty |

`patterns` is sorted by number. `by_number` is a `MappingProxyType`. Link arrays on `Pattern` keep the order stored in the file. The seed files store those arrays in ascending order.

`missing_targets` lists every `larger` or `smaller` number absent from `by_number`, sorted by `(source, field, target)` with `larger` before `smaller`.

`back_edges` lists every `smaller` target that is present in `by_number` and lower than the source, sorted by `(source, target)`. A missing number is only a `LinkRef`. A link from a pattern to its own number is neither: the target exists, and it is not lower. Cycles are U2 (`acyclic`). The seed has no self-links; a test asserts that.

`Catalog.ok` ignores `back_edges`. A downward link on a complete graph is a successful load with a non-empty report.

### Seed files

Flat files, one pattern each. Slug is the name in lowercase, with each run of non-alphanumeric characters replaced by one hyphen, hyphens trimmed. No zero-padding.

| File | Name | Confidence | Smaller | Larger |
|---|---|---|---|---|
| `catalog/105-south-facing-outdoors.json` | South Facing Outdoors | 2 | 106, 107, 128 | |
| `catalog/106-positive-outdoor-space.json` | Positive Outdoor Space | 1 | 167 | 105 |
| `catalog/107-wings-of-light.json` | Wings of Light | 1 | 128, 159, 190 | 105 |
| `catalog/110-main-entrance.json` | Main Entrance | 1 | 112, 130 | |
| `catalog/112-entrance-transition.json` | Entrance Transition | 1 | 130 | 110 |
| `catalog/127-intimacy-gradient.json` | Intimacy Gradient | 1 | 130 | |
| `catalog/128-indoor-sunlight.json` | Indoor Sunlight | 1 | 159 | 105, 107 |
| `catalog/130-entrance-room.json` | Entrance Room | 1 | | 110, 112, 127 |
| `catalog/159-light-on-two-sides-of-every-room.json` | Light on Two Sides of Every Room | 2 | 180 | 107, 128 |
| `catalog/167-six-foot-balcony.json` | Six-Foot Balcony | 1 | | 106 |
| `catalog/180-window-place.json` | Window Place | 2 | | 159 |
| `catalog/190-ceiling-height-variety.json` | Ceiling Height Variety | 1 | | 107 |

Every row has `scale: "building"`. `source.number` equals `number`. `source.book` is `A Pattern Language`.

Confidence `2` for 105, 159, and 180 follows those headings' two asterisks. The other nine store `1` as a placeholder until the heading's asterisk count replaces it. Tests lock 105, 159, and 180 to `2`, and lock every confidence to the range 0–2. They do not lock the placeholders.

Link provenance: 105's stored smaller list is 106 Positive Outdoor Space, 107 Wings of Light, and 128 Indoor Sunlight. The same name list also cites 104, 111, 161, and 162; those stay out of the file because this unit's catalog is the twelve. Every other edge in the table is the proposed induced graph that keeps the twelve connected and keeps each smaller target above its source. Torian confirms or replaces edges against the book. Replacing an edge updates the JSON and the exact-link test together.

Stored smaller targets are all inside the twelve, and each is greater than its source. On this seed, `back_edges` is empty and numeric order is a valid sequence in the sense U2 asks `decide` to prove: each completing pattern has a higher number than the pattern it completes. A confirmed book link that points downward is stored and shows up as a `back-edge:` line. That line is the signal that numeric order is no longer a valid sequence for the seed.

The inverse holds for every stored edge: if `t` is in `p.smaller`, then `p` is in `t.larger`, and the reverse. A test asserts that on the seed. The loader does not invent the inverse.

### Conditions, summaries, forces

One condition per pattern. Computed `id` equals `check`. Params are the initial `[P]` values; U4 reads the same keys. `latitude_deg` is the project override key of the same name. U1 does not merge overrides.

| No. | Kind | id / check | Params or question |
|---|---|---|---|
| 105 | computed | `south-facing-outdoors` | `{"latitude_deg": 0}` |
| 106 | computed | `positive-outdoor-space` | `{"min_convexity_ratio": 0.75}` |
| 107 | computed | `wings-of-light` | `{"max_depth_m": 8}` |
| 110 | judged | `main-entrance` | Is the entrance seen from the approach? |
| 112 | computed | `entrance-transition` | `{}` |
| 127 | computed | `intimacy-gradient` | `{}` |
| 128 | computed | `indoor-sunlight` | `{"latitude_deg": 0}` |
| 130 | computed | `entrance-room` | `{}` |
| 159 | computed | `light-on-two-sides` | `{"min_orientations": 2}` |
| 167 | computed | `six-foot-balcony` | `{"min_depth_m": 1.83}` |
| 180 | judged | `window-place` | Does the main room have a window with a place to sit? |
| 190 | computed | `ceiling-height-variety` | `{"min_height_difference_m": 0.3}` |

`1.83` and `2` are the quantities already stated in `DESIGN.full.md` §1.5. `0.75`, `8`, and `0.3` are initial parameters. `latitude_deg: 0` is the default until a project sets the latitude.

Summaries (`draft: true`), one line each:

| No. | `summary.text` |
|---|---|
| 105 | The main outdoor zone lies on the equator-facing side of the building. |
| 106 | Each outdoor zone is mostly enclosed. |
| 107 | No occupied space sits deeper than a set depth from an exterior wall. |
| 110 | The entrance is visible from the approach. |
| 112 | The path from the street to the main door passes through a transition zone. |
| 127 | From the entrance, public rooms come before semi-private rooms, then private rooms. |
| 128 | Daytime rooms sit on the equator-facing side. |
| 130 | The main door opens into a room. |
| 159 | Each occupied room has windows in two walls of different orientation. |
| 167 | Every balcony is at least 1.83 m deep. |
| 180 | The main room has a window with a place to sit. |
| 190 | Ceiling heights across occupied rooms vary by at least a set amount. |

Forces (`draft: true`), two names each:

| No. | Force names |
|---|---|
| 105 | winter sun on outdoor ground; building mass shading that ground |
| 106 | an outdoor room wants enclosure; enclosure can cut off sun |
| 107 | occupied rooms want daylight; a deep plan leaves an interior dark |
| 110 | arrival wants a visible door; the door can sit out of sight of the approach |
| 112 | the street is public; the interior is private |
| 127 | a house holds public and private rooms; a door can open into the most private room |
| 128 | daytime rooms want sun; those rooms can sit on the shaded side |
| 130 | arrival wants a room; the door can open into a corridor |
| 159 | a room wants light from two directions; one window wall leaves it flat |
| 167 | a balcony wants room to sit; a narrow ledge is only a step |
| 180 | a window wants a place beside it; the glass can have nowhere to sit |
| 190 | rooms want heights that match their use; one ceiling height makes them feel alike |

Example file `catalog/167-six-foot-balcony.json`:

```json
{
  "number": 167,
  "name": "Six-Foot Balcony",
  "scale": "building",
  "confidence": 1,
  "larger": [106],
  "smaller": [],
  "summary": {
    "text": "Every balcony is at least 1.83 m deep.",
    "draft": true
  },
  "forces": [
    {"name": "a balcony wants room to sit", "draft": true},
    {"name": "a narrow ledge is only a step", "draft": true}
  ],
  "conditions": [
    {
      "id": "six-foot-balcony",
      "kind": "computed",
      "check": "six-foot-balcony",
      "params": {"min_depth_m": 1.83}
    }
  ],
  "source": {"book": "A Pattern Language", "number": 167}
}
```

Judged example, condition only:

```json
{
  "id": "main-entrance",
  "kind": "judged",
  "question": "Is the entrance seen from the approach?"
}
```

## Module map

```text
schema/catalog.schema.json
schema/projects.schema.json
schema/pattern-instance.schema.json
schema/check-report.schema.json
schema/step.schema.json
catalog/105-south-facing-outdoors.json
catalog/… eleven more <number>-<slug>.json
src/pattern_language/catalog.py          new
src/pattern_language/__init__.py         export the loader
src/pattern_language/gate.py             unchanged
scripts/validate_catalog.py              print link report after scan
tests/test_catalog.py                    new
tests/test_gate.py                       workspace count
tests/test_boundaries.py                 ship check and CLI stdout
README.md                                U1 scope
AGENTS.md                                path table
docs/design/DESIGN.md                    short U1 pointer after the U0 gate
```

`projects/.gitkeep`, `schema/.gitkeep`, and `catalog/.gitkeep` stay. The gate ignores dotfiles and non-JSON. `lean/` is untouched. `pyproject.toml` gains no dependency and no `[project.scripts]` entry.

`catalog.py` imports `json`, `dataclasses`, `types.MappingProxyType`, and `pattern_language.gate.scan`. It does not import `ifcopenshell` or `bpy`.

Docs the implementer updates, in place:

- `README.md` — five schemas, twelve records, loader, and the `back-edges` line from the validate command. Keep the number-and-name citation rule.
- `AGENTS.md` — `schema/` holds the five documents; `catalog/` holds the twelve records. Leave the sentence that U0 adds none of those, and leave the ban on a `pl` command.
- `docs/design/DESIGN.md` — add a U1 section after U0: records live in `catalog/` and `projects/`; link existence and back-edges come from `load_catalog`, and `scan` still only checks JSON Schema. The empty-tree rule stays.

## Signatures

`src/pattern_language/catalog.py`:

```python
def load_catalog(root: Path) -> Catalog: ...

class CatalogLoadError(Exception):
    errors: tuple[str, ...]

@dataclass(frozen=True)
class Catalog:
    patterns: tuple[Pattern, ...]
    by_number: Mapping[int, Pattern]
    missing_targets: tuple[LinkRef, ...]
    back_edges: tuple[BackEdge, ...]

    @property
    def ok(self) -> bool: ...
```

`load_catalog` resolves `root`, runs `scan(root)`, and raises `CatalogLoadError(scan.errors)` when `scan.ok` is false. It then parses each scan path whose first relative part is `catalog` (parse at this edge; the schema check already passed). A second file with the same `number` raises `CatalogLoadError` with one string:

```text
duplicate pattern number: 105 (catalog/105-south-facing-outdoors.json, catalog/105-other.json)
```

The two paths are sorted. `by_number` is a `MappingProxyType`. Construction of `Pattern` reads the known keys and trusts their types.

`scripts/validate_catalog.py` after a clean scan:

```python
catalog = load_catalog(root)
for edge in catalog.back_edges:
    print(f"back-edge: {edge.source} {edge.target}")
print(f"back-edges: {len(catalog.back_edges)}")
if catalog.missing_targets:
    for link in catalog.missing_targets:
        print(
            f"missing target: {link.source} {link.field} {link.target}",
            file=sys.stderr,
        )
    return 1
print(f"ok: {len(result.records)} records")
return 0
```

`ok:` counts gate records, catalog plus projects. On this branch that count is 12. `len(catalog.patterns)` is the pattern count, also 12 while `projects/` has no JSON.

`__all__` becomes:

```python
["Catalog", "CatalogLoadError", "CatalogScan", "DirectorySchemaMap", "load_catalog", "scan"]
```

## Rationale

The live gate already decides which files are records and which schema covers them. U1 uses that map as it stands.

- The pattern schema is `schema/catalog.schema.json` because the records live in `catalog/`. A file named `schema/pattern.schema.json` would cover a directory `pattern/`, which `scan` does not walk.
- The project-language schema is `schema/projects.schema.json` for the same reason. With zero project files, the schema is loaded into the map and applied to nothing. The empty `projects/` directory still passes `scan`.
- The other three schemas exist so U1 delivers five, and their stems are the directory names a later unit will add to `RECORD_ROOTS`. Until those directories exist, the keys sit in the map and no record selects them.
- Link checks live in the loader. `scan` has no notion of pattern numbers. Folding the graph into the gate would change the U0 contract that an empty tree and a schema-valid JSON object are the gate's whole job.
- Back-edges are a field on a successful `Catalog`, a stdout line, and a count line that is `0` for this seed. The seed stores a forward graph so U2 can ask `decide` to prove numeric order. A fixture with a downward `smaller` link is what proves the loader returns that edge.
- Out-of-twelve numbers are left out of the JSON. Stored that way, they would be `missing_targets` and the unit would fail its own done-when. The seed is the induced graph on these twelve numbers. 104, 111, 161, and 162 are the out-of-set names beside 105; they are omitted on that boundary.
- Closed objects, a 240-character summary cap, and no problem or solution fields are the copyright rule expressed in the schema.
- No new package, no Mathlib, no `pl` entry point, no edit to `gate.py`.

## CI impact

`.github/workflows/ci.yml` stays on the same four steps: `uv sync --frozen`, `uv run pytest`, `uv run python scripts/validate_catalog.py`, `lake build` in `lean/`. `uv.lock` stays. Lean stays an empty namespace with an empty package list.

What changes inside those steps:

| Check | U1 result |
|---|---|
| `uv run pytest` | Workspace tests expect 12 catalog records, five schema files, and a loader whose seed has `missing_targets == ()` and `back_edges == ()`. `test_empty_catalog_and_projects_pass` remains on `tmp_path`. `test_u0_has_no_pl_command` remains. |
| `validate_catalog.py` | Exit 0. Stdout is `back-edges: 0` then `ok: 12 records`. |
| `lake build` | Unchanged. |

Tests that assert an empty workspace catalog are the ones to update:

- `tests/test_gate.py`: `test_workspace_catalog_is_empty` becomes a workspace scan of 12 successful records.
- `tests/test_boundaries.py`: `test_u0_ships_no_records_or_schemas` becomes the five schema paths, twelve catalog JSON files, and zero project JSON files.
- `tests/test_boundaries.py`: `test_validate_catalog_cli_accepts_empty_workspace` expects the two stdout lines above. Add a `tmp_path` CLI case that still expects `ok: 0 records` and `back-edges: 0` for an empty layout with no schema files.

New `tests/test_catalog.py` assertions on the repo:

- `set(catalog.by_number) == {105, 106, 107, 110, 112, 127, 128, 130, 159, 167, 180, 190}`
- `catalog.missing_targets == ()` and `catalog.back_edges == ()` and `catalog.ok`
- filenames match `<number>-<slug>.json`
- every `summary.draft` and every force `draft` is true
- every `scale` is `building`
- `source.number == number`
- the smaller/larger table above, both directions
- confidence 2 at 105, 159, and 180

Fixture assertions, schema copied from `schema/catalog.schema.json` into `tmp_path`:

- patterns 20 and 10, with 20's `smaller` equal to `[10]`, yield `BackEdge(20, 10)` and empty `missing_targets`
- pattern 105 with `smaller` equal to `[104]` yields `LinkRef(105, "smaller", 104)` and empty `back_edges`

`gate.py` tests that build their own one-off schemas on `tmp_path` stay. They never read the repo schemas.
