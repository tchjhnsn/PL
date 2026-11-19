"""``pl check``, ``pl sequence``, and ``pl step``."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pattern_language.catalog import CatalogLoadError, load_catalog
from pattern_language.checker import fails_gate, report_json, run
from pattern_language.conditions.evidence import CheckError
from pattern_language.parameters import load_project
from pattern_language.sequence import SequenceError, sequence
from pattern_language.step import build_step, step_json
from pattern_language.topology import TopologyError

_CHECK_USAGE = "usage: pl check <model.ifc> --language <project.json>"
_SEQUENCE_USAGE = "usage: pl sequence <project.json>"
_STEP_USAGE = (
    "usage: pl step <before.ifc> <after.ifc> --language <project.json> --pattern <n>"
)


class _Parser(argparse.ArgumentParser):
    pl_usage = _CHECK_USAGE

    def error(self, message: str) -> None:
        raise CheckError(self.pl_usage)


def main(argv: list[str] | None = None) -> int:
    """Dispatch pl check, pl sequence, and pl step.

    check keeps the U4 signature and the U4 exits.
    sequence exits 0 when sequence returns, and 2 on SequenceError,
    CatalogLoadError, CheckError, or OSError.
    step exits 0 when preserved is true, 1 when it is false, and 2
    on the same errors. A schema failure is CheckError.
    """
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        return _fail("unknown command")
    command, rest = argv[0], argv[1:]
    if command == "check":
        return _check(rest)
    if command == "sequence":
        return _sequence(rest)
    if command == "step":
        return _step(rest)
    return _fail("unknown command")


def _check(argv: list[str]) -> int:
    """``pl check <model.ifc> --language <project.json> [--out PATH] [--root PATH]``.

    ``--root`` defaults to the current directory. Relative model and language
    paths open from the current directory. ``model.file`` in the report is the
    model argument, posix-separated, not resolved.
    """
    try:
        args = _parse_check(argv)
        root = _from_cwd(args.root).resolve()
        model_path = _from_cwd(args.model)
        language_path = _from_cwd(args.language)
        catalog = load_catalog(root)
        project = load_project(
            language_path,
            schema_path=root / "schema" / "projects.schema.json",
        )
        report = run(
            catalog,
            project,
            model_path,
            model_file=args.model.replace("\\", "/"),
            schema_path=root / "schema" / "check-report.schema.json",
        )
        text = report_json(report)
        if args.out is not None:
            _from_cwd(args.out).write_text(text, encoding="utf-8")
        sys.stdout.write(text)
    except CheckError as exc:
        return _fail(str(exc))
    except CatalogLoadError as exc:
        return _fail(str(exc))
    except TopologyError as exc:
        return _fail(str(exc))
    except OSError as exc:
        return _fail(str(exc))
    return 1 if fails_gate(report) else 0


def _sequence(argv: list[str]) -> int:
    """``pl sequence <project.json> [--root PATH]``.

    Stdout is a JSON array of pattern numbers, indented two spaces, with one
    trailing newline. The project path opens from the current directory.
    """
    try:
        args = _parse_sequence(argv)
        root = _from_cwd(args.root).resolve()
        catalog = load_catalog(root)
        project = load_project(
            _from_cwd(args.project),
            schema_path=root / "schema" / "projects.schema.json",
        )
        order = sequence(catalog, project)
        sys.stdout.write(json.dumps(list(order), indent=2) + "\n")
    except (SequenceError, CatalogLoadError, CheckError, OSError) as exc:
        return _fail(str(exc))
    return 0


def _step(argv: list[str]) -> int:
    """``pl step <before.ifc> <after.ifc> --language <project.json> --pattern <n>``.

    Exits 0 when preserved is true and 1 when it is false. Stdout is the step.
    """
    try:
        args = _parse_step(argv)
        root = _from_cwd(args.root).resolve()
        catalog = load_catalog(root)
        project = load_project(
            _from_cwd(args.language),
            schema_path=root / "schema" / "projects.schema.json",
        )
        step = build_step(
            catalog,
            project,
            _from_cwd(args.before),
            _from_cwd(args.after),
            pattern=args.pattern,
            before_file=args.before.replace("\\", "/"),
            after_file=args.after.replace("\\", "/"),
            schema_path=root / "schema" / "step.schema.json",
        )
        text = step_json(step)
        if args.out is not None:
            _from_cwd(args.out).write_text(text, encoding="utf-8")
        sys.stdout.write(text)
    except (SequenceError, CatalogLoadError, CheckError, TopologyError, OSError) as exc:
        return _fail(str(exc))
    return 0 if step.preserved else 1


def _parse_check(argv: list[str]) -> argparse.Namespace:
    parser = _Parser(prog="pl check", add_help=False)
    parser.pl_usage = _CHECK_USAGE
    parser.add_argument("model")
    parser.add_argument("--language", required=True)
    parser.add_argument("--out")
    parser.add_argument("--root", default=".")
    return parser.parse_args(argv)


def _parse_sequence(argv: list[str]) -> argparse.Namespace:
    parser = _Parser(prog="pl sequence", add_help=False)
    parser.pl_usage = _SEQUENCE_USAGE
    parser.add_argument("project")
    parser.add_argument("--root", default=".")
    return parser.parse_args(argv)


def _parse_step(argv: list[str]) -> argparse.Namespace:
    parser = _Parser(prog="pl step", add_help=False)
    parser.pl_usage = _STEP_USAGE
    parser.add_argument("before")
    parser.add_argument("after")
    parser.add_argument("--language", required=True)
    parser.add_argument("--pattern", required=True, type=int)
    parser.add_argument("--out")
    parser.add_argument("--root", default=".")
    return parser.parse_args(argv)


def _from_cwd(raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    return Path.cwd() / path


def _fail(message: str) -> int:
    line = " ".join(message.splitlines())
    sys.stderr.write(line + "\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
