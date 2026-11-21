import { Context, Effect } from "effect"
import type {
  BonsaiMissing,
  BlenderMissing,
  DriveRunFailed,
  ExportUnwired,
  IfcInvalid,
  PlCheckFailed,
} from "./errors.ts"
import type { CheckReport } from "./types.ts"

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
