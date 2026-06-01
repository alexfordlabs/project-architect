"""Tests for the check_19_audit_freshness auditor check.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
"""

import json
import tempfile
import unittest
from pathlib import Path

from architect_brain.checks import check_19_audit_freshness
from architect_brain.checks.check_19_audit_freshness import CHECK_ID, NAME, SEVERITY, run


def _make_state(tmp: str) -> Path:
    """Create ``<tmp>/docs/_architect_state`` and return it."""
    state = Path(tmp) / "docs" / "_architect_state"
    state.mkdir(parents=True)
    return state


def _write_workflow(state_dir: Path, workflow: dict) -> None:
    (state_dir / "workflow.json").write_text(
        json.dumps(workflow), encoding="utf-8"
    )


class TestCheck19Contract(unittest.TestCase):
    def test_module_contract(self):
        self.assertEqual(CHECK_ID, "19")
        self.assertEqual(NAME, "audit_freshness")
        self.assertEqual(SEVERITY, "BLOCKING")
        self.assertTrue(callable(run))
        self.assertEqual(check_19_audit_freshness.CHECK_ID, "19")
        self.assertTrue(callable(check_19_audit_freshness.run))


class TestCheck19Degraded(unittest.TestCase):
    def test_no_state_dir_contents_passes(self):
        # Fresh project: no workflow.json at all => nothing to verify.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "19")
            self.assertEqual(result.severity, "BLOCKING")
            self.assertEqual(result.findings, ())

    def test_empty_workflow_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_workflow(state, {})
            result = run(state)
            self.assertTrue(result.passed)

    def test_no_audits_not_locked_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_workflow(
                state, {"current_phase": "docs", "locked": False, "audits": []}
            )
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())


class TestCheck19Pass(unittest.TestCase):
    def test_audit_before_lock_passes(self):
        # The good case: the recorded audit ran BEFORE the lock.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_workflow(
                state,
                {
                    "locked": True,
                    "locked_at": "2026-05-29T12:00:00Z",
                    "audits": [
                        {"ts": "2026-05-29T11:00:00Z", "result": "pass"},
                        {"ts": "2026-05-29T11:59:00Z", "result": "pass"},
                    ],
                },
            )
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())

    def test_audit_equal_to_lock_passes(self):
        # max(audit.ts) == locked_at is NOT strictly AFTER => pass.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_workflow(
                state,
                {
                    "locked": True,
                    "locked_at": "2026-05-29T12:00:00Z",
                    "audits": [{"ts": "2026-05-29T12:00:00Z", "result": "pass"}],
                },
            )
            result = run(state)
            self.assertTrue(result.passed)

    def test_audits_present_not_locked_passes(self):
        # Audits recorded but not locked yet => no post-lock comparison possible.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_workflow(
                state,
                {
                    "locked": False,
                    "audits": [{"ts": "2026-05-29T11:00:00Z", "result": "pass"}],
                },
            )
            result = run(state)
            self.assertTrue(result.passed)

    def test_audits_present_locked_but_no_locked_at_passes(self):
        # locked True but locked_at missing => cannot prove post-lock => pass.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_workflow(
                state,
                {
                    "locked": True,
                    "audits": [{"ts": "2026-05-29T11:00:00Z", "result": "pass"}],
                },
            )
            result = run(state)
            self.assertTrue(result.passed)


class TestCheck19Fail(unittest.TestCase):
    def test_locked_no_audit_fails_blocking(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_workflow(
                state,
                {"locked": True, "locked_at": "2026-05-29T12:00:00Z", "audits": []},
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            self.assertEqual(result.check_id, "19")
            self.assertEqual(len(result.findings), 1)
            self.assertIn("locked", result.findings[0].message)
            self.assertIn("no audit", result.findings[0].message)

    def test_locked_missing_audits_key_fails(self):
        # audits key entirely absent + locked => still the locked-without-audit case.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_workflow(
                state, {"locked": True, "locked_at": "2026-05-29T12:00:00Z"}
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            self.assertEqual(len(result.findings), 1)

    def test_post_lock_audit_fails_blocking(self):
        # The v8-adapted post-lock case: newest audit.ts AFTER locked_at.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_workflow(
                state,
                {
                    "locked": True,
                    "locked_at": "2026-05-29T12:00:00Z",
                    "audits": [
                        {"ts": "2026-05-29T11:00:00Z", "result": "pass"},
                        {"ts": "2026-05-29T12:30:00Z", "result": "pass"},
                    ],
                },
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            self.assertEqual(result.check_id, "19")
            self.assertEqual(len(result.findings), 1)
            # The newest ts and the lock ts both appear in the message.
            self.assertIn("2026-05-29T12:30:00Z", result.findings[0].message)
            self.assertIn("2026-05-29T12:00:00Z", result.findings[0].message)

    def test_post_lock_uses_newest_audit(self):
        # Even if an earlier audit is pre-lock, the NEWEST audit being post-lock fails.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_workflow(
                state,
                {
                    "locked": True,
                    "locked_at": "2026-05-29T10:00:00Z",
                    "audits": [
                        {"ts": "2026-05-29T09:00:00Z"},
                        {"ts": "2026-05-29T09:30:00Z"},
                        {"ts": "2026-05-29T10:00:01Z"},
                    ],
                },
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertIn("2026-05-29T10:00:01Z", result.findings[0].message)


class TestCheck19BlockedVettingAudit(unittest.TestCase):
    """A LOCK is only meaningful atop a CLEAN pre-lock audit, never a blocked one
    (the v8.0.1 enforcement fix: read the vetting audit's `result`, not just `ts`)."""

    def test_locked_atop_blocked_pre_lock_audit_fails_blocking(self):
        # The vetting (newest pre-lock) audit was BLOCKED => the lock is unverified.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_workflow(
                state,
                {
                    "locked": True,
                    "locked_at": "2026-05-29T12:00:00Z",
                    "audits": [
                        {"ts": "2026-05-29T11:00:00Z", "result": "clean"},
                        {"ts": "2026-05-29T11:59:00Z", "result": "blocked"},
                    ],
                },
            )
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            self.assertEqual(result.check_id, "19")
            self.assertEqual(len(result.findings), 1)
            self.assertIn("blocked", result.findings[0].message.lower())
            # The vetting audit's timestamp appears in the message.
            self.assertIn("2026-05-29T11:59:00Z", result.findings[0].message)

    def test_locked_atop_clean_pre_lock_audit_passes(self):
        # Regression guard: a clean vetting audit must still pass.
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp)
            _write_workflow(
                state,
                {
                    "locked": True,
                    "locked_at": "2026-05-29T12:00:00Z",
                    "audits": [
                        {"ts": "2026-05-29T11:00:00Z", "result": "blocked"},
                        {"ts": "2026-05-29T11:59:00Z", "result": "clean"},
                    ],
                },
            )
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())


if __name__ == "__main__":
    unittest.main()
