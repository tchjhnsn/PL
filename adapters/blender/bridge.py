"""Session transitions for the live Blender path, and the Bonsai load stub.

``Session`` does not import ``bpy``. ``bonsai`` is imported only when a live
call needs it.
"""

from __future__ import annotations

import re
from pathlib import Path

_STAMP = re.compile(r"^[0-9]{8}T[0-9]{6}Z$")

TRANSITIONS: dict[tuple[str, str], str] = {
    ("Disconnected", "connect"): "Connected",
    ("Connected", "request_check"): "Exporting",
    ("Exporting", "exported"): "Checking",
    ("Exporting", "fail"): "Error",
    ("Checking", "reported"): "ShowingReport",
    ("ShowingReport", "edit"): "Editing",
    ("Editing", "done"): "Exporting",
    ("ShowingReport", "idle"): "Connected",
    ("Error", "shown"): "Connected",
    ("Connected", "disconnect"): "Disconnected",
}


class BridgeError(Exception):
    """Bonsai is not enabled, or there is no open run to continue."""


class Session:
    """§2.5 state names. ``act`` writes no file and opens no socket."""

    state: str = "Disconnected"

    def act(self, event: str) -> str:
        """Return the next state. Raise KeyError on a pair the table omits."""
        try:
            nxt = TRANSITIONS[(self.state, event)]
        except KeyError:
            raise KeyError((self.state, event)) from None
        self.state = nxt
        return self.state


def load_snapshot(path: Path) -> None:
    """Open this IFC in the current Blender file through Bonsai.

    Raise BridgeError("Bonsai is not enabled") when the Bonsai import
    is absent. Write no step in that case.
    """
    bonsai = _require_bonsai()
    import bpy

    loader = getattr(getattr(bpy, "ops", None), "bim", None)
    load_project = getattr(loader, "load_project", None)
    if load_project is None or bonsai is None:
        raise BridgeError("Bonsai load is not wired")
    load_project(filepath=str(path))


def apply_next(runs: Path, *, root: Path) -> Path:
    """Record the next seed step and ask Bonsai to open the new IFC.

    When the Bonsai import is absent, raise BridgeError before a step is written.
    After step 12, run pl check into report.json.
    """
    _require_bonsai()
    directory = _open_run(runs)
    from pattern_language.runs import SEED_SEQUENCE, _record_report, record_step

    completed = _completed_steps(directory)
    if completed >= len(SEED_SEQUENCE):
        raise BridgeError("run is complete")
    if not (directory / "model-00.ifc").is_file():
        raise BridgeError("model-00.ifc is missing")
    pattern = SEED_SEQUENCE[completed]
    step_path = record_step(directory, root=root, pattern=pattern)
    load_snapshot(directory / f"model-{completed + 1:02d}.ifc")
    if completed + 1 == len(SEED_SEQUENCE):
        _record_report(directory, root=root)
    return step_path


def _require_bonsai() -> object:
    try:
        import bonsai
    except ImportError as exc:
        raise BridgeError("Bonsai is not enabled") from exc
    return bonsai


def _open_run(runs: Path) -> Path:
    found: list[Path] = []
    if runs.is_dir():
        for child in runs.iterdir():
            if not child.is_dir() or _STAMP.fullmatch(child.name) is None:
                continue
            if (child / "report.json").is_file():
                continue
            found.append(child)
    if not found:
        raise BridgeError("no open run")
    return max(found, key=lambda path: path.name)


def _completed_steps(directory: Path) -> int:
    from pattern_language.runs import SEED_SEQUENCE

    count = 0
    while count < len(SEED_SEQUENCE) and (directory / f"step-{count + 1:02d}.json").is_file():
        count += 1
    return count
