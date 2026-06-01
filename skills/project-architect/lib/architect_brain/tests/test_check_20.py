"""Tests for the check_20_no_oob_phase_advance auditor check.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
"""

import json
import tempfile
import unittest
from pathlib import Path

from architect_brain.checks import check_20_no_oob_phase_advance
from architect_brain.checks.check_20_no_oob_phase_advance import (
    CHECK_ID,
    NAME,
    SEVERITY,
    run,
)


def _make_state(tmp: str) -> Path:
    """Create ``<tmp>/docs/_architect_state`` and return it."""
    state = Path(tmp) / "docs" / "_architect_state"
    state.mkdir(parents=True)
    return state


def _phase_advanced_line(to: str, frm=None, *, ulid: str) -> str:
    """A well-formed PhaseAdvanced event JSONL line advancing to ``to``."""
    return json.dumps(
        {
            "id": ulid,
            "ts": "2026-05-27T15:23:11Z",
            "by": "orchestrator",
            "phase": to,
            "type": "PhaseAdvanced",
            "payload": {"from": frm, "to": to},
        },
        separators=(",", ":"),
    )


def _write_phase_sequence(state_dir: Path, phases: list[str]) -> None:
    """Write a PhaseAdvanced event for each phase, in order, to events.jsonl."""
    lines = []
    prev = None
    for i, phase in enumerate(phases):
        ulid = f"01J000000000000000000000{chr(ord('A') + i)}"
        lines.append(_phase_advanced_line(phase, prev, ulid=ulid))
        prev = phase
    (state_dir / "events.jsonl").write_text(
        "".join(line + "\n" for line in lines), encoding="utf-8"
    )


def _write_lines(state_dir: Path, lines: list[str]) -> None:
    (state_dir / "events.jsonl").write_text(
        "".join(line + "\n" for line in lines), encoding="utf-8"
    )


def _write_workflow(state_dir: Path, current_phase) -> None:
    payload = {"schema_version": "4.0"}
    if current_phase is not None:
        payload["current_phase"] = current_phase
    (state_dir / "workflow.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


class TestCheck20Contract(unittest.TestCase):
    def test_module_contract(self):
        self.assertEqual(CHECK_ID, "20")
        self.assertEqual(NAME, "no_oob_phase_advance")
        self.assertEqual(SEVERITY, "BLOCKING")
        self.assertTrue(callable(run))
        self.assertEqual(check_20_no_oob_phase_advance.CHECK_ID, "20")
        self.assertTrue(callable(check_20_no_oob_phase_advance.run))


class TestCheck20Degraded(unittest.TestCase):
    def test_empty_state_passes(self):
        # Fresh project: no events.jsonl, no workflow.json → nothing to verify.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "20")
            self.assertEqual(result.findings, ())

    def test_empty_events_file_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_lines(state, [])
            self.assertTrue(run(state).passed)

    def test_single_phase_advance_passes(self):
        # <1 backward transition → pass; one advance trivially monotonic.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_phase_sequence(state, ["kickoff"])
            self.assertTrue(run(state).passed)

    def test_malformed_event_line_does_not_raise(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_lines(state, ["{not json at all", "also garbage"])
            # iter_events skips bad lines → no PhaseAdvanced → pass, no raise.
            result = run(state)
            self.assertTrue(result.passed)

    def test_non_phaseadvanced_events_ignored(self):
        # Only DecisionMade-style events present → no entered phases → pass.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            line = json.dumps(
                {
                    "id": "01J0000000000000000000000A",
                    "ts": "2026-05-27T15:23:11Z",
                    "by": "user",
                    "phase": "vision",
                    "type": "DecisionMade",
                    "payload": {"key": "stack.language", "value": "rust"},
                }
            )
            _write_lines(state, [line])
            self.assertTrue(run(state).passed)


class TestCheck20Pass(unittest.TestCase):
    def test_full_canonical_ladder_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_phase_sequence(
                state,
                [
                    "kickoff", "vision", "architecture", "stack", "cost",
                    "docs", "iteration", "lock", "tooling", "handoff",
                    "complete",
                ],
            )
            _write_workflow(state, "complete")
            self.assertTrue(run(state).passed)

    def test_equal_index_tolerated(self):
        # Re-entering the same phase (equal index) is non-decreasing → pass.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_phase_sequence(state, ["kickoff", "vision", "vision"])
            _write_workflow(state, "vision")
            self.assertTrue(run(state).passed)

    def test_v8_reorder_architecture_before_stack_passes(self):
        # The v8 ladder reorders architecture BEFORE stack; this must pass.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_phase_sequence(
                state, ["kickoff", "vision", "architecture", "stack"]
            )
            _write_workflow(state, "stack")
            self.assertTrue(run(state).passed)

    def test_skipped_phase_still_monotonic_passes(self):
        # Skipping a phase forward (e.g. straight to cost) is still
        # non-decreasing → pass (this check guards order, not coverage).
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_phase_sequence(state, ["kickoff", "vision", "cost"])
            _write_workflow(state, "cost")
            self.assertTrue(run(state).passed)

    def test_current_phase_at_furthest_entered_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_phase_sequence(state, ["kickoff", "vision", "architecture"])
            _write_workflow(state, "architecture")
            self.assertTrue(run(state).passed)

    def test_current_phase_ahead_of_entered_passes(self):
        # current_phase ahead of furthest entered is fine (not behind).
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_phase_sequence(state, ["kickoff", "vision"])
            _write_workflow(state, "stack")
            self.assertTrue(run(state).passed)

    def test_no_workflow_with_good_events_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_phase_sequence(state, ["kickoff", "vision", "stack"])
            # No workflow.json → current_phase unset → only event order matters.
            self.assertTrue(run(state).passed)


