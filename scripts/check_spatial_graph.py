#!/usr/bin/env python3
"""Integrity check for the spatial concept graph (orphan edges, unknown rels)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "docs" / "design" / "spatial-concept-graph.json"
ALLOWED = {"depends_on", "parent_of", "sibling_of", "maps_to", "specializes", "renders_as"}


def main() -> int:
    g = json.loads(GRAPH.read_text(encoding="utf-8"))
    ids = {n["id"] for n in g["nodes"]}
    errors: list[str] = []
    for e in g["edges"]:
        if e["rel"] not in ALLOWED:
            errors.append(f"bad rel {e}")
        if e["from"] not in ids:
            errors.append(f"missing from: {e}")
        if e["to"] not in ids:
            errors.append(f"missing to: {e}")
    # every node should have at least one edge (except allow orphans with note)
    touched = set()
    for e in g["edges"]:
        touched.add(e["from"])
        touched.add(e["to"])
    orphans = sorted(ids - touched)
    if orphans:
        errors.append(f"orphans: {orphans}")
    if errors:
        print("FAIL")
        for err in errors[:40]:
            print(err)
        if len(errors) > 40:
            print(f"... +{len(errors) - 40} more")
        return 1
    print(
        f"ok: {g['stats']['nodes']} nodes, {g['stats']['edges']} edges, "
        f"status={g['stats']['by_status']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
