import { Effect } from "effect"
import { PlCheckFailed } from "./errors.ts"
import { BlenderHost, DriveRun, Fs, PlCli } from "./services.ts"
import { PASS_SATISFIED, SEED_SEQUENCE, type CheckReport } from "./types.ts"

function sameNumbers(
  got: ReadonlyArray<number>,
  want: ReadonlyArray<number>,
): boolean {
  return got.length === want.length && got.every((n, i) => n === want[i])
}

function assertPassReport(report: CheckReport, model: string) {
  return Effect.gen(function* () {
    if (!sameNumbers(report.satisfied, PASS_SATISFIED)) {
      return yield* new PlCheckFailed({
        exitCode: 1,
        model,
        message: `satisfied mismatch: ${JSON.stringify(report.satisfied)}`,
      })
    }
    for (const n of [110, 180] as const) {
      const row = report.instances.find((i) => i.pattern === n)
      if (!row || row.status !== "needs_judgment") {
        return yield* new PlCheckFailed({
          exitCode: 1,
          model,
          message: `pattern ${n} expected needs_judgment`,
        })
      }
      if (report.satisfied.includes(n)) {
        return yield* new PlCheckFailed({
          exitCode: 1,
          model,
          message: `pattern ${n} must stay out of satisfied`,
        })
      }
    }
  })
}

function assertFailReport(report: CheckReport, model: string) {
  return Effect.gen(function* () {
    const computed = PASS_SATISFIED
    for (const n of computed) {
      const row = report.instances.find((i) => i.pattern === n)
      if (!row || row.status !== "violated") {
        return yield* new PlCheckFailed({
          exitCode: 0,
          model,
          message: `pattern ${n} expected violated on fail house`,
        })
      }
    }
    if (report.satisfied.length !== 0) {
      return yield* new PlCheckFailed({
        exitCode: 0,
        model,
        message: `fail house satisfied must be empty`,
      })
    }
  })
}

export const headless = Effect.gen(function* () {
  const pl = yield* PlCli
  const drive = yield* DriveRun

  const seq = yield* pl.sequence("projects/seed-house.json")
  if (!sameNumbers(seq, SEED_SEQUENCE)) {
    return yield* new PlCheckFailed({
      exitCode: 1,
      model: "projects/seed-house.json",
      message: `sequence mismatch: ${JSON.stringify(seq)}`,
    })
  }

  const pass = yield* pl.check({
    model: "fixtures/pass-house.ifc",
    language: "projects/seed-house.json",
  })
  if (pass.exitCode !== 0) {
    return yield* new PlCheckFailed({
      exitCode: pass.exitCode,
      model: "fixtures/pass-house.ifc",
      message: "pass house must exit 0",
    })
  }
  yield* assertPassReport(pass.report, "fixtures/pass-house.ifc")

  const fail = yield* pl.check({
    model: "fixtures/fail-house.ifc",
    language: "projects/seed-house.json",
  })
  if (fail.exitCode !== 1) {
    return yield* new PlCheckFailed({
      exitCode: fail.exitCode,
      model: "fixtures/fail-house.ifc",
      message: "fail house must exit 1",
    })
  }
  yield* assertFailReport(fail.report, "fixtures/fail-house.ifc")

  yield* drive.check()

  return {
    ok: true as const,
    sequence: seq,
    passSatisfied: pass.report.satisfied,
  }
})

export const live = Effect.gen(function* () {
  const pl = yield* PlCli
  const drive = yield* DriveRun
  const blender = yield* BlenderHost
  const fs = yield* Fs

  yield* blender.probe()
  const { stamp } = yield* drive.write()
  yield* fs.ensureDir("exports")
  // exportIfc loads fixtures/pass-house.ifc then writes the export path
  // in one Blender process (import alone would not persist into a second process).
  yield* blender.exportIfc("exports/seed-house.ifc")

  const checked = yield* pl.check({
    model: "exports/seed-house.ifc",
    language: "projects/seed-house.json",
  })
  if (checked.exitCode !== 0) {
    return yield* new PlCheckFailed({
      exitCode: checked.exitCode,
      model: "exports/seed-house.ifc",
      message: "live export must pass pl check",
    })
  }
  yield* assertPassReport(checked.report, "exports/seed-house.ifc")

  const latest = yield* fs.latestReport("runs")
  yield* assertPassReport(latest.report, latest.path)

  return {
    ok: true as const,
    stamp,
    exportPath: "exports/seed-house.ifc",
    reportPath: latest.path,
  }
})
