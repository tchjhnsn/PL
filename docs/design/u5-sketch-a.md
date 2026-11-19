# U5 candidate A — numeric sequence, step diff

U5 adds `pl sequence <project.json>` and `pl step <before.ifc> <after.ifc> --language <project.json>`.
It is done when the seed sequence equals `numericOrder` in `Buildings.lean`, the list `numericOrder_valid` proves is a `ValidSequence`, and the pass house followed by the fail house writes a step with `preserved: false`.
`sequence` prints the project selection in ascending pattern number.
`step` runs the checker on each model and diffs the two check-reports into `schema/step.schema.json`.
The fixture pair is `fixtures/pass-house.ifc` then `fixtures/fail-house.ifc`.
110 Main Entrance and 180 Window Place stay out of `satisfied`, so they leave `preserved` alone.
A selected pattern that is satisfied before and absent after makes `preserved` false and the command exits 1.
Exit 0 means the step preserved. Exit 2 is usage or a load error.
No new IFC, no Lean edit, and no sixth schema.

Cite pattern numbers and names only.

## Usage

From the repo root:

```bash
uv run pl sequence projects/seed-house.json
uv run pl step fixtures/pass-house.ifc fixtures/fail-house.ifc --language projects/seed-house.json
```

Stdout is JSON, indented two spaces, keys sorted, one trailing newline. Stderr is empty when the command produces a document.

`pl sequence` exits 0. The seed document is:

```json
{
  "project": "seed-house",
  "sequence": [105, 106, 107, 110, 112, 127, 128, 130, 159, 167, 180, 190]
}
```

`pl step` exits 0 when `preserved` is true and exits 1 when `preserved` is false. The document is on stdout in both cases. The pass house then the fail house exits 1. The pass house twice exits 0.

Exit 2 prints one stderr line and no stdout. `pl` with no command, and any command other than `check`, `sequence`, or `step`, prints `unknown command`. A bare `sequence` or `step` prints its usage line:

```text
usage: pl sequence <project.json>
usage: pl step <before.ifc> <after.ifc> --language <project.json>
```

`pl check` keeps its arguments, its usage line, and its exits: 0 on the pass house, 1 on the fail house, 2 on a load error.

Both new commands take `--root PATH`, default `.`, and `--out PATH`. `--root` is the catalog root, resolved. Relative project and model paths open from the current directory. `before.file` and `after.file` are the model arguments, slash-separated, unresolved. `--out` writes the same bytes as stdout.

Library:

```python
from pathlib import Path
from pattern_language.catalog import load_catalog
from pattern_language.checker import run
from pattern_language.parameters import load_project
from pattern_language.sequencer import sequence_of, step_between

root = Path(".").resolve()
project = load_project(Path("projects/seed-house.json"), schema_path=root / "schema" / "projects.schema.json")
catalog = load_catalog(root)
order = sequence_of(project, catalog)
before = run(catalog, project, Path("fixtures/pass-house.ifc"), model_file="fixtures/pass-house.ifc", schema_path=root / "schema" / "check-report.schema.json")
after = run(catalog, project, Path("fixtures/fail-house.ifc"), model_file="fixtures/fail-house.ifc", schema_path=root / "schema" / "check-report.schema.json")
step = step_between(before, after, selection=project.patterns, start=project.start, schema_path=root / "schema" / "step.schema.json")
```

## Call sites

| Caller | What it does |
|---|---|
| `src/pattern_language/cli.py` | Dispatches `check`, `sequence`, and `step`. |
| `src/pattern_language/sequencer.py` | Sorts a selection. Diffs two `CheckReport` values into a step and validates it. |
| `src/pattern_language/checker.py` | Unchanged. `run` still writes one check-report. |
| `tests/test_sequencer.py` | Seed order against `numericOrder`, the preservation diff, the two-house step. |
| `tests/test_cli.py` | Exits for `sequence` and `step`. The unknown-command test stops treating those words as unknown. |

`pattern_language/__init__.py` stays on `load_catalog` and `scan`. Importing the package does not import the sequencer or the checker.

