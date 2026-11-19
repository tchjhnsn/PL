# U3 candidate A — two houses, ten witnesses

U3 writes small IFC houses and reads each one into a BOT-shaped graph. It is done when tests assert zones, adjacency, window orientations, and heights from each fixture, and each of the ten computed patterns has a pass witness on one house and a fail witness on the other.

The ten computed patterns are 105, 106, 107, 112, 127, 128, 130, 159, 167, and 190. 110 and 180 are judged. They get no house.

Two files carry all twenty witnesses. `fixtures/pass-house.ifc` holds the ten pass witnesses. `fixtures/fail-house.ifc` holds the ten fail witnesses. A witness is a fact on the graph (a tag, a door pair, a footprint, an exterior segment, a window orientation, a height). The witnesses do not cancel, so a separate model per pattern would repeat the same site, storey, and reader asserts. U3 does not run a condition. U4 is the registry that turns these facts into pass or fail.

`src/pattern_language/topology.py` is the only module that imports `ifcopenshell`. The script calls `write_fixtures`. Tests call `read_topology`. Nothing imports `bpy`.

North is +Y, east is +X, units are metres. The catalog value `latitude_deg: 0` stays in the JSON. This unit does not read it. Equator-facing, given a latitude, is a U4 reading of the site north vector plus footprints.

## Usage

From the repo root:

```bash
uv run python scripts/make_fixtures.py
uv run python scripts/make_fixtures.py --check
```

The first command writes `fixtures/pass-house.ifc` and `fixtures/fail-house.ifc`. The second writes both houses to a temporary directory, reads the committed files and the fresh files, and compares the two `Topology` values. It exits 0 when they match. It exits 1, and does not write into `fixtures/`, when a committed file is missing or the graphs differ. Stderr is `stale: fixtures/pass-house.ifc` or `stale: fixtures/fail-house.ifc`.

`--check` compares graphs, not STEP bytes. IfcOpenShell's writer is not a stable serialization. Hand-editing a fixture changes the graph and fails `--check`.

Library:

```python
from pathlib import Path
from pattern_language.topology import read_topology, write_fixtures

write_fixtures(Path("fixtures"))
graph = read_topology(Path("fixtures/pass-house.ifc"))
```

`read_topology` raises `TopologyError` on a file it cannot read as this graph: length unit other than metre, a space with no extruded body, a duplicate zone name, a window that is not on one footprint edge, or a facing that is not cardinal.

## Call sites

| Caller | What it does |
|---|---|
| `scripts/make_fixtures.py` | Calls `write_fixtures` on `fixtures/`, or compares graphs under `--check`. Does not import `ifcopenshell`. |
| `src/pattern_language/topology.py` | Writes the two houses and reads any of these IFC files into `Topology`. The only `ifcopenshell` import. |
| `tests/test_topology.py` | Reads both fixtures. Asserts zones, adjacency, window orientations, and heights. Asserts one witness per computed pattern on each house. Regenerates and compares. |
| `tests/test_boundaries.py` | Allows `ifcopenshell` only in `src/pattern_language/topology.py`. `bpy` stays forbidden in every Python file. |
| U4 checker | Later caller of `read_topology` on these two paths. U3 does not add it. |

`pattern_language/__init__.py` does not import `topology`. Importing the package does not load `ifcopenshell`. There is no `pl` command and no `[project.scripts]` entry.

`scan` does not read `fixtures/`. The two IFC files are not records.

## Data shapes

The graph is the BOT relations in §2.2, frozen, with no IFC objects left on it. Names are the stable ids in tests. `GlobalId` is deterministic so two reads of one write compare equal, and tests do not depend on it.

