"""``pl check`` command. Sequence and step are later units."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pattern_language.catalog import CatalogLoadError, load_catalog
from pattern_language.checker import fails_gate, report_json, run
from pattern_language.conditions.evidence import CheckError
from pattern_language.parameters import load_project
from pattern_language.topology import TopologyError

_USAGE = "usage: pl check <model.ifc> --language <project.json>"


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CheckError(_USAGE)


def main(argv: list[str] | None = None) -> int:
    """``pl check <model.ifc> --language <project.json> [--out PATH] [--root PATH]``.

    ``--root`` defaults to the current directory. Relative model and language
    paths open from the current directory. ``model.file`` in the report is the
    model argument, posix-separated, not resolved.
    """
    if argv is None:
        argv = sys.argv[1:]
    if not argv or argv[0] != "check":
        return _fail("unknown command")
    try:
        args = _parse(argv[1:])
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


def _parse(argv: list[str]) -> argparse.Namespace:
    parser = _Parser(prog="pl check", add_help=False)
    parser.add_argument("model")
    parser.add_argument("--language", required=True)
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
