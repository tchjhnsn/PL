# U9 — Measure conditions

Contract (accepted). A condition may read a frozen `Topology` or a SpatialStructure plan. `CHECKS` still maps each catalog check id to the Topology function from U4. The plan reading is a private helper (`meets_clear_width`); wiring that helper into `evaluate` is a later unit.

## Goal

167 Six-Foot Balcony can read a named measure on a SpatialStructure plan with the catalog threshold `min_depth_m` (1.83). `pl check` on an IFC house keeps calling `six_foot_balcony.check` through `CHECKS`.

U8 left the plan in `schema/spatial-structure.schema.json`, `load_spatial`, and `clear_width`. U9 says how a condition uses that reading. Wiring the plan into `evaluate` waits until this contract’s acceptance tests are the ones a later change extends.

## Two subjects

A measure condition takes one subject and the mapping from `params_for`. The checker selects the subject from what the caller loaded. It does not select by pattern number.

**Topology.** `read_topology` returns the frozen graph. `checker.evaluate` passes `(topology, center, params)` to `CHECKS[condition.check]`. `center` is the single zone of kind Building. `CheckFn` stays `Callable[[Topology, str, Mapping], Evidence]`.

For 167 Six-Foot Balcony that function is `conditions/six_foot_balcony.py`. It keeps spaces under `center` whose tags include `balcony`, reads `balcony_depth` against boundaries with `external` false, and passes when every depth is at least `min_depth_m`. No such space yields `applicable` false and `passed` false. The measured key is `min_depth_m`, the shallowest depth, rendered with `dec`.

**SpatialStructure plan.** The subject is the dict `load_spatial` has already validated. The condition opens no file and imports neither `ifcopenshell` nor `bpy`. `clear_width` in `spatial_structure.py` returns the place’s first measure of kind `width`, otherwise the first of kind `depth`, otherwise `None`.

## Predicate

On the seed district (`demo/data/plan-model.json`):

```text
clear_width(plan, "a-balcony") >= 1.83
```

`a-balcony` has role `balcony` and measure `m-balcony-depth` (kind `depth`, `value_m` 6.0). `clear_width` returns 6.0. 6.0 meets 1.83, so the predicate holds. 1.83 is `min_depth_m` on 167 Six-Foot Balcony. The plan path uses that parameter. It does not invent a second threshold.

| Reading | Instance |
|---|---|
| a number greater than or equal to `min_depth_m` | `satisfied` (`applicable` true, `passed` true) |
| a number below `min_depth_m` | `violated` (`applicable` true, `passed` false) |
| no width and no depth on that place | `not_applicable` (`applicable` false, `passed` false) |

A missing measure matches a Topology that has no balcony-tagged space: the check does not apply. The report status is `not_applicable`, which still fails `fails_gate`, the same way an unchecked computed instance does today.

## Whole plan, when wired

The helper below is one place. The checker fold, still unwired, follows the Topology rule of “every balcony”:

1. Candidates are `places_with_role(plan, "balcony")`. On the seed district that set includes `a-balcony`.
2. No candidate yields not applicable.
3. A candidate whose `clear_width` is `None` yields not applicable. The plan has not measured that balcony.
4. Otherwise the instance passes when every reading is at least `min_depth_m`.

`center` on this path is the place id for a single-place call (`a-balcony`). Evidence subjects are those place ids. The measured pair is `("min_depth_m", dec(shallowest))`, the same key the Topology check writes.

The signature that later unit may give the registered function, after `CheckFn` grows the union:

```python
def check(subject: Topology | dict[str, Any], center: str, params: Mapping[str, Any]) -> Evidence:
    ...
```

`isinstance(subject, Topology)` keeps today’s balcony-depth path. A dict calls `meets_clear_width` with `require_number(params, "min_depth_m", CHECK_ID)`. That branch is not in `six_foot_balcony.py` in this sketch, so `evaluate` cannot pass a plan by accident.

## Helper

`src/pattern_language/conditions/plan_clearance.py` defines `meets_clear_width(plan, place_id, minimum_m) -> bool | None`.

- `True` when `clear_width` is a number and the number is at least `minimum_m`.
- `False` when the number is below `minimum_m`.
- `None` when `clear_width` returns `None`.

The helper calls `clear_width` only. It does not call `load_spatial`, has no `CHECK_ID`, and builds no `Evidence`. `conditions/registry.py` does not import it. `conditions/measure.py` stays arithmetic on `Topology` and does not import the plan dict.

`_require_registry` still requires `set(CHECKS)` to equal the computed check ids in the catalog. That set is the ten U4 ids, including `six-foot-balcony` → `six_foot_balcony.check`.

## Non-goals

- A new `CHECKS` key, or a second function stored under `six-foot-balcony`.
- A change to `CheckFn`, `evaluate`, `pl check`, `pl step`, or the MCP tools.
- Recomputing `balcony_depth` from a plan ring. The plan path reads the named measure.
- A schema document, a Lean edit, or a catalog-gate scan of `schema/spatial-structure.schema.json`.
- Book text. Cite 167 Six-Foot Balcony by number and name.
- Retiring the IFC witnesses. Pass house and fail house remain the Topology witnesses (`min_depth_m` measured `2.000` and `1.000`).

U10 may add MCP tools. This sketch adds none.

## Acceptance

```bash
uv run pytest tests/test_checks.py tests/test_spatial_structure.py tests/test_boundaries.py
uv run pl check fixtures/pass-house.ifc --language projects/seed-house.json
uv run pl check fixtures/fail-house.ifc --language projects/seed-house.json
```

The pass command exits 0. The fail command exits 1. Both still report 167 Six-Foot Balcony under check id `six-foot-balcony`. 110 Main Entrance and 180 Window Place stay `needs_judgment` and stay out of `satisfied`.

`tests/test_spatial_structure.py` holds the plan predicate:

- `clear_width(plan, "a-balcony") == 6.0` on `demo/data/plan-model.json`.
- `meets_clear_width(plan, "a-balcony", 1.83) is True`.
- `meets_clear_width(plan, "no-such-place", 1.83) is None`.
- A plan whose only measure of `a-balcony` is depth `1.0` returns `False`.
- The helper’s module is absent from `CHECKS`. `len(CHECKS)` is 10. `CHECKS["six-foot-balcony"]` is `six_foot_balcony.check`.

`tests/test_boundaries.py` still rejects `ifcopenshell`, `bpy`, and `bonsai` outside their allowed files. The helper imports `pattern_language.spatial_structure` only.

## Exit

These commands are the witness that the sketch did not move U4. The unit that teaches `evaluate` to pass a plan uses this contract and opens a draft pull request. Agents do not merge.
