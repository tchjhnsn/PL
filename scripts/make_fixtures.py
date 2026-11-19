"""Write the two U3 houses, or check that the committed graphs are fresh.

IFC bytes are not the oracle. ``--check`` compares topology graphs and the
sibling expected JSON. It does not write into ``fixtures/``.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from pattern_language.topology import TopologyError, read_ifc, to_json, write_fixtures

REPO_ROOT = Path(__file__).resolve().parents[1]
HOUSES = ("pass-house", "fail-house")


def main(argv: list[str] | None = None) -> int:
    """Write both houses, or compare committed fixtures when ``--check`` is set."""
    parser = argparse.ArgumentParser(
        description="Write the two U3 houses and their expected topology JSON.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Compare committed graphs and expected JSON. Write nothing on failure.",
    )
    args = parser.parse_args(argv)
    fixtures = REPO_ROOT / "fixtures"
    if args.check:
        return _check(fixtures)
    write_fixtures(fixtures)
    for name in HOUSES:
        graph = read_ifc(fixtures / f"{name}.ifc")
        (fixtures / f"{name}.expected.json").write_text(to_json(graph), encoding="utf-8")
    print("wrote: 2 houses")
    return 0


def _check(fixtures: Path) -> int:
    stale: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        fresh_dir = Path(tmp)
        write_fixtures(fresh_dir)
        for name in HOUSES:
            ifc_path = fixtures / f"{name}.ifc"
            json_path = fixtures / f"{name}.expected.json"
            if not ifc_path.is_file():
                stale.append(f"fixtures/{name}.ifc")
            if not json_path.is_file():
                stale.append(f"fixtures/{name}.expected.json")
            if not ifc_path.is_file() or not json_path.is_file():
                continue
            try:
                committed = read_ifc(ifc_path)
                fresh = read_ifc(fresh_dir / f"{name}.ifc")
            except TopologyError:
                stale.append(f"fixtures/{name}.ifc")
                continue
            fresh_json = to_json(fresh)
            if json_path.read_text(encoding="utf-8") != fresh_json:
                stale.append(f"fixtures/{name}.expected.json")
            if committed != fresh or to_json(committed) != fresh_json:
                stale.append(f"fixtures/{name}.ifc")
    if stale:
        for line in stale:
            print(f"stale: {line}", file=sys.stderr)
        return 1
    print("fresh: 2 houses")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