`sequencer.py` imports `CheckReport` and `CheckError`. It does not call `read_topology`, and it does not import `ifcopenshell` or `bpy`. The CLI calls `run` twice, then `step_between`. The sequencer sees reports, which is the §2.2 split: the checker owns reports, the sequencer owns the step.

## Sequence

`sequence_of` returns `tuple(sorted(project.patterns))`. The projects schema already requires a non-empty unique list of integers from 1 to 253, so the result is strictly increasing.

Each number must be a key of `catalog.by_number`. A miss raises `CheckError` with `missing pattern: <n>`, the same line `evaluate` uses. The seed twelve all resolve.

The function reads numbers. It does not read `smaller`, `larger`, or `scale`. On this catalog every smaller edge raises the pattern number, which `Buildings.lean` records as `edgeIncreases` inside `acyclic`, and `numericOrder_valid` is `by decide` on that ascending list. Sorting the seed selection is that list:

```text
105, 106, 107, 110, 112, 127, 128, 130, 159, 167, 180, 190
```

`projects/seed-house.json` selects those twelve and sets `start` to 105. `start` is stored on the project and is not a rotation. The first entry is the least selected number, which on this file is also `start`.

A shorter project is sorted the same way. `sequence_of` on patterns `[190, 105, 110]` returns `(105, 110, 190)`. The done-when comparison is the seed, whose selection is the whole carrier of `language`. That is the list `ValidSequence language numericOrder` talks about. `indexBefore` in `Sequence.lean` is false when either endpoint is missing from the list, so the proof statement is the full `numericOrder`. This unit checks the seed against that list.

There is no sequence schema. The five schema files stay. Stdout is the object above, with `project` set to `project.id`.

## Step

`step_between` takes the before report, the after report, the selection, and `start`.

The two reports must carry the same `project` id. Otherwise `CheckError` is `project mismatch`. The CLI never builds that pair: both `run` calls receive the one loaded project.

`satisfied_before` and `satisfied_after` are the report tuples, copied in the order `run` already uses, numeric ascending. On the seed houses those are the ten computed numbers, and `[]`.

`preserved` is `Preserving` from `Preservation.lean`, with `sat` read off `satisfied`:

```python
def is_preserving(selection: tuple[int, ...], before: tuple[int, ...], after: tuple[int, ...]) -> bool:
    held = set(before)
    later = set(after)
    return all(number in later for number in selection if number in held)
```

A selected pattern that was satisfied before is satisfied after. 110 and 180 are in the seed selection and in neither satisfied list, on both houses. The implication holds for them because they were not satisfied before. `needs_judgment` does not appear in the step. `fails_gate` stays on `pl check`. A violated or `not_applicable` instance changes the step only when its number leaves `satisfied`.

`pattern` is one integer, required by `schema/step.schema.json`:

1. The least number in `satisfied_after` and not in `satisfied_before`.
2. Otherwise the least number in `satisfied_before` and not in `satisfied_after`.
3. Otherwise `start`.

`load_project` already requires `start` to be a selected number. The first two clauses only return numbers that `run` placed in `satisfied`, which are selected numbers. The value is inside 1..253.

On the pass house then the fail house, clause 1 is empty and clause 2 yields 105. The step is:

```json
{
  "after": {
    "file": "fixtures/fail-house.ifc",
    "sha256": "<hex of that file>"
  },
  "before": {
    "file": "fixtures/pass-house.ifc",
    "sha256": "<hex of that file>"
  },
  "pattern": 105,
  "preserved": false,
  "satisfied_after": [],
  "satisfied_before": [105, 106, 107, 112, 127, 128, 130, 159, 167, 190]
}
```

The hashes are the `model.sha256` values `run` computed. The test hashes the two files itself and compares. 105 is in `satisfied_before` and absent from `satisfied_after`, which is the witness that `is_preserving` is false.

On the pass house twice, both diffs are empty, so `pattern` is `start` (105), both satisfied lists are the ten numbers, and `preserved` is true. That is `Preserving.refl` on one report. It needs no third file.

`step_between` validates the dict with `Draft202012Validator` against `schema/step.schema.json` before returning. A miss raises `CheckError` with the validator message. The schema file is unchanged: `before`, `after`, `pattern`, `satisfied_before`, `satisfied_after`, `preserved`.

