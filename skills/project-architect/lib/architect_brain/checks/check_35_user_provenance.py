"""check_35 -- a locked project must carry at least one user-sourced decision.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT

The event log's ``by`` field distinguishes a user-confirmed answer (``"user"``)
from an orchestrator assumption (``"orchestrator"`` / ``"<agent-name>"``). A
LOCKED project whose ``DecisionMade`` events are ALL orchestrator-sourced (zero
``by:"user"``) means the interview was never recorded as user-confirmed — the
"didn't ask the questions" failure mode, which is otherwise invisible in the
ledger (every decision defaults to ``by:"orchestrator"``).

Ships at WARNING per the mature-linter ``ship-WARNING-then-promote`` idiom
(severity.py): it makes under-asking VISIBLE + auditable now, and is a candidate
for promotion to BLOCKING once ``--by user`` recording (SKILL Kickoff/Vision/
Stack answer callsites) is broadly verified. Passes when the project isn't locked
(interview may be ongoing) or has no decisions yet (nothing to attribute).
"""

from __future__ import annotations

from pathlib import Path

from architect_brain.checks import _state
from architect_brain.severity import CheckResult, Finding

CHECK_ID = "35"
NAME = "user_provenance"
SEVERITY = "WARNING"


def _pass(summary: str) -> CheckResult:
    return CheckResult(
        check_id=CHECK_ID, passed=True, severity=SEVERITY, summary=summary, findings=(),
    )


def run(state_dir) -> CheckResult:
    """Flag a locked project whose decisions are all orchestrator-sourced."""
    state_dir = Path(state_dir)
    workflow = _state.load_workflow(state_dir)

    if workflow.get("locked") is not True:
        return _pass("not locked; interview provenance not yet required")

    decisions = [e for e in _state.iter_events(state_dir) if e.type == "DecisionMade"]
    if not decisions:
        return _pass("no decisions recorded; nothing to attribute")

    user_sourced = sum(1 for e in decisions if e.by == "user")
    if user_sourced:
        return _pass(f"{user_sourced} of {len(decisions)} decision(s) are user-sourced")

    return CheckResult(
        check_id=CHECK_ID,
        passed=False,
        severity=SEVERITY,
        summary=f"locked with {len(decisions)} decisions, none user-sourced",
        findings=(
            Finding(
                message=(
                    f"all {len(decisions)} decisions are by:\"orchestrator\"/agent, none "
                    "by:\"user\" — record answers the user actually gave with "
                    "`architect-brain set-decision <key> <value> --by user` so a skipped "
                    "interview is auditable, not invisible"
                ),
                location=str(state_dir / "events.jsonl"),
            ),
        ),
    )
