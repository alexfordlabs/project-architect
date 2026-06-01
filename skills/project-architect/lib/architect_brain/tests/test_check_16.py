"""Tests for the check_16_phase_gates auditor check.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT

Covers the v8-ADAPTATION: v8 has no ``phase_progress.prerequisites_satisfied``;
the analog of "no premature/out-of-order phase" is EVENT-CHAIN CONTINUITY over
the PhaseAdvanced events in events.jsonl. Each subsequent event's ``from`` must
equal the previous event's ``to``.
"""

import tempfile
import unittest
from pathlib import Path

from architect_brain.checks import check_16_phase_gates
from architect_brain.checks.check_16_phase_gates import CHECK_ID, NAME, SEVERITY, run


def _make_state(tmp: str) -> Path:
    """Create ``<tmp>/docs/_architect_state`` and return it."""
    state = Path(tmp) / "docs" / "_architect_state"
    state.mkdir(parents=True)
    return state


def _write_events(state_dir: Path, lines: list[str]) -> None:
    (state_dir / "events.jsonl").write_text(
        "".join(line + "\n" for line in lines), encoding="utf-8"
    )


_ULIDS = [
    "01J0000000000000000000000A",
    "01J0000000000000000000000B",
    "01J0000000000000000000000C",
    "01J0000000000000000000000D",
    "01J0000000000000000000000E",
]


def _phase_advanced(idx: int, frm, to: str) -> str:
    """A well-formed PhaseAdvanced JSONL line with payload {from, to}.

    ``frm`` of None serialises as JSON ``null`` (the initial-event form).
    """
    import json

    payload = {"from": frm, "to": to}
    return json.dumps(
        {
            "id": _ULIDS[idx],
            "ts": "2026-05-27T15:23:11Z",
            "by": "orchestrator",
            "phase": to,
            "type": "PhaseAdvanced",
            "payload": payload,
        },
        separators=(",", ":"),
    )


def _other_event(idx: int, ev_type: str = "DecisionMade") -> str:
    """A non-PhaseAdvanced event (must be ignored by the chain walk)."""
    import json

    return json.dumps(
        {
            "id": _ULIDS[idx],
            "ts": "2026-05-27T15:23:11Z",
            "by": "orchestrator",
            "phase": "vision",
            "type": ev_type,
            "payload": {"key": "stack.runtime", "value": "node"},
        },
        separators=(",", ":"),
    )


class TestCheck16Contract(unittest.TestCase):
    def test_module_contract(self):
        self.assertEqual(CHECK_ID, "16")
        self.assertEqual(NAME, "phase_gates")
        self.assertEqual(SEVERITY, "BLOCKING")
        self.assertTrue(callable(run))
        self.assertEqual(check_16_phase_gates.CHECK_ID, "16")
        self.assertEqual(check_16_phase_gates.NAME, "phase_gates")
        self.assertEqual(check_16_phase_gates.SEVERITY, "BLOCKING")
        self.assertTrue(callable(check_16_phase_gates.run))


class TestCheck16Degraded(unittest.TestCase):
    def test_no_events_file_passes(self):
        # Fresh project: no events.jsonl at all → nothing to verify.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "16")
            self.assertEqual(result.severity, "BLOCKING")
            self.assertEqual(result.findings, ())

    def test_empty_events_file_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_events(state, [])
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_single_phase_advanced_passes(self):
        # Fewer than 2 PhaseAdvanced events → nothing to compare.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_events(state, [_phase_advanced(0, None, "kickoff")])
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_no_phase_advanced_events_passes(self):
        # Events exist but none are PhaseAdvanced → nothing to compare.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_events(state, [_other_event(0), _other_event(1)])
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_malformed_event_line_does_not_raise(self):
        # iter_events skips malformed lines; the single valid PhaseAdvanced
        # that remains is < 2 → passes (and must NOT raise).
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_events(
                state,
                ["{not json at all", _phase_advanced(0, None, "kickoff")],
            )
            result = run(state)
            self.assertTrue(result.passed)


class TestCheck16Pass(unittest.TestCase):
    def test_continuous_chain_passes(self):
        # null -> kickoff -> vision -> architecture: each from == prev to.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_events(
                state,
                [
                    _phase_advanced(0, None, "kickoff"),
                    _phase_advanced(1, "kickoff", "vision"),
                    _phase_advanced(2, "vision", "architecture"),
                ],
            )
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_interleaved_non_phase_events_ignored(self):
        # Non-PhaseAdvanced events between the phase transitions don't break
        # the chain — only PhaseAdvanced events are walked, in log order.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_events(
                state,
                [
                    _phase_advanced(0, None, "kickoff"),
                    _other_event(1),
                    _phase_advanced(2, "kickoff", "vision"),
                    _other_event(3),
                    _phase_advanced(4, "vision", "architecture"),
                ],
            )
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())


class TestCheck16Fail(unittest.TestCase):
    def test_chain_break_fails_blocking(self):
        # kickoff -> vision, then a jump claiming from=cost (a phase that was
        # never reached) → break: expected from='vision', got from='cost'.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_events(
                state,
                [
                    _phase_advanced(0, None, "kickoff"),
                    _phase_advanced(1, "kickoff", "vision"),
                    _phase_advanced(2, "cost", "tooling"),
                ],
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            self.assertEqual(result.check_id, "16")
            self.assertEqual(len(result.findings), 1)
            msg = result.findings[0].message
            self.assertIn("phase chain break", msg)
            self.assertIn("expected from='vision'", msg)
            self.assertIn("got from='cost'", msg)
            self.assertIn("to='tooling'", msg)

    def test_multiple_breaks_each_reported(self):
        # Two separate discontinuities → two findings.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_events(
                state,
                [
                    _phase_advanced(0, None, "kickoff"),
                    _phase_advanced(1, "vision", "architecture"),  # break #1
                    _phase_advanced(2, "stack", "cost"),  # break #2
                ],
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            self.assertEqual(len(result.findings), 2)
            self.assertIn("expected from='kickoff'", result.findings[0].message)
            self.assertIn("got from='vision'", result.findings[0].message)
            self.assertIn("expected from='architecture'", result.findings[1].message)
            self.assertIn("got from='stack'", result.findings[1].message)

    def test_first_event_from_nonnull_then_break(self):
        # The first PhaseAdvanced's 'from' is never gated (may be None or
        # any value). The break is detected on the SUBSEQUENT event.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_events(
                state,
                [
                    _phase_advanced(0, "kickoff", "vision"),
                    _phase_advanced(1, "architecture", "stack"),  # break
                ],
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(len(result.findings), 1)
            self.assertIn("expected from='vision'", result.findings[0].message)
            self.assertIn("got from='architecture'", result.findings[0].message)


if __name__ == "__main__":
    unittest.main()