```python
ZoneKind = Literal["Site", "Building", "Storey", "Space"]
Cardinal = Literal["north", "south", "east", "west"]
Point = tuple[float, float]

@dataclass(frozen=True, slots=True)
class Zone:
    name: str
    kind: ZoneKind
    parent: str | None
    tags: frozenset[str]
    footprint: tuple[Point, ...]   # empty for site, building, storey
    height_m: float | None         # extrusion depth; None for site, building, storey

@dataclass(frozen=True, slots=True)
class Boundary:
    space: str
    other: str | None              # None when the segment is exterior
    start: Point
    end: Point
    external: bool

@dataclass(frozen=True, slots=True)
class Opening:
    name: str
    kind: Literal["window", "door"]
    orientation: Cardinal
    spaces: tuple[str, ...]        # one space for a window, two sorted names for a door

@dataclass(frozen=True, slots=True)
class Topology:
    north: Point                   # (0.0, 1.0)
    zones: tuple[Zone, ...]
    adjacent: tuple[tuple[str, str], ...]
    boundaries: tuple[Boundary, ...]
    openings: tuple[Opening, ...]
```

| Field | BOT | Meaning |
|---|---|---|
| `Zone.kind` | `bot:Zone` | `Site`, `Building`, `Storey`, or `Space`. |
| `Zone.parent` and the zone list | `bot:containsZone` | Site contains the building, the building contains the storey, the storey contains every space. |
| `adjacent` | `bot:adjacentZone` | Undirected pairs of spaces that share a boundary segment. Sorted. Derived from `boundaries` where `other` is set. |
| `Opening` | `bot:Element` and `bot:hasElement` | Windows and doors. A door is `bot:interfaceOf` the two spaces in `spaces`. |
| `Boundary` | `bot:interfaceOf` | One segment of a space profile, the neighbor on that segment, or exterior. |
| `height_m` | space body | Clear height in metres. |
| `footprint` | space body | Plan ring in metres. |
| `tags` | — | Words copied from `IfcSpace.Description`. Not a BOT class. The closed set is below. |
| `north` | site true north | Plan vector. +Y in both houses. |

`adjacent` stores each pair once, names in lexicographic order, pairs sorted. `zones` are sorted by name. `openings` are sorted by name. `boundaries` are sorted by `(space, start, end)`. Tags are a `frozenset`. Rings are closed-point dropped, counter-clockwise, rotated so the lexicographic minimum point is first, coordinates rounded to millimetres (`round(x, 3)`).

Tag words, and no others:

`outdoor`, `street`, `transition`, `public`, `semi-private`, `private`, `daytime`, `corridor`, `living`, `room`, `balcony`, `occupied`.

These are the words already used in §1.5. The writer rejects any other tag. The reader raises `TopologyError` on any other word. Empty description is the empty set (the two flank spaces).

`IfcSpace.Description` is the only place tags live. `PredefinedType` is `SPACE` on every space and is not read. A custom property set would be a second vocabulary.

## The two houses

Both houses are one `IfcProject`, one `IfcSite` named `site`, one `IfcBuilding` named `house`, one `IfcBuildingStorey` named `ground` at elevation 0. Every space is an `IfcSpace` extruded +Z. Outdoor rooms are spaces, so one reader covers them. There are no slabs. Height is the extrusion depth.

Walls are axis-aligned. Where two space rings overlap on a collinear run longer than 50 mm, the overlap is an internal boundary and both spaces list each other. The uncovered remainder of each ring is an exterior boundary. A partial overlap splits one profile edge into two boundary segments. The writer raises if a ring edge is not axis-aligned.

Openings sit on a ring edge. Facing is the outward normal of the nearest footprint edge (counter-clockwise ring, right-hand normal), snapped to the dominant axis. A tie raises `TopologyError`. Off-center openings on a straight edge keep that edge's facing. Tests place more than one opening on an edge.

### Pass house

Occupied rooms are 4 m by 4 m, so every point of each is within 4 m of a full exterior side. That is inside the 8 m depth on 107. Ceiling heights differ by 0.6 m, above the 0.3 m parameter on 190. The balcony is 2.00 m deep, above 1.83 m.

| Space | Tags | Ring (min point first, CCW) | Height |
|---|---|---|---|
| `street` | `street` | (0,−2) (8,−2) (8,0) (0,0) | 3.0 |
| `court` | `outdoor` `transition` | (0,0) (8,0) (8,4) (0,4) | 3.0 |
| `hall` | `room` `public` `occupied` | (0,4) (4,4) (4,8) (0,8) | 2.4 |
| `living` | `living` `semi-private` `daytime` `occupied` | (4,4) (8,4) (8,8) (4,8) | 3.0 |
| `bedroom` | `room` `private` `occupied` | (4,8) (8,8) (8,12) (4,12) | 2.7 |
| `balcony` | `balcony` `outdoor` | (8,8) (10,8) (10,12) (8,12) | 3.0 |

