"""Contract for the Decided WebGL quality slice."""

from __future__ import annotations

from pathlib import Path


def test_webgl_quality_keeps_decided_stages_and_tone_mapping(repo_root: Path) -> None:
    source = (repo_root / "demo" / "webgl.js").read_text()
    assert 'STAGE_ORDER = ["survey", "land", "foundation", "frame", "openings", "patterns"]' in source
    assert "ACESFilmicToneMapping" in source
    assert "SRGBColorSpace" in source
    assert "PCFSoftShadowMap" in source
    assert "makeTiledTexture" in source
    assert "paintGrass" in source
    assert "paintGravel" in source
    assert "paintPlaster" in source
    assert "InstancedMesh" in source
    assert "applySunTime" in source
    assert "EffectComposer" in source
    assert "UnrealBloomPass" in source
    assert "MeshPhysicalMaterial" in source
    assert "buildUnderstory" in source
    assert "buildWalls" in source
    assert "plan.walls" in source
    assert "isGateOpening" in source
    assert "bpy" not in source
    assert "ifcopenshell" not in source

    html = (repo_root / "demo" / "index.html").read_text()
    assert 'id="sun-time"' in html
    assert 'id="bloom-toggle"' in html

    plan = (repo_root / "demo" / "data" / "plan-model.json").read_text()
    assert '"id": "a-door-approach"' in plan
    assert "Court Gate" in plan
    assert '"id": "w-court-s"' in plan

    note = (repo_root / "docs" / "design" / "WEBGL-QUALITY.md").read_text()
    assert "threejs-archviz.vercel.app" in note
    assert "Deferred" in note
    assert "midday" in note.lower() or "sunset" in note.lower()
    assert "110 Main Entrance" in note
    assert "180 Window Place" in note

    u13 = (repo_root / "docs" / "design" / "U13-APPROACH-ENCLOSURE.md").read_text()
    assert "buildWalls" in u13 or "plan.walls" in u13
    assert "110 Main Entrance" in u13
    assert "112" in u13
