"""Validate the pattern-language catalog and exit non-zero on errors.

On a clean scan, print each back-edge, then ``back-edges: N``, then
``ok: N records``. Missing targets go to stderr and exit 1.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pattern_language.catalog import CatalogLoadError, load_catalog
from pattern_language.gate import scan

REPO_ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    """Scan a catalog root, then report back-edges and missing targets."""
    parser = argparse.ArgumentParser(
        description="Validate catalog and project records and report link gaps.",
    )
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=REPO_ROOT,
        help="Repository root. Defaults to the parent of scripts/.",
    )
    args = parser.parse_args(argv)
    result = scan(args.root)
    if not result.ok:
        for error in result.errors:
            print(error, file=sys.stderr)
        return 1
    try:
        catalog = load_catalog(args.root)
    except CatalogLoadError as exc:
        for error in exc.errors:
            print(error, file=sys.stderr)
        return 1
    for edge in catalog.back_edges:
        print(f"back-edge: {edge.source} {edge.target}")
    print(f"back-edges: {len(catalog.back_edges)}")
    if catalog.missing_targets:
        for link in catalog.missing_targets:
            print(
                f"missing target: {link.source} {link.field} {link.target}",
                file=sys.stderr,
            )
        return 1
    print(f"ok: {len(result.records)} records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
