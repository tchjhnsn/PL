"""Sidebar panel. Draws the newest check-report, or a fixed fallback line."""

from __future__ import annotations

import json
from pathlib import Path

import bpy


class PL_PT_report(bpy.types.Panel):
    """Newest check-report in the 3D View sidebar."""

    bl_idname = "PL_PT_report"
    bl_label = "Pattern Language"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Pattern Language"

    def draw(self, context: bpy.types.Context) -> None:
        column = self.layout.column(align=True)
        lines = _report_lines(context)
        if not lines:
            column.label(text="report unavailable")
        else:
            for line in lines:
                column.label(text=line)
        column.operator("pattern_language.apply_next", text="Apply Next")


class PL_OT_apply_next(bpy.types.Operator):
    """Write the next snapshot and ask Bonsai to open it."""

    bl_idname = "pattern_language.apply_next"
    bl_label = "Apply Next"

    def execute(self, context: bpy.types.Context) -> set[str]:
        repo = _repo(context)
        if repo is None:
            self.report({"WARNING"}, "report unavailable")
            return {"CANCELLED"}
        try:
            from .bridge import apply_next

            apply_next(repo / "runs", root=repo)
        except Exception as exc:
            self.report({"WARNING"}, str(exc) or "report unavailable")
            return {"CANCELLED"}
        return {"FINISHED"}


def _report_lines(context: bpy.types.Context) -> tuple[str, ...] | None:
    try:
        from pattern_language.catalog import load_catalog
        from pattern_language.runs import latest_report, report_lines
    except Exception:
        return None
    repo = _repo(context)
    if repo is None:
        return None
    try:
        report_path = latest_report(repo / "runs")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        catalog = load_catalog(repo)
        names = {pattern.number: pattern.name for pattern in catalog.patterns}
        return report_lines(report, names)
    except Exception:
        return None


def _repo(context: bpy.types.Context) -> Path | None:
    raw = ""
    try:
        addon = context.preferences.addons.get(__package__ or "")
        if addon is not None:
            raw = str(getattr(addon.preferences, "repo", "") or "")
    except Exception:
        raw = ""
    if raw:
        candidate = Path(bpy.path.abspath(raw))
        if (candidate / "projects" / "seed-house.json").is_file():
            return candidate
    candidate = Path(__file__).resolve().parents[2]
    if (candidate / "projects" / "seed-house.json").is_file():
        return candidate
    return None
