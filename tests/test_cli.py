"""``pl check`` exit codes."""

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
    assert capsys.readouterr().out == ""
    assert main(["sequence"]) == 2
    assert capsys.readouterr().out == ""
    assert main(["step"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "unknown command\n"


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
