"""City fabric kit — multi-neighborhood quarters with green fingers and civic program.

Continuous Country Fingers (not per-block park crumbs). Varied residential heights.
Cite pattern numbers/names only.
"""

from __future__ import annotations

from typing import Any

from pattern_language.kits.frontage_lot import FrontageLotSpec, merge_kit, stamp_frontage_lot
from pattern_language.kits.program_place import ProgramPlaceSpec, stamp_program_place

STREET_W = 14.0
PITCH = 90.0
BLOCK = PITCH - STREET_W


def _ring(x0: float, y0: float, x1: float, y1: float) -> tuple[tuple[float, float], ...]:
    return ((x0, y0), (x1, y0), (x1, y1), (x0, y1))


def _inset(x0: float, y0: float, x1: float, y1: float, m: float) -> tuple[tuple[float, float], ...]:
    return _ring(x0 + m, y0 + m, x1 - m, y1 - m)


def _program_for(col: int, row: int, cols: int, rows: int) -> str | None:
    """Assign program; None → residential. Finger columns handled separately."""
    if col % 4 == 3:
        return "finger"  # continuous park strip, not a cell mass
    if row == rows - 1:
        last = cols - 1 if (cols - 1) % 4 != 3 else cols - 2
        if col in (0, last) and col % 4 != 3:
            return "utility"
    if col == cols // 2 and row == rows // 2:
        return "town_hall"
    if col == cols // 2 + 1 and row == rows // 2 and (cols // 2 + 1) % 4 != 3:
        return "police"
    if col == cols // 2 - 1 and row == rows // 2 and (cols // 2 - 1) % 4 != 3:
        return "bank"
    if col == cols // 2 and row == rows // 2 + 1 and rows // 2 + 1 < rows:
        return "clinic"
    if col % 4 == 0 and row % 3 == 1:
        return "school"
    if col % 4 == 1 and row % 3 == 1:
        return "playground"
    if row == 0 and col % 4 == 0:
        return "shop"
    if row == 0 and col % 4 == 1:
        return "market"
    if row == 0 and col % 4 == 2:
        return "grocery"
    return None


