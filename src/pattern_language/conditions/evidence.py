"""Return value of one pure check."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


class CheckError(Exception):
    """Unknown check id, missing param, bad project override, or a rejected report."""


@dataclass(frozen=True, slots=True)
class Evidence:
    check: str
    passed: bool
    applicable: bool
    subjects: tuple[str, ...]
    measured: tuple[tuple[str, str], ...]


def make_evidence(
    check: str,
    *,
    passed: bool,
    applicable: bool,
    subjects: Iterable[str] = (),
    measured: Iterable[tuple[str, str]] = (),
) -> Evidence:
    """Freeze one check result. A check that does not apply has passed false."""
    return Evidence(
        check=check,
        passed=passed if applicable else False,
        applicable=applicable,
        subjects=tuple(sorted(subjects)),
        measured=tuple(sorted(measured)),
    )