`court` is the only space tagged `outdoor` and not `balcony`. Its centroid is (4, 2). The occupied centroid is at Y = 7.333. The court is south of the occupied rooms. Both outdoor footprints (`court`, `balcony`) are rectangles.

`hall` touches `bedroom` at the point (4, 8) only. That is not a shared segment, so they are not adjacent.

Doors:

| Name | Spaces |
|---|---|
| `approach-door` | `court`, `street` |
| `main-door` | `court`, `hall` |
| `hall-living` | `hall`, `living` |
| `living-bedroom` | `living`, `bedroom` |
| `bedroom-balcony` | `balcony`, `bedroom` |

Windows, one edge each, facing from that edge:

| Name | Space | Facing |
|---|---|---|
| `hall-south` | `hall` | south |
| `hall-west` | `hall` | west |
| `living-south` | `living` | south |
| `living-east` | `living` | east |
| `bedroom-north` | `bedroom` | north |
| `bedroom-west` | `bedroom` | west |

Exterior sides used by the depth witness: `hall` west, `living` east, `bedroom` north and west. `living`'s south side is the court and its west side is `hall`. The east side is free because the balcony is on `bedroom`, not on `living`.

Door distance from `hall`, the indoor side of `main-door`: `hall` 0 (`public`), `living` 1 (`semi-private`), `bedroom` 2 (`private`). The same distances hold on `adjacent`, because `hall` is not adjacent to `bedroom`.

### Fail house

One geometric fault per computed pattern, named zones. `west-flank` and `east-flank` exist so the long sides of `bedroom` are internal. They have no tags and no doors.

| Space | Tags | Ring | Height |
|---|---|---|---|
| `street` | `street` | (0,−2) (8,−2) (8,0) (0,0) | 2.4 |
| `corridor` | `corridor` | (0,0) (8,0) (8,2) (0,2) | 2.4 |
| `west-flank` | — | (0,2) (4,2) (4,12) (0,12) | 2.4 |
| `bedroom` | `room` `private` `occupied` | (4,2) (8,2) (8,12) (4,12) | 2.4 |
| `east-flank` | — | (8,2) (11,2) (11,12) (8,12) | 2.4 |
| `dayroom` | `public` `daytime` `occupied` | (0,12) (6,12) (6,15) (0,15) | 2.4 |
| `balcony` | `balcony` `outdoor` | (−1,12) (0,12) (0,15) (−1,15) | 2.4 |
| `court` | `outdoor` | (0,15) (8,15) (8,16) (2,16) (2,22) (0,22) | 3.0 |

`court` is an L. Area 20, convex hull area 38, ratio 20/38, below the 0.75 parameter on 106. The balcony stays a rectangle, so the L is the convexity witness and the balcony is the depth witness. `court` is again the only space tagged `outdoor` and not `balcony`. Its centroid is (2.2, 17.6), north of every occupied room (occupied rooms end at Y = 15).

`bedroom` is 4 m by 10 m. Its only exterior boundary segment is (6, 12)–(8, 12). South is `corridor`, west is `west-flank`, east is `east-flank`, and (4, 12)–(6, 12) is `dayroom`. A point at the south end is 10 m from that exterior segment, past the 8 m depth on 107. The single window sits on that segment and faces north, so 159 fails on `bedroom` while `dayroom` still has two orientations.

Doors:

| Name | Spaces |
|---|---|
| `main-door` | `corridor`, `street` |
| `corridor-bedroom` | `bedroom`, `corridor` |
| `bedroom-dayroom` | `bedroom`, `dayroom` |
| `dayroom-balcony` | `balcony`, `dayroom` |

No space is tagged `transition`. `street` is adjacent only to `corridor`.

Windows:

| Name | Space | Facing |
|---|---|---|
| `bedroom-north` | `bedroom` | north |
| `dayroom-north` | `dayroom` | north |
| `dayroom-west` | `dayroom` | west |