def generate_city_fabric(
    *,
    origin_x: float = 0.0,
    origin_y: float = 100.0,
    cols: int = 12,
    rows: int = 10,
    district_id: str = "district-metro",
) -> dict[str, Any]:
    """Return mergeable plan fragments for a multi-neighborhood city quarter."""
    parts: dict[str, list] = {
        "places": [],
        "walls": [],
        "openings": [],
        "nodes": [],
        "edges": [],
        "measures": [],
        "interfaces": [],
        "interactions": [],
    }
    prefix = district_id.replace("district-", "")
    width = cols * PITCH + STREET_W
    height = rows * PITCH + STREET_W
    x0, y0 = origin_x, origin_y
    x1, y1 = x0 + width, y0 + height

    parts["places"].append(
        {
            "id": district_id,
            "label": "City quarter" if "east" not in prefix else "East city quarter",
            "component": "district",
            "kind": "land",
            "ring": [list(p) for p in _ring(x0, y0, x1, y1)],
            "roles": ["district", "city", "neighborhood"],
            "patterns": [3, 8, 14],
            "role": "City quarter with continuous green fingers and civic program.",
            "parent": None,
            "stage": "survey",
        }
    )

    for r in range(rows + 1):
        sy = y0 + r * PITCH
        sid = f"{prefix}-st-h-{r}"
        parts["places"].append(
            {
                "id": sid,
                "label": f"Street H{r}",
                "component": "street",
                "kind": "void",
                "ring": [list(p) for p in _ring(x0, sy, x1, sy + STREET_W)],
                "roles": ["street", "public", "row", "arterial" if r in (0, rows) else "local"],
                "patterns": [14, 15],
                "role": "East–west city street.",
                "parent": None,
                "enclosure_hw": 0.45,
                "stage": "land",
            }
        )

    for c in range(cols + 1):
        sx = x0 + c * PITCH
        sid = f"{prefix}-st-v-{c}"
        parts["places"].append(
            {
                "id": sid,
                "label": f"Street V{c}",
                "component": "street",
                "kind": "void",
                "ring": [list(p) for p in _ring(sx, y0, sx + STREET_W, y1)],
                "roles": ["street", "public", "row", "arterial" if c in (0, cols) else "local"],
                "patterns": [14, 15],
                "role": "North–south city street.",
                "parent": None,
                "enclosure_hw": 0.45,
                "stage": "land",
            }
        )

    for r in range(rows + 1):
        for c in range(cols + 1):
            parts["nodes"].append(
                {
                    "id": f"n-{prefix}-j-h{r}-v{c}",
                    "x": x0 + c * PITCH + STREET_W / 2,
                    "y": y0 + r * PITCH + STREET_W / 2,
                    "kind": "intersection",
                    "label": f"J{r},{c}",
                }
            )
        for c in range(cols):
            parts["edges"].append(
                {
                    "id": f"e-{prefix}-h{r}-{c}",
                    "a": f"n-{prefix}-j-h{r}-v{c}",
                    "b": f"n-{prefix}-j-h{r}-v{c + 1}",
                    "mode": "vehicle",
                    "hierarchy": "arterial" if r in (0, rows) else "local",
                    "width_m": STREET_W - 2,
                    "directed": False,
                    "label": f"H{r} seg {c}",
                    "polyline": [
                        [x0 + c * PITCH + STREET_W / 2, y0 + r * PITCH + STREET_W / 2],
                        [x0 + (c + 1) * PITCH + STREET_W / 2, y0 + r * PITCH + STREET_W / 2],
                    ],
                }
            )
    for c in range(cols + 1):
        for r in range(rows):
            parts["edges"].append(
                {
                    "id": f"e-{prefix}-v{c}-{r}",
                    "a": f"n-{prefix}-j-h{r}-v{c}",
                    "b": f"n-{prefix}-j-h{r + 1}-v{c}",
                    "mode": "vehicle",
                    "hierarchy": "arterial" if c in (0, cols) else "local",
                    "width_m": STREET_W - 2,
                    "directed": False,
                    "label": f"V{c} seg {r}",
                    "polyline": [
                        [x0 + c * PITCH + STREET_W / 2, y0 + r * PITCH + STREET_W / 2],
                        [x0 + c * PITCH + STREET_W / 2, y0 + (r + 1) * PITCH + STREET_W / 2],
                    ],
                }
            )

    # Continuous Country Fingers — one park strip per finger column (3 City Country Fingers).
    for col in range(cols):
        if col % 4 != 3:
            continue
        bx0 = x0 + STREET_W + col * PITCH
        by0 = y0 + STREET_W
        bx1 = bx0 + BLOCK
        by1 = y0 + STREET_W + rows * PITCH - STREET_W  # top of last block row
        # last block top = y0 + STREET_W + (rows-1)*PITCH + BLOCK = y0 + rows*PITCH
        by1 = y0 + rows * PITCH
        merge_kit(
            parts,
            stamp_program_place(
                ProgramPlaceSpec(
                    key=f"{prefix}-finger-{col}",
                    label=f"Country finger {col // 4 + 1}",
                    program="park",
                    ring=_ring(bx0, by0, bx1, by1),
                    parent=district_id,
                )
            ),
        )

    for row in range(rows):
        for col in range(cols):
            bx0 = x0 + STREET_W + col * PITCH
            by0 = y0 + STREET_W + row * PITCH
            bx1, by1 = bx0 + BLOCK, by0 + BLOCK
            bid = f"{prefix}-block-{col}-{row}"
            prog = _program_for(col, row, cols, rows)

            parts["places"].append(
                {
                    "id": bid,
                    "label": f"Block {col},{row}",
                    "component": "block",
                    "kind": "land",
                    "ring": [list(p) for p in _ring(bx0, by0, bx1, by1)],
                    "roles": ["block"],
                    "patterns": [14, 15],
                    "role": f"City block ({col},{row})"
                    + (f" — {prog}" if prog and prog != "finger" else " — living" if not prog else " — green finger"),
                    "parent": district_id,
                    "stage": "land",
                }
            )

            if prog == "finger":
                continue

            if prog in {
                "school",
                "playground",
                "town_hall",
                "police",
                "bank",
                "utility",
                "market",
                "grocery",
                "shop",
                "clinic",
            }:
                inset = 8.0 if prog in {"town_hall", "school"} else 6.0
                h = {
                    "town_hall": 14.0,
                    "school": 9.0,
                    "bank": 10.0,
                    "police": 8.0,
                    "clinic": 8.0,
                    "market": 7.0,
                    "shop": 5.5,
                    "grocery": 5.0,
                    "utility": 4.5,
                    "playground": 0.0,
                }[prog]
                mass = None if prog == "playground" else _inset(bx0, by0, bx1, by1, inset)
                # Shops: three bay frontage along the street edge of the block
                if prog in {"shop", "grocery", "market"} and mass is not None:
                    bay_w = (bx1 - bx0 - 4) / 3
                    for bi in range(3):
                        sx0 = bx0 + 2 + bi * bay_w
                        sx1 = sx0 + bay_w - 1.5
                        depth = 18 + (bi % 3) * 4
                        bay_prog = "grocery" if prog == "grocery" and bi == 1 else (
                            "market" if prog == "market" else "shop"
                        )
                        merge_kit(
                            parts,
                            stamp_program_place(
                                ProgramPlaceSpec(
                                    key=f"{prefix}-{prog}-{col}-{row}-b{bi}",
                                    label=f"{bay_prog.replace('_', ' ').title()} {col},{row}.{bi + 1}",
                                    program=bay_prog,
                                    ring=_ring(sx0, by0, sx1, by0 + depth + 8),
                                    mass_ring=_ring(sx0 + 1, by0 + 5, sx1 - 1, by0 + depth),
                                    height_m=h + bi * 0.4,
                                    parent=bid,
                                )
                            ),
                        )
                    continue

                merge_kit(
                    parts,
                    stamp_program_place(
                        ProgramPlaceSpec(
                            key=f"{prefix}-{prog}-{col}-{row}",
                            label={
                                "school": f"School {col},{row}",
                                "playground": f"Playground {col},{row}",
                                "town_hall": "Local Town Hall",
                                "police": "Police station",
                                "bank": "Bank",
                                "utility": f"Utility yard {col},{row}",
                                "clinic": "Health center",
                            }[prog],
                            program=prog,
                            ring=_ring(bx0, by0, bx1, by1),
                            mass_ring=mass,
                            height_m=h,
                            parent=bid,
                        )
                    ),
                )
                continue

            # Residential: 2–3 lots, varied heights, no garden walls (city massing LOD)
            mid = (bx0 + bx1) / 2
            street_id = f"{prefix}-st-h-{row}"
            sw_y = by0 - STREET_W / 2
            splits = (
                (bx0, mid - 1.0, f"{prefix}-r{col}{row}a", 5.5 + (col + row) % 3),
                (mid + 1.0, bx1, f"{prefix}-r{col}{row}b", 7.0 + (col * 2 + row) % 4),
            )
            for i, (lx0, lx1, key, ht) in enumerate(splits):
                court_d = 4.5 + ((col + row + i) % 3)
                merge_kit(
                    parts,
                    stamp_frontage_lot(
                        FrontageLotSpec(
                            key=key,
                            label=key.split("-")[-1].upper(),
                            block_id=bid,
                            street_id=street_id,
                            lot_ring=_ring(lx0, by0, lx1, by1),
                            found_ring=_ring(lx0 + 1.5, by0 + court_d, lx1 - 1.5, by1 - 2),
                            court_ring=_ring(lx0 + 1.5, by0, lx1 - 1.5, by0 + court_d),
                            mass_ring=_ring(lx0 + 1.5, by0 + court_d, lx1 - 1.5, by1 - 2),
                            gate_xy=((lx0 + lx1) / 2, by0),
                            path_ring=None,
                            mass_height_m=ht,
                            land_use="living",
                            sidewalk_place=street_id,
                            sidewalk_y=sw_y,
                            with_walls=False,
                        )
                    ),
                )

    # Country fringe south of the quarter
    country_d = 48.0
    cy0, cy1 = y1, y1 + country_d
    merge_kit(
        parts,
        stamp_program_place(
            ProgramPlaceSpec(
                key=f"{prefix}-country",
                label="Country fringe",
                program="park",
                ring=_ring(x0, cy0, x1, cy1),
                parent=district_id,
            )
        ),
    )
    parts["places"].append(
        {
            "id": f"{prefix}-country-road",
            "label": "Country road",
            "component": "street",
            "kind": "void",
            "ring": [list(p) for p in _ring(x0, cy1, x1, cy1 + 10.0)],
            "roles": ["street", "public", "row", "country", "local"],
            "patterns": [3, 14],
            "role": "Country road along the city fringe.",
            "parent": None,
            "enclosure_hw": 0.12,
            "stage": "land",
        }
    )

    parts["measures"].append(
        {
            "id": f"m-{prefix}-width",
            "label": "City quarter width",
            "a": [x0, y0 + height / 2],
            "b": [x1, y0 + height / 2],
            "value_m": round(width, 1),
            "kind": "width",
            "of": district_id,
            "patterns": [3, 14],
        }
    )
    parts["measures"].append(
        {
            "id": f"m-{prefix}-depth",
            "label": "City quarter depth",
            "a": [x0 + width / 2, y0],
            "b": [x0 + width / 2, y1],
            "value_m": round(height, 1),
            "kind": "depth",
            "of": district_id,
            "patterns": [3, 14],
        }
    )
    return parts
