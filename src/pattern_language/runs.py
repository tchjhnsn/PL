"""Record one seed-house run as prefixes, step files, and a check-report.

``pl step`` writes each step file. ``pl check`` writes ``report.json``.
This module does not decide ``preserved``.
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pattern_language.catalog import load_catalog
from pattern_language.conditions.evidence import CheckError
from pattern_language.parameters import load_project
from pattern_language.sequence import sequence
from pattern_language.topology import prefix, write_ifc

SEED_SEQUENCE = (105, 106, 107, 110, 112, 127, 128, 130, 159, 167, 180, 190)

# One row per model index. Each row is the pieces added to the previous model.
# 00 street; then 105, 106, 107, 110, 112, 127, 128, 130, 159, 167, 180, 190.
_GROWTH: tuple[tuple[frozenset[str], frozenset[str]], ...] = (
    (frozenset({"street"}), frozenset()),
    (frozenset({"court", "hall"}), frozenset()),
    (frozenset(), frozenset({"approach-door"})),
    (frozenset(), frozenset({"hall-south"})),
    (frozenset(), frozenset()),
    (frozenset(), frozenset({"main-door"})),
    (frozenset({"living", "bedroom"}), frozenset({"hall-living", "living-bedroom"})),
    (frozenset(), frozenset({"living-south"})),
    (frozenset(), frozenset({"living-east"})),
    (frozenset(), frozenset({"hall-west", "bedroom-north", "bedroom-west"})),
    (frozenset({"balcony"}), frozenset({"bedroom-balcony"})),
    (frozenset(), frozenset()),
    (frozenset(), frozenset()),
)

_STAMP = re.compile(r"^[0-9]{8}T[0-9]{6}Z$")


class RunError(Exception):
    """The seed sequence was not the one this run writes, a step exited 1,
    or the final check exited 1. The caller deletes the run directory.
    """


def _snapshots() -> tuple[tuple[frozenset[str], frozenset[str]], ...]:
    spaces: set[str] = set()
    openings: set[str] = set()
    rows: list[tuple[frozenset[str], frozenset[str]]] = []
    for add_spaces, add_openings in _GROWTH:
        spaces.update(add_spaces)
        openings.update(add_openings)
        rows.append((frozenset(spaces), frozenset(openings)))
    return tuple(rows)


_SNAPSHOTS = _snapshots()


def record_run(directory: Path, *, root: Path) -> Path:
    """Write model-00.ifc through model-12.ifc, twelve step files, and report.json.

    directory is the run directory, created by the caller.
    root is the repository root, passed as pl --root.
    The subprocess cwd is directory.
    Raise RunError("sequence is not the seed run") before any IFC write
    when sequence(catalog, seed project) is not the twelve snapshot keys
    in that order.
    Raise RunError("preserved is false: N") when pl step exits 1.
    Raise RunError("check failed") when pl check exits 1.
    Raise CheckError and TopologyError unchanged when a model cannot be written.
    """
    catalog = load_catalog(root)
    project = load_project(
        root / "projects" / "seed-house.json",
        schema_path=root / "schema" / "projects.schema.json",
    )
    if sequence(catalog, project) != SEED_SEQUENCE:
        raise RunError("sequence is not the seed run")
    _write_model(directory, 0)
    for pattern in SEED_SEQUENCE:
        record_step(directory, root=root, pattern=pattern)
    _record_report(directory, root=root)
    return directory


def record_step(directory: Path, *, root: Path, pattern: int) -> Path:
    """Write the next model and one step file for a run that already has model-00.ifc.

    pattern is the next unused number in the seed sequence.
    Raise RunError when that number is not the next snapshot.
    The step file is the pl step stdout, written with --out.
    Exit 1 raises RunError and leaves the previous step files in place
    for the caller to delete.
    """
    completed = _completed_steps(directory)
    if completed >= len(SEED_SEQUENCE) or pattern != SEED_SEQUENCE[completed]:
        raise RunError(f"pattern is not the next snapshot: {pattern}")
    index = completed + 1
    _write_model(directory, index)
    before = f"model-{index - 1:02d}.ifc"
    after = f"model-{index:02d}.ifc"
    out_name = f"step-{index:02d}.json"
    language = str(root / "projects" / "seed-house.json")
    completed_proc = _cli(
        directory,
        [
            "step",
            before,
            after,
            "--language",
            language,
            "--pattern",
            str(pattern),
            "--out",
            out_name,
            "--root",
            str(root),
        ],
    )
    _require_ok(completed_proc, fail=f"preserved is false: {pattern}")
    return directory / out_name


def latest_report(runs: Path) -> Path:
    """Path of report.json in the lexicographically latest stamp directory.

    Raise CheckError("no report") when no child matches the stamp and
    contains report.json.
    """
    found: list[Path] = []
    if runs.is_dir():
        for child in runs.iterdir():
            if not child.is_dir() or _STAMP.fullmatch(child.name) is None:
                continue
            report = child / "report.json"
            if report.is_file():
                found.append(report)
    if not found:
        raise CheckError("no report")
    return max(found, key=lambda path: path.parent.name)


def report_lines(report: Mapping[str, Any], names: Mapping[int, str]) -> tuple[str, ...]:
    """One line per instance: ``NNN Name: status``.

    Order is the order of report["instances"].
    """
    lines: list[str] = []
    for instance in report["instances"]:
        number = int(instance["pattern"])
        lines.append(f"{number} {names[number]}: {instance['status']}")
    return tuple(lines)


def _write_model(directory: Path, index: int) -> None:
    spaces, openings = _SNAPSHOTS[index]
    write_ifc(prefix(spaces, openings), directory / f"model-{index:02d}.ifc")


def _record_report(directory: Path, *, root: Path) -> Path:
    language = str(root / "projects" / "seed-house.json")
    completed_proc = _cli(
        directory,
        [
            "check",
            "model-12.ifc",
            "--language",
            language,
            "--out",
            "report.json",
            "--root",
            str(root),
        ],
    )
    _require_ok(completed_proc, fail="check failed")
    return directory / "report.json"


def _completed_steps(directory: Path) -> int:
    count = 0
    while count < len(SEED_SEQUENCE) and (directory / f"step-{count + 1:02d}.json").is_file():
        count += 1
    return count


def _cli(directory: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "pattern_language.cli", *args],
        cwd=directory,
        capture_output=True,
        text=True,
        check=False,
    )


def _require_ok(completed: subprocess.CompletedProcess[str], *, fail: str) -> None:
    if completed.returncode == 1:
        raise RunError(fail)
    if completed.returncode != 0:
        message = completed.stderr.strip() or fail
        raise CheckError(message)
