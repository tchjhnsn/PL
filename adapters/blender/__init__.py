"""Pattern Language add-on. ``bpy`` is imported inside register and unregister."""

from __future__ import annotations

bl_info = {
    "name": "Pattern Language",
    "author": "Pattern Language",
    "version": (0, 0, 1),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Pattern Language",
    "description": "Show the newest pattern-language check report.",
    "category": "Scene",
}

_CLASSES: list[object] = []


def register() -> None:
    """Register the panel, Apply Next, and the repository preference."""
    import bpy

    from . import panel

    class PL_Preferences(bpy.types.AddonPreferences):
        bl_idname = __package__

        repo: bpy.props.StringProperty(
            name="Repository",
            subtype="DIR_PATH",
            description="Repository root that contains runs/",
        )

    _CLASSES.clear()
    _CLASSES.extend([PL_Preferences, panel.PL_PT_report, panel.PL_OT_apply_next])
    for cls in _CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    """Unregister the classes register() added."""
    import bpy

    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
    _CLASSES.clear()
