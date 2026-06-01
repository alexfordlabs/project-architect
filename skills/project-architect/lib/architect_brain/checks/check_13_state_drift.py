"""check_13 -- the event log must not lag committed git reality.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT

v8-ADAPTATION of v7's check_13_state_drift, which compared
``state.last_updated_at`` against the HEAD commit timestamp. v8 has no
``last_updated_at`` field; the authoritative freshness signal is the
append-only event log. Drift here means the newest recorded event lags the
HEAD commit by more than a 60s grace window -- i.e. code was committed but the
event log wasn't updated, leaving every downstream freshness consumer reading
stale answers. WARNING (not blocking): drift confuses but does not corrupt, and
the fix is mechanical. Defers (passes) whenever it cannot make a positive
claim -- non-git dirs, no events, no commits, unparseable newest ts.
"""

from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path

from architect_brain.checks import _state
from architect_brain.severity import CheckResult, Finding

CHECK_ID = "13"
NAME = "state_drift"
SEVERITY = "WARNING"

_GRACE_SECONDS = 60


def _pass(summary: str) -> CheckResult:
    return CheckResult(
        check_id=CHECK_ID, passed=True, severity=SEVERITY,
        summary=summary, findings=(),
    )


def _is_git_repo(proj: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "-C", str(proj), "rev-parse", "--git-dir"],
            capture_output=True,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def _head_commit_epoch(proj: Path) -> int | None:
    """Unix epoch (committer time) of HEAD, or None if no commits / git fails."""
    try:
        result = subprocess.run(
            ["git", "-C", str(proj), "log", "-1", "--format=%ct"],
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    raw = result.stdout.strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _newest_event_ts(state_dir) -> str | None:
    """The ``ts`` of the last (newest) event, or None if the log is unreadable.

    ``iter_events`` parses each JSONL line and can raise on a malformed line or
    an unknown event type; we swallow that and decline (defer to check_12 /
    json_valid) rather than crash the auditor.
    """
    newest = None
    try:
        for event in _state.iter_events(state_dir):
            newest = event.ts
    except Exception:
        return None
    return newest


def _ts_to_epoch(ts: str) -> int | None:
    """Parse an ISO-8601 ts to a unix epoch; None on failure.

    Normalises a trailing ``Z`` to ``+00:00`` so ``datetime.fromisoformat``
    accepts it on every supported Python.
    """
    value = ts[:-1] + "+00:00" if ts.endswith("Z") else ts
    try:
        return int(datetime.fromisoformat(value).timestamp())
    except (ValueError, TypeError):
        return None


def run(state_dir) -> CheckResult:
    """Flag drift when the newest event lags HEAD by more than the grace window."""
    state_dir = Path(state_dir)
    proj = _state.project_root(state_dir)

    if not _is_git_repo(proj):
        return _pass("not a git repository")

    newest_ts = _newest_event_ts(state_dir)
    if not newest_ts:
        return _pass("no events recorded")

    head_epoch = _head_commit_epoch(proj)
    if head_epoch is None:
        return _pass("no commits")

    event_epoch = _ts_to_epoch(newest_ts)
    if event_epoch is None:
        # Defer to check_12 (iso8601/timestamp validity).
        return _pass("newest event ts unparseable (deferred)")

    delta = head_epoch - event_epoch
    if delta > _GRACE_SECONDS:
        finding = Finding(
            message=f"newest event ts lags HEAD commit by {delta}s",
            location=str(state_dir / "events.jsonl"),
        )
        return CheckResult(
            check_id=CHECK_ID, passed=False, severity=SEVERITY,
            summary=f"event log lags HEAD by {delta}s",
            findings=(finding,),
        )

    return _pass(f"event log within {_GRACE_SECONDS}s of HEAD (delta={delta}s)")
