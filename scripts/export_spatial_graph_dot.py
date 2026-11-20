#!/usr/bin/env python3
"""Export spatial-concept-graph.json as Graphviz DOT (deps + specializes only by default)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "docs" / "design" / "spatial-concept-graph.json"
OUT = ROOT / "docs" / "design" / "spatial-concept-graph.dot"

FOCUS_RELS = {"depends_on", "specializes", "parent_of", "maps_to"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all-rels", action="store_true", help="Include sibling_of and renders_as")
    ap.add_argument("-o", type=Path, default=OUT)
    args = ap.parse_args()
    g = json.loads(GRAPH.read_text(encoding="utf-8"))
    allowed = FOCUS_RELS if not args.all_rels else FOCUS_RELS | {"sibling_of", "renders_as"}
    lines = [
        "digraph SpatialConcepts {",
        "  rankdir=LR;",
        '  node [shape=box, fontname="Helvetica", fontsize=9];',
        '  edge [fontsize=8];',
    ]
    status_color = {
        "have": "#d7e5dc",
        "partial": "#f0e6c8",
        "todo": "#f0d4d4",
        "placeholder": "#e8e8e8",
    }
    for n in g["nodes"]:
        fill = status_color.get(n["status"], "#fff")
        label = f"{n['id']}\\n{n['name']}"
        lines.append(f'  "{n["id"]}" [label="{label}", style=filled, fillcolor="{fill}"];')
    for e in g["edges"]:
        if e["rel"] not in allowed:
            continue
        if e["rel"] == "sibling_of" and e["from"] > e["to"]:
            continue
        lines.append(f'  "{e["from"]}" -> "{e["to"]}" [label="{e["rel"]}"];')
    lines.append("}")
    args.o.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {args.o.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
