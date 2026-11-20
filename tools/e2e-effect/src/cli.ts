#!/usr/bin/env bun
import { Effect } from "effect"
import type { E2EError } from "./errors.ts"
import { AppLive } from "./layers.ts"
import { headless, live } from "./pipeline.ts"

const mode = process.argv[2] ?? "headless"

function printError(err: E2EError): void {
  console.error(JSON.stringify({ _tag: err._tag, ...err }, null, 2))
}

const program =
  mode === "live"
    ? live
    : mode === "headless"
      ? headless
      : Effect.dieMessage(`usage: bun run src/cli.ts [headless|live]`)

Effect.runPromise(
  program.pipe(
    Effect.provide(AppLive),
    Effect.tap((result) =>
      Effect.sync(() => {
        console.log(JSON.stringify(result, null, 2))
      }),
    ),
    Effect.catchAll((err) =>
      Effect.sync(() => {
        printError(err as E2EError)
        process.exitCode = 1
      }),
    ),
  ),
)
