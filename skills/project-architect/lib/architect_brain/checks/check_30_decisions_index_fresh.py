"""check_30 -- the on-disk ADR ledger must equal the event-log replay.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

BLOCKING. Recomputes the decisions index (the ADR ledger) from events.jsonl via
``replay`` and compares it to ``decisions/index.json`` on disk, ignoring the
volatile ``regenerated_at`` stamp. Drift means the materialised ledger lags the
authoritative event log -- a stale answer for every consumer of the ADR index.
``replay`` uses the strict event reader and can raise on a corrupt log, so it is
wrapped: an unreplayable log is itself a BLOCKING finding, never a crash.
"""

from __future__ import annotations

from pathlib import Path

from architect_brain.checks import _state
from architect_brain.projections import replay
from architect_brain.severity import CheckResult, Finding

CHECK_ID = "30"
NAME = "decisions_index_fresh"
SEVERITY = "BLOCKING"


def run(state_dir) -> CheckResult:
    """Flag drift between ``decisions/index.json`` and the event-log replay."""
    state_dir = Path(state_dir)

    try:
        expected = replay(state_dir / "events.jsonl")["_decisions_index"]
    except Exception as exc:  # replay's strict reader raises on a corrupt log
        finding = Finding(
            message=f"event log unreplayable: {exc}",
            location=str(state_dir / "events.jsonl"),
        )
        return CheckResult(
            check_id=CHECK_ID, passed=False, severity=SEVERITY,
            summary="event log unreplayable", findings=(finding,),
        )

    actual = _state.load_decisions_index(state_dir)

    expected_adrs = expected.get("adrs", [])
    actual_adrs = actual.get("adrs", [])

    if (
        expected_adrs == actual_adrs
        and expected.get("schema_version") == actual.get("schema_version")
    ):
        return CheckResult(
            check_id=CHECK_ID, passed=True, severity=SEVERITY,
            summary=f"decisions index matches replay ({len(expected_adrs)} adrs)",
            findings=(),
        )

    finding = Finding(
        message=(
            f"decisions/index.json drifts from replay "
            f"(expected {len(expected_adrs)} adrs, on-disk {len(actual_adrs)})"
        ),
        location=str(state_dir / "decisions" / "index.json"),
    )
    return CheckResult(
        check_id=CHECK_ID, passed=False, severity=SEVERITY,
        summary="decisions index drifts from replay", findings=(finding,),
    )
