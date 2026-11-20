"""Seed catalog loader: links, drafts, back-edges, and missing targets."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from types import MappingProxyType

import pytest
from jsonschema import Draft202012Validator

from pattern_language import CatalogLoadError, load_catalog
from pattern_language.catalog import BackEdge, LinkRef, get, pattern_record, search

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")

NUMBERS = {105, 106, 107, 110, 112, 127, 128, 130, 159, 167, 180, 190}

EXPECTED: dict[int, dict[str, object]] = {
    105: {
        "name": "South Facing Outdoors",
        "larger": (),
        "smaller": (106, 107, 128),
        "summary": "The main outdoor zone lies on the equator-facing side of the building.",
        "forces": ("winter sun on outdoor ground", "building mass shading that ground"),
        "kind": "computed",
        "id": "south-facing-outdoors",
        "params": {"latitude_deg": 0},
        "question": None,
    },
    106: {
        "name": "Positive Outdoor Space",
        "larger": (105,),
        "smaller": (167,),
        "summary": "Each outdoor zone is mostly enclosed.",
        "forces": ("an outdoor room wants enclosure", "enclosure can cut off sun"),
        "kind": "computed",
        "id": "positive-outdoor-space",
        "params": {"min_convexity_ratio": 0.75},
        "question": None,
    },
    107: {
        "name": "Wings of Light",
        "larger": (105,),
        "smaller": (128, 159, 190),
        "summary": "No occupied space sits deeper than a set depth from an exterior wall.",
        "forces": ("occupied rooms want daylight", "a deep plan leaves an interior dark"),
        "kind": "computed",
        "id": "wings-of-light",
        "params": {"max_depth_m": 8},
        "question": None,
    },
    110: {
        "name": "Main Entrance",
        "larger": (),
        "smaller": (112, 130),
        "summary": "The entrance is visible from the approach.",
        "forces": (
            "arrival wants a visible door",
            "the door can sit out of sight of the approach",
        ),
        "kind": "judged",
        "id": "main-entrance",
        "params": None,
        "question": "Is the entrance seen from the approach?",
    },
    112: {
        "name": "Entrance Transition",
        "larger": (110,),
        "smaller": (130,),
        "summary": "The path from the street to the main door passes through a transition zone.",
        "forces": ("the street is public", "the interior is private"),
        "kind": "computed",
        "id": "entrance-transition",
        "params": {},
        "question": None,
    },
    127: {
        "name": "Intimacy Gradient",
        "larger": (),
        "smaller": (130,),
        "summary": (
            "From the entrance, public rooms come before semi-private rooms, then private rooms."
        ),
        "forces": (
            "a house holds public and private rooms",
            "a door can open into the most private room",
        ),
        "kind": "computed",
        "id": "intimacy-gradient",
        "params": {},
        "question": None,
    },
    128: {
        "name": "Indoor Sunlight",
        "larger": (105, 107),
        "smaller": (159,),
        "summary": "Daytime rooms sit on the equator-facing side.",
        "forces": ("daytime rooms want sun", "those rooms can sit on the shaded side"),
        "kind": "computed",
        "id": "indoor-sunlight",
        "params": {"latitude_deg": 0},
        "question": None,
    },
    130: {
        "name": "Entrance Room",
        "larger": (110, 112, 127),
        "smaller": (),
        "summary": "The main door opens into a room.",
        "forces": ("arrival wants a room", "the door can open into a corridor"),
        "kind": "computed",
        "id": "entrance-room",
        "params": {},
        "question": None,
    },
    159: {
        "name": "Light on Two Sides of Every Room",
        "larger": (107, 128),
        "smaller": (180,),
        "summary": "Each occupied room has windows in two walls of different orientation.",
        "forces": (
            "a room wants light from two directions",
            "one window wall leaves it flat",
        ),
        "kind": "computed",
        "id": "light-on-two-sides",
        "params": {"min_orientations": 2},
        "question": None,
    },
    167: {
        "name": "Six-Foot Balcony",
        "larger": (106,),
        "smaller": (),
        "summary": "Every elevated balcony is at least 1.83 m deep.",
        "forces": ("a balcony wants room to sit", "a narrow ledge is only a step"),
        "kind": "computed",
        "id": "six-foot-balcony",
        "params": {"min_depth_m": 1.83, "min_elevation_m": 2.4},
        "question": None,
    },
    180: {
        "name": "Window Place",
        "larger": (159,),
        "smaller": (),
        "summary": "The main room has a window with a place to sit.",
        "forces": (
            "a window wants a place beside it",
            "the glass can have nowhere to sit",
        ),
        "kind": "judged",
        "id": "window-place",
        "params": None,
        "question": "Does the main room have a window with a place to sit?",
    },
    190: {
        "name": "Ceiling Height Variety",
        "larger": (107,),
        "smaller": (),
        "summary": "Ceiling heights across occupied rooms vary by at least a set amount.",
        "forces": (
            "rooms want heights that match their use",
            "one ceiling height makes them feel alike",
        ),
        "kind": "computed",
        "id": "ceiling-height-variety",
        "params": {"min_height_difference_m": 0.3},
        "question": None,
    },
}


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _prepare(tmp_path: Path, repo_root: Path) -> Path:
    for name in ("schema", "catalog", "projects"):
        (tmp_path / name).mkdir()
    schema = repo_root / "schema" / "catalog.schema.json"
    (tmp_path / "schema" / "catalog.schema.json").write_text(
        schema.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return tmp_path


def _minimal(
    number: int,
    *,
    name: str | None = None,
    smaller: list[int] | None = None,
    larger: list[int] | None = None,
) -> dict[str, object]:
    label = name or f"Pattern {number}"
    condition_id = _slug(label)
    return {
        "number": number,
        "name": label,
        "scale": "building",
        "confidence": 1,
        "larger": [] if larger is None else larger,
        "smaller": [] if smaller is None else smaller,
        "summary": {"text": f"Pattern {number} is a fixture.", "draft": True},
        "forces": [{"name": "a fixture names one force", "draft": True}],
        "conditions": [
            {
                "id": condition_id,
                "kind": "computed",
                "check": condition_id,
                "params": {},
            }
        ],
        "source": {"book": "A Pattern Language", "number": number},
    }


def _write(root: Path, record: dict[str, object], filename: str | None = None) -> None:
    if filename is None:
        filename = f"{record['number']}-{_slug(str(record['name']))}.json"
    path = root / "catalog" / filename
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


def _cli(repo_root: Path, root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(repo_root / "scripts" / "validate_catalog.py"), str(root)],
        check=False,
        capture_output=True,
        text=True,
    )


def test_seed_catalog(repo_root: Path) -> None:
    catalog = load_catalog(repo_root)
    assert set(catalog.by_number) == NUMBERS
    assert isinstance(catalog.by_number, MappingProxyType)
    assert catalog.missing_targets == ()
    assert catalog.back_edges == ()
    assert catalog.ok
    assert [item.number for item in catalog.patterns] == sorted(NUMBERS)
    for number, expected in EXPECTED.items():
        pattern = catalog.by_number[number]
        assert pattern.name == expected["name"]
        assert pattern.scale == "building"
        assert pattern.larger == expected["larger"]
        assert pattern.smaller == expected["smaller"]
        assert pattern.path == f"catalog/{number}-{_slug(pattern.name)}.json"
        assert pattern.summary.text == expected["summary"]
        assert pattern.summary.draft is True
        assert tuple(force.name for force in pattern.forces) == expected["forces"]
        assert pattern.forces
        assert all(force.draft is True for force in pattern.forces)
        assert 0 <= pattern.confidence <= 2
        assert pattern.source.book == "A Pattern Language"
        assert pattern.source.number == number
        assert pattern.number not in pattern.smaller
        assert pattern.number not in pattern.larger
        condition = pattern.conditions[0]
        assert len(pattern.conditions) == 1
        assert condition.kind == expected["kind"]
        assert condition.id == expected["id"]
        if condition.kind == "computed":
            assert condition.check == expected["id"]
            assert dict(condition.params or {}) == expected["params"]
            assert condition.question is None
        else:
            assert condition.check is None
            assert condition.params is None
            assert condition.question == expected["question"]
        for target in pattern.smaller:
            assert pattern.number in catalog.by_number[target].larger
        for target in pattern.larger:
            assert pattern.number in catalog.by_number[target].smaller
    for number in (105, 159, 180):
        assert catalog.by_number[number].confidence == 2


def test_pattern_record_matches_the_catalog_file(repo_root: Path) -> None:
    catalog = load_catalog(repo_root)
    schema = json.loads((repo_root / "schema" / "catalog.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    south = pattern_record(get(catalog, 105))
    judged = pattern_record(get(catalog, 110))
    assert south == json.loads(
        (repo_root / "catalog" / "105-south-facing-outdoors.json").read_text(encoding="utf-8")
    )
    assert judged == json.loads(
        (repo_root / "catalog" / "110-main-entrance.json").read_text(encoding="utf-8")
    )
    assert south["name"] == "South Facing Outdoors"
    assert south["conditions"][0]["check"] == "south-facing-outdoors"
    assert "params" in south["conditions"][0]
    assert "question" not in south["conditions"][0]
    assert judged["conditions"][0]["question"] == "Is the entrance seen from the approach?"
    assert "check" not in judged["conditions"][0]
    assert "params" not in judged["conditions"][0]
    validator.validate(south)
    validator.validate(judged)


def test_search_filters_number_name_and_scale(repo_root: Path) -> None:
    catalog = load_catalog(repo_root)
    assert [item.number for item in search(catalog, name="Entrance")] == [110, 112, 130]
    assert [item.number for item in search(catalog, name="entrance")] == [110, 112, 130]
    assert search(catalog, number=105, name="Entrance") == ()
    assert search(catalog, scale="town") == ()
    assert [item.number for item in search(catalog, scale="building")] == sorted(NUMBERS)
    assert [item.number for item in search(catalog)] == sorted(NUMBERS)


def test_get_missing_pattern_names_the_number(repo_root: Path) -> None:
    catalog = load_catalog(repo_root)
    with pytest.raises(CatalogLoadError) as caught:
        get(catalog, 200)
    assert str(caught.value) == "missing pattern: 200"


def test_downward_smaller_link_is_a_back_edge(tmp_path: Path, repo_root: Path) -> None:
    root = _prepare(tmp_path, repo_root)
    _write(root, _minimal(20, smaller=[10]))
    _write(root, _minimal(10))
    catalog = load_catalog(root)
    assert catalog.back_edges == (BackEdge(20, 10),)
    assert catalog.missing_targets == ()
    assert catalog.ok
    assert catalog.by_number[10].larger == ()
    assert catalog.by_number[20].smaller == (10,)


def test_dangling_smaller_link_is_a_missing_target(tmp_path: Path, repo_root: Path) -> None:
    root = _prepare(tmp_path, repo_root)
    _write(root, _minimal(105, smaller=[104]))
    catalog = load_catalog(root)
    assert catalog.missing_targets == (LinkRef(105, "smaller", 104),)
    assert catalog.back_edges == ()
    assert not catalog.ok


def test_self_link_is_neither_missing_nor_back_edge(tmp_path: Path, repo_root: Path) -> None:
    root = _prepare(tmp_path, repo_root)
    _write(root, _minimal(15, smaller=[15]))
    catalog = load_catalog(root)
    assert catalog.missing_targets == ()
    assert catalog.back_edges == ()
    assert catalog.ok


def test_downward_larger_link_is_not_a_back_edge(tmp_path: Path, repo_root: Path) -> None:
    root = _prepare(tmp_path, repo_root)
    _write(root, _minimal(20, larger=[10]))
    _write(root, _minimal(10))
    catalog = load_catalog(root)
    assert catalog.back_edges == ()
    assert catalog.missing_targets == ()
    assert catalog.by_number[10].smaller == ()


def test_missing_targets_sort_larger_before_smaller(tmp_path: Path, repo_root: Path) -> None:
    root = _prepare(tmp_path, repo_root)
    _write(root, _minimal(30, larger=[2], smaller=[1]))
    catalog = load_catalog(root)
    assert catalog.missing_targets == (
        LinkRef(30, "larger", 2),
        LinkRef(30, "smaller", 1),
    )
    assert catalog.back_edges == ()


def test_duplicate_pattern_number_raises(tmp_path: Path, repo_root: Path) -> None:
    root = _prepare(tmp_path, repo_root)
    _write(root, _minimal(105), "105-south-facing-outdoors.json")
    _write(root, _minimal(105, name="Other"), "105-other.json")
    with pytest.raises(CatalogLoadError) as caught:
        load_catalog(root)
    assert caught.value.errors == (
        "duplicate pattern number: 105 "
        "(catalog/105-other.json, catalog/105-south-facing-outdoors.json)",
    )


def test_scan_errors_raise_catalog_load_error(tmp_path: Path) -> None:
    for name in ("schema", "catalog", "projects"):
        (tmp_path / name).mkdir()
    (tmp_path / "catalog" / "orphan.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(CatalogLoadError) as caught:
        load_catalog(tmp_path)
    assert "record without schema: catalog/orphan.json" in caught.value.errors


def test_problem_field_fails_schema(tmp_path: Path, repo_root: Path) -> None:
    root = _prepare(tmp_path, repo_root)
    record = _minimal(167)
    record["problem"] = "A pasted paragraph has nowhere to land."
    _write(root, record)
    with pytest.raises(CatalogLoadError) as caught:
        load_catalog(root)
    assert any(error.startswith("schema: ") for error in caught.value.errors)


def test_cli_reports_downward_smaller_link(tmp_path: Path, repo_root: Path) -> None:
    root = _prepare(tmp_path, repo_root)
    _write(root, _minimal(20, smaller=[10]))
    _write(root, _minimal(10))
    completed = _cli(repo_root, root)
    assert completed.returncode == 0
    assert completed.stdout == "back-edge: 20 10\nback-edges: 1\nok: 2 records\n"
    assert completed.stderr == ""


def test_cli_reports_missing_target_on_stderr(tmp_path: Path, repo_root: Path) -> None:
    root = _prepare(tmp_path, repo_root)
    _write(root, _minimal(105, smaller=[104]))
    completed = _cli(repo_root, root)
    assert completed.returncode == 1
    assert completed.stdout == "back-edges: 0\n"
    assert completed.stderr == "missing target: 105 smaller 104\n"
