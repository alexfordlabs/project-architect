"""check_20 -- phases must be entered in non-decreasing canonical-ladder order.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

v8-ADAPTATION of v7's check_20_no_oob_phase_advance. v7 read the monolithic
state's ``phase_progress`` map and verified gap-freeness against the current
``phase`` (catching a bypassed gate). v8 has no phase_progress map; the
authoritative phase history is the append-only event log. This check
reconstructs the entered-phase sequence from the ``PhaseAdvanced`` events and
verifies it is monotonic non-decreasing against the canonical v8 ladder
(NOTE the reorder: architecture BEFORE stack, cost as its own phase). A phase
entered out of order, an unknown phase name, or a ``current_phase`` that has
regressed behind the furthest entered phase is BLOCKING -- it means a gate was
bypassed or the workflow state is corrupt, neither of which has a mechanical
fix. Distinct from check_16 (chain continuity): this guards ORDER, not
coverage. Degrades to a pass on fresh/empty state (< 1 PhaseAdvanced).
"""

from __future__ import annotations

from pathlib import Path

from architect_brain.checks import _state
from architect_brain.severity import CheckResult, Finding

CHECK_ID = "20"
NAME = "no_oob_phase_advance"
SEVERITY = "BLOCKING"

# Canonical v8 phase ladder (the values set-phase writes + PhaseAdvanced.to
# carries). preflight is the banner-only opener and never appears here.
LADDER = [
    "kickoff",
    "vision",
    "architecture",
    "stack",
    "cost",
    "docs",
    "iteration",
    "lock",
    "tooling",
    "handoff",
    "complete",
]
_INDEX = {name: i for i, name in enumerate(LADDER)}


def run(state_dir) -> CheckResult:
    """Flag any backward/unknown phase entry reconstructed from the event log."""
    state_dir = Path(state_dir)

    entered = [
        event.payload["to"]
        for event in _state.iter_events(state_dir)
        if event.type == "PhaseAdvanced"
        and isinstance(event.payload, dict)
        and "to" in event.payload
    ]

    findings: list[Finding] = []
    prev_idx = -1
    prev_phase: str | None = None
    max_entered_idx = -1

    for phase in entered:
        if phase == "preflight":
            # Banner-only opener — never on the ladder, never out-of-order.
            # Pre-v9.2 SKILL.md instructed `set-phase preflight` at run open,
            # so real projects carry it in their append-only log forever;
            # treating it as unknown permanently blocked their audits (v9.2).
            continue
        if phase not in _INDEX:
            findings.append(Finding(message=f"unknown phase '{phase}' entered"))
            continue
        idx = _INDEX[phase]
        if idx < prev_idx:
            findings.append(
                Finding(
                    message=(
                        f"phase '{phase}' entered out of order "
                        f"after '{prev_phase}'"
                    )
                )
            )
        else:
            prev_idx = idx
            prev_phase = phase
        if idx > max_entered_idx:
            max_entered_idx = idx

    cur = _state.load_workflow(state_dir).get("current_phase")
    if (
        cur in _INDEX
        and max_entered_idx >= 0
        and _INDEX[cur] < max_entered_idx
    ):
        findings.append(
            Finding(
                message=(
                    f"current_phase '{cur}' is behind the furthest "
                    f"entered phase"
                )
            )
        )

    passed = not findings
    if passed:
        summary = (
            f"phase order monotonic through {len(entered)} entry(ies)"
            if entered
            else "no phase transitions to verify"
        )
    else:
        summary = f"{len(findings)} out-of-order/unknown phase entry(ies)"

    return CheckResult(
        check_id=CHECK_ID,
        passed=passed,
        severity=SEVERITY,
        summary=summary,
        findings=tuple(findings),
    )
