export type CheckInstance = {
  readonly pattern: number
  readonly status: string
}

export type CheckReport = {
  readonly satisfied: ReadonlyArray<number>
  readonly instances: ReadonlyArray<CheckInstance>
}

export const PASS_SATISFIED = [
  105, 106, 107, 112, 127, 128, 130, 159, 167, 190,
] as const

export const SEED_SEQUENCE = [
  105, 106, 107, 110, 112, 127, 128, 130, 159, 167, 180, 190,
] as const
