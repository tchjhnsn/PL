"""U11: CityJSON LoD0 + TrafficArea parity for the seed district."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CITY = ROOT / "demo" / "data" / "district.city.json"


def test_cityjson_has_traffic_areas_and_lod0() -> None:
    doc = json.loads(CITY.read_text(encoding="utf-8"))
    assert doc["type"] == "CityJSON"
    assert doc["version"] == "2.0"
    objs = doc["CityObjects"]

    assert objs["street-main"]["type"] == "Road"
    assert set(objs["street-main"]["children"]) == {"carriageway-main", "sidewalk-main-n"}
    assert objs["carriageway-main"]["type"] == "TrafficArea"
    assert objs["carriageway-main"]["parents"] == ["street-main"]
    assert objs["carriageway-main"]["attributes"]["function"] == "drivingLane"
    assert objs["sidewalk-main-n"]["attributes"]["function"] == "footpath"

    for oid in ("carriageway-main", "sidewalk-main-n", "lot-a", "green-shared", "pond-a", "house-a"):
        assert oid in objs
        lods = {str(g.get("lod")) for g in objs[oid]["geometry"]}
        assert "0" in lods, f"{oid} missing LoD0"

    trees = [k for k, v in objs.items() if v["type"] == "SolitaryVegetationObject"]
    assert len(trees) >= 5
    assert any(v["type"] == "LandUse" for v in objs.values())
    assert objs["pond-a"]["type"] == "WaterBody"