Door distance from `corridor`, the indoor side of `main-door`: `bedroom` 1 (`private`), `dayroom` 2 (`public`). There is no `semi-private` space. On `adjacent`, `west-flank` also touches `dayroom`, and the shortest distance is still private 1, public 2.

Occupied heights are 2.4 and 2.4. Spaces without `occupied` are not part of the 190 witness.

## Witnesses

Tests assert these facts on the graph. They do not call a check function. The parameter column is the catalog value U4 will use; U3 only needs the fact to sit on the passing side or the failing side of it.

| No. | Pass house | Fail house |
|---|---|---|
| 105 | `court` centroid Y = 2, south of the occupied centroid Y = 7.333 | `court` centroid Y = 17.6, north of every occupied room |
| 106 | `court` and `balcony` rings are rectangles | `court` ring is the L above; `balcony` stays a rectangle |
| 107 | every `occupied` ring is 4 m by 4 m and has a full exterior side | `bedroom`'s only exterior segment is (6, 12)–(8, 12), and the room is 10 m long |
| 112 | door chain `street` — `court` — `hall`, and `court` is tagged `transition` | door from `street` to `corridor`, and no tag `transition` |
| 127 | from `hall`: `public` at 0, `semi-private` at 1, `private` at 2 | from `corridor`: `private` at 1, `public` at 2 |
| 128 | the only `daytime` space is `living`, centroid Y = 6 | the only `daytime` space is `dayroom`, centroid Y = 13.5 |
| 130 | `main-door` joins `court` and `hall`; `hall` is tagged `room` and is not tagged `corridor` or `living` | `main-door` joins `street` and `corridor`; `corridor` is tagged `corridor` |
| 159 | `hall` {south, west}, `living` {south, east}, `bedroom` {north, west} | `bedroom` {north}; `dayroom` {north, west} |
| 167 | `balcony` extends 2.00 m east of the shared edge x = 8 | `balcony` extends 1.00 m west of the shared edge x = 0 |
| 190 | occupied heights `hall` 2.4, `living` 3.0, `bedroom` 2.7 | occupied heights `bedroom` 2.4, `dayroom` 2.4 |

110 and 180 are absent from this table.

Both the door graph and `adjacent` support the 112 and 127 rows. U4 can use either relation. The flank shortcut on the fail house does not put `public` closer than `private`.

## Why one fail house is enough

Each fail is local to a named zone, and no fail removes the fact another witness needs.

- 105 moves `court` north. 112 removes `transition` from the south door chain. The north court is not on that chain.
- 106 deforms `court` only. 167 shrinks `balcony` and leaves it rectangular, so it is not the convexity witness.
- 107 and 159 share `bedroom` (one short exterior wall, one window on it). They are different fields: a boundary segment and an opening. `dayroom` keeps two window facings so 159's failing space is `bedroom`.
- 130's door target is `corridor`, which has no intimacy tag. 127's order is the next doors: private, then public. `dayroom` is tagged `public`, not `living`, so it is not a second 130 target.
- 128 puts the only `daytime` space on the north. 190 sets both occupied heights equal. Flanks and `corridor` are not `occupied`, so they do not add a height, a window obligation, or a depth obligation.
- The pass house keeps `living` off the entrance door, so the space tagged `living` is not the 130 target. `hall` is tagged `room` and `public`.

An eleventh pattern that needed a contradictory plan would get its own file. These ten do not.

## Reader

`read_topology(path)`:

