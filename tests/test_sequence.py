"""Sequence matches numericOrder and the orderOk Bool."""

from __future__ import annotations

import ast
import importlib.util
import re
from pathlib import Path
from types import MappingProxyType

import pytest

from pattern_language.catalog import (
    Catalog,
    DraftText,
    Pattern,
    Source,
    load_catalog,
)
from pattern_language.parameters import Project, load_project
from pattern_language.sequence import (
    SequenceError,
    index_before,
    order_ok,
    sequence,
    smaller_edges,
)

_SEED_NUMBERS = frozenset(
    {105, 106, 107, 110, 112, 127, 128, 130, 159, 167, 180, 190}
)
_NUMERIC_ORDER = re.compile(r"def numericOrder : List Pat := \[(.*?)\]", re.S)
_SMALLER_EDGES = re.compile(
    r"def smallerEdges : List \(Pat × Pat\) := \[(.*?)\]",
    re.S,
)


def test_sequence_matches_parsed_numeric_order(repo_root: Path) -> None:
    catalog = load_catalog(repo_root)
    project = load_project(
        repo_root / "projects" / "seed-house.json",
        schema_path=repo_root / "schema" / "projects.schema.json",
    )
    order = sequence(catalog, project)
    committed = (
        repo_root / "lean" / "PatternLanguage" / "Instantiations" / "Buildings.lean"
    ).read_text(encoding="utf-8")
    rendered = _render(repo_root)(catalog)
    assert _parse_numeric_order(committed) == order
    assert _parse_numeric_order(rendered) == order
    edges = smaller_edges(catalog, order)
    assert _parse_smaller_edges(committed) == edges
    assert _parse_smaller_edges(rendered) == edges
    assert order_ok(order, edges) is True


def test_reversed_order_fails_on_the_first_smaller_edge(repo_root: Path) -> None:
    catalog = load_catalog(repo_root)
    project = load_project(
        repo_root / "projects" / "seed-house.json",
        schema_path=repo_root / "schema" / "projects.schema.json",
    )
    order = sequence(catalog, project)
    edges = smaller_edges(catalog, order)
    reversed_order = tuple(reversed(order))
    assert order_ok(reversed_order, edges) is False
    assert (106, 105) in edges
    assert index_before(reversed_order, 105, 106) is False


def test_index_before_matches_first_index() -> None:
    order = (4, 9, 4)
    assert index_before(order, 4, 9) is True
    assert index_before(order, 9, 4) is False
    assert index_before(order, 4, 4) is False
    assert index_before((4, 9), 4, 4) is False
    assert index_before(order, 4, 1) is False
    assert index_before(order, 1, 9) is False
    assert index_before((), 4, 9) is False


def test_subset_sequences_in_ascending_numbers(repo_root: Path) -> None:
    catalog = load_catalog(repo_root)
    project = _project((190, 105, 106), start=190)
    assert sequence(catalog, project) == (105, 106, 190)


def test_one_pattern_has_no_induced_edge(repo_root: Path) -> None:
    catalog = load_catalog(repo_root)
    project = _project((190,), start=190)
    assert sequence(catalog, project) == (190,)
    assert smaller_edges(catalog, (190,)) == ()


def test_back_edge_rejects_ascending_order() -> None:
    catalog = _catalog(
        (
            _pattern(105, smaller=(106,)),
            _pattern(106, smaller=(105,)),
        )
    )
    with pytest.raises(SequenceError, match=r"^sequence is not valid$"):
        sequence(catalog, _project((105, 106), start=105))


def test_missing_pattern_names_the_number(repo_root: Path) -> None:
    catalog = load_catalog(repo_root)
    with pytest.raises(SequenceError, match=r"^missing pattern: 200$"):
        sequence(catalog, _project((200,), start=200))


def test_sequence_module_has_no_seed_number_literals(repo_root: Path) -> None:
    tree = ast.parse(
        (repo_root / "src" / "pattern_language" / "sequence.py").read_text(encoding="utf-8")
    )
    found = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, int)
        and not isinstance(node.value, bool)
        and node.value in _SEED_NUMBERS
    ]
    assert found == []


def _parse_numeric_order(text: str) -> tuple[int, ...]:
    match = _NUMERIC_ORDER.search(text)
    assert match is not None
    return tuple(int(number) for number in re.findall(r"\.p(\d+)", match.group(1)))


def _parse_smaller_edges(text: str) -> tuple[tuple[int, int], ...]:
    match = _SMALLER_EDGES.search(text)
    assert match is not None
    pairs = re.findall(r"\(\.p(\d+), \.p(\d+)\)", match.group(1))
    return tuple((int(smaller), int(completed)) for smaller, completed in pairs)


def _render(repo_root: Path):
    path = repo_root / "scripts" / "catalog_to_lean.py"
    spec = importlib.util.spec_from_file_location("catalog_to_lean_sequence", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.render


def _project(patterns: tuple[int, ...], *, start: int) -> Project:
    return Project(
        id="probe",
        patterns=patterns,
        start=start,
        units="si",
        latitude_deg=None,
        by_pattern=MappingProxyType({}),
    )


def _pattern(number: int, *, smaller: tuple[int, ...]) -> Pattern:
    return Pattern(
        number=number,
        name="probe",
        scale="building",
        confidence=1,
        larger=(),
        smaller=smaller,
        summary=DraftText(text="probe", draft=True),
        forces=(),
        conditions=(),
        source=Source(book="probe", number=number),
        path=f"catalog/{number}.json",
    )


def _catalog(patterns: tuple[Pattern, ...]) -> Catalog:
    ordered = tuple(sorted(patterns, key=lambda item: item.number))
    return Catalog(
        patterns=ordered,
        by_number=MappingProxyType({item.number: item for item in ordered}),
        missing_targets=(),
        back_edges=(),
    )
