"""Tests for the check_11_schema_version auditor check."""

import tempfile
import unittest
from pathlib import Path

from architect_brain.checks import check_11_schema_version
from architect_brain.checks.check_11_schema_version import (
    CHECK_ID,
    NAME,
    SEVERITY,
    run,
)


def _state(tmp: str, probe: str | None) -> Path:
    """Build a tempdir state dir; write the schema_version probe iff ``probe`` is not None."""
    state = Path(tmp) / "docs" / "_architect_state"
    state.mkdir(parents=True)
    if probe is not None:
        (state / "schema_version").write_text(probe, encoding="utf-8")
    return state


class TestCheck11(unittest.TestCase):

    def test_module_contract(self):
        self.assertEqual(CHECK_ID, "11")
        self.assertEqual(NAME, "schema_version")
        self.assertEqual(SEVERITY, "WARNING")
        self.assertEqual(check_11_schema_version.CHECK_ID, "11")
        self.assertEqual(check_11_schema_version.NAME, "schema_version")
        self.assertEqual(check_11_schema_version.SEVERITY, "WARNING")
        self.assertTrue(callable(run))
        self.assertTrue(hasattr(check_11_schema_version, "run"))

    def test_pass_when_probe_is_4_0(self):
        # Exactly what projections_to_disk writes: "4.0\n".
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, "4.0\n")
            result = run(state)
            self.assertTrue(result.passed)
            self.assertEqual(result.check_id, "11")
            self.assertEqual(result.findings, ())

    def test_pass_when_probe_is_4_0_no_trailing_newline(self):
        # .strip() handles a probe without the trailing newline too.
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, "4.0")
            result = run(state)
            self.assertTrue(result.passed)

    def test_pass_when_probe_has_surrounding_whitespace(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, "  4.0  \n")
            self.assertTrue(run(state).passed)

    def test_fail_when_probe_missing(self):
        # Degraded/fresh-but-no-probe path: this is a WARNING, not a silent pass,
        # because the probe is written unconditionally by projections_to_disk.
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, None)
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")
            self.assertEqual(len(result.findings), 1)
            self.assertIn("missing", result.findings[0].message.lower())

    def test_fail_when_probe_wrong_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, "3.0\n")
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")
            self.assertEqual(len(result.findings), 1)
            self.assertIn("3.0", result.findings[0].message)
            self.assertIn("4.0", result.findings[0].message)

    def test_fail_when_probe_empty(self):
        # An empty probe strips to "" which != "4.0" -> wrong value.
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, "\n")
            result = run(state)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")
            self.assertEqual(len(result.findings), 1)

    def test_never_raises_on_missing_state_dir(self):
        # Defensive: a state_dir that does not exist must still return a CheckResult.
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "does" / "not" / "exist"
            result = run(missing)
            self.assertFalse(result.passed)
            self.assertEqual(result.severity, "WARNING")

    def test_accepts_str_state_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = _state(tmp, "4.0\n")
            result = run(str(state))
            self.assertTrue(result.passed)


if __name__ == "__main__":
    unittest.main()