1. Open the file with IfcOpenShell. Require one `IfcSite`, one `IfcBuilding`, one `IfcBuildingStorey`.
2. Require the length unit to be metre. Read true north from the geometric context. Both houses set it to (0, 1, 0); the XY part is `north`.
3. Walk `IfcRelAggregates` for site → building → storey, and `IfcRelContainedInSpatialStructure` for spaces on the storey. Windows and doors are contained in the storey, which is ordinary IFC, and are not children of the space.
4. Read each space body: one `IfcExtrudedAreaSolid` along +Z. `height_m` is `Depth`. The footprint is the profile polyline times the placement's XY origin. Profiles in these houses are written in world XY with placement origin (0, 0, 0), so the ring is the profile.
5. Split `Description` on whitespace into tags.
6. Read `IfcRelSpaceBoundary` into `Boundary`. `external` is true when `InternalOrExternalBoundary` is `EXTERNAL`. `other` is the space on the paired boundary that shares the wall; it is `None` when the boundary is exterior.
7. Derive `adjacent` from internal boundaries.
8. Read each `IfcWindow` and `IfcDoor`. The opening point is the placement's XY translation. Facing is the outward normal of the nearest edge of the host space, within 50 mm. A door's `spaces` are the two spaces of the wall it fills, sorted by name. A window's `spaces` is the one host space.

The reader does not compute convexity, depth-to-wall, door distance, or "south of". Those are tests and, later, checks. The reader does not import shapely or networkx.

## Writer

`write_fixtures(directory)` overwrites the two IFC files and leaves any other file in the directory alone. It builds each house from the tables above.

Use IfcOpenShell's `api` for the file, the metre unit, the body context, and the project / site / building / storey tree (`project.create_file` at IFC4, `unit.assign_unit`, `context.add_context`, `root.create_entity`, `aggregate.assign_object`, `spatial.assign_container`). Space bodies, walls, and space boundaries are `create_entity` calls on that file. The extrusion profile is `IfcArbitraryClosedProfileDef`, which is what the L requires; the rectangle helper would not express 106's fail witness.

`GlobalId` is `ifcopenshell.guid.compress` of `uuid.uuid5` over a fixed namespace and `"{house}/{element-name}"`. Header `time_stamp` is `2026-11-19T00:00:00`. Owner history uses that same instant. Names come from the tables.

The writer does not read the catalog. Pattern numbers are not written into the IFC. The link from pattern to house is the test table.

## Module map

```text
src/pattern_language/topology.py     write_fixtures, read_topology, Topology
scripts/make_fixtures.py             CLI only
fixtures/pass-house.ifc              generated, committed
fixtures/fail-house.ifc              generated, committed
tests/test_topology.py               readback and the ten witnesses
tests/test_boundaries.py             one allowed ifcopenshell importer
pyproject.toml                       ifcopenshell dependency
uv.lock                              frozen lock refreshed
README.md                            U3 paragraph
AGENTS.md                            topology row, fixtures row, import rule, U3 section
docs/design/DESIGN.md                short U3 pointer after U2
```

`catalog.py`, `gate.py`, the twelve JSON files, the five schemas, and `lean/` stay. `fixtures/.gitkeep` can stay beside the IFC files. `projects/` stays empty.

Docs the implementer updates, in place:

- `README.md` — `make_fixtures.py`, the two fixture paths, and `read_topology`. Keep the number-and-name citation rule.
- `AGENTS.md` — `topology.py` reads and writes IFC and is the only module that imports `ifcopenshell`. `fixtures/` holds the two generated houses. The core import sentence gains that exception and still forbids `bpy`.
- `docs/design/DESIGN.md` — a U3 section after U2: two generated houses, one pass witness and one fail witness per computed pattern, tests read zones, adjacency, window orientations, and heights.

## Signatures

`src/pattern_language/topology.py`:

```python
def read_topology(path: Path) -> Topology: ...

def write_fixtures(directory: Path) -> tuple[Path, Path]: ...
```

`write_fixtures` returns `(directory / "pass-house.ifc", directory / "fail-house.ifc")`.

`scripts/make_fixtures.py`:

```python
def main(argv: list[str] | None = None) -> int: ...
```

`main` finds the repo as the parent of `scripts/`, the same default as `scripts/validate_catalog.py`. No positional root. `--check` returns 1 without writing into `fixtures/` when the graphs differ.

`topology.py` imports `ifcopenshell` and `ifcopenshell.api` (and `ifcopenshell.guid`). It does not import `bpy`, `catalog`, or `gate`. `make_fixtures.py` imports `read_topology` and `write_fixtures`.

## Tests

`tests/test_topology.py` holds the expected zones, adjacency, openings, and heights as literals. It does not import the writer tables and compare the file to itself.

