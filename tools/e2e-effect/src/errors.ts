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

export type E2EError =
  | BlenderMissing
  | BonsaiMissing
  | PlCheckFailed
  | DriveRunFailed
  | ExportUnwired
  | IfcInvalid
