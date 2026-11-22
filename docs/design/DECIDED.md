# Decided — survey, sync/async unlocks, then form

Decided is the **process layer**: what must exist before the next authoring or check step is legal. It is orthogonal to the **language sequence** (`pl sequence`, Lean `Sequence`) and to **preservation** (`pl step`).

**Survey inventory** is more than lots and north: ground cover (grass, gravel, …), plantings (pines, shade trees), and water (authored ponds OK on a greenfield). Geometry must pass `scripts/lint_spatial.py` (no illegal lot/pad/shell overlap; `sit-on` containment; clearance gaps).

| Order | Question | Owner |
|---|---|---|
| Survey / site | What is the land, north, sun, grade? | Decided Stage 0 |
| Language sequence | Which patterns come before which? | Catalog larger/smaller |
| Construction / authoring | Foundation → frame → openings | Decided Stages 2–4 |

Funny house boxes and unclear ground come from skipping Stages 0–2.

## Stages

| Id | Name | Produces | WebGL shows |
|---|---|---|---|
| `survey` | Survey | Extent, datum, OrientationFrame, contours, solar/wind overlays | Terrain tint, north rose, sun sector, contour stubs |
| `land` | Land | Lots, ROW, parcels, grade/drainage | Lot lines, ROW fills, grade plane |
| `foundation` | Foundations | Pads/footprints, elevation, clearances, sit-on links | Pads on lots; “sits on” only |
| `frame` | Frames | Walls, storeys, roof envelope | Stick / wall shells (not pretty houses) |
| `openings` | Openings | Installed windows/doors (proposals may exist earlier) | Punched openings |
| `patterns` | Patterns | Language run + check evidence | Pattern focus + measured chips |

Pretty skins are **Stage 3–4 cosmetics**. Stages 0–2 are truth: land and structure.

## Sync vs async

### Synchronous (must finish before unlock)

- Survey frame (`north`, `latitude_deg`, extent, grade datum) before any equator/orientation check may be `satisfied`.
- Land lots/ROW before building footprints.
- Foundation geometry (footprint + elevation + clearances) before frame on that lot.
- Frame (walls/storeys) before openings are **installed** (design *proposals* may appear earlier).
- Within one building: foundation → frame → openings is a sync chain.

### Asynchronous (parallel once unlocked)

- Foundations on different lots after land exists.
- Catalog references / research while survey is in progress (not model satisfaction).
- Finish detail on one building while another is foundation-only.
- Judgment patterns (110 Main Entrance, 180 Window Place) after their subjects exist.

### Unlock predicates

| Unlock | Requires | Enables |
|---|---|---|
| `survey.complete` | Seed survey record valid | Land authoring; orientation checks |
| `land.lots` | Survey complete + lots/ROW | Foundation pads (async per lot) |
| `foundation.ready(lot)` | Pad + sit-on land + clearances | Frame for that lot |
| `frame.ready(building)` | Walls/storeys for building | Opening install |
| `openings.installed` + frame | Host edges exist | Checks that need windows (e.g. 159) |

## Relation to `pl sequence` / preserving

- Language order answers “which pattern before which.”
- Decided answers “which *process artifact* before which.”
- A preserving step can fail even when Decided stages are complete (language violation).
- Orientation checks without a survey frame are not legally `satisfied` in the Decided UI (see `SATISFACTION.md`). Offline fixtures may still carry a baked frame for CI.

## How far WebGL goes

| Stage | In scope | Out of scope |
|---|---|---|
| Survey / land | Semantic ground, north, sun wedge, lots | Surveyor-grade DEM |
| Foundations | Pads, clearances, sit-on | Rebar, soils reports |
| Frames / openings | Volumes + openings + unlock state | Photoreal BIM |
| Patterns | Focus + measured evidence | Replacing `pl check` |

Full IFC authoring remains the optional Blender + Bonsai path.

## Seed artifacts

- Process graph: `demo/data/process-stages.json` (schema: `schema/process-stage.schema.json`)
- Survey: `demo/data/seed-district-survey.json`
- SpatialStructure gains land + foundation places and `interactions` (sit-on, clearance)

Cite pattern numbers and names only. Do not copy book text.
