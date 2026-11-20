# End-to-end contract: Blender, Bonsai, and Effect

Contract for one free-tool use case. A later change adds `tools/e2e-effect` and wires `adapters/blender/export_ifc.py` until the predicates below hold. This file adds no schema, no Lean module, and no `pl` command.

Python remains the checker, the sequencer, and the run writer. The TypeScript program shells those commands.

## 1. Persona

A solo designer, with no paid CAD seat. The workstation is Blender 4.x, the Bonsai add-on, and this repository's `uv` environment so `pl` is on `PATH`. The designer opens an IFC in Blender, reads the Pattern Language sidebar, and re-exports when the model changes.

## 2. Job

One seed-house job, `projects/seed-house.json`, with `latitude_deg` 40.

1. A preserving twelve-step run along the seed sequence.
2. `pl check` on the finished model.
3. That IFC open in Blender through Bonsai, with the Pattern Language panel drawing `runs/<stamp>/report.json`.

`pl step` writes each step file and is the judge of `preserved`. Each logged step has `preserved` true.

The seed sequence, in order, with catalog names:

| Step | Number | Name | Condition |
|---|---|---|---|
| 01 | 105 | South Facing Outdoors | computed |
| 02 | 106 | Positive Outdoor Space | computed |
| 03 | 107 | Wings of Light | computed |
| 04 | 110 | Main Entrance | judged |
| 05 | 112 | Entrance Transition | computed |
| 06 | 127 | Intimacy Gradient | computed |
| 07 | 128 | Indoor Sunlight | computed |
| 08 | 130 | Entrance Room | computed |
| 09 | 159 | Light on Two Sides of Every Room | computed |
| 10 | 167 | Six-Foot Balcony | computed |
| 11 | 180 | Window Place | judged |
| 12 | 190 | Ceiling Height Variety | computed |

On the finished pass model the ten computed instances are `satisfied`. 110 Main Entrance and 180 Window Place are `needs_judgment`, with unanswered evidence, and they are absent from `satisfied`.

The panel uses `latest_report` on `runs/`. It draws `report_lines`: one line `NNN Name: status` per instance, in report order. With no stamp that contains `report.json`, the panel draws `report unavailable`.

## 3. Effect role

`tools/e2e-effect` is a thin TypeScript CLI. It depends on the `effect` package. It starts Python with `uv run` and reads the process status and stdout.

It shells `pl` and `scripts/drive_run.py`. A rewrite of the Python core is outside this contract. The package does not reimplement `load_catalog`, `CHECKS`, `sequence`, `preserving`, `read_ifc`, `write_ifc`, or `record_run`.

Entry: `tools/e2e-effect/src/cli.ts`. Two subcommands:

- `headless` runs the four commands in §7. It does not spawn Blender.
- `live` runs §8. It calls `BlenderHost`.

The program is an `Effect` that requires the four services in §5. Default layers shell out. Tests may substitute layers. On failure the CLI writes one JSON object to stderr whose `_tag` is one of §4, and exits 1. Exit 0 means the requested predicate held.

The fail-house predicate holds when `pl check` exits 1. `headless` still exits 0 when that predicate matches.

## 4. Typed error tags

Each failure is a `Data.TaggedError`. The class name is the `_tag`.

```typescript
import { Data } from "effect"

export class BlenderMissing extends Data.TaggedError("BlenderMissing")<{
  readonly message: string
}> {}

export class BonsaiMissing extends Data.TaggedError("BonsaiMissing")<{
  readonly message: string
}> {}

export class PlCheckFailed extends Data.TaggedError("PlCheckFailed")<{
  readonly exitCode: number
  readonly model: string
  readonly message: string
}> {}

export class DriveRunFailed extends Data.TaggedError("DriveRunFailed")<{
  readonly exitCode: number
  readonly message: string
}> {}

export class ExportUnwired extends Data.TaggedError("ExportUnwired")<{
  readonly message: string
}> {}

export class IfcInvalid extends Data.TaggedError("IfcInvalid")<{
  readonly path: string
  readonly message: string
}> {}
```

| Signal | Tag |
|---|---|
| `blender` is missing, or `blender --version` is not 4.x | `BlenderMissing` |
| Blender runs and `import bonsai` fails, or `load_snapshot` / Apply Next raises `BridgeError("Bonsai is not enabled")` | `BonsaiMissing` |
| A check the predicate required to pass exits 1, the parsed `satisfied` list or instance statuses disagree with the predicate, or `pl` exits 2 for a usage or schema error | `PlCheckFailed` |
| `scripts/drive_run.py` exits 1 or 2, or `--check` reports a broken run | `DriveRunFailed` |
| `export_ifc` raises `RuntimeError("Bonsai export is not wired")` | `ExportUnwired` |
| The model path is missing, or `pl check` / `pl step` exits 2 because the file is not a readable IFC (`TopologyError`) | `IfcInvalid` |

The fail-house command's exit 1 is the predicate in §7. That result is not `PlCheckFailed`.

`headless` does not call `export_ifc`, so it does not return `ExportUnwired`. `ExportUnwired` is the `live` result until §8 replaces the raise.

