"""IFC export slot. Calls Bonsai's save operator through ``bpy`` only."""

from __future__ import annotations

from pathlib import Path


def export_ifc(path: str) -> None:
    """Write the current scene to ``path`` via ``bpy.ops.bim.save_project``.

    Does not ``import bonsai`` — ``bridge.py`` remains the only bonsai importer.
    Raises ``RuntimeError("Bonsai export is not wired")`` when the bim operator
    is absent (Bonsai add-on not enabled).
    """
    import bpy

    target = Path(path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    bim = getattr(getattr(bpy, "ops", None), "bim", None)
    save_project = getattr(bim, "save_project", None)
    if save_project is None:
        raise RuntimeError("Bonsai export is not wired")

    result = save_project(filepath=str(target), should_save_as=True)
    if result == {"CANCELLED"}:
        raise RuntimeError("Bonsai export is not wired")
