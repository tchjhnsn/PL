"""Twelve preserving steps, then the pass-house report."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from pattern_language.catalog import load_catalog
from pattern_language.checker import report_json, run
from pattern_language.conditions.evidence import CheckError
from pattern_language.parameters import load_project
from pattern_language.runs import SEED_SEQUENCE, latest_report, record_run, report_lines
from pattern_language.step import build_step, step_json
from pattern_language.topology import TopologyError, prefix, read_ifc, to_json

# Empirical satisfied lists from prefix + pl check on the seed project.
# They match the U7 snapshot table. No row was adjusted.
_SATISFIED = (
    (),
    (105, 106, 107),
    (105, 106, 107),
    (105, 106, 107),
    (105, 106, 107),
    (105, 106, 107, 112, 130),
    (105, 106, 107, 112, 127, 128, 130, 190),
    (105, 106, 107, 112, 127, 128, 130, 190),
    (105, 106, 107, 112, 127, 128, 130, 190),
    (105, 106, 107, 112, 127, 128, 130, 159, 190),
    (105, 106, 107, 112, 127, 128, 130, 159, 167, 190),
    (105, 106, 107, 112, 127, 128, 130, 159, 167, 190),
    (105, 106, 107, 112, 127, 128, 130, 159, 167, 190),
)

_UNCHANGED = {4, 11, 12}

_REPORT_LINES = (
    "105 South Facing Outdoors: satisfied",
    "106 Positive Outdoor Space: satisfied",
    "107 Wings of Light: satisfied",
    "110 Main Entrance: needs_judgment",
    "112 Entrance Transition: satisfied",
    "127 Intimacy Gradient: satisfied",
    "128 Indoor Sunlight: satisfied",
    "130 Entrance Room: satisfied",
    "159 Light on Two Sides of Every Room: satisfied",
    "167 Six-Foot Balcony: satisfied",
    "180 Window Place: needs_judgment",
    "190 Ceiling Height Variety: satisfied",
)


@pytest.fixture(scope="module")
def seed_run(tmp_path_factory: pytest.TempPathFactory, repo_root: Path) -> Path:
    directory = tmp_path_factory.mktemp("seed-run")
    return record_run(directory, root=repo_root)


def test_prefix_rejects_an_unknown_name() -> None:
    with pytest.raises(TopologyError, match="unknown name"):
        prefix(frozenset({"street", "attic"}), frozenset())


def test_record_run_ledger(seed_run: Path, repo_root: Path) -> None:
    for index in range(13):
        assert (seed_run / f"model-{index:02d}.ifc").is_file()
    assert (seed_run / "report.json").is_file()

    catalog = load_catalog(repo_root)
    project = load_project(
        repo_root / "projects" / "seed-house.json",
        schema_path=repo_root / "schema" / "projects.schema.json",
    )
    step_schema = json.loads((repo_root / "schema" / "step.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(step_schema)
    steps: list[dict] = []
    for index, pattern in enumerate(SEED_SEQUENCE, start=1):
        path = seed_run / f"step-{index:02d}.json"
        assert path.is_file()
        text = path.read_text(encoding="utf-8")
        payload = json.loads(text)
        validator.validate(payload)
        before = f"model-{index - 1:02d}.ifc"
        after = f"model-{index:02d}.ifc"
        built = build_step(
            catalog,
            project,
            seed_run / before,
            seed_run / after,
            pattern=pattern,
            before_file=before,
            after_file=after,
            schema_path=repo_root / "schema" / "step.schema.json",
        )
        assert text == step_json(built)
        assert payload["pattern"] == pattern
        assert payload["preserved"] is True
        assert payload["before"]["file"] == before
        assert payload["after"]["file"] == after
        assert tuple(payload["satisfied_before"]) == _SATISFIED[index - 1]
        assert tuple(payload["satisfied_after"]) == _SATISFIED[index]
        assert set(payload["satisfied_before"]) <= set(payload["satisfied_after"])
        assert 110 not in payload["satisfied_before"]
        assert 110 not in payload["satisfied_after"]
        assert 180 not in payload["satisfied_before"]
        assert 180 not in payload["satisfied_after"]
        steps.append(payload)

    assert [item["pattern"] for item in steps] == list(SEED_SEQUENCE)
    # Step 10 keeps 105 South Facing Outdoors. Dropping the balcony is not this table.
    assert steps[9]["satisfied_after"] == [105, 106, 107, 112, 127, 128, 130, 159, 167, 190]
    for index in range(len(steps) - 1):
        assert steps[index]["after"]["sha256"] == steps[index + 1]["before"]["sha256"]

    graphs = [to_json(read_ifc(seed_run / f"model-{index:02d}.ifc")) for index in range(13)]
    for index in range(1, 13):
        if index in _UNCHANGED:
            assert graphs[index] == graphs[index - 1]
        else:
            assert graphs[index] != graphs[index - 1]
    house = to_json(read_ifc(repo_root / "fixtures" / "pass-house.ifc"))
    assert graphs[12] == house

    final = json.loads((seed_run / "report.json").read_text(encoding="utf-8"))
    pass_report = run(
        catalog,
        project,
        repo_root / "fixtures" / "pass-house.ifc",
        model_file="fixtures/pass-house.ifc",
        schema_path=repo_root / "schema" / "check-report.schema.json",
    )
    pass_body = json.loads(report_json(pass_report))
    assert final["project"] == pass_body["project"] == "seed-house"
    assert final["satisfied"] == pass_body["satisfied"] == [
        105,
        106,
        107,
        112,
        127,
        128,
        130,
        159,
        167,
        190,
    ]
    assert final["instances"] == pass_body["instances"]
    assert final["model"]["file"] == "model-12.ifc"
    assert final["model"]["sha256"] == steps[11]["after"]["sha256"]
    assert final["model"]["file"] != pass_body["model"]["file"]
    by_status = {item["pattern"]: item["status"] for item in final["instances"]}
    assert by_status[110] == "needs_judgment"
    assert by_status[180] == "needs_judgment"
    assert 110 not in final["satisfied"]
    assert 180 not in final["satisfied"]
    names = {pattern.number: pattern.name for pattern in catalog.patterns}
    assert report_lines(final, names) == _REPORT_LINES


def test_latest_report_picks_the_later_stamp(tmp_path: Path) -> None:
    runs = tmp_path / "runs"
    early = runs / "20261119T090000Z"
    late = runs / "20261119T100000Z"
    newer = runs / "20261119T110000Z"
    early.mkdir(parents=True)
    late.mkdir()
    newer.mkdir()
    (early / "report.json").write_text("{}\n", encoding="utf-8")
    (late / "report.json").write_text("{}\n", encoding="utf-8")
    assert latest_report(runs) == late / "report.json"
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(CheckError, match="no report"):
        latest_report(empty)


def test_drive_run_check(repo_root: Path) -> None:
    before = {path.name for path in (repo_root / "runs").iterdir()}
    module = _load_module(repo_root / "scripts" / "drive_run.py", "drive_run")
    assert module.main(["--check"]) == 0
    after = {path.name for path in (repo_root / "runs").iterdir()}
    assert before == after


def test_session_transitions(repo_root: Path) -> None:
    bridge = _load_module(
        repo_root / "adapters" / "blender" / "bridge.py",
        "pattern_language_blender_bridge",
    )
    session = bridge.Session()
    assert session.state == "Disconnected"
    assert session.act("connect") == "Connected"
    assert session.act("request_check") == "Exporting"
    assert session.act("exported") == "Checking"
    assert session.act("reported") == "ShowingReport"
    assert session.act("idle") == "Connected"
    assert session.act("disconnect") == "Disconnected"
    with pytest.raises(KeyError):
        session.act("request_check")
    session.act("connect")
    session.act("request_check")
    session.act("exported")
    session.act("reported")
    session.act("edit")
    assert session.act("done") == "Exporting"
    assert session.act("fail") == "Error"
    assert session.act("shown") == "Connected"
    assert "bpy" not in sys.modules
    assert "bonsai" not in sys.modules


def test_load_snapshot_without_bonsai(repo_root: Path) -> None:
    bridge = _load_module(
        repo_root / "adapters" / "blender" / "bridge.py",
        "pattern_language_blender_bridge_load",
    )
    with pytest.raises(bridge.BridgeError, match="Bonsai is not enabled"):
        bridge.load_snapshot(Path("model.ifc"))


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
