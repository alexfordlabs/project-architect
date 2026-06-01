"""Tests for the check_05_json_valid auditor check + the ALL_CHECKS registry."""

import tempfile
import unittest
from pathlib import Path

from architect_brain.checks import ALL_CHECKS, check_05_json_valid


def _state(tmp: str, files: dict[str, str]) -> Path:
    state = Path(tmp) / "docs" / "_architect_state"
    state.mkdir(parents=True)
    for rel, content in files.items():
        p = state / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return state


class TestCheck05(unittest.TestCase):

    def test_module_contract(self):
        self.assertEqual(check_05_json_valid.CHECK_ID, "05")
        self.assertTrue(hasattr(check_05_json_valid, "run"))

    def test_registered_in_all_checks(self):
        self.assertIn(check_05_json_valid, ALL_CHECKS)

    def test_pass_when_all_json_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {"stack.json": '{"ok": true}', "decisions/index.json": '{"adrs": []}'})
            result = check_05_json_valid.run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "05")

    def test_fail_on_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {"stack.json": '{"ok": true}', "broken.json": "{not json"})
            result = check_05_json_valid.run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "BLOCKING")
            self.assertTrue(any("broken.json" in (f.location or "") for f in result.findings))

    def test_pass_when_no_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, {})
            self.assertTrue(check_05_json_valid.run(state).passed)


if __name__ == "__main__":
    unittest.main()