class TestCheck20Fail(unittest.TestCase):
    def test_backward_advance_fails_blocking(self):
        # v8 ladder: stack (index 3) entered AFTER cost (index 4) → backward.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_phase_sequence(
                state, ["kickoff", "vision", "architecture", "cost", "stack"]
            )
            _write_workflow(state, "stack")
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            self.assertEqual(result.check_id, "20")
            self.assertTrue(
                any("out of order" in f.message for f in result.findings)
            )
            self.assertTrue(
                any(
                    "'stack'" in f.message and "'cost'" in f.message
                    for f in result.findings
                )
            )

    def test_unknown_phase_fails_blocking(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_phase_sequence(state, ["kickoff", "bogus_phase", "vision"])
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            self.assertTrue(
                any(
                    "unknown phase" in f.message and "bogus_phase" in f.message
                    for f in result.findings
                )
            )

    def test_current_phase_behind_furthest_entered_fails(self):
        # Events reach 'stack' but workflow.current_phase regressed to 'vision'.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_phase_sequence(
                state, ["kickoff", "vision", "architecture", "stack"]
            )
            _write_workflow(state, "vision")
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            self.assertTrue(
                any(
                    "current_phase 'vision'" in f.message
                    and "behind" in f.message
                    for f in result.findings
                )
            )

    def test_v7_phase_names_are_unknown_in_v8(self):
        # v7 used phase_0/phase_1/... ; in v8 those are unknown phases.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_phase_sequence(state, ["phase_0", "phase_1"])
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            self.assertTrue(
                any("unknown phase" in f.message for f in result.findings)
            )

    def test_unknown_current_phase_does_not_trigger_behind_finding(self):
        # current_phase that's not in the ladder is ignored for the
        # behind-check (no crash, no spurious finding) — events are clean.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_phase_sequence(state, ["kickoff", "vision"])
            _write_workflow(state, "some_unknown_phase")
            result = run(state)
            self.assertTrue(result.passed)


if __name__ == "__main__":
    unittest.main()
