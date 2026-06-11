"""4-tier auditor severity model (spec §5.4).

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

Generalises v7's binary pass/fail. Tiers, least→most blocking:
  INFO      — informational only
  WARNING   — logged + visible, does NOT block LOCK
  BLOCKING  — blocks LOCK unless an --ack=<reason> override is given
  FATAL     — blocks LOCK unconditionally (no override)
This lets a rule ship as WARNING → observe → promote to BLOCKING, the way
mature linters (clippy, ESLint, ruff) evolve.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

# Ascending order of how much a failure blocks LOCK.
SEVERITY_LEVELS: tuple[str, ...] = ("INFO", "WARNING", "BLOCKING", "FATAL")


def severity_rank(severity: str) -> int:
    """Rank a severity (higher int = more blocking). Raise ValueError if unknown."""
    try:
        return SEVERITY_LEVELS.index(severity)
    except ValueError:
        raise ValueError(f"unknown severity: {severity!r}") from None


def worst_severity(severities: Iterable[str]) -> str | None:
    """Return the most-blocking severity in the iterable, or None if empty."""
    items = list(severities)
    if not items:
        return None
    return max(items, key=severity_rank)


def blocks_lock(severity: str, acked: bool = False) -> bool:
    """Whether a FAILING check of this severity blocks LOCK.

    FATAL always blocks (ack cannot override); BLOCKING blocks unless ``acked``;
    WARNING and INFO never block.
    """
    if severity == "FATAL":
        return True
    if severity == "BLOCKING":
        return not acked
    return False


@dataclass(frozen=True)
class Finding:
    """One specific issue found by a check (message + optional file/location)."""

    message: str
    location: str | None = None


@dataclass(frozen=True)
class CheckResult:
    """The outcome of one auditor check.

    ``severity`` is one of SEVERITY_LEVELS and is meaningful chiefly when
    ``passed`` is False (it decides whether the failure blocks LOCK).
    """

    check_id: str
    passed: bool
    severity: str
    summary: str
    findings: tuple[Finding, ...] = ()