On each committed fixture:

- zone names, kinds, parents, tags, normalized rings, heights
- `adjacent` pairs
- window name, space, and facing
- door name and the two spaces
- `north == (0.0, 1.0)`
- containment `site` → `house` → `ground` → every space

One parametrized test, ids `105` through `190` skipping 110 and 180, asserts the witness row for `pass-house` and the witness row for `fail-house`. The 107 fail row asserts the exterior segment, not only the ring. The 112 and 127 rows assert door pairs and tags. The 167 row asserts the balcony ring.

`test_committed_fixtures_match_writer` writes to `tmp_path` and asserts `read_topology` equality with the committed files.

`test_make_fixtures_check` runs the script with `--check` and expects exit 0. A mutated copy is not required in CI; the equality test is the staleness guard. The script test covers the exit code on the real repo.

`tests/test_boundaries.py` `test_import_boundary_forbids_ifcopenshell_and_bpy` becomes: `bpy` in any Python file fails; `ifcopenshell` fails except in `src/pattern_language/topology.py`. `test_importing_gate_does_not_load_forbidden_modules` stays. `test_u0_has_no_pl_command` stays.

The fixture directory contains exactly those two `.ifc` files.

## Rationale

- §3.3 asks for one passing house and one failing house per computed pattern. The pass house is that passing house for each of the ten, and the fail house is that failing house for each of the ten. The file count is two because the twenty facts fit.
- The unit check in §3.3 is readback: zones, adjacency, window orientations, heights. Witness rows that are rings, exterior segments, or door pairs are the same readback, aimed at one pattern so U4 inherits a file that already distinguishes the condition.
- Condition code stays out. A `satisfied: bool` on `Topology` would move U4 into this unit.
- `topology.py` owns both write and read so the IfcOpenShell import has one module, matching the handoff rule. The script is the command, not a second importer.
- Tags ride in `Description` so the file stays IFC4 and the vocabulary stays the §1.5 words. BOT has no public / private / daytime classes.
- Adjacency is whatever the space boundaries say. The reader does not infer neighbors with a geometry library. The writer emits the boundaries, including the split north edge of the fail `bedroom`, because that segment is the 107 witness.
- Shapely and networkx are not added. Convexity and path distance are arithmetic over the rings and door list U4 can do, or shapely can do then. This unit's tests use the literal coordinates.
- No schema, no catalog edit, no project file, no Lean edit, no `pl` command. `latitude_deg` stays 0.
- STEP is not the oracle. The graph is. A lockfile bump that rewrites entity order without changing the graph still passes `--check`.

## CI impact

`.github/workflows/ci.yml` gains no step. `uv run pytest` already runs the readback, the witness table, and `--check`.

`pyproject.toml` gains `ifcopenshell` under `[project].dependencies`. `uv.lock` is regenerated. `uv sync --frozen` on CI installs that wheel. IfcOpenShell publishes wheels; the runner does not need a system library.

| Check | U3 result |
|---|---|
| `uv run pytest` | `test_topology.py` reads both houses and asserts the four readback families plus ten witness pairs. `--check` exits 0. |
| `validate_catalog.py` | Unchanged. `fixtures/` is still outside the scan. |
| `catalog_to_lean.py --check` | Unchanged. |
| `lake build` | Unchanged. |
| Import boundary | `ifcopenshell` appears in `topology.py` only. `bpy` appears nowhere. |

## What this unit leaves

U4 adds `conditions/`, the registry, and `pl check`. It reads these two paths, evaluates each computed check, and expects the pass house to satisfy all ten and the fail house to violate all ten. Judged 110 and 180 stay unanswered.

U4 owns the definitions this unit deliberately does not apply: convexity ratio, distance to the nearest exterior segment, door-graph order of intimacy tags, which outdoor space is the main one (here, the only `outdoor` space that is not `balcony`), and how `latitude_deg` rotates "south". The fixture numbers sit on the passing or failing side of the parameters already stored on the seed: 0.75, 8 m, 1.83 m, 0.3 m.

Expected check reports under `fixtures/` are U4. Town scale, CityJSON, and Blender are later units.
