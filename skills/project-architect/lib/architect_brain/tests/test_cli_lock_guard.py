"""Tests for the mechanical LOCK gate on `append-event --type LockSet`.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT

The v8.0.1 enforcement fix: emitting a LockSet that *locks* the design
(`payload.locked` True, or absent — a bare LockSet defaults to locked) must
REFUSE unless the most recent recorded audit verdict is `clean`. This converts
the LOCK gate from advisory SKILL prose into a mechanical block the orchestrator
cannot step past. `--force` is the audited escape hatch.
"""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from architect_brain.__main__ import main


class TestLockGuard(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.docs = Path(self.tmp.name) / "docs"
        self.docs.mkdir()
        main(["init", "--docs-dir", str(self.docs)])

    def tearDown(self):
        self.tmp.cleanup()

    def _state_dir(self) -> Path:
        return self.docs / "_architect_state"

    def _record_audit(self, result: str) -> None:
        """Append an AuditCompleted event with the given verdict via append-event."""
        main([
            "append-event", "--docs-dir", str(self.docs),
            "--type", "AuditCompleted",
            "--payload", json.dumps(
                {"result": result, "checks_passed": 30, "checks_failed": 4}
            ),
        ])

    def _lock(self, *extra: str, payload: dict | None = None) -> tuple[int, str]:
        """Run `append-event --type LockSet`; return (exit_code, stderr)."""
        pl = {"locked": True, "version": "v1.0"} if payload is None else payload
        err = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(err):
            code = main([
                "append-event", "--docs-dir", str(self.docs),
                "--type", "LockSet", "--payload", json.dumps(pl), *extra,
            ])
        return code, err.getvalue()

    def _is_locked(self) -> bool:
        wf = json.loads((self._state_dir() / "workflow.json").read_text())
        return wf.get("locked") is True

    def _lockset_events(self) -> int:
        log = (self._state_dir() / "events.jsonl").read_text().splitlines()
        return sum(1 for line in log if line and json.loads(line)["type"] == "LockSet")

    # ── refusal cases ────────────────────────────────────────────────────────
    def test_lockset_refused_when_latest_audit_blocked(self):
        self._record_audit("blocked")
        code, err = self._lock()
        self.assertEqual(code, 1)
        self.assertIn("blocked", err.lower())
        self.assertFalse(self._is_locked())
        self.assertEqual(self._lockset_events(), 0)  # the event was NOT written

    def test_lockset_refused_when_no_audit_recorded(self):
        # No audit at all => the lock is unverified => refuse.
        code, err = self._lock()
        self.assertEqual(code, 1)
        self.assertIn("audit", err.lower())
        self.assertFalse(self._is_locked())

    def test_bare_lockset_defaults_to_locked_and_is_guarded(self):
        # A LockSet with no `locked` key defaults to locked=True (projections.py),
        # so the guard must fire on it too.
        self._record_audit("blocked")
        code, _ = self._lock(payload={"version": "v1.0"})
        self.assertEqual(code, 1)
        self.assertFalse(self._is_locked())

    def test_lockset_refused_when_blocked_is_the_newest_audit(self):
        # A clean audit followed by a blocked one => newest is blocked => refuse.
        self._record_audit("clean")
        self._record_audit("blocked")
        code, _ = self._lock()
        self.assertEqual(code, 1)
        self.assertFalse(self._is_locked())

    # ── allow cases ──────────────────────────────────────────────────────────
    def test_lockset_allowed_when_latest_audit_clean(self):
        self._record_audit("clean")
        code, _ = self._lock()
        self.assertEqual(code, 0)
        self.assertTrue(self._is_locked())
        self.assertEqual(self._lockset_events(), 1)

    def test_lockset_clean_after_blocked_allowed(self):
        # blocked then re-run clean => newest is clean => allow.
        self._record_audit("blocked")
        self._record_audit("clean")
        code, _ = self._lock()
        self.assertEqual(code, 0)
        self.assertTrue(self._is_locked())

    def test_force_overrides_blocked_audit(self):
        self._record_audit("blocked")
        code, err = self._lock("--force")
        self.assertEqual(code, 0)
        self.assertTrue(self._is_locked())
        self.assertIn("force", err.lower())  # the override is announced

    def test_unlock_lockset_is_not_guarded(self):
        # An UNLOCK (locked=false, the /iterate-design path) must always be allowed,
        # even atop a blocked audit — it isn't a lock.
        self._record_audit("blocked")
        code, _ = self._lock(payload={"locked": False, "version": "v1.1-draft"})
        self.assertEqual(code, 0)
        self.assertFalse(self._is_locked())

    def test_non_lockset_event_is_not_guarded(self):
        # Sanity: a normal DecisionMade is unaffected by the guard even with no audit.
        code = main([
            "append-event", "--docs-dir", str(self.docs),
            "--type", "DecisionMade",
            "--payload", json.dumps({"key": "stack.frontend.framework", "value": "next.js"}),
        ])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
