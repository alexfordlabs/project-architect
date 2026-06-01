"""Tests for the check_31_resume_test auditor check.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from architect_brain import projections
from architect_brain.checks import check_31_resume_test
from architect_brain.checks.check_31_resume_test import CHECK_ID, NAME, SEVERITY, run


def _make_state(tmp: str) -> Path:
    """Create ``<tmp>/docs/_architect_state`` and return it.

    project_root = state_dir.parent.parent = ``<tmp>``.
    """
    state = Path(tmp) / "docs" / "_architect_state"
    state.mkdir(parents=True)
    return state


def _decision_line(key: str, value, *, ulid: str = "01J0000000000000000000000A") -> str:
    """A minimal well-formed DecisionMade JSONL event line."""
    return json.dumps(
        {
            "id": ulid,
            "ts": "2026-05-27T15:23:11Z",
            "by": "orchestrator",
            "phase": "stack",
            "type": "DecisionMade",
            "payload": {"key": key, "value": value},
        },
        separators=(",", ":"),
        sort_keys=True,
    )


def _write_events(state_dir: Path, lines: list[str]) -> None:
    (state_dir / "events.jsonl").write_text(
        "".join(line + "\n" for line in lines), encoding="utf-8"
    )


def _materialise(state_dir: Path) -> None:
    """Replay events.jsonl → projections → write a CONSISTENT state to disk."""
    replayed = projections.replay(state_dir / "events.jsonl")
    projections.projections_to_disk(state_dir, replayed)


class TestCheck31Contract(unittest.TestCase):
    def test_module_contract(self):
        self.assertEqual(CHECK_ID, "31")
        self.assertEqual(NAME, "resume_test")
        self.assertEqual(SEVERITY, "FATAL")
        self.assertTrue(callable(run))
        self.assertEqual(check_31_resume_test.CHECK_ID, "31")
        self.assertTrue(callable(check_31_resume_test.run))


class TestCheck31Degraded(unittest.TestCase):
    def test_empty_state_no_events_passes(self):
        # No events at all → replay yields empty projections; projections_to_disk
        # writes them; everything matches. Pass.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_events(state, [])
            _materialise(state)
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "31")
            self.assertEqual(result.findings, ())

    def test_no_events_file_no_projections_passes(self):
        # Neither events.jsonl nor projection files on disk. replay over a
        # missing log yields empty projections; every on-disk file is absent
        # but every replayed concern is empty → no drift. Pass.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())


class TestCheck31Pass(unittest.TestCase):
    def test_consistent_state_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_events(
                state,
                [
                    _decision_line("stack.backend.framework", "fastapi"),
                    _decision_line(
                        "vision.problem",
                        "users can't find X",
                        ulid="01J0000000000000000000000B",
                    ),
                ],
            )
            _materialise(state)
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_key_order_and_whitespace_are_not_drift(self):
        # Rewrite a concern file with different key ordering + indentation. The
        # PARSED dict is identical → no drift (proves parsed-dict comparison).
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_events(state, [_decision_line("stack.backend.framework", "fastapi")])
            _materialise(state)
            stack_path = state / "stack.json"
            parsed = json.loads(stack_path.read_text(encoding="utf-8"))
            # Re-serialise with NO sort_keys and a different indent.
            stack_path.write_text(
                json.dumps(parsed, indent=4, sort_keys=False), encoding="utf-8"
            )
            result = run(state)
            self.assertTrue(result.passed)


class TestCheck31Fail(unittest.TestCase):
    def test_tampered_concern_file_fails_fatal(self):
        # Materialise a consistent state, then hand-edit stack.json to inject a
        # bogus decision the event log doesn't contain → replay != on-disk.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_events(state, [_decision_line("stack.backend.framework", "fastapi")])
            _materialise(state)
            stack_path = state / "stack.json"
            parsed = json.loads(stack_path.read_text(encoding="utf-8"))
            parsed["decisions"]["stack.bogus.injected"] = "not-in-the-log"
            stack_path.write_text(json.dumps(parsed, indent=2), encoding="utf-8")
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "FATAL")
            self.assertEqual(result.check_id, "31")
            self.assertTrue(result.findings)
            self.assertTrue(
                any("stack.json" in f.message for f in result.findings),
                result.findings,
            )

    def test_tampered_flat_index_fails_fatal(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_events(state, [_decision_line("stack.backend.framework", "fastapi")])
            _materialise(state)
            flat_path = state / "99-flat-index.json"
            parsed = json.loads(flat_path.read_text(encoding="utf-8"))
            parsed["decisions"]["vision.tampered"] = "ghost"
            flat_path.write_text(json.dumps(parsed, indent=2), encoding="utf-8")
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "FATAL")
            self.assertTrue(
                any("99-flat-index.json" in f.message for f in result.findings),
                result.findings,
            )

    def test_missing_concern_file_with_nonempty_replay_fails(self):
        # Consistent state, then DELETE a concern file that replay populates.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_events(state, [_decision_line("stack.backend.framework", "fastapi")])
            _materialise(state)
            (state / "stack.json").unlink()
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "FATAL")
            self.assertTrue(
                any("stack.json" in f.message for f in result.findings),
                result.findings,
            )

    def test_unreplayable_log_fails_fatal(self):
        # replay() uses the STRICT reader and RAISES on a corrupt log. The check
        # must catch that and emit a single FATAL finding, not crash the auditor.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_events(state, ["{not valid json at all"])
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "FATAL")
            self.assertTrue(result.findings)
            self.assertIn("unreplayable", result.findings[0].message.lower())

    def test_replay_raising_does_not_propagate(self):
        # Belt-and-suspenders: even if replay raises an arbitrary exception, the
        # check returns a FATAL CheckResult rather than letting it propagate.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_events(state, [_decision_line("stack.backend.framework", "fastapi")])
            _materialise(state)
            with mock.patch.object(
                check_31_resume_test, "replay", side_effect=RuntimeError("boom")
            ):
                result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "FATAL")
            self.assertIn("unreplayable", result.findings[0].message.lower())


if __name__ == "__main__":
    unittest.main()
