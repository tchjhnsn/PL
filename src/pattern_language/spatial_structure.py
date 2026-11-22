"""Load and query SpatialStructure plan-models (demo mid-layer).

Pure helpers for places, network edges, and named measures. No IFC / bpy.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA = ROOT / "schema" / "spatial-structure.schema.json"


def load_spatial(path: str | Path, *, validate: bool = True) -> dict[str, Any]:
    plan = json.loads(Path(path).read_text(encoding="utf-8"))
    if validate:
        from jsonschema import Draft202012Validator

        schema = json.loads(DEFAULT_SCHEMA.read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(plan)
    return plan


def places_with_role(plan: dict[str, Any], role: str) -> list[dict[str, Any]]:
    return [p for p in plan.get("places", []) if role in (p.get("roles") or [])]


def measure_of(
    plan: dict[str, Any],
    place_id: str,
    kind: str | None = None,
) -> list[dict[str, Any]]:
    out = []
    for m in plan.get("measures", []):
        if m.get("of") != place_id:
            continue
        if kind is not None and m.get("kind") != kind:
            continue
        out.append(m)
    return out


def measure_value(plan: dict[str, Any], measure_id: str) -> float:
    for m in plan.get("measures", []):
        if m.get("id") == measure_id:
            return float(m["value_m"])
    raise KeyError(measure_id)


def clear_width(plan: dict[str, Any], place_id: str) -> float | None:
    for kind in ("width", "depth"):
        found = measure_of(plan, place_id, kind=kind)
        if found:
            return float(found[0]["value_m"])
    return None


def edge_width(plan: dict[str, Any], edge_id: str) -> float | None:
    for e in plan.get("network", {}).get("edges", []):
        if e.get("id") == edge_id:
            return float(e["width_m"])
    return None


def edge_by_id(plan: dict[str, Any], edge_id: str) -> dict[str, Any] | None:
    for e in plan.get("network", {}).get("edges", []):
        if e.get("id") == edge_id:
            return e
    return None


def place_by_id(plan: dict[str, Any], place_id: str) -> dict[str, Any] | None:
    for p in plan.get("places", []):
        if p.get("id") == place_id:
            return p
    return None