## 5. Effect Context.Tag services

Four services. The identifiers are the `Context.Tag` names `PlCli`, `DriveRun`, `BlenderHost`, and `Fs`.

`PlCli.check` returns the report together with exit 0 or exit 1 when stdout is a check-report. The predicate in the CLI decides whether exit 1 is expected. Exit 2 on an unreadable model is `IfcInvalid`. Any other exit 2 is `PlCheckFailed`.

```typescript
import { Context, Effect } from "effect"

export class PlCli extends Context.Tag("PlCli")<
  PlCli,
  {
    readonly sequence: (
      project: string,
    ) => Effect.Effect<ReadonlyArray<number>, PlCheckFailed>
    readonly check: (input: {
      readonly model: string
      readonly language: string
    }) => Effect.Effect<
      { readonly exitCode: 0 | 1; readonly report: CheckReport },
      PlCheckFailed | IfcInvalid
    >
    readonly step: (input: {
      readonly before: string
      readonly after: string
      readonly language: string
      readonly pattern: number
    }) => Effect.Effect<
      { readonly exitCode: 0 | 1; readonly preserved: boolean },
      PlCheckFailed | IfcInvalid
    >
  }
>() {}

export class DriveRun extends Context.Tag("DriveRun")<
  DriveRun,
  {
    readonly check: () => Effect.Effect<void, DriveRunFailed>
    readonly write: () => Effect.Effect<{ readonly stamp: string }, DriveRunFailed>
  }
>() {}

export class BlenderHost extends Context.Tag("BlenderHost")<
  BlenderHost,
  {
    readonly probe: () => Effect.Effect<
      { readonly blender: string },
      BlenderMissing | BonsaiMissing
    >
    readonly importIfc: (
      path: string,
    ) => Effect.Effect<void, BlenderMissing | BonsaiMissing | IfcInvalid>
    readonly exportIfc: (
      path: string,
    ) => Effect.Effect<
      void,
      BlenderMissing | BonsaiMissing | ExportUnwired | IfcInvalid
    >
  }
>() {}

export class Fs extends Context.Tag("Fs")<
  Fs,
  {
    readonly latestReport: (
      runsDir: string,
    ) => Effect.Effect<
      { readonly path: string; readonly report: CheckReport },
      DriveRunFailed
    >
    readonly ensureDir: (path: string) => Effect.Effect<void, IfcInvalid>
  }
>() {}
```

`CheckReport` is the JSON `pl check` already validates against `schema/check-report.schema.json`. The predicates read `satisfied` and each `instances[].pattern` / `instances[].status`.

Default layer commands, cwd the repository root:

| Service method | Command |
|---|---|
| `PlCli.sequence` | `uv run pl sequence <project>` |
| `PlCli.check` | `uv run pl check <model> --language <project>` |
| `PlCli.step` | `uv run pl step <before> <after> --language <project> --pattern <n>` |
| `DriveRun.check` | `uv run python scripts/drive_run.py --check` |
| `DriveRun.write` | `uv run python scripts/drive_run.py` |
| `BlenderHost.probe` | `blender --version`, then a background Blender run that imports `bpy` and `bonsai` |
| `BlenderHost.importIfc` | Blender calls `load_snapshot` (`bpy.ops.bim.load_project`) |
| `BlenderHost.exportIfc` | Blender calls `export_ifc` |
| `Fs.latestReport` | The lexicographically latest `runs/<stamp>/report.json`, the same rule as `latest_report` |
| `Fs.ensureDir` | Create `exports/` before a live export |

`DriveRun.check` succeeds on exit 0 and stdout `fresh: 12 steps`. `DriveRun.write` succeeds on exit 0 and stdout `wrote: runs/<stamp>`, with `<stamp>` matching `^[0-9]{8}T[0-9]{6}Z$`.

`Fs` does not parse IFC. A missing report is `DriveRunFailed` with message `no report`.

## 6. Success artifacts

| Path | Who writes it |
|---|---|
| `runs/<YYYYMMDDTHHMMSSZ>/report.json` | `DriveRun.write` and the Blender session. It is `pl check` on `model-12.ifc`. |
| `exports/seed-house.ifc` | The live export only. Optional for headless acceptance. |

The stamp directory also holds `model-00.ifc` through `model-12.ifc` and `step-01.json` through `step-12.json`. The panel's ledger is that directory. Headless `--check` uses a temporary directory and leaves `runs/` unchanged.

`exports/seed-house.ifc` is present after a successful `live` run. `headless` does not create it.

## 7. Headless acceptance

From the repository root. These commands do not start Blender. CI already runs the pass check, the sequence, and `drive_run.py --check`. CI does not install Blender or Bonsai, and it does not run `live`.

```bash
uv run pl sequence projects/seed-house.json
uv run pl check fixtures/pass-house.ifc --language projects/seed-house.json
uv run pl check fixtures/fail-house.ifc --language projects/seed-house.json
uv run python scripts/drive_run.py --check
```

Predicates:

1. **Sequence.** Exit 0. Stdout is this JSON array, indent 2, with one trailing newline:

   ```json
   [
     105,
     106,
     107,
     110,
     112,
     127,
     128,
     130,
     159,
     167,
     180,
     190
   ]
   ```

