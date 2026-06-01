"""Tests for architect_brain.ui.banner — ported from v7 bin/architect-ui."""

import unittest

from architect_brain.ui import banner


class TestBanner(unittest.TestCase):

    def test_contains_architect_literal(self):
        # The plain-text tagline guarantees the literal substring (the test
        # contract carried over from v7 — block-char art alone wouldn't match).
        self.assertIn("architect", banner())

    def test_contains_project_architect(self):
        self.assertIn("project-architect", banner())

    def test_has_tagline(self):
        self.assertIn("design-first", banner())

    def test_has_blockchar_row(self):
        # the wordmark uses Unicode block chars
        self.assertIn("█", banner())

    def test_trailing_newline_and_deterministic(self):
        out = banner()
        self.assertTrue(out.endswith("\n"))
        self.assertEqual(banner(), banner())


if __name__ == "__main__":
    unittest.main()
