"""Tests for architect_brain.severity.CheckResult + Finding dataclasses."""

import dataclasses
import unittest

from architect_brain.severity import CheckResult, Finding


class TestCheckResult(unittest.TestCase):

    def test_construct_minimal(self):
        r = CheckResult(check_id="05", passed=True, severity="INFO", summary="ok")
        self.assertEqual(r.check_id, "05")
        self.assertTrue(r.passed)
        self.assertEqual(r.severity, "INFO")
        self.assertEqual(r.summary, "ok")
        self.assertEqual(r.findings, ())

    def test_with_findings(self):
        f = Finding(message="broken link", location="docs/X.md:12")
        r = CheckResult(check_id="01", passed=False, severity="BLOCKING",
                        summary="1 broken link", findings=(f,))
        self.assertEqual(len(r.findings), 1)
        self.assertEqual(r.findings[0].message, "broken link")
        self.assertEqual(r.findings[0].location, "docs/X.md:12")

    def test_finding_location_optional(self):
        f = Finding(message="no location")
        self.assertIsNone(f.location)

    def test_checkresult_is_frozen(self):
        r = CheckResult(check_id="05", passed=True, severity="INFO", summary="ok")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            r.passed = False  # type: ignore[misc]

    def test_finding_is_frozen(self):
        f = Finding(message="x")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            f.message = "y"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
