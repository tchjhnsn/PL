#!/usr/bin/env python3
"""Lint SpatialStructure plan geometry (overlap, sit-on, clearance)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pattern_language.spatial_lint import lint_plan  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "plan",
        nargs="?",
        default=str(ROOT / "demo" / "data" / "plan-model.json"),
        help="Path to plan-model.json",
    )
    args = parser.parse_args(argv)
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    errors = lint_plan(plan)
    if errors:
        for line in errors:
            print(line, file=sys.stderr)
        print(f"fail: {len(errors)} spatial lint errors", file=sys.stderr)
        return 1
    print(f"ok: spatial lint ({len(plan.get('places', []))} places)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
