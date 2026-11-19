"""IFC export slot. The Bonsai operator is chosen when the live path is wired."""

from __future__ import annotations


def export_ifc(path: str) -> None:
    """Write the current scene to ``path``. This unit does not call Bonsai."""
    import bpy

    raise RuntimeError("Bonsai export is not wired")
