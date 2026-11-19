"""Import, Lean, and ship boundaries for the catalog."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

WATCHED_IMPORTS = frozenset({"ifcopenshell", "bpy", "bonsai"})

SCHEMA_FILES = (
    "schema/catalog.schema.json",
    "schema/check-report.schema.json",
    "schema/pattern-instance.schema.json",
    "schema/projects.schema.json",
    "schema/step.schema.json",
)

CATALOG_FILES = (
    "catalog/105-south-facing-outdoors.json",
    "catalog/106-positive-outdoor-space.json",
    "catalog/107-wings-of-light.json",
    "catalog/110-main-entrance.json",
    "catalog/112-entrance-transition.json",
    "catalog/127-intimacy-gradient.json",
    "catalog/128-indoor-sunlight.json",
    "catalog/130-entrance-room.json",
    "catalog/159-light-on-two-sides-of-every-room.json",
    "catalog/167-six-foot-balcony.json",
    "catalog/180-window-place.json",
    "catalog/190-ceiling-height-variety.json",
)


def _python_files(root: Path) -> list[Path]:
    skipped = {".venv", ".lake", "__pycache__", ".git"}
    files: list[Path] = []
    for path in root.rglob("*.py"):
        if skipped.intersection(path.parts):
            continue
        files.append(path)
    return files


def _forbidden_import_sites(tree: ast.AST) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []

    class Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.stack: list[str] = []

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self.stack.append(node.name)
            self.generic_visit(node)
            self.stack.pop()

        visit_AsyncFunctionDef = visit_FunctionDef

        def _record(self, module: str) -> None:
            root = module.split(".", 1)[0]
            if root not in WATCHED_IMPORTS:
                return
            allowed = {"read_ifc", "write_ifc"} & set(self.stack)
            where = next(iter(allowed)) if allowed else (self.stack[-1] if self.stack else "<module>")
            found.append((where, root))

        def visit_Import(self, node: ast.Import) -> None:
            for alias in node.names:
                self._record(alias.name)

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            if node.module:
                self._record(node.module)

    Visitor().visit(tree)
    return found


def test_import_boundary_forbids_ifcopenshell_and_bpy(repo_root: Path) -> None:
    offenders: list[str] = []
    for path in _python_files(repo_root):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        relative = path.relative_to(repo_root).as_posix()
        for where, root in _forbidden_import_sites(tree):
            if root == "ifcopenshell":
                allowed = relative == "src/pattern_language/topology.py" and where in {
                    "read_ifc",
                    "write_ifc",
                }
            elif root == "bpy":
                allowed = relative.startswith("adapters/blender/")
            elif root == "bonsai":
                allowed = relative == "adapters/blender/bridge.py"
            else:
                allowed = False
            if not allowed:
                offenders.append(f"{relative} imports {root} in {where}")
    assert offenders == []


def test_importing_gate_does_not_load_forbidden_modules() -> None:
    script = (
        "import sys\n"
        "import pattern_language\n"
        "import pattern_language.gate\n"
        "import pattern_language.topology\n"
        "import pattern_language.checker\n"
        "import pattern_language.conditions.registry\n"
        "forbidden = {'ifcopenshell', 'bpy'}\n"
        "loaded = sorted(forbidden & sys.modules.keys())\n"
        "assert not loaded, loaded\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


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


def test_u1_ships_five_schemas_and_twelve_records(repo_root: Path) -> None:
    schemas = sorted(
        path.relative_to(repo_root).as_posix()
        for path in (repo_root / "schema").rglob("*.json")
    )
    catalog = sorted(
        path.relative_to(repo_root).as_posix()
        for path in (repo_root / "catalog").rglob("*.json")
    )
    assert schemas == sorted(SCHEMA_FILES)
    assert catalog == sorted(CATALOG_FILES)
    projects = sorted(
        path.relative_to(repo_root).as_posix()
        for path in (repo_root / "projects").rglob("*.json")
    )
    assert projects == ["projects/seed-house.json"]
    for relative in SCHEMA_FILES:
        schema = json.loads((repo_root / relative).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)


def test_u4_pl_check_is_the_only_command(repo_root: Path) -> None:
    pyproject = (repo_root / "pyproject.toml").read_text(encoding="utf-8")
    section = pyproject.split("[project.scripts]", 1)[1].split("[", 1)[0]
    entries = [line.strip() for line in section.splitlines() if line.strip()]
    assert entries == ['pl = "pattern_language.cli:main"']
    assert not list(repo_root.glob("scripts/pl*"))


def test_ci_workflow_covers_gate_and_lean(repo_root: Path) -> None:
    workflow = (repo_root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "uv sync --frozen" in workflow
    assert "uv run pytest" in workflow
    assert "uv run python scripts/validate_catalog.py" in workflow
    assert "uv run python scripts/catalog_to_lean.py --check" in workflow
    assert (
        "uv run pl check fixtures/pass-house.ifc --language projects/seed-house.json"
        in workflow
    )
    assert "uv run pl sequence projects/seed-house.json" in workflow
    assert "uv run python scripts/drive_run.py --check" in workflow
    assert "leanprover/lean-action@v1" in workflow
    assert "lake-package-directory: lean" in workflow


def test_importing_sequence_does_not_load_checker_or_ifcopenshell() -> None:
    script = (
        "import sys\n"
        "import pattern_language.sequence\n"
        "assert 'pattern_language.checker' not in sys.modules\n"
        "assert 'ifcopenshell' not in sys.modules\n"
        "assert 'bpy' not in sys.modules\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


def test_runs_does_not_reimplement_preserving(repo_root: Path) -> None:
    path = repo_root / "src" / "pattern_language" / "runs.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    banned = {"preserving", "build_step", "CHECKS", "evaluate"}
    found: list[str] = []
    constants: list[str] = []
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else None
            if isinstance(func, ast.Attribute):
                name = func.attr
            if name in banned:
                found.append(name)
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            constants.append(node.value)
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    assert found == []
    assert "step" in constants
    assert "check" in constants
    assert "pattern_language.checker" not in modules
    assert "pattern_language.step" not in modules


def test_importing_runs_leaves_blender_and_ifcopenshell_unloaded() -> None:
    script = (
        "import sys\n"
        "import pattern_language.runs\n"
        "for name in ('bpy', 'bonsai', 'ifcopenshell'):\n"
        "    assert name not in sys.modules, name\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


def test_importing_step_does_not_load_ifcopenshell() -> None:
    script = (
        "import sys\n"
        "import pattern_language.step\n"
        "assert 'ifcopenshell' not in sys.modules\n"
        "assert 'bpy' not in sys.modules\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


_SERVER_CALLS = frozenset(
    {
        "read_ifc",
        "write_ifc",
        "read_topology",
        "CHECKS",
        "order_ok",
        "smaller_edges",
        "preserving",
        "fails_gate",
        "main",
    }
)


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _main_guard(node: ast.AST) -> bool:
    if not isinstance(node, ast.If) or not isinstance(node.test, ast.Compare):
        return False
    test = node.test
    if not isinstance(test.left, ast.Name) or test.left.id != "__name__":
        return False
    if len(test.ops) != 1 or not isinstance(test.ops[0], ast.Eq):
        return False
    if len(test.comparators) != 1 or not isinstance(test.comparators[0], ast.Constant):
        return False
    return test.comparators[0].value == "__main__"


def test_mcp_server_is_a_file_not_a_package(repo_root: Path) -> None:
    assert not (repo_root / "mcp" / "__init__.py").exists()
    path = repo_root / "mcp" / "server.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    guard: list[str] = []
    other: list[str] = []
    for node in tree.body:
        bucket = guard if _main_guard(node) else other
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                name = _call_name(child.func)
                if name in _SERVER_CALLS:
                    bucket.append(name)
    assert other == []
    assert guard == ["main"]


def test_validate_catalog_cli_accepts_seed_catalog(repo_root: Path) -> None:
    completed = subprocess.run(
        [sys.executable, str(repo_root / "scripts" / "validate_catalog.py")],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert completed.stdout == "back-edges: 0\nok: 13 records\n"
    assert completed.stderr == ""


def test_validate_catalog_cli_accepts_empty_tree(tmp_path: Path, repo_root: Path) -> None:
    for name in ("schema", "catalog", "projects"):
        (tmp_path / name).mkdir()
    completed = subprocess.run(
        [sys.executable, str(repo_root / "scripts" / "validate_catalog.py"), str(tmp_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert completed.stdout == "back-edges: 0\nok: 0 records\n"
    assert completed.stderr == ""


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
    assert completed.stdout == ""
    assert "record without schema: catalog/orphan.json" in completed.stderr
