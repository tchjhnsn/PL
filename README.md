# Pattern language

U0 scaffold for an empty pattern-language catalog. The gate accepts an empty `catalog/` and `projects/` tree. Records without a schema fail validation.

## U1

Five JSON Schemas live in `schema/`: `catalog`, `projects`, `pattern-instance`, `check-report`, and `step`. Twelve seed records live in `catalog/`. `projects/seed-house.json` selects those twelve patterns. `load_catalog` reads the records `scan` accepted and reports missing link targets and back-edges. It still returns the twelve patterns.

From the repo root, `uv run python scripts/validate_catalog.py` prints:

```text
back-edges: 0
ok: 13 records
```

The Lean library is `PatternLanguage` on toolchain `leanprover/lean4:v4.33.1`. It has no dependencies.

## U2

`scripts/catalog_to_lean.py` renders `lean/PatternLanguage/Instantiations/Buildings.lean` from the seed catalog. The laws live in `lean/PatternLanguage/`. `decide` proves that numeric order is a valid sequence for the twelve patterns. `lake build` checks that proof.

```bash
uv run python scripts/catalog_to_lean.py
uv run python scripts/catalog_to_lean.py --check
cd lean && lake build
```

`--check` exits 0 when the committed file matches the render, and exits 1 without writing when the file is stale.

## U3

`scripts/make_fixtures.py` writes `fixtures/pass-house.ifc` and `fixtures/fail-house.ifc`, each with a sibling `.expected.json`. `read_topology` reads a house into zones, adjacency, window orientations, and heights. The ten computed patterns each have a pass witness on one house and a fail witness on the other. 110 Main Entrance and 180 Window Place have no house.

```bash
uv run python scripts/make_fixtures.py
uv run python scripts/make_fixtures.py --check
```

`--check` exits 0 when the committed graphs match a fresh write, and exits 1 without writing into `fixtures/` when a file is missing or stale. It compares graphs, not STEP bytes.

## U4

`pl check` reads a house with `read_topology` and writes one check-report. Each computed check is a module under `conditions/`, keyed in `CHECKS` by `condition.check`. The pass house satisfies the ten computed checks. The fail house violates all ten. 110 Main Entrance and 180 Window Place come out as `needs_judgment` with unanswered evidence, and they are absent from `satisfied`. The pass command exits 0. The fail command exits 1.

```bash
uv run pl check fixtures/pass-house.ifc --language projects/seed-house.json
uv run pl check fixtures/fail-house.ifc --language projects/seed-house.json
```

## U5

`pl sequence` prints the seed project in ascending pattern number. That list is `numericOrder` in `Buildings.lean`. `pl step` writes one step from two check-reports. The pass house then the fail house reports `preserved: false` and exits 1, because 105 South Facing Outdoors was satisfied and is gone. The pass house twice reports `preserved: true` and exits 0. 110 Main Entrance and 180 Window Place stay out of `satisfied`.

```bash
uv run pl sequence projects/seed-house.json
uv run pl step fixtures/pass-house.ifc fixtures/fail-house.ifc --language projects/seed-house.json --pattern 112
uv run pl step fixtures/pass-house.ifc fixtures/pass-house.ifc --language projects/seed-house.json --pattern 105
```

## Commands

```bash
uv sync
uv run pytest
uv run python scripts/validate_catalog.py
uv run python scripts/catalog_to_lean.py --check
uv run python scripts/make_fixtures.py --check
uv run pl check fixtures/pass-house.ifc --language projects/seed-house.json
uv run pl sequence projects/seed-house.json
cd lean && lake build
```

Cite pattern numbers and names only. Do not copy book text into this repository.