`step_json` uses the same encoding as `report_json`.

Stable stderr lines, besides the ones `run` and `load_project` already print:

| Situation | Line |
|---|---|
| Selected number absent from the catalog | `missing pattern: <n>` |
| Report project ids differ | `project mismatch` |

A model path over 240 characters, a missing file, a bad project, and a topology error still come from `run` or `load_project` and still exit 2.

## Data shapes

```python
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
```

## Signatures

`src/pattern_language/sequencer.py`:

```python
def sequence_of(project: Project, catalog: Catalog) -> tuple[int, ...]: ...

def is_preserving(
    selection: tuple[int, ...],
    before: tuple[int, ...],
    after: tuple[int, ...],
) -> bool: ...

def applied_pattern(before: tuple[int, ...], after: tuple[int, ...], start: int) -> int: ...

def step_between(
    before: CheckReport,
    after: CheckReport,
    *,
    selection: tuple[int, ...],
    start: int,
    schema_path: Path,
) -> Step: ...

def step_json(step: Step) -> str: ...
```

`cli.py` keeps `main(argv: list[str] | None = None) -> int`. The first token selects the parser. `check` stays `_parse` as it is today. `sequence` takes the project path, `--root`, and `--out`. `step` takes two model paths, required `--language`, `--root`, and `--out`.

The step command loads the catalog and the project once, calls `run` on the before file, calls `run` on the after file, then calls `step_between`. A failure on the before file prints nothing. A failure on the after file prints nothing.

Exit from a produced step is `0 if step.preserved else 1`.

## Tests

`tests/test_sequencer.py`:

- Parse `def numericOrder` in `lean/PatternLanguage/Instantiations/Buildings.lean` and collect the twelve `.p<number>` arms. `sequence_of` on `projects/seed-house.json` equals that tuple, and equals `tuple(sorted(project.patterns))`.
- A temp project whose `patterns` are `[190, 105, 110]` sequences as `(105, 110, 190)`.
- A temp project whose `patterns` are `[200]` raises `CheckError` `missing pattern: 200`.
- `is_preserving((105, 106), (105,), (105, 106))` is true. `is_preserving((105, 106), (105, 106), (106,))` is false. `is_preserving((110, 180), (), ())` is true.
- `applied_pattern((105,), (105, 106), 105)` is 106. `applied_pattern((105, 106), (106,), 106)` is 105. `applied_pattern((105,), (105,), 112)` is 112.
- `step_between` on two constructed `CheckReport` values with those satisfied lists validates against `schema/step.schema.json`.
- `main(["step", "fixtures/pass-house.ifc", "fixtures/fail-house.ifc", "--language", "projects/seed-house.json"])` from the repo root returns 1, stderr empty, and the JSON above: files, hashes, `pattern` 105, `preserved` false, the ten-number before list, the empty after list.
- The same command with the pass house in both positions returns 0, `preserved` true, `pattern` 105, and both satisfied lists equal to the ten computed numbers.

`tests/test_cli.py`:

- `main([])` and `main(["nope"])` return 2 with stderr `unknown command\n` and empty stdout.
- `main(["sequence"])` and `main(["step"])` return 2 with empty stdout and their usage line.
- `main(["sequence", "projects/seed-house.json"])` from the repo root returns 0 and the seed sequence object.
- `main(["check", ...])` on both houses is unchanged.

`tests/test_boundaries.py` keeps the import scan. `sequencer.py` adds no `ifcopenshell` and no `bpy` import. The subprocess that imports `pattern_language.checker` stays green because the sequencer is not on that import path. `schema/step.schema.json` stays in the schema list and is not given a record root.

`catalog_to_lean.py --check` stays green. The sequencer does not write Lean. `make_fixtures.py` stays as it is. The two houses and their `.expected.json` files stay.

## Module map

```text
src/pattern_language/sequencer.py     sequence_of, step_between, step_json
src/pattern_language/cli.py           check, sequence, step
tests/test_sequencer.py               the unit check
tests/test_cli.py                     usage lines and exits
README.md                             U5 paragraph and the two commands
AGENTS.md                             sequencer row, both commands, U5 section
docs/design/DESIGN.md                 short U5 section after U4
```

