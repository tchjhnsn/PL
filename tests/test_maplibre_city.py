"""U20: MapLibre city surface over district GeoJSON."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo"


def test_maplibre_city_surface_files() -> None:
    html = (DEMO / "map.html").read_text(encoding="utf-8")
    js = (DEMO / "map.js").read_text(encoding="utf-8")
    assert "maplibre-gl" in html
    assert 'id="map"' in html
    assert "City map" in html or "Seed City" in html
    assert "SpatialStructure" not in html
    assert "MapLibre figure" not in html
    assert "district.geojson" in js
    assert "maplibregl.Map" in js
    assert "__plMap" in js
    assert "fill-extrusion" not in js  # LoD0 figure–ground, not extruded twin

    index = (DEMO / "index.html").read_text(encoding="utf-8")
    assert "map.html" in index

    geo = json.loads((DEMO / "data" / "district.geojson").read_text(encoding="utf-8"))
    assert geo["type"] == "FeatureCollection"
    assert len(geo["features"]) >= 40
    comps = {f["properties"].get("component") for f in geo["features"]}
    assert "street" in comps
    assert "parcel" in comps or "block" in comps

    note = (ROOT / "docs" / "design" / "U20-MAPLIBRE-CITY.md").read_text(encoding="utf-8")
    assert "MapLibre" in note
    assert "Non-goals" in note
