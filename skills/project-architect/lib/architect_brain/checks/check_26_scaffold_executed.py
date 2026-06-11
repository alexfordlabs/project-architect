"""check_26 -- at handoff, every recorded project_layout path must exist on disk.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

v8-ADAPTATION of v7's check_26_scaffold_executed. Guards plan-vs-execution: a
project may report COMPLETE carrying a layout plan (crates/, apps/) whose
directories were never created because the Tooling-Execution phase never ran --
a false COMPLETE. Gate-then-verify: it only applies once the workflow has
reached the handoff window, then confirms each layout path resolves on disk.

v8 phase keys: the gate fires only for ``current_phase`` in
{tooling, handoff, complete} (v7 used the legacy ``phase_8``/``complete``). The
layout is read from the flat decision map under ``project_layout`` (falling back
to ``tooling.project_layout``) and the explicit opt-out is ``scaffold.deferred``
== True. Those keys are pinned by Wave 6/7; until then the check degrades to a
pass whenever they are absent (graceful degradation, exactly v7's
decline-to-claim idiom).
"""

from __future__ import annotations

from pathlib import Path

from architect_brain.checks import _state
from architect_brain.severity import CheckResult, Finding

CHECK_ID = "26"
NAME = "scaffold_executed"
SEVERITY = "BLOCKING"

# v8 phases that constitute the handoff window (scaffold must be materialised).
_HANDOFF_PHASES = {"tooling", "handoff", "complete"}


def _pass(summary: str) -> CheckResult:
    return CheckResult(
        check_id=CHECK_ID, passed=True, severity=SEVERITY,
        summary=summary, findings=(),
    )


def run(state_dir) -> CheckResult:
    """Verify recorded scaffold paths exist once the project reaches handoff."""
    state_dir = Path(state_dir)
    cur = _state.load_workflow(state_dir).get("current_phase")

    # GATE: scaffold execution is only expected in the handoff window.
    if cur not in _HANDOFF_PHASES:
        return _pass(f"phase '{cur}' is pre-handoff; scaffold not yet expected")

    dec = _state.load_decisions(state_dir)

    # Explicit user opt-out.
    if dec.get("scaffold.deferred") is True:
        return _pass("scaffolding explicitly deferred")

    layout = dec.get("project_layout") or dec.get("tooling.project_layout")
    if not isinstance(layout, dict) or not layout:
        return _pass("project_layout empty; cannot confirm")

    # VERIFY: every recorded layout path must exist on disk.
    proj = _state.project_root(state_dir)
    findings: list[Finding] = []
    for path in layout.values():
        if not (proj / path).exists():
            findings.append(
                Finding(
                    message=f"project_layout path missing on disk: {path}",
                    location=str(path),
                )
            )

    if not findings:
        return _pass(f"all {len(layout)} project_layout path(s) exist on disk")

    return CheckResult(
        check_id=CHECK_ID, passed=False, severity=SEVERITY,
        summary=f"{len(findings)} project_layout path(s) missing on disk",
        findings=tuple(findings),
    )
