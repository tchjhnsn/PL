"""Validate the pattern-language catalog and exit non-zero on errors."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pattern_language.gate import scan

REPO_ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    """Scan a catalog root and print one line per error."""
    parser = argparse.ArgumentParser(description="Validate catalog and project records.")
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=REPO_ROOT,
        help="Repository root. Defaults to the parent of scripts/.",
    )
    args = parser.parse_args(argv)
    result = scan(args.root)
    if result.ok:
        print(f"ok: {len(result.records)} records")
        return 0
    for error in result.errors:
        print(error, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
