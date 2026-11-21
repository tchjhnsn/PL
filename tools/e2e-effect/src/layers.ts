import { Effect, Layer } from "effect"
import { spawnSync } from "node:child_process"
import {
  existsSync,
  mkdirSync,
  readdirSync,
  readFileSync,
  mkdtempSync,
  writeFileSync,
  rmSync,
} from "node:fs"
import { join, resolve } from "node:path"
import { tmpdir } from "node:os"
import {
  BlenderMissing,
  BonsaiMissing,
  DriveRunFailed,
  ExportUnwired,
  IfcInvalid,
  PlCheckFailed,
} from "./errors.ts"
import { BlenderHost, DriveRun, Fs, PlCli } from "./services.ts"
import type { CheckReport } from "./types.ts"

const ROOT = resolve(import.meta.dir, "../../..")

function runUv(args: string[]): {
  exitCode: number
  stdout: string
  stderr: string
} {
  const result = spawnSync("uv", ["run", ...args], {
    cwd: ROOT,
    encoding: "utf8",
    env: process.env,
  })
  return {
    exitCode: result.status ?? 2,
    stdout: result.stdout ?? "",
    stderr: result.stderr ?? "",
  }
}

function parseReport(stdout: string): CheckReport {
  return JSON.parse(stdout) as CheckReport
}

export const PlCliLive = Layer.succeed(PlCli, {
  sequence: (project) =>
    Effect.gen(function* () {
      const { exitCode, stdout, stderr } = runUv(["pl", "sequence", project])
      if (exitCode !== 0) {
        return yield* new PlCheckFailed({
          exitCode,
          model: project,
          message: stderr || stdout || "pl sequence failed",
        })
      }
      return JSON.parse(stdout) as ReadonlyArray<number>
    }),

  check: ({ model, language }) =>
    Effect.gen(function* () {
      const { exitCode, stdout, stderr } = runUv([
        "pl",
        "check",
        model,
        "--language",
        language,
      ])
      if (exitCode === 2) {
        const msg = stderr || stdout
        if (/TopologyError|not a readable|IFC|ifc/i.test(msg)) {
          return yield* new IfcInvalid({ path: model, message: msg })
        }
        return yield* new PlCheckFailed({
          exitCode,
          model,
          message: msg || "pl check usage/schema error",
        })
      }
      if (exitCode !== 0 && exitCode !== 1) {
        return yield* new PlCheckFailed({
          exitCode,
          model,
          message: stderr || stdout || "pl check unexpected exit",
        })
      }
      try {
        const report = parseReport(stdout)
        return { exitCode: exitCode as 0 | 1, report }
      } catch (err) {
        return yield* new PlCheckFailed({
          exitCode,
          model,
          message: `unreadable check report: ${String(err)}`,
        })
      }
    }),

  step: ({ before, after, language, pattern }) =>
    Effect.gen(function* () {
      const { exitCode, stdout, stderr } = runUv([
        "pl",
        "step",
        before,
        after,
        "--language",
        language,
        "--pattern",
        String(pattern),
      ])
      if (exitCode === 2) {
        return yield* new IfcInvalid({
          path: after,
          message: stderr || stdout || "pl step failed",
        })
      }
      if (exitCode !== 0 && exitCode !== 1) {
        return yield* new PlCheckFailed({
          exitCode,
          model: after,
          message: stderr || stdout || "pl step unexpected exit",
        })
      }
      let preserved = false
      try {
        preserved = Boolean((JSON.parse(stdout) as { preserved?: boolean }).preserved)
      } catch {
        preserved = exitCode === 0
      }
      return { exitCode: exitCode as 0 | 1, preserved }
    }),
})

export const DriveRunLive = Layer.succeed(DriveRun, {
  check: () =>
    Effect.gen(function* () {
      const { exitCode, stdout, stderr } = runUv([
        "python",
        "scripts/drive_run.py",
        "--check",
      ])
      if (exitCode !== 0 || !stdout.includes("fresh: 12 steps")) {
        return yield* new DriveRunFailed({
          exitCode,
          message: stderr || stdout || "drive_run --check failed",
        })
      }
    }),

  write: () =>
    Effect.gen(function* () {
      const { exitCode, stdout, stderr } = runUv(["python", "scripts/drive_run.py"])
      const match = /wrote:\s*runs\/([0-9]{8}T[0-9]{6}Z)/.exec(stdout)
      if (exitCode !== 0 || match === null) {
        return yield* new DriveRunFailed({
          exitCode,
          message: stderr || stdout || "drive_run write failed",
        })
      }
      return { stamp: match[1]! }
    }),
})

function findBlender(): string | null {
  const candidates = ["blender", "blender-4.2", "blender-4.5"]
  for (const name of candidates) {
    const which = spawnSync("which", [name], { encoding: "utf8" })
    if (which.status === 0 && which.stdout.trim()) return which.stdout.trim()
  }
  return null
}

