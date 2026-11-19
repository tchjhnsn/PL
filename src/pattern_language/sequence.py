"""Python twin of ``Sequence.lean``.

``index_before`` and ``order_ok`` are the Bool procedures. ``sequence`` emits
the project selection in ascending number order when that order is valid on
the induced smaller-edges. This module does not import the checker.
"""

from __future__ import annotations

from collections.abc import Sequence

from pattern_language.catalog import Catalog
from pattern_language.parameters import Project


class SequenceError(Exception):
    """Missing pattern, pattern outside the project, or ascending order
    that fails order_ok. The CLI prints one line and exits 2.
    """


def index_before(order: Sequence[int], earlier: int, later: int) -> bool:
    """First index of earlier is strictly less than first index of later.

    False when either number is absent. Matches Sequence.indexBefore,
    including the match arm that returns false.
    """
    earlier_at = _first_index(order, earlier)
    later_at = _first_index(order, later)
    if earlier_at is None or later_at is None:
        return False
    return earlier_at < later_at


def order_ok(order: Sequence[int], edges: Sequence[tuple[int, int]]) -> bool:
    """True when every edge (q, p) has index_before(order, p, q).

    Matches Sequence.orderOk. An empty edge list is true.
    """
    return all(index_before(order, p, q) for q, p in edges)


def smaller_edges(
    catalog: Catalog, selected: Sequence[int]
) -> tuple[tuple[int, int], ...]:
    """Induced (q, p) pairs.

    p lists q in smaller, both numbers are in selected, and q is in
    catalog.by_number. Same orientation as Buildings.smallerEdges.
    Patterns are visited in ascending number order, and each pattern's
    smaller tuple is visited in stored order.
    """
    chosen = set(selected)
    edges: list[tuple[int, int]] = []
    for number in sorted(chosen):
        pattern = catalog.by_number.get(number)
        if pattern is None:
            continue
        for smaller in pattern.smaller:
            if smaller in chosen and smaller in catalog.by_number:
                edges.append((smaller, number))
    return tuple(edges)


def sequence(catalog: Catalog, project: Project) -> tuple[int, ...]:
    """Selected numbers in ascending order, when that order is valid.

    Raise SequenceError when a selected number is missing from the catalog.
    Raise SequenceError("sequence is not valid") when order_ok is false
    on smaller_edges(catalog, the ascending tuple).
    """
    order = tuple(sorted(project.patterns))
    for number in order:
        if number not in catalog.by_number:
            raise SequenceError(f"missing pattern: {number}")
    if not order_ok(order, smaller_edges(catalog, order)):
        raise SequenceError("sequence is not valid")
    return order


def _first_index(order: Sequence[int], number: int) -> int | None:
    for index, item in enumerate(order):
        if item == number:
            return index
    return None
