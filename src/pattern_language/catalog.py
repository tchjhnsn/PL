"""Load pattern records and report missing targets and back-edges.

``load_catalog`` runs ``scan`` and parses catalog records the gate accepted.
Project records stay in the scan and stay out of ``Catalog``.
``search``, ``get``, and ``pattern_record`` read that catalog.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal

from pattern_language.gate import scan

LinkField = Literal["larger", "smaller"]


class CatalogLoadError(Exception):
    """Scan errors, or two catalog files that share a pattern number."""

    errors: tuple[str, ...]

    def __init__(self, errors: str | tuple[str, ...]) -> None:
        if isinstance(errors, str):
            self.errors = (errors,)
        else:
            self.errors = tuple(errors)
        super().__init__("\n".join(self.errors))


@dataclass(frozen=True)
class DraftText:
    text: str
    draft: bool


@dataclass(frozen=True)
class Force:
    name: str
    draft: bool


@dataclass(frozen=True)
class Condition:
    id: str
    kind: str
    check: str | None = None
    params: Mapping[str, Any] | None = None
    question: str | None = None


@dataclass(frozen=True)
class Source:
    book: str
    number: int


@dataclass(frozen=True)
class Reference:
    url: str
    title: str
    retrieved: str
    note: str


@dataclass(frozen=True)
class Pattern:
    number: int
    name: str
    scale: str
    confidence: int
    larger: tuple[int, ...]
    smaller: tuple[int, ...]
    summary: DraftText
    forces: tuple[Force, ...]
    conditions: tuple[Condition, ...]
    source: Source
    path: str
    uses: tuple[str, ...] = ()
    references: tuple[Reference, ...] = ()


@dataclass(frozen=True)
class LinkRef:
    source: int
    field: LinkField
    target: int


@dataclass(frozen=True)
class BackEdge:
    source: int
    target: int


@dataclass(frozen=True)
class Catalog:
    patterns: tuple[Pattern, ...]
    by_number: Mapping[int, Pattern]
    missing_targets: tuple[LinkRef, ...]
    back_edges: tuple[BackEdge, ...]

    @property
    def ok(self) -> bool:
        return not self.missing_targets


def load_catalog(root: Path) -> Catalog:
    """Load catalog records under ``root``.

    Raises ``CatalogLoadError`` when ``scan`` reports errors or two catalog
    files share a number. Missing targets and back-edges are returned on the
    catalog.
    """
    root = root.resolve()
    result = scan(root)
    if not result.ok:
        raise CatalogLoadError(result.errors)
    patterns: list[Pattern] = []
    seen: dict[int, str] = {}
    for record in result.records:
        relative = record.relative_to(result.root)
        if not relative.parts or relative.parts[0] != "catalog":
            continue
        payload = json.loads(record.read_text(encoding="utf-8"))
        path = relative.as_posix()
        pattern = _pattern_from_object(payload, path)
        previous = seen.get(pattern.number)
        if previous is not None:
            left, right = sorted((previous, path))
            raise CatalogLoadError(
                f"duplicate pattern number: {pattern.number} ({left}, {right})"
            )
        seen[pattern.number] = path
        patterns.append(pattern)
    ordered = tuple(sorted(patterns, key=lambda item: item.number))
    by_number = MappingProxyType({item.number: item for item in ordered})
    return Catalog(
        patterns=ordered,
        by_number=by_number,
        missing_targets=_missing_targets(ordered, by_number),
        back_edges=_back_edges(ordered, by_number),
    )


def search(
    catalog: Catalog,
    *,
    number: int | None = None,
    name: str | None = None,
    scale: str | None = None,
) -> tuple[Pattern, ...]:
    """Patterns whose fields match every provided filter.

    number and scale are exact. name is a case-insensitive substring
    of Pattern.name. An empty filter returns catalog.patterns.
    """
    needle = None if name is None else name.lower()
    found: list[Pattern] = []
    for pattern in catalog.patterns:
        if number is not None and pattern.number != number:
            continue
        if scale is not None and pattern.scale != scale:
            continue
        if needle is not None and needle not in pattern.name.lower():
            continue
        found.append(pattern)
    return tuple(found)


def get(catalog: Catalog, number: int) -> Pattern:
    """Return the pattern with this number.

    Raise CatalogLoadError with ``missing pattern: N`` when the number
    is absent.
    """
    pattern = catalog.by_number.get(number)
    if pattern is None:
        raise CatalogLoadError(f"missing pattern: {number}")
    return pattern


def pattern_record(pattern: Pattern) -> dict[str, Any]:
    """The catalog schema object for this pattern.

    Omits path. A condition omits check, params, and question when
    the value is None. Optional uses and references are omitted when empty.
    """
    record: dict[str, Any] = {
        "number": pattern.number,
        "name": pattern.name,
        "scale": pattern.scale,
        "confidence": pattern.confidence,
        "larger": list(pattern.larger),
        "smaller": list(pattern.smaller),
        "summary": {"text": pattern.summary.text, "draft": pattern.summary.draft},
        "forces": [{"name": force.name, "draft": force.draft} for force in pattern.forces],
        "conditions": [_condition_record(condition) for condition in pattern.conditions],
        "source": {"book": pattern.source.book, "number": pattern.source.number},
    }
    if pattern.uses:
        record["uses"] = list(pattern.uses)
    if pattern.references:
        record["references"] = [
            {
                "url": item.url,
                "title": item.title,
                "retrieved": item.retrieved,
                "note": item.note,
            }
            for item in pattern.references
        ]
    return record



def _condition_record(condition: Condition) -> dict[str, Any]:
    record: dict[str, Any] = {"id": condition.id, "kind": condition.kind}
    if condition.check is not None:
        record["check"] = condition.check
    if condition.params is not None:
        record["params"] = dict(condition.params)
    if condition.question is not None:
        record["question"] = condition.question
    return record


def _pattern_from_object(payload: dict[str, Any], path: str) -> Pattern:
    summary = payload["summary"]
    source = payload["source"]
    references = tuple(
        Reference(
            url=item["url"],
            title=item["title"],
            retrieved=item["retrieved"],
            note=item["note"],
        )
        for item in payload.get("references", [])
    )
    return Pattern(
        number=payload["number"],
        name=payload["name"],
        scale=payload["scale"],
        confidence=payload["confidence"],
        larger=tuple(payload["larger"]),
        smaller=tuple(payload["smaller"]),
        summary=DraftText(text=summary["text"], draft=summary["draft"]),
        forces=tuple(
            Force(name=force["name"], draft=force["draft"]) for force in payload["forces"]
        ),
        conditions=tuple(_condition(item) for item in payload["conditions"]),
        source=Source(book=source["book"], number=source["number"]),
        path=path,
        uses=tuple(payload.get("uses", [])),
        references=references,
    )


def _condition(raw: dict[str, Any]) -> Condition:
    params = raw.get("params")
    if params is not None:
        params = MappingProxyType(dict(params))
    return Condition(
        id=raw["id"],
        kind=raw["kind"],
        check=raw.get("check"),
        params=params,
        question=raw.get("question"),
    )


def _missing_targets(
    patterns: tuple[Pattern, ...],
    by_number: Mapping[int, Pattern],
) -> tuple[LinkRef, ...]:
    found: list[LinkRef] = []
    for pattern in patterns:
        for field in ("larger", "smaller"):
            targets = pattern.larger if field == "larger" else pattern.smaller
            for target in targets:
                if target not in by_number:
                    found.append(LinkRef(pattern.number, field, target))
    found.sort(key=lambda link: (link.source, link.field, link.target))
    return tuple(found)


def _back_edges(
    patterns: tuple[Pattern, ...],
    by_number: Mapping[int, Pattern],
) -> tuple[BackEdge, ...]:
    found: list[BackEdge] = []
    for pattern in patterns:
        for target in pattern.smaller:
            if target in by_number and target < pattern.number:
                found.append(BackEdge(pattern.number, target))
    found.sort(key=lambda edge: (edge.source, edge.target))
    return tuple(found)
