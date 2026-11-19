"""Import and Lean dependency boundaries for the U0 scaffold."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

FORBIDDEN_IMPORTS = frozenset({"ifcopenshell", "bpy"})


def _python_files(root: Path) -> list[Path]:
    skipped = {".venv", ".lake", "__pycache__", ".git"}
    files: list[Path] = []
    for path in root.rglob("*.py"):
        if skipped.intersection(path.parts):
            continue
        files.append(path)
    return files


def _imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module.split(".", 1)[0])
    return found


def test_import_boundary_forbids_ifcopenshell_and_bpy(repo_root: Path) -> None:
    offenders: list[str] = []
    for path in _python_files(repo_root):
        imported = _imported_roots(path) & FORBIDDEN_IMPORTS
        offenders.extend(f"{path.relative_to(repo_root)} imports {name}" for name in sorted(imported))
    assert offenders == []


def test_importing_gate_does_not_load_forbidden_modules() -> None:
    import pattern_language.gate  # noqa: F401

    assert FORBIDDEN_IMPORTS.isdisjoint(sys.modules)


def test_lean_has_no_mathlib(repo_root: Path) -> None:
    lean = repo_root / "lean"
    texts: list[str] = []
    for path in lean.rglob("*"):
        if not path.is_file() or ".lake" in path.parts:
            continue
        texts.append(path.read_text(encoding="utf-8"))
    combined = "\n".join(texts)
    assert "Mathlib" not in combined
    assert "mathlib" not in combined
    manifest = json.loads((lean / "lake-manifest.json").read_text(encoding="utf-8"))
    assert manifest["packages"] == []


def test_u0_ships_no_records_or_schemas(repo_root: Path) -> None:
    assert list((repo_root / "schema").rglob("*.json")) == []
    assert list((repo_root / "catalog").rglob("*.json")) == []
    assert list((repo_root / "projects").rglob("*.json")) == []


def test_u0_has_no_pl_command(repo_root: Path) -> None:
    pyproject = (repo_root / "pyproject.toml").read_text(encoding="utf-8")
    assert "[project.scripts]" not in pyproject
    assert not list(repo_root.glob("scripts/pl*"))


def test_ci_workflow_covers_gate_and_lean(repo_root: Path) -> None:
    workflow = (repo_root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "uv sync --frozen" in workflow
    assert "uv run pytest" in workflow
    assert "uv run python scripts/validate_catalog.py" in workflow
    assert "leanprover/lean-action@v1" in workflow
    assert "lake-package-directory: lean" in workflow


def test_validate_catalog_cli_accepts_empty_workspace(repo_root: Path) -> None:
    completed = subprocess.run(
        [sys.executable, str(repo_root / "scripts" / "validate_catalog.py")],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert "ok: 0 records" in completed.stdout


def test_validate_catalog_cli_rejects_record_without_schema(tmp_path: Path, repo_root: Path) -> None:
    for name in ("schema", "catalog", "projects"):
        (tmp_path / name).mkdir()
    (tmp_path / "catalog" / "orphan.json").write_text("{}\n", encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, str(repo_root / "scripts" / "validate_catalog.py"), str(tmp_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 1
    assert "record without schema: catalog/orphan.json" in completed.stderr
