"""check_19 -- a locked project must carry a clean pre-lock vetting audit.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

v8-ADAPTATION of v7's check_19_audit_freshness. v7 read
``state.last_audit.ran_at`` + ``documents_generated[].generated_at`` from the
monolithic state.json; v8 reads the ``audits`` ledger off the workflow
projection (each entry an ISO-8601-stamped ``{ts, result, ...}``). A LOCK is
only meaningful if the audit that vetted it ran AT-OR-BEFORE the lock AND was
CLEAN. So four BLOCKING defects on a locked project: (a) no recorded audit at
all, (b) no audit at-or-before the lock (every audit is post-lock — the lock
was never vetted), (c) a vetting audit whose ``result`` was ``blocked`` (the
lock is unverified; re-run the auditor to a clean verdict and re-lock), or
(d) the newest POST-lock audit is ``blocked`` (the state degraded after lock).
The ``result`` read (c) is the v8.0.1 enforcement fix — earlier the check
verified only that an audit *ran*, never that it *passed*. v9.2 fix
(tiger-panther): a clean post-lock audit no longer fails the check — SKILL
Phase 9 (Tooling Execution) runs AFTER lock and prescribes re-audits, so
"any post-lock audit = defect" made the skill contradict its own gate.
v7's "audit ran before the newest doc was generated_at" sub-check is DROPPED
-- v8's ``docs.completed`` ledger carries no timestamps to compare against.
ISO-8601 UTC instants compare correctly under a plain lexicographic string
comparison, so no date parsing is needed.
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

    # Audits present: three defects, all provable only when locked AND a
    # locked_at exists to compare against — (a) no audit at-or-before the lock
    # (the lock was never vetted), (b) the vetting audit was itself BLOCKED,
    # (c) the newest post-lock audit is BLOCKED (state degraded after lock).
    # Clean post-lock audits are fine: SKILL Phase 9 prescribes them (v9.2).
    if locked and locked_at:
        dated = [
            a
            for a in audits
            if isinstance(a, dict) and isinstance(a.get("ts"), str)
        ]
        if dated:
            pre_lock = [a for a in dated if a["ts"] <= locked_at]
            if not pre_lock:
                return _fail(
                    "locked without a pre-lock vetting audit",
                    f"every recorded audit ran AFTER the lock ({locked_at}) "
                    "-- the lock was never vetted; re-run the auditor to a "
                    "clean verdict and re-lock",
                    workflow_path,
                )
            # The newest at-or-before-lock audit IS the one that vetted the
            # lock. A LOCK is only meaningful atop a CLEAN verdict; a lock
            # placed on a BLOCKED audit is unverified (re-run clean + re-lock).
            vetting = max(pre_lock, key=lambda a: a["ts"])
            if vetting.get("result") == "blocked":
                return _fail(
                    "locked atop a blocked audit",
                    f"the pre-lock audit that vetted this lock was BLOCKED "
                    f"(ran {vetting['ts']}); re-run the auditor to a clean verdict "
                    "and re-lock",
                    workflow_path,
                )
            newest = max(dated, key=lambda a: a["ts"])
            if newest["ts"] > locked_at and newest.get("result") == "blocked":
                return _fail(
                    "newest post-lock audit is blocked",
                    f"the newest audit ({newest['ts']}) ran after the lock and "
                    "was BLOCKED -- the state degraded after lock; fix the "
                    "findings and re-audit to a clean verdict",
                    workflow_path,
                )

    return _pass("audit present; lock vetted by a clean pre-lock audit")
