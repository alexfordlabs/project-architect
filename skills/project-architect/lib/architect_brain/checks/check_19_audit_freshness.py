"""check_19 -- a locked project must carry a pre-lock audit, never a post-lock one.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

v8-ADAPTATION of v7's check_19_audit_freshness. v7 read
``state.last_audit.ran_at`` + ``documents_generated[].generated_at`` from the
monolithic state.json; v8 reads the ``audits`` ledger off the workflow
projection (each entry an ISO-8601-stamped ``{ts, result, ...}``). A LOCK is
only meaningful if the audit that vetted it ran BEFORE the lock AND was CLEAN.
So three BLOCKING defects: a locked project with (a) no recorded audit, (b) a
newest audit that ran AFTER the lock (post-lock audit), or (c) a pre-lock
vetting audit whose ``result`` was ``blocked`` (the lock is unverified; the fix
is to re-run the auditor to a clean verdict and re-lock, not a mechanical edit).
The ``result`` read (c) is the v8.0.1 enforcement fix — earlier the check
verified only that an audit *ran*, never that it *passed*. v7's "audit ran
before the newest doc was
generated_at" sub-check is DROPPED -- v8's ``docs.completed`` ledger carries no
timestamps to compare against. ISO-8601 UTC instants compare correctly under a
plain lexicographic string comparison, so no date parsing is needed.
"""

from __future__ import annotations

from pathlib import Path

from architect_brain.checks import _state
from architect_brain.severity import CheckResult, Finding

CHECK_ID = "19"
NAME = "audit_freshness"
SEVERITY = "BLOCKING"


def _pass(summary: str) -> CheckResult:
    return CheckResult(
        check_id=CHECK_ID, passed=True, severity=SEVERITY,
        summary=summary, findings=(),
    )


def _fail(summary: str, message: str, location: str) -> CheckResult:
    return CheckResult(
        check_id=CHECK_ID, passed=False, severity=SEVERITY,
        summary=summary, findings=(Finding(message=message, location=location),),
    )


def run(state_dir) -> CheckResult:
    """Flag a locked project lacking a pre-lock audit (or carrying a post-lock one)."""
    state_dir = Path(state_dir)
    workflow_path = str(state_dir / "workflow.json")

    workflow = _state.load_workflow(state_dir)
    locked = workflow.get("locked") is True
    locked_at = workflow.get("locked_at")

    audits = workflow.get("audits")
    audits = audits if isinstance(audits, list) else []

    if not audits:
        if locked:
            return _fail(
                "locked without a recorded audit",
                "project is locked but no audit was recorded",
                workflow_path,
            )
        return _pass("no audit yet; not required pre-lock")

    # Audits present: two defects, both provable only when locked AND a locked_at
    # exists to compare against — (a) the newest audit ran AFTER the lock
    # (post-lock audit), or (b) the audit that VETTED the lock was itself BLOCKED.
    if locked and locked_at:
        dated = [
            a
            for a in audits
            if isinstance(a, dict) and isinstance(a.get("ts"), str)
        ]
        if dated:
            newest = max(dated, key=lambda a: a["ts"])
            if newest["ts"] > locked_at:
                return _fail(
                    "audit ran after lock (post-lock audit)",
                    f"newest audit ran ({newest['ts']}) AFTER lock ({locked_at}) "
                    "-- post-lock audit",
                    workflow_path,
                )
            # newest["ts"] <= locked_at: this IS the pre-lock audit that vetted
            # the lock. A LOCK is only meaningful atop a CLEAN verdict; a lock
            # placed on a BLOCKED audit is unverified (re-run clean + re-lock).
            if newest.get("result") == "blocked":
                return _fail(
                    "locked atop a blocked audit",
                    f"the pre-lock audit that vetted this lock was BLOCKED "
                    f"(ran {newest['ts']}); re-run the auditor to a clean verdict "
                    "and re-lock",
                    workflow_path,
                )

    return _pass("audit present and pre-lock")
