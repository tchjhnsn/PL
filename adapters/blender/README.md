# Blender live path

This path is gated. CI does not install Blender or Bonsai, and it does not import the add-on. A person runs it on a machine that has all three of the following:

- Blender 4.x
- the Bonsai add-on enabled
- this repository's `uv` environment, so `pl` is on `PATH`

## Install

Install the add-on from the `adapters/blender` folder and enable Pattern Language. Enabling it runs `register` and shows the Pattern Language tab in the 3D View sidebar.

Set the add-on preference Repository to this repository root when the folder was copied out of the tree. The panel reads `runs/` under that root.

Until a stamp directory contains `report.json`, the panel draws `report unavailable`. After `drive_run.py` or Apply Next writes that file, the panel draws one line per instance from `report_lines`.

`export_ifc` calls `bpy.ops.bim.save_project` (save-as). It raises `RuntimeError("Bonsai export is not wired")` when the `bim` operator is missing. Apply Next raises `BridgeError("Bonsai is not enabled")` when Bonsai cannot be imported, and it writes no step in that case.

End-to-end Effect CLI (headless + live): `docs/design/E2E-BONSAI-EFFECT.md` and `tools/e2e-effect/`.

## Commands

From the repository root, the recorded run and the three commands the live session calls:

```bash
uv run python scripts/drive_run.py
uv run pl sequence projects/seed-house.json
uv run pl check path/to/export.ifc --language projects/seed-house.json
uv run pl step path/to/previous.ifc path/to/export.ifc --language projects/seed-house.json --pattern 105
```

`drive_run.py` writes `runs/<YYYYMMDDTHHMMSSZ>/` with `model-00.ifc` through `model-12.ifc`, twelve step files, and `report.json`. That is the ledger the panel reads. The merge check is `uv run python scripts/drive_run.py --check`. It uses a temporary directory and does not need Blender.

Once a Bonsai export exists, the scene becomes an IFC, `pl check` is the check, and the report is what the panel shows. The next edit is a new export. This unit stops before that Bonsai call.
