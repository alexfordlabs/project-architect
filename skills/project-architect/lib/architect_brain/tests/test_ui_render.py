"""Tests for architect_brain.ui progress / step / phase_bar (ported from v7)."""

import unittest

from architect_brain.ui import phase_bar, progress, step


class TestProgress(unittest.TestCase):

    def test_zero_is_empty_bar(self):
        out = progress(0, 11, "x")
        self.assertIn("0%", out)
        self.assertNotIn("█", out)

    def test_full_is_hundred_percent(self):
        out = progress(11, 11, "x")
        self.assertIn("100%", out)
        self.assertNotIn("░", out)

    def test_divide_by_zero_guard(self):
        out = progress(5, 0, "x")     # total <= 0 must not crash
        self.assertIn("0%", out)

    def test_overcount_clamps(self):
        out = progress(99, 11, "x")   # current > total clamps to 100%/full
        self.assertIn("100%", out)

    def test_includes_label_and_counts(self):
        out = progress(3, 11, "Architecture")
        self.assertIn("3/11", out)
        self.assertIn("Architecture", out)

    def test_trailing_newline(self):
        self.assertTrue(progress(1, 11, "x").endswith("\n"))


class TestStep(unittest.TestCase):

    def test_symbol_and_text(self):
        self.assertEqual(step("✓", "done"), "✓ done\n")


class TestPhaseBar(unittest.TestCase):

    def test_architecture_is_step_3(self):
        out = phase_bar("architecture")
        self.assertIn("3/11", out)
        self.assertIn("Architecture", out)

    def test_stack_is_step_4_after_architecture(self):
        # v8 reorder: Tech Stack comes AFTER Architecture
        out = phase_bar("stack")
        self.assertIn("4/11", out)
        self.assertIn("Tech stack", out)

    def test_cost_is_step_5(self):
        self.assertIn("5/11", phase_bar("cost"))

    def test_complete_is_step_11(self):
        self.assertIn("11/11", phase_bar("complete"))

    def test_preflight_is_banner_only(self):
        self.assertEqual(phase_bar("preflight"), "")

    def test_unknown_key_is_noop(self):
        self.assertEqual(phase_bar("bogus"), "")

    def test_deterministic(self):
        self.assertEqual(phase_bar("architecture"), phase_bar("architecture"))


if __name__ == "__main__":
    unittest.main()
