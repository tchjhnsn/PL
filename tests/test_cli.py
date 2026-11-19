"""Exit codes for ``pl check``, ``pl sequence``, and ``pl step``."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from pattern_language.cli import main


def test_check_pass_house_exits_zero(monkeypatch, capsys, repo_root: Path) -> None:
    monkeypatch.chdir(repo_root)
    code = main(
        [
            "check",
            "fixtures/pass-house.ifc",
            "--language",
            "projects/seed-house.json",
            "--root",
            str(repo_root),
        ]
    )
    captured = capsys.readouterr()
    assert code == 0
    assert captured.err == ""
    report = json.loads(captured.out)
    _validate(repo_root, report)
    assert report["project"] == "seed-house"
    assert report["model"]["file"] == "fixtures/pass-house.ifc"
    assert report["satisfied"] == [105, 106, 107, 112, 127, 128, 130, 159, 167, 190]


def test_check_fail_house_exits_one(monkeypatch, capsys, repo_root: Path) -> None:
    monkeypatch.chdir(repo_root)
    code = main(
        [
            "check",
            "fixtures/fail-house.ifc",
            "--language",
            "projects/seed-house.json",
            "--root",
            str(repo_root),
        ]
    )
    captured = capsys.readouterr()
    assert code == 1
    assert captured.err == ""
    report = json.loads(captured.out)
    _validate(repo_root, report)
    assert report["satisfied"] == []
    judged = [item for item in report["instances"] if item["status"] == "needs_judgment"]
    assert [item["pattern"] for item in judged] == [110, 180]


def test_unknown_commands_exit_two(capsys) -> None:
    assert main([]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "unknown command\n"
    assert main(["nope"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "unknown command\n"


def test_bare_sequence_and_step_print_usage(capsys) -> None:
    assert main(["sequence"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "usage: pl sequence <project.json>\n"
    assert main(["step"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == (
        "usage: pl step <before.ifc> <after.ifc> "
        "--language <project.json> --pattern <n>\n"
    )


def test_sequence_seed_exits_zero(monkeypatch, capsys, repo_root: Path) -> None:
    monkeypatch.chdir(repo_root)
    code = main(
        ["sequence", "projects/seed-house.json", "--root", str(repo_root)]
    )
    captured = capsys.readouterr()
    assert code == 0
    assert captured.err == ""
    assert json.loads(captured.out) == [
        105,
        106,
        107,
        110,
        112,
        127,
        128,
        130,
        159,
        167,
        180,
        190,
    ]
    assert captured.out == json.dumps(json.loads(captured.out), indent=2) + "\n"


def test_step_pass_then_fail_exits_one(monkeypatch, capsys, repo_root: Path) -> None:
    monkeypatch.chdir(repo_root)
    code = main(
        [
            "step",
            "fixtures/pass-house.ifc",
            "fixtures/fail-house.ifc",
            "--language",
            "projects/seed-house.json",
            "--pattern",
            "112",
            "--root",
            str(repo_root),
        ]
    )
    captured = capsys.readouterr()
    assert code == 1
    assert captured.err == ""
    step = json.loads(captured.out)
    _validate_step(repo_root, step)
    assert step["preserved"] is False
    assert step["pattern"] == 112
    assert step["satisfied_before"] == [105, 106, 107, 112, 127, 128, 130, 159, 167, 190]
    assert step["satisfied_after"] == []


def test_step_same_house_twice_exits_zero(monkeypatch, capsys, repo_root: Path) -> None:
    monkeypatch.chdir(repo_root)
    code = main(
        [
            "step",
            "fixtures/pass-house.ifc",
            "fixtures/pass-house.ifc",
            "--language",
            "projects/seed-house.json",
            "--pattern",
            "105",
            "--root",
            str(repo_root),
        ]
    )
    captured = capsys.readouterr()
    assert code == 0
    assert captured.err == ""
    step = json.loads(captured.out)
    _validate_step(repo_root, step)
    assert step["preserved"] is True
    assert step["before"]["sha256"] == step["after"]["sha256"]


def test_step_writes_out_and_stdout(monkeypatch, capsys, tmp_path: Path, repo_root: Path) -> None:
    monkeypatch.chdir(repo_root)
    out = tmp_path / "step.json"
    code = main(
        [
            "step",
            "fixtures/pass-house.ifc",
            "fixtures/fail-house.ifc",
            "--language",
            "projects/seed-house.json",
            "--pattern",
            "112",
            "--root",
            str(repo_root),
            "--out",
            str(out),
        ]
    )
    captured = capsys.readouterr()
    assert code == 1
    assert captured.out == out.read_text(encoding="utf-8")
    assert captured.out.endswith("\n")
    assert json.loads(captured.out)["preserved"] is False


def test_step_rejects_pattern_outside_the_language(
    monkeypatch, capsys, repo_root: Path
) -> None:
    monkeypatch.chdir(repo_root)
    code = main(
        [
            "step",
            "fixtures/pass-house.ifc",
            "fixtures/pass-house.ifc",
            "--language",
            "projects/seed-house.json",
            "--pattern",
            "99",
            "--root",
            str(repo_root),
        ]
    )
    captured = capsys.readouterr()
    assert code == 2
    assert captured.out == ""
    assert captured.err == "pattern is not in language: 99\n"


def test_check_writes_out_and_stdout(monkeypatch, capsys, tmp_path: Path, repo_root: Path) -> None:
    monkeypatch.chdir(repo_root)
    out = tmp_path / "report.json"
    code = main(
        [
            "check",
            "fixtures/pass-house.ifc",
            "--language",
            "projects/seed-house.json",
            "--root",
            str(repo_root),
            "--out",
            str(out),
        ]
    )
    captured = capsys.readouterr()
    assert code == 0
    assert captured.out == out.read_text(encoding="utf-8")
    assert captured.out.endswith("\n")


def _validate(repo_root: Path, report: dict) -> None:
    schema = json.loads(
        (repo_root / "schema" / "check-report.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(schema).validate(report)


def _validate_step(repo_root: Path, step: dict) -> None:
    schema = json.loads(
        (repo_root / "schema" / "step.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(schema).validate(step)
