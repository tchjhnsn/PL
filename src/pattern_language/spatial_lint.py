"""Plan geometry lint: overlap, sit-on containment, clearance.

Pure AABB helpers for axis-aligned rings (seed district). Touching edges
are allowed; positive-area overlap is not. No IFC / bpy.
"""

from __future__ import annotations

from typing import Any, Iterable

EPS = 1e-6


def aabb(ring: Iterable[Iterable[float]]) -> tuple[float, float, float, float]:
    xs = [float(p[0]) for p in ring]
    ys = [float(p[1]) for p in ring]
    return min(xs), min(ys), max(xs), max(ys)


def area(box: tuple[float, float, float, float]) -> float:
    xmin, ymin, xmax, ymax = box
    return max(0.0, xmax - xmin) * max(0.0, ymax - ymin)


def overlap_area(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    return max(0.0, ix1 - ix0) * max(0.0, iy1 - iy0)


def overlaps(a_ring: Iterable[Iterable[float]], b_ring: Iterable[Iterable[float]]) -> bool:
    return overlap_area(aabb(a_ring), aabb(b_ring)) > EPS


def covered_by(inner: Iterable[Iterable[float]], outer: Iterable[Iterable[float]]) -> bool:
    """Boundary-inclusive containment of AABB(inner) inside AABB(outer)."""
    ix0, iy0, ix1, iy1 = aabb(inner)
    ox0, oy0, ox1, oy1 = aabb(outer)
    return (
        ix0 >= ox0 - EPS
        and iy0 >= oy0 - EPS
        and ix1 <= ox1 + EPS
        and iy1 <= oy1 + EPS
    )


def separation_m(a_ring: Iterable[Iterable[float]], b_ring: Iterable[Iterable[float]]) -> float:
    """Clear gap between AABBs; 0 when they touch or overlap."""
    ax0, ay0, ax1, ay1 = aabb(a_ring)
    bx0, by0, bx1, by1 = aabb(b_ring)
    dx = max(0.0, max(ax0 - bx1, bx0 - ax1))
    dy = max(0.0, max(ay0 - by1, by0 - ay1))
    if dx > 0 and dy > 0:
        return (dx * dx + dy * dy) ** 0.5
    return max(dx, dy)


def _place_map(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {p["id"]: p for p in plan.get("places", []) if p.get("id")}


def _peer_ids(places: list[dict[str, Any]], *, kinds: set[str] | None = None, roles: set[str] | None = None) -> list[str]:
    out = []
    for p in places:
        if kinds is not None and p.get("kind") not in kinds:
            continue
        if roles is not None:
            pr = set(p.get("roles") or [])
            if not pr.intersection(roles):
                continue
        out.append(p["id"])
    return out


def lint_plan(plan: dict[str, Any]) -> list[str]:
    """Return human-readable errors (empty when the plan passes)."""
    errors: list[str] = []
    places = list(plan.get("places") or [])
    by_id = _place_map(plan)

    def ring_of(pid: str) -> list | None:
        p = by_id.get(pid)
        if not p or not p.get("ring"):
            return None
        return p["ring"]

    # Peer parcels / lots must not area-overlap.
    lots = _peer_ids(places, roles={"lot", "parcel"})
    for i, a in enumerate(lots):
        ra = ring_of(a)
        if ra is None:
            continue
        for b in lots[i + 1 :]:
            rb = ring_of(b)
            if rb is None:
                continue
            if overlaps(ra, rb):
                errors.append(f"overlap: lots {a} and {b}")

    # Shared green / open space must not area-overlap parcels.
    greens = [p["id"] for p in places if p.get("id") == "green-shared" or "green" in (p.get("roles") or [])]
    for g in greens:
        rg = ring_of(g)
        if rg is None:
            continue
        for lot in lots:
            rl = ring_of(lot)
            if rl is None:
                continue
            if overlaps(rg, rl):
                errors.append(f"overlap: {g} and lot {lot}")

    # Foundations must not area-overlap each other.
    pads = _peer_ids(places, kinds={"foundation"})
    for i, a in enumerate(pads):
        ra = ring_of(a)
        if ra is None:
            continue
        for b in pads[i + 1 :]:
            rb = ring_of(b)
            if rb is None:
                continue
            if overlaps(ra, rb):
                errors.append(f"overlap: foundations {a} and {b}")

    # Occupied shells (rooms + massing solids) must not area-overlap peers
    # on the same storey. Stacked storeys (upper floor ≥ lower ceiling) may share XY.
    by_id = {p["id"]: p for p in places if "id" in p}

    def floor_elev(pid: str) -> float:
        p = by_id.get(pid) or {}
        v = p.get("floor_elevation_m")
        return float(v) if isinstance(v, (int, float)) else 0.0

    def clear_height(pid: str) -> float:
        p = by_id.get(pid) or {}
        v = p.get("height_m")
        return float(v) if isinstance(v, (int, float)) else 0.0

    def stacked_ok(a: str, b: str) -> bool:
        fa, fb = floor_elev(a), floor_elev(b)
        if fa > fb + EPS:
            return fa + EPS >= fb + clear_height(b)
        if fb > fa + EPS:
            return fb + EPS >= fa + clear_height(a)
        return False

    shells = [
        p["id"]
        for p in places
        if p.get("kind") in {"room", "solid"}
        or (p.get("kind") == "void" and "balcony" in (p.get("roles") or []))
    ]
    for i, a in enumerate(shells):
        ra = ring_of(a)
        if ra is None:
            continue
        for b in shells[i + 1 :]:
            rb = ring_of(b)
            if rb is None:
                continue
            if overlaps(ra, rb) and not stacked_ok(a, b):
                errors.append(f"overlap: shells {a} and {b}")

    for ix in plan.get("interactions") or []:
        kind = ix.get("kind")
        a, b = ix.get("a"), ix.get("b")
        ra, rb = ring_of(a or ""), ring_of(b or "")
        if ra is None or rb is None:
            errors.append(f"interaction {ix.get('id')}: missing place {a!r} or {b!r}")
            continue
        if kind == "sit-on":
            if not covered_by(ra, rb):
                errors.append(f"sit-on: {a} not contained by {b}")
        elif kind == "clearance":
            need = float(ix.get("min_m") or 0.0)
            gap = separation_m(ra, rb)
            if gap + EPS < need:
                errors.append(f"clearance: {a}–{b} gap {gap:.3f} m < {need} m")

    return errors
