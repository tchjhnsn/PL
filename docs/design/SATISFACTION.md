# When `satisfied` is legal

A pattern instance may be `satisfied` only when every predicate the check names is defined in the model and the measured values pass. Status chips without those predicates are not evidence.

**Decided** (`docs/design/DECIDED.md`) adds process unlocks: a survey frame must complete before orientation checks are treated as legally satisfiable in the WebGL stage viewer. Language `pl sequence` remains a separate order from construction stages.

## Shared frame

Orientation checks need an **OrientationFrame** (`schema/orientation-frame.schema.json`):

| Field | Role |
|---|---|
| `north` | Plan-plane vector toward geographic north (IFC TrueNorth; seed `(0, 1)`). |
| `latitude_deg` | Site latitude from the project (`projects/seed-house.json`). Catalog placeholders may be `0`; the project overrides. |
| cardinals | Opening `north\|south\|east\|west` from host-edge outward normal vs `north`. |

Equator-ward (used by 105 South Facing Outdoors and 128 Indoor Sunlight) is `-north` when `latitude_deg > 0`, `+north` when `latitude_deg < 0`, and **undefined** when `latitude_deg` is `0` (check fails).

## Tags

Spaces carry tags from `ALLOWED_TAGS` in `topology.py`. Checks select subjects by tag (`outdoor`, `occupied`, `balcony`, …). Unknown tags are rejected at assemble/read.

## Elevation

`Zone.floor_elevation_m` is metres above site grade. Storeys carry the same field as IFC `Elevation`. A space tagged `balcony` is only a balcony for 167 Six-Foot Balcony when `floor_elevation_m >= min_elevation_m` (default 2.4). Otherwise the check is **not applicable** — a ground patio is not a balcony.

## Evidence

Computed check-reports store `kind: check`, `check`, `passed`, and `measured` key/value pairs (including frame fields the check used). Judgment patterns stay `needs_judgment` with unanswered questions and never enter `satisfied`.

## Seed witnesses

| Pattern | Pass predicate (summary) |
|---|---|
| 105 South Facing Outdoors | One main outdoor (non-balcony) centroid equator-ward of occupied mass |
| 167 Six-Foot Balcony | Every elevated balcony’s shallowest depth ≥ 1.83 m |

Cite pattern numbers and names only. Do not copy book text.
