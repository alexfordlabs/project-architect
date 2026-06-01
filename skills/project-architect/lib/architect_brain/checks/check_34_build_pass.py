"""check_34_build_pass -- the Phase-8 scaffold build must be green or diagnostic-exhausted.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT

NEW v8 check (spec §5.4). Guards the Tooling-Execution phase: when the
orchestrator runs the scaffolded build it records the outcome under the flat
decision ``tooling.build_outcome`` (fallback: the ``tooling`` projection's
``build_outcome`` field). A recorded ``green`` or ``exhausted_with_diagnostic``
outcome passes; any other recorded value (e.g. ``failed`` / ``red``) is a
BLOCKING defect. A falsy/absent outcome passes — the build simply has not run
yet and is not required before Phase 8 (graceful degradation, v7's
decline-to-claim idiom).
"""

from __future__ import annotations

from pathlib import Path

from architect_brain.checks import _state
from architect_brain.severity import CheckResult, Finding

CHECK_ID = "34"
NAME = "build_pass"
SEVERITY = "BLOCKING"

# Recorded outcomes that satisfy the gate.
_ACCEPTED = {"green", "exhausted_with_diagnostic"}


def _pass(summary: str) -> CheckResult:
    return CheckResult(
        check_id=CHECK_ID, passed=True, severity=SEVERITY,
        summary=summary, findings=(),
    )


def run(state_dir) -> CheckResult:
    """Verify a recorded build outcome is green / exhausted_with_diagnostic."""
    state_dir = Path(state_dir)

    # Flat decision key wins; fall back to the tooling projection field.
    outcome = _state.load_decisions(state_dir).get("tooling.build_outcome")
    if not outcome:
        outcome = _state.load_projection(state_dir, "tooling").get("build_outcome")

    # Falsy/absent → build not yet run; not required pre-Phase-8.
    if not outcome:
        return _pass("build not yet run; not required pre-Phase-8")

    if outcome in _ACCEPTED:
        return _pass(f"build_outcome={outcome}")

    finding = Finding(
        message=(
            f"build_outcome is '{outcome}', "
            "expected green|exhausted_with_diagnostic"
        ),
        location=str(state_dir / "99-flat-index.json"),
    )
    return CheckResult(
        check_id=CHECK_ID, passed=False, severity=SEVERITY,
        summary=f"build_outcome is '{outcome}' (expected green|exhausted_with_diagnostic)",
        findings=(finding,),
    )
