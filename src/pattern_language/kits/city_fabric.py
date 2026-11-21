"""Procedural city fabric — neighborhoods, green fingers, civic program.

This is how we grow a metropolis: stamp blocks and program places under lint,
cite town-scale pattern numbers/names only, never book text.
"""

from __future__ import annotations

from typing import Any

from pattern_language.kits.frontage_lot import FrontageLotSpec, merge_kit, stamp_frontage_lot
from pattern_language.kits.program_place import ProgramPlaceSpec, stamp_program_place

# Block module: street + buildable cell (metres).
STREET_W = 12.0
PITCH = 84.0  # street + block ≈ 72 m lots
BLOCK = PITCH - STREET_W


def _ring(x0: float, y0: float, x1: float, y1: float) -> tuple[tuple[float, float], ...]:
    return ((x0, y0), (x1, y0), (x1, y1), (x0, y1))


def _inset(x0: float, y0: float, x1: float, y1: float, m: float) -> tuple[tuple[float, float], ...]:
    return _ring(x0 + m, y0 + m, x1 - m, y1 - m)


def _program_for(col: int, row: int, cols: int, rows: int) -> str | None:
    """Assign civic/commercial program; None → residential frontage pair."""
    # Utilities on the metro edge (before park so fingers don't eat them).
    if row == rows - 1 and col in (0, cols - 1) and col % 4 != 3:
        return "utility"
    if row == rows - 1 and col == cols - 2 and (cols - 1) % 4 == 3:
        return "utility"
    # North–south country fingers (City Country Fingers) every 4th column.
    if col % 4 == 3:
        return "park"
    # City center civic cluster
    if col == cols // 2 and row == rows // 2:
        return "town_hall"
    if col == cols // 2 + 1 and row == rows // 2:
        return "police"
    if col == cols // 2 - 1 and row == rows // 2:
        return "bank"
    if col == cols // 2 and row == rows // 2 + 1:
        return "clinic"
    # School + playground per neighborhood (2×2 of blocks)
    if col % 4 == 0 and row % 3 == 1:
        return "school"
    if col % 4 == 1 and row % 3 == 1:
        return "playground"
    # Shopping street on row 0 spine (between green fingers)
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
    origin_y: float = 90.0,
    cols: int = 8,
    rows: int = 6,
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

    width = cols * PITCH + STREET_W
    height = rows * PITCH + STREET_W
    x0, y0 = origin_x, origin_y
    x1, y1 = x0 + width, y0 + height

    prefix = district_id.replace("district-", "")
    parts["places"].append(
        {
            "id": district_id,
            "label": "Metro Quarter" if prefix == "metro" else f"Metro Quarter ({prefix})",
            "component": "district",
            "kind": "land",
            "ring": [list(p) for p in _ring(x0, y0, x1, y1)],
            "roles": ["district", "neighborhood", "city"],
            "patterns": [3, 8, 14],
            "role": "Multi-neighborhood city quarter with green fingers and civic program.",
            "parent": None,
            "stage": "survey",
        }
    )

    # Arterial streets — horizontal
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
                "roles": ["street", "public", "row", "local" if r not in (0, rows) else "arterial"],
                "patterns": [14, 15],
                "role": "East–west city street.",
                "parent": None,
                "enclosure_hw": 0.4,
                "stage": "land",
            }
        )
        parts["nodes"].append(
            {
                "id": f"n-{sid}",
                "x": (x0 + x1) / 2,
                "y": sy + STREET_W / 2,
                "kind": "intersection",
                "label": f"H{r}",
            }
        )

    # Arterial streets — vertical
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
                "roles": ["street", "public", "row", "local" if c not in (0, cols) else "arterial"],
                "patterns": [14, 15],
                "role": "North–south city street.",
                "parent": None,
                "enclosure_hw": 0.4,
                "stage": "land",
            }
        )
        parts["nodes"].append(
            {
                "id": f"n-{sid}",
                "x": sx + STREET_W / 2,
                "y": (y0 + y1) / 2,
                "kind": "intersection",
                "label": f"V{c}",
            }
        )

    # Network: connect street centers into a grid
    for r in range(rows + 1):
        for c in range(cols):
            ax = x0 + c * PITCH + STREET_W / 2
            y = y0 + r * PITCH + STREET_W / 2
            parts["nodes"].append(
                {
                    "id": f"n-{prefix}-j-h{r}-v{c}",
                    "x": ax,
                    "y": y,
                    "kind": "intersection",
                    "label": f"J{r},{c}",
                }
            )
        parts["nodes"].append(
            {
                "id": f"n-{prefix}-j-h{r}-v{cols}",
                "x": x0 + cols * PITCH + STREET_W / 2,
                "y": y0 + r * PITCH + STREET_W / 2,
                "kind": "intersection",
                "label": f"J{r},{cols}",
            }
        )
        for c in range(cols):
            na = f"n-{prefix}-j-h{r}-v{c}"
            nb = f"n-{prefix}-j-h{r}-v{c + 1}"
            parts["edges"].append(
                {
                    "id": f"e-{prefix}-h{r}-{c}",
                    "a": na,
                    "b": nb,
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
            na = f"n-{prefix}-j-h{r}-v{c}"
            nb = f"n-{prefix}-j-h{r + 1}-v{c}"
            parts["edges"].append(
                {
                    "id": f"e-{prefix}-v{c}-{r}",
                    "a": na,
                    "b": nb,
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

    # Blocks + program
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
                    "role": f"City block ({col},{row})" + (f" — {prog}" if prog else " — living"),
                    "parent": district_id,
                    "stage": "land",
                }
            )

            if prog == "park":
                merge_kit(
                    parts,
                    stamp_program_place(
                        ProgramPlaceSpec(
                            key=f"{prefix}-park-{col}-{row}",
                            label=f"Green finger {col},{row}",
                            program="park",
                            ring=_ring(bx0, by0, bx1, by1),
                            parent=bid,
                        )
                    ),
                )
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
                mass = _inset(bx0, by0, bx1, by1, 6.0)
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
                                "market": f"Market {col},{row}",
                                "grocery": f"Corner grocery {col},{row}",
                                "shop": f"Shops {col},{row}",
                                "clinic": "Health center",
                            }[prog],
                            program=prog,
                            ring=_ring(bx0, by0, bx1, by1),
                            mass_ring=None if prog in {"playground"} else mass,
                            parent=bid,
                        )
                    ),
                )
                continue

            # Residential: two frontage lots facing the street south of the block
            mid = (bx0 + bx1) / 2
            gap = 2.0
            street_id = f"{prefix}-st-h-{row}"
            sw_y = by0 - STREET_W / 2
            for i, (lx0, lx1, key) in enumerate(
                (
                    (bx0, mid - gap / 2, f"{prefix}-r{col}{row}a"),
                    (mid + gap / 2, bx1, f"{prefix}-r{col}{row}b"),
                )
            ):
                court_d = 5.0
                merge_kit(
                    parts,
                    stamp_frontage_lot(
                        FrontageLotSpec(
                            key=key,
                            label=key.upper(),
                            block_id=bid,
                            street_id=street_id,
                            lot_ring=_ring(lx0, by0, lx1, by1),
                            found_ring=_ring(lx0 + 2, by0 + court_d, lx1 - 2, by1 - 2),
                            court_ring=_ring(lx0 + 2, by0, lx1 - 2, by0 + court_d),
                            mass_ring=_ring(lx0 + 2, by0 + court_d, lx1 - 2, by1 - 2),
                            gate_xy=((lx0 + lx1) / 2, by0),
                            path_ring=None,
                            mass_height_m=6.0 + (i % 2) * 0.5,
                            land_use="living",
                            sidewalk_place=street_id,
                            sidewalk_y=sw_y,
                        )
                    ),
                )

    # Country edge south of the quarter — continuous green that the fingers meet
    # (3 City Country Fingers / countryside fringe).
    country_d = 36.0
    cy0, cy1 = y1, y1 + country_d
    parts["places"].append(
        {
            "id": f"{prefix}-country-south",
            "label": "Country fringe",
            "component": "park",
            "kind": "void",
            "ring": [list(p) for p in _ring(x0, cy0, x1, cy1)],
            "roles": ["park", "green", "grass", "outdoor", "public", "country"],
            "patterns": [3, 60],
            "role": "Countryside fringe meeting the city fingers.",
            "parent": district_id,
            "stage": "land",
        }
    )
    parts["places"].append(
        {
            "id": f"{prefix}-country-road",
            "label": "Country road",
            "component": "street",
            "kind": "void",
            "ring": [list(p) for p in _ring(x0, cy1, x1, cy1 + 8.0)],
            "roles": ["street", "public", "row", "country", "local"],
            "patterns": [3, 14],
            "role": "Country road along the metro fringe.",
            "parent": None,
            "enclosure_hw": 0.15,
            "stage": "land",
        }
    )

    parts["measures"].append(
        {
            "id": f"m-{prefix}-width",
            "label": "Metro quarter width",
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
            "label": "Metro quarter depth",
            "a": [x0 + width / 2, y0],
            "b": [x0 + width / 2, y1],
            "value_m": round(height, 1),
            "kind": "depth",
            "of": district_id,
            "patterns": [3, 14],
        }
    )

    return parts
