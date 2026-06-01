"""check_16 -- phase transitions form a continuous event chain.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT

v8-ADAPTATION of v7's check_16_phase_gates. v7 walked
``state.phase_progress`` and asserted ``prerequisites_satisfied=true`` on every
phase with logged work -- a safety net against premature/out-of-order dispatch.
v8's event-sourced state has no ``phase_progress.prerequisites_satisfied`` field;
the analog of "no premature/out-of-order phase" is EVENT-CHAIN CONTINUITY of the
PhaseAdvanced events in ``events.jsonl``: each subsequent transition must depart
from where the previous one arrived (``this.from == prev.to``). A discontinuity
means a phase was entered without the orchestrator having advanced out of the
prior phase -- BLOCKING, because downstream artifacts produced from a phase that
was jumped into are silently under-resourced. Distinct from check_20, which
validates the ordinal-prefix ordering against the canonical ladder. Passes
(nothing to verify) when there are fewer than two PhaseAdvanced events.
"""

from __future__ import annotations

from pathlib import Path

from architect_brain.checks import _state
from architect_brain.severity import CheckResult, Finding

CHECK_ID = "16"
NAME = "phase_gates"
SEVERITY = "BLOCKING"


def run(state_dir) -> CheckResult:
    """Flag any PhaseAdvanced whose ``from`` != the previous event's ``to``."""
    state_dir = Path(state_dir)

    # iter_events is crash-safe: malformed/unknown/missing-key lines are skipped.
    transitions = [
        event
        for event in _state.iter_events(state_dir)
        if event.type == "PhaseAdvanced"
    ]

    if len(transitions) < 2:
        return CheckResult(
            check_id=CHECK_ID, passed=True, severity=SEVERITY,
            summary="phase chain continuous (nothing to verify)", findings=(),
        )

    findings: list[Finding] = []
    log_location = str(state_dir / "events.jsonl")
    prev = transitions[0]
    for event in transitions[1:]:
        prev_to = prev.payload.get("to")
        this_from = event.payload.get("from")
        this_to = event.payload.get("to")
        if this_from != prev_to:
            findings.append(
                Finding(
                    message=(
                        f"phase chain break: expected from='{prev_to}', "
                        f"got from='{this_from}' -> to='{this_to}'"
                    ),
                    location=log_location,
                )
            )
        prev = event

    passed = not findings
    summary = (
        "phase chain continuous"
        if passed
        else f"{len(findings)} phase chain break(s)"
    )
    return CheckResult(
        check_id=CHECK_ID, passed=passed, severity=SEVERITY,
        summary=summary, findings=tuple(findings),
    )
