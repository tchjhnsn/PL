"""Record one seed-house run, or check that contract in a temporary directory.

The default command writes ``runs/<YYYYMMDDTHHMMSSZ>/`` under the current
directory. ``--check`` writes the same run in a temporary directory, asserts
the contract, and removes it.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from pattern_language.catalog import CatalogLoadError
from pattern_language.conditions.evidence import CheckError
from pattern_language.runs import RunError, record_run
from pattern_language.sequence import SequenceError
from pattern_language.topology import TopologyError, read_ifc, to_json

REPO_ROOT = Path(__file__).resolve().parents[1]
_FINAL_SATISFIED = [105, 106, 107, 112, 127, 128, 130, 159, 167, 190]


class _ContractError(Exception):
    """``--check`` found a run that does not match the seed-house contract."""


def main(argv: list[str] | None = None) -> int:
    """Write one run, or check the contract in a temporary directory.

    No arguments: create runs/<stamp>/ under the current directory and
    call record_run. Exit 0 when report.json is written.
    --check: call record_run in a temporary directory, assert the contract,
    and exit 0. The temporary directory is removed.
    Exit 1 when record_run raises RunError. The stamp directory is removed.
    Exit 2 on usage, CatalogLoadError, CheckError, TopologyError, or OSError.
    """
    parser = argparse.ArgumentParser(description="Record one seed-house run.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Assert the contract in a temporary directory. Write nothing under runs/.",
    )
    args = parser.parse_args(argv)
    if args.check:
        return _check()
    return _write()


def _write() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    directory = Path.cwd() / "runs" / stamp
    if directory.exists():
        print("run exists", file=sys.stderr)
        return 2
    directory.mkdir(parents=True)
    try:
        record_run(directory, root=REPO_ROOT)
    except RunError as exc:
        shutil.rmtree(directory)
        print(exc, file=sys.stderr)
        return 1
    except (CatalogLoadError, CheckError, TopologyError, SequenceError, OSError) as exc:
        shutil.rmtree(directory, ignore_errors=True)
        print(exc, file=sys.stderr)
        return 2
    print(f"wrote: runs/{stamp}")
    return 0


def _check() -> int:
    try:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "run"
            directory.mkdir()
            record_run(directory, root=REPO_ROOT)
            _assert_contract(directory)
    except (RunError, _ContractError) as exc:
        print(exc, file=sys.stderr)
        return 1
    except (CatalogLoadError, CheckError, TopologyError, SequenceError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 2
    print("fresh: 12 steps")
    return 0


def _assert_contract(directory: Path) -> None:
    for index in range(1, 13):
        path = directory / f"step-{index:02d}.json"
        if not path.is_file():
            raise _ContractError(f"missing {path.name}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("preserved") is not True:
            raise _ContractError(f"preserved is false: {payload.get('pattern')}")
    report_path = directory / "report.json"
    if not report_path.is_file():
        raise _ContractError("missing report.json")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("satisfied") != _FINAL_SATISFIED:
        raise _ContractError(f"satisfied {report.get('satisfied')}")
    by_status = {item["pattern"]: item["status"] for item in report["instances"]}
    if by_status.get(110) != "needs_judgment" or by_status.get(180) != "needs_judgment":
        raise _ContractError("110 and 180 are not needs_judgment")
    if 110 in report["satisfied"] or 180 in report["satisfied"]:
        raise _ContractError("110 or 180 is in satisfied")
    model = to_json(read_ifc(directory / "model-12.ifc"))
    house = to_json(read_ifc(REPO_ROOT / "fixtures" / "pass-house.ifc"))
    if model != house:
        raise _ContractError("model-12 is not the pass house")


if __name__ == "__main__":
    raise SystemExit(main())
