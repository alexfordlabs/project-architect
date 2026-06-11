"""Tests for check_35_user_provenance (v8.0.1).

A LOCKED project whose DecisionMade events are ALL orchestrator-sourced (zero
by:"user") means the interview was never recorded as user-confirmed — the
"didn't ask the questions" failure mode, otherwise invisible in the ledger.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
"""

import json
import tempfile
import unittest
from pathlib import Path

from architect_brain.checks import check_35_user_provenance
from architect_brain.checks.check_35_user_provenance import CHECK_ID, NAME, SEVERITY, run


def _make_state(tmp: str, *, locked: bool, decisions: list[tuple[str, str]]) -> Path:
    """Create state with a workflow (locked flag) + DecisionMade events.

    ``decisions`` is a list of (by, key) pairs.
    """
    state = Path(tmp) / "docs" / "_architect_state"
    state.mkdir(parents=True)
    (state / "workflow.json").write_text(
        json.dumps({"locked": locked, "audits": []}), encoding="utf-8"
    )
    lines = []
    for i, (by, key) in enumerate(decisions):
        lines.append(json.dumps({
            "id": f"01HXYZABCDEFG12345678{i:05d}",
            "ts": "2026-05-29T11:00:00Z",
            "by": by,
            "phase": "stack",
            "type": "DecisionMade",
            "payload": {"key": key, "value": "v"},
        }))
    (state / "events.jsonl").write_text(
        ("\n".join(lines) + "\n") if lines else "", encoding="utf-8"
    )
    return state


class TestCheck35Contract(unittest.TestCase):
    def test_module_contract(self):
        self.assertEqual(CHECK_ID, "35")
        self.assertEqual(NAME, "user_provenance")
        self.assertEqual(SEVERITY, "WARNING")
        self.assertTrue(callable(run))


class TestCheck35Pass(unittest.TestCase):
    def test_not_locked_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp, locked=False, decisions=[("orchestrator", "stack.a")])
            self.assertTrue(run(state).passed)

    def test_locked_no_decisions_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp, locked=True, decisions=[])
            self.assertTrue(run(state).passed)

    def test_locked_with_user_decision_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp, locked=True, decisions=[
                ("orchestrator", "git.repo_init"),
                ("user", "stack.frontend.framework"),
            ])
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.findings, ())


class TestCheck35Fail(unittest.TestCase):
    def test_locked_all_orchestrator_fails_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _make_state(tmp, locked=True, decisions=[
                ("orchestrator", "stack.frontend.framework"),
                ("orchestrator", "stack.backend.language"),
                ("architecture-specialist", "architecture.style"),
            ])
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")
            self.assertEqual(result.check_id, "35")
            self.assertEqual(len(result.findings), 1)
            self.assertIn("user", result.findings[0].message.lower())


if __name__ == "__main__":
    unittest.main()
