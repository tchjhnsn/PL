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
    assert "InstancedMesh" in source
    assert "bpy" not in source
    assert "ifcopenshell" not in source

    note = (repo_root / "docs" / "design" / "WEBGL-QUALITY.md").read_text()
    assert "threejs-archviz.vercel.app" in note
    assert "Deferred" in note
    assert "110 Main Entrance" in note
    assert "180 Window Place" in note