Unchanged: `checker.py`, `conditions/`, `topology.py`, the twelve catalog files, `projects/seed-house.json`, both IFC fixtures, `schema/`, `lean/`, `uv.lock`, `pyproject.toml`. The `pl` script entry is already `pattern_language.cli:main`.

Docs the implementer updates, in place:

- `README.md` — a U5 section: `pl sequence` prints numeric order, `pl step` writes a step, the pass-then-fail command reports `preserved: false` and exits 1.
- `AGENTS.md` — `sequencer.py` orders a project and diffs two reports. `cli.py` has `check`, `sequence`, and `step`. The U4 sentence that sequence and step stay later becomes history. The command block and the CI sentence gain `pl sequence projects/seed-house.json`.
- `docs/design/DESIGN.md` — a U5 section after U4: numeric order matches `numericOrder_valid` on the seed, and the two houses are the step that reports `preserved: false`.

## Rationale

- §2.2 gives the sequencer two jobs: order a project language, and compute a step from two reports. Sorting the selection is the order. `step_between` is the diff. The CLI is the only place that turns IFC into reports.
- §2.6 defines `ValidSequence` as `indexBefore` of the completing pattern before the smaller one, and the seed proof is `numericOrder_valid`. The Python check is equality with that generated list. The proof stays `by decide` in Lean. Geometry stays on the fixture tests.
- §2.6 defines `Preserving` as: every selected pattern that held before holds after. `is_preserving` is that quantifier, with `sat` meaning membership in `satisfied`. Reflexivity is the pass house compared with itself. One dropped earlier pattern is the pass house then the fail house. 105 is the least such pattern, and it is the `pattern` field on that step.
- §1.4 and `schema/step.schema.json` already name the six fields. U1 shipped the schema. U5 fills it. A new schema would be a second contract for the same record.
- §3.3 asks for a fixture pair that breaks an earlier pattern. The fail house violates every computed pattern the pass house satisfies, including 105, the first number in the sequence. Writing another house would repeat that witness.
- 110 and 180 are `needs_judgment` on both houses and are absent from `satisfied`. Preservation talks about `sat`. Unanswered evidence is not a loss of satisfaction.
- `pl check` exits 1 when the report is real and the gate fails, and exits 2 when it cannot produce the report. `pl step` uses that same split for `preserved`. CI runs the command that exits 0. Pytest runs the command that exits 1.

## CI impact

`.github/workflows/ci.yml` gains one step after the pass-house check:

```yaml
- run: uv run pl sequence projects/seed-house.json
```

The pass-then-fail step exits 1, so it stays in pytest, as the fail-house `pl check` already does. `uv.lock` is unchanged.

| Check | U5 result |
|---|---|
| `uv run pytest` | Seed sequence equals `numericOrder`. Pass then fail is a valid step with `preserved: false`. Pass then pass has `preserved: true`. |
| `pl sequence` on the seed | Exit 0. The twelve numbers in ascending order. |
| `pl step` pass then fail | Exit 1. `pattern` 105. `preserved` false. |
| `pl check` on the pass house | Unchanged, exit 0. |
| `validate_catalog.py` | `back-edges: 0` and `ok: 13 records`. |
| `catalog_to_lean.py --check` | Unchanged. |
| `lake build` | Unchanged. `numericOrder_valid` still compiles. |
| Import boundary | `ifcopenshell` still appears only inside `read_ifc` and `write_ifc`. `bpy` appears nowhere. |

## What this unit leaves

`Selection` and `DownClosed` are named in §2.6 and are absent from `Sequence.lean`. A later change can require a project to contain every smaller target of a selected pattern. This unit sorts whatever the project lists, and the proved comparison is the full seed.

A later command can name the applied pattern itself. This unit fills `pattern` from the satisfied-set diff, then from `start`.

`Preserving.trans`, `Run`, and `Applies` stay in Lean. Python checks one pair of reports. A chain of steps is a later unit.

U6 is the MCP server, including `language_sequence` and `model_step`, over these two results. U7 is the Blender adapter. `adapters/blender/` and `mcp/` stay empty. Nothing imports `bpy`.
