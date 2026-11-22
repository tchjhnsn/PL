"""Load and query the urban design typology ontology + component library."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
ONTOLOGY_PATH = ROOT / "schema" / "ontology" / "urban-typologies.json"
SCHEMA_PATH = ROOT / "schema" / "ontology" / "urban-typologies.schema.json"


class UrbanTypologyError(ValueError):
    """Invalid or inconsistent urban typology document."""


@lru_cache(maxsize=1)
def load_urban_typologies(*, validate: bool = True) -> dict[str, Any]:
    """Return the ontology document (cached). Validates against schema when asked."""
    doc = json.loads(ONTOLOGY_PATH.read_text(encoding="utf-8"))
    if validate:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(doc)
        _check_refs(doc)
    return doc


def _check_refs(doc: dict[str, Any]) -> None:
    type_ids = {t["id"] for t in doc["types"]}
    layer_ids = {layer["id"] for layer in doc["layers"]}
    source_ids = {s["id"] for s in doc["sources"]}
    for t in doc["types"]:
        if t["layer"] not in layer_ids:
            raise UrbanTypologyError(f"{t['id']}: unknown layer {t['layer']}")
        for src in t.get("sources") or []:
            if src not in source_ids:
                raise UrbanTypologyError(f"{t['id']}: unknown source {src}")
        parent = t.get("parent")
        if parent and parent not in type_ids:
            raise UrbanTypologyError(f"{t['id']}: unknown parent {parent}")
    for comp in doc["components"]:
        for ut in comp["implements"]:
            if ut not in type_ids:
                raise UrbanTypologyError(f"{comp['id']}: unknown type {ut}")


def types_in_layer(layer: str, *, doc: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    data = doc or load_urban_typologies()
    return [t for t in data["types"] if t["layer"] == layer]


def get_type(type_id: str, *, doc: dict[str, Any] | None = None) -> dict[str, Any]:
    data = doc or load_urban_typologies()
    for t in data["types"]:
        if t["id"] == type_id:
            return t
    raise KeyError(type_id)


def get_component(comp_id: str, *, doc: dict[str, Any] | None = None) -> dict[str, Any]:
    data = doc or load_urban_typologies()
    for c in data["components"]:
        if c["id"] == comp_id:
            return c
    raise KeyError(comp_id)


def components_for_type(type_id: str, *, doc: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    data = doc or load_urban_typologies()
    return [c for c in data["components"] if type_id in c["implements"]]


def implemented_kits(*, doc: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    data = doc or load_urban_typologies()
    return [c for c in data["components"] if c["status"] == "implemented" and c.get("kit")]


def match_place_roles(
    roles: list[str] | tuple[str, ...] | None,
    *,
    component: str | None = None,
    doc: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Return typology types whose spatial.roles intersect place roles (and optional component)."""
    data = doc or load_urban_typologies()
    role_set = set(roles or [])
    hits: list[dict[str, Any]] = []
    for t in data["types"]:
        spatial = t["spatial"]
        if component and spatial.get("component") != component:
            continue
        declared = set(spatial.get("roles") or [])
        if role_set & declared:
            hits.append(t)
    return hits
