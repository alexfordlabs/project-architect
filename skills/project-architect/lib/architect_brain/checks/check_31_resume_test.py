"""check_31 -- FATAL: the central event-replay invariant, operationalised.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT

The whole point of v8's event-sourced state is that on-disk projections are
DERIVED data: replaying events.jsonl from empty must reproduce them exactly. If
a projection file drifts from its replay (hand-edit, partial write, stale
materialisation), resume/situation-routing reads a lie. This check replays the
log and compares each concern projection + the flat-index to its on-disk file
as PARSED dicts (key-order / whitespace insensitive). Any drift -- or an
unreplayable log -- is FATAL (no --ack override). decisions/index.json is NOT
compared here: its regenerated_at stamp is write-time volatile (check_30's job).
"""

from __future__ import annotations

from pathlib import Path

from architect_brain.checks import _state
from architect_brain.projections import CONCERN_NAMES, replay
from architect_brain.severity import CheckResult, Finding

CHECK_ID = "31"
NAME = "resume_test"
SEVERITY = "FATAL"


def _has_decisions(projection) -> bool:
    """Whether a replayed projection carries any decisions (non-empty)."""
    if not isinstance(projection, dict):
        return False
    return bool(projection.get("decisions"))


def run(state_dir) -> CheckResult:
    """Verify every on-disk projection equals its replay from events.jsonl."""
    state_dir = Path(state_dir)

    try:
        replayed = replay(state_dir / "events.jsonl")
    except Exception as exc:  # strict reader RAISES on a corrupt log
        finding = Finding(
            message=f"event log unreplayable: {exc}",
            location=str(state_dir / "events.jsonl"),
        )
        return CheckResult(
            check_id=CHECK_ID, passed=False, severity=SEVERITY,
            summary="event log unreplayable", findings=(finding,),
        )

    findings: list[Finding] = []

    # (replay key, on-disk filename) pairs: the 11 concerns + the flat-index.
    # decisions/index.json is deliberately excluded (volatile regenerated_at).
    targets: list[tuple[str, str]] = [
        (concern, f"{concern}.json") for concern in CONCERN_NAMES
    ]
    targets.append(("_flat_index", "99-flat-index.json"))

    for replay_key, filename in targets:
        expected = replayed[replay_key]
        on_disk = _state.load_json(state_dir / filename)
        if on_disk is None:
            # File absent (or unparseable — check_05 owns that verdict). Only a
            # problem if replay says this projection should be non-empty.
            if _has_decisions(expected):
                findings.append(
                    Finding(
                        message=f"{filename} missing but replay is non-empty",
                        location=filename,
                    )
                )
            continue
        if on_disk != expected:
            findings.append(
                Finding(message=f"{filename}: replay != on-disk", location=filename)
            )

    passed = not findings
    summary = (
        "all projections match replay"
        if passed
        else f"{len(findings)} projection(s) drift from replay"
    )
    return CheckResult(
        check_id=CHECK_ID, passed=passed, severity=SEVERITY,
        summary=summary, findings=tuple(findings),
    )
