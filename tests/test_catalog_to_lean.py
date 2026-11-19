"""The committed building instantiation matches the catalog render."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

from pattern_language.catalog import load_catalog


def _render(repo_root: Path):
    path = repo_root / "scripts" / "catalog_to_lean.py"
    spec = importlib.util.spec_from_file_location("catalog_to_lean", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.render


def test_render_matches_committed_buildings(repo_root: Path) -> None:
    text = _render(repo_root)(load_catalog(repo_root))
    committed = (
        repo_root / "lean" / "PatternLanguage" / "Instantiations" / "Buildings.lean"
    ).read_text(encoding="utf-8")
    assert text == committed
    assert "theorem numericOrder_ok" in text
    assert "by decide" in text
    assert "(.p106, .p105)" in text
    assert "(.p180, .p159)" in text
    assert "p105" in text
    assert "South" not in text


def test_check_matches_committed_file(repo_root: Path) -> None:
    completed = subprocess.run(
        [sys.executable, str(repo_root / "scripts" / "catalog_to_lean.py"), "--check"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""
