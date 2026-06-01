"""check_12 -- every state timestamp parses as a full ISO8601 datetime.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT

Adapts v7's check_12_iso8601_timestamps to v8. v7 walked timestamp *fields* in
the monolithic state.json (started_at / last_updated_at / per-phase / per-doc);
v8 keeps timestamps in three places instead: the append-only event log (each
event's ``ts``), the workflow projection (``locked_at`` + ``audits[].ts``), and
the decisions index (``regenerated_at``). A value is OK iff it is a string that
``datetime.fromisoformat`` parses (after normalising a trailing 'Z') AND carries
a 'T' or space time-separator -- a bare date silently coerces to midnight and
corrupts chronological queries. ADR ``date`` fields are date-only by design and
are NOT flagged. WARNING: malformed timestamps surface loudly without blocking
LOCK.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from architect_brain.checks import _state
from architect_brain.severity import CheckResult, Finding

CHECK_ID = "12"
NAME = "iso8601_timestamps"
SEVERITY = "WARNING"


def parse_iso8601_datetime(value) -> tuple[bool, str]:
    """Return ``(ok, error)`` for ``value``.

    Accepts the canonical ISO8601 datetime forms with a 'T' separator, plus the
    looser form with a space separator between date and time. Rejects bare-date
    strings ("2026-05-29"), non-strings, and anything ``fromisoformat`` can't
    parse. Mirrors v7 check_12's helper exactly.
    """
    if not isinstance(value, str):
        return False, f"non-string value of type {type(value).__name__}"
    # Normalize trailing 'Z' → '+00:00'. Python 3.11+ accepts 'Z' natively, but
    # 3.10 does not — the explicit replace keeps the check portable.
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        datetime.fromisoformat(normalized)
    except (ValueError, TypeError) as exc:
        return False, f"unparseable: {exc}"
    # Require an explicit time component: fromisoformat accepts bare dates and
    # returns midnight, which silently confuses downstream comparisons.
    if "T" not in value and " " not in value:
        return False, "date-only (no time component); use full ISO8601 datetime"
    return True, ""


def run(state_dir) -> CheckResult:
    """Validate every timestamp in the event log, workflow, and decisions index."""
    state_dir = Path(state_dir)
    findings: list[Finding] = []

    def check(source: str, value) -> None:
        # Skip explicit nulls — nullable fields (e.g. locked_at before lock) are
        # allowed to be None; only flag values that *claim to be* a timestamp.
        if value is None:
            return
        ok, err = parse_iso8601_datetime(value)
        if not ok:
            findings.append(
                Finding(message=f"{source}={value!r}: {err}", location=source)
            )

    # Event log: each event's `ts`.
    for i, event in enumerate(_state.iter_events(state_dir)):
        check(f"events[{i}].ts", event.ts)

    # Workflow projection: locked_at + per-audit ts.
    workflow = _state.load_workflow(state_dir)
    if "locked_at" in workflow:
        check("workflow.locked_at", workflow["locked_at"])
    audits = workflow.get("audits")
    if isinstance(audits, list):
        for i, audit in enumerate(audits):
            if isinstance(audit, dict) and "ts" in audit:
                check(f"workflow.audits[{i}].ts", audit["ts"])

    # Decisions index regeneration stamp (ADR date fields are date-only by
    # design and intentionally NOT checked here).
    decisions_index = _state.load_decisions_index(state_dir)
    if "regenerated_at" in decisions_index:
        check("decisions_index.regenerated_at", decisions_index["regenerated_at"])

    passed = not findings
    summary = (
        "all timestamps are valid ISO8601 datetimes"
        if passed
        else f"{len(findings)} malformed timestamp(s)"
    )
    return CheckResult(
        check_id=CHECK_ID, passed=passed, severity=SEVERITY,
        summary=summary, findings=tuple(findings),
    )
