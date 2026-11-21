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

    assert "addPorch" in source
    assert "addStair" in source
    assert "shellBottom" in source or "elevated" in source
    assert "setCamera" in source

    plan = (repo_root / "demo" / "data" / "plan-model.json").read_text()
    assert '"id": "a-door-approach"' in plan
    assert "Court Gate" in plan
    assert '"id": "w-court-s"' in plan
    assert '"id": "a-porch"' in plan
    assert '"component": "porch"' in plan
    assert '"id": "m-porch-depth"' in plan

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

    u14 = (repo_root / "docs" / "design" / "U14-ENTRANCE-PORCH.md").read_text()
    assert "a-porch" in u14
    assert "addPorch" in u14 or "canopy" in u14
    assert "112" in u14
    assert "130" in u14

    assert '"id": "b-court"' in plan
    assert '"id": "c-court"' in plan
    assert '"id": "d-court"' in plan
    assert '"id": "b-door-approach"' in plan
    assert '"id": "w-b-court-s"' in plan
    assert '"id": "m-frontage-b"' in plan
    assert '"id": "path-approach-b"' in plan

    u15 = (repo_root / "docs" / "design" / "U15-STREET-FRONTAGE.md").read_text()
    assert "plot series" in u15.lower() or "frontage" in u15.lower()
    assert "b-court" in u15
    assert "Non-goals" in u15

    assert '"id": "a-stair"' in plan
    assert "a-door-bed" not in plan
    assert '"id": "m-building-line-main"' in plan
    u16 = (repo_root / "docs" / "design" / "U16-HOUSE-STOREY.md").read_text()
    assert "roof" in u16.lower()
    assert "a-stair" in u16
    assert "stacked" in u16.lower() or "storey" in u16.lower()

    assert '"id": "block-south"' in plan
    assert '"id": "block-north"' in plan
    assert '"id": "street-cross"' in plan
    assert '"id": "path-midblock"' in plan
    assert '"id": "n-junc-cross"' in plan
    assert '"id": "m-frontage-rhythm-main"' in plan
    assert '"id": "m-frontage-rhythm-cross"' in plan
    assert '"id": "m-building-line-cross"' in plan
    assert '"id": "n-addr-w"' in plan
    assert '"id": "w-door-approach"' in plan
    u17 = (repo_root / "docs" / "design" / "U17-BLOCK-STREET.md").read_text()
    assert "block-south" in u17
    assert "street-cross" in u17
    u18 = (repo_root / "docs" / "design" / "U18-RHYTHM-ADDRESS.md").read_text()
    assert "rhythm" in u18.lower()
    assert "n-addr-w" in u18 or "workshop" in u18.lower()
    assert (repo_root / ".agents" / "skills" / "threejs-procedural-architecture" / "SKILL.md").is_file()
    assert (repo_root / ".agents" / "skills" / "threejs-procedural-buildings-and-cities" / "SKILL.md").is_file()

    assert '"id": "block-east"' in plan
    assert '"id": "street-east"' in plan
    assert '"id": "district-seed"' in plan
    assert '"id": "lot-e"' in plan
    assert '"id": "n-addr-e"' in plan
    assert '"id": "m-enclosure-main"' in plan
    assert "component === \"district\"" in source or "component === 'district'" in source
    u19 = (repo_root / "docs" / "design" / "U19-SECOND-BLOCK.md").read_text()
    assert "block-east" in u19
    assert "district-seed" in u19
