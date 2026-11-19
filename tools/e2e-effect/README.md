# pl e2e-effect

Thin [Effect](https://effect.website) TypeScript CLI that shells the Pattern Language Python tools.

## Install

```bash
# from repo root
export PATH="$HOME/.local/bin:$HOME/.bun/bin:$PATH"
cd tools/e2e-effect
bun install
```

## Commands

```bash
bun run e2e:headless   # pl sequence, pass/fail check, drive_run --check
bun run e2e:live       # requires Blender 4.x + Bonsai; import/export + pl check
```

`headless` exits 0 when all predicates in `docs/design/E2E-BONSAI-EFFECT.md` §7 hold. Failures print one JSON object on stderr with `_tag` set to a typed error.

## Non-goals

Does not reimplement `pl`, Lean, or conditions. Does not launch Blender from CI.