export const BlenderHostLive = Layer.succeed(BlenderHost, {
  probe: () =>
    Effect.gen(function* () {
      const blender = findBlender()
      if (!blender) {
        return yield* new BlenderMissing({ message: "blender not on PATH" })
      }
      const ver = spawnSync(blender, ["--version"], { encoding: "utf8" })
      const text = `${ver.stdout ?? ""}${ver.stderr ?? ""}`
      if (ver.status !== 0 || !/Blender 4\./.test(text)) {
        return yield* new BlenderMissing({
          message: `expected Blender 4.x, got: ${text.trim() || "unknown"}`,
        })
      }
      const probeScript = `
import sys
try:
    import bonsai
except ImportError as exc:
    print("BONSAI_MISSING:" + str(exc))
    sys.exit(3)
print("ok")
`
      const probe = spawnSync(
        blender,
        ["--background", "--python-expr", probeScript],
        { encoding: "utf8", env: process.env },
      )
      const out = `${probe.stdout ?? ""}${probe.stderr ?? ""}`
      if (probe.status === 3 || out.includes("BONSAI_MISSING")) {
        return yield* new BonsaiMissing({
          message: out.trim() || "import bonsai failed",
        })
      }
      if (probe.status !== 0) {
        return yield* new BonsaiMissing({
          message: out.trim() || "blender probe failed",
        })
      }
      return { blender }
    }),

  importIfc: (path) =>
    Effect.gen(function* () {
      const blender = findBlender()
      if (!blender) {
        return yield* new BlenderMissing({ message: "blender not on PATH" })
      }
      const absIn = resolve(ROOT, path)
      if (!existsSync(absIn)) {
        return yield* new IfcInvalid({ path, message: "file missing" })
      }
      const dir = mkdtempSync(join(tmpdir(), "pl-e2e-"))
      const scriptPath = join(dir, "import_ifc.py")
      writeFileSync(
        scriptPath,
        `
import addon_utils
addon_utils.enable("bonsai", default_set=True, persistent=True)
import sys
from pathlib import Path
sys.path.insert(0, ${JSON.stringify(join(ROOT, "adapters"))})
from blender.bridge import BridgeError, load_snapshot
try:
    load_snapshot(Path(${JSON.stringify(absIn)}))
except BridgeError as exc:
    print("BRIDGE:" + str(exc))
    raise SystemExit(3)
except Exception as exc:
    print("IMPORT:" + str(exc))
    raise SystemExit(2)
print("imported")
`,
        "utf8",
      )
      const result = spawnSync(blender, ["--background", "--python", scriptPath], {
        encoding: "utf8",
        cwd: ROOT,
        env: process.env,
      })
      rmSync(dir, { recursive: true, force: true })
      const out = `${result.stdout ?? ""}${result.stderr ?? ""}`
      if (result.status === 3 || out.includes("Bonsai is not enabled")) {
        return yield* new BonsaiMissing({ message: out.trim() })
      }
      if (result.status !== 0) {
        return yield* new IfcInvalid({ path, message: out.trim() || "import failed" })
      }
    }),

  exportIfc: (path) =>
    Effect.gen(function* () {
      const blender = findBlender()
      if (!blender) {
        return yield* new BlenderMissing({ message: "blender not on PATH" })
      }
      const abs = resolve(ROOT, path)
      const dir = mkdtempSync(join(tmpdir(), "pl-e2e-"))
      const scriptPath = join(dir, "export_ifc.py")
      // Live export assumes a project is already loaded in this Blender invocation.
      // Combined import+export script for a single Blender process:
      writeFileSync(
        scriptPath,
        `
import addon_utils
addon_utils.enable("bonsai", default_set=True, persistent=True)
import sys
from pathlib import Path
sys.path.insert(0, ${JSON.stringify(join(ROOT, "adapters"))})
from blender.bridge import BridgeError, load_snapshot
from blender.export_ifc import export_ifc
src = Path(${JSON.stringify(resolve(ROOT, "fixtures/pass-house.ifc"))})
dst = Path(${JSON.stringify(abs)})
try:
    load_snapshot(src)
    export_ifc(str(dst))
except BridgeError as exc:
    print("BRIDGE:" + str(exc))
    raise SystemExit(3)
except RuntimeError as exc:
    if "not wired" in str(exc):
        print("UNWIRED:" + str(exc))
        raise SystemExit(4)
    print("EXPORT:" + str(exc))
    raise SystemExit(2)
except Exception as exc:
    print("EXPORT:" + str(exc))
    raise SystemExit(2)
print("exported")
`,
        "utf8",
      )
      const result = spawnSync(blender, ["--background", "--python", scriptPath], {
        encoding: "utf8",
        cwd: ROOT,
        env: process.env,
      })
      rmSync(dir, { recursive: true, force: true })
      const out = `${result.stdout ?? ""}${result.stderr ?? ""}`
      if (result.status === 4 || out.includes("UNWIRED:")) {
        return yield* new ExportUnwired({
          message: out.trim() || "Bonsai export is not wired",
        })
      }
      if (result.status === 3 || out.includes("Bonsai is not enabled")) {
        return yield* new BonsaiMissing({ message: out.trim() })
      }
      if (result.status !== 0) {
        return yield* new IfcInvalid({ path: abs, message: out.trim() || "export failed" })
      }
    }),
})

export const FsLive = Layer.succeed(Fs, {
  latestReport: (runsDir) =>
    Effect.gen(function* () {
      const abs = resolve(ROOT, runsDir)
      if (!existsSync(abs)) {
        return yield* new DriveRunFailed({
          exitCode: 1,
          message: "no report",
        })
      }
      const stamps = readdirSync(abs)
        .filter((name) => /^[0-9]{8}T[0-9]{6}Z$/.test(name))
        .sort()
      for (let i = stamps.length - 1; i >= 0; i--) {
        const reportPath = join(abs, stamps[i]!, "report.json")
        if (existsSync(reportPath)) {
          const report = JSON.parse(readFileSync(reportPath, "utf8")) as CheckReport
          return { path: reportPath, report }
        }
      }
      return yield* new DriveRunFailed({ exitCode: 1, message: "no report" })
    }),

  ensureDir: (path) =>
    Effect.sync(() => {
      mkdirSync(resolve(ROOT, path), { recursive: true })
    }),
})

export const AppLive = Layer.mergeAll(PlCliLive, DriveRunLive, BlenderHostLive, FsLive)