2. **Pass house.** Exit 0. `satisfied` is exactly `[105, 106, 107, 112, 127, 128, 130, 159, 167, 190]`. Those ten instances are `satisfied`. 110 Main Entrance and 180 Window Place are `needs_judgment` and are absent from `satisfied`.

3. **Fail house.** Exit 1. The same ten computed instances are `violated`. 110 Main Entrance and 180 Window Place are `needs_judgment` and are absent from `satisfied`. `headless` treats this exit 1 as a matched predicate.

4. **`drive_run.py --check`.** Exit 0. Stdout is `fresh: 12 steps`. No stamp directory is left under `runs/`. In the temporary run, `step-01.json` through `step-12.json` each have `preserved` true, `report.json` matches the pass `satisfied` list, 110 Main Entrance and 180 Window Place are `needs_judgment` and stay out of `satisfied`, and `model-12.ifc` reads back equal to `fixtures/pass-house.ifc` as topology JSON (`to_json(read_ifc(...))`).

`headless` exits 0 only when all four predicates hold.

## 8. Live path

Gated the same way as `adapters/blender/README.md`. A person runs it on a machine with Blender 4.x, Bonsai enabled, and this repository's `uv` environment. CI does not launch Blender.

Install the add-on from `adapters/blender` and enable Pattern Language. When the folder was copied out of the tree, set the add-on preference Repository to this repository root. The panel reads `runs/` under that root.

`adapters/blender/export_ifc.py` is the export slot. Today the function imports `bpy` and raises `RuntimeError("Bonsai export is not wired")`. The wired function still imports `bpy` inside the function, calls the Bonsai save operator through `bpy`, and writes the current scene to `path`. It does not `import bonsai`. `adapters/blender/bridge.py` remains the only module that imports `bonsai`. Until that operator call is the body, `BlenderHost.exportIfc` fails with `ExportUnwired`.

`live` then does four steps:

1. `uv run python scripts/drive_run.py` writes `runs/<stamp>/`. The panel draws one `report_lines` row per instance from that `report.json`.
2. Import `fixtures/pass-house.ifc` through `load_snapshot` (`bpy.ops.bim.load_project`). When Bonsai cannot be imported, `BridgeError("Bonsai is not enabled")` is raised and no step is written. The Effect tag is `BonsaiMissing`.
3. `export_ifc` writes `exports/seed-house.ifc`.
4. `uv run pl check exports/seed-house.ifc --language projects/seed-house.json` exits 0 and matches the pass predicate in §7.

`BlenderHost.probe` runs before those steps. A failed probe is `BlenderMissing` or `BonsaiMissing`, and `live` does not write `exports/seed-house.ifc`.

The `Session` table in `bridge.py` stays the live transitions. Apply Next stays `apply_next`: it records the next seed step through `record_step` and asks Bonsai to open the new IFC. The export slot writes the scene the designer is looking at.

## 9. Non-goals

- Revit, or any other paid CAD.
- A rewrite of `conditions/`, `checker.py`, `sequence.py`, `step.py`, or the Lean library.
- Demo SVG or plan-symbology polish.
- Marketing pages or pitch copy.

Also out of this contract: a new `pl` subcommand, a new schema document, a new MCP tool, a Mathlib dependency, and launching Blender from CI. `bpy` stays under `adapters/blender/`. `bonsai` stays in `adapters/blender/bridge.py`. `ifcopenshell` stays inside `read_ifc` and `write_ifc` in `topology.py`. The TypeScript package does not import those modules.

## 10. Citation

Cite pattern numbers and names only. Do not copy book text into this contract, the CLI, the catalog, or the add-on.

## 11. Evidence (executed)

Recorded on the cloud agent host after implementing `tools/e2e-effect` and wiring `export_ifc`.

### Headless

```bash
cd tools/e2e-effect && bun run e2e:headless
```

Exit 0. Stdout included `ok: true`, seed sequence `105…190`, and pass `satisfied` `[105, 106, 107, 112, 127, 128, 130, 159, 167, 190]`.

Direct Python witnesses also held: `pl sequence`, pass check exit 0, fail check exit 1, `drive_run.py --check` → `fresh: 12 steps`, and a written run under `runs/` with all twelve steps `preserved` true.

### Live

Installed Blender 4.2.9 LTS (portable) and Bonsai `0.9.1-alpha` (py311 linux zip + wheels). Wired `adapters/blender/export_ifc.py` to `bpy.ops.bim.save_project(..., should_save_as=True)`.

```bash
cd tools/e2e-effect && bun run e2e:live
```

Exit 0. Example result:

```json
{
  "ok": true,
  "stamp": "20261119T225612Z",
  "exportPath": "exports/seed-house.ifc",
  "reportPath": "/agent/repos/pl/runs/20261119T225612Z/report.json"
}
```

`pl check exports/seed-house.ifc --language projects/seed-house.json` exit 0 with the same pass `satisfied` list; 110 Main Entrance and 180 Window Place stay `needs_judgment`.
