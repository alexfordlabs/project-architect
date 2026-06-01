"""Tests for architect_brain.severity — the 4-tier auditor severity model."""

import unittest

from architect_brain.severity import (
    SEVERITY_LEVELS,
    blocks_lock,
    severity_rank,
    worst_severity,
)


class TestSeverity(unittest.TestCase):

    def test_four_levels(self):
        self.assertEqual(set(SEVERITY_LEVELS), {"INFO", "WARNING", "BLOCKING", "FATAL"})

    def test_rank_ordering(self):
        self.assertLess(severity_rank("INFO"), severity_rank("WARNING"))
        self.assertLess(severity_rank("WARNING"), severity_rank("BLOCKING"))
        self.assertLess(severity_rank("BLOCKING"), severity_rank("FATAL"))

    def test_rank_unknown_raises(self):
        with self.assertRaises(ValueError):
            severity_rank("BOGUS")

    def test_worst_of_mixed(self):
        self.assertEqual(worst_severity(["INFO", "FATAL", "WARNING"]), "FATAL")
        self.assertEqual(worst_severity(["INFO", "WARNING"]), "WARNING")

    def test_worst_of_empty_is_none(self):
        self.assertIsNone(worst_severity([]))

    def test_fatal_always_blocks(self):
        self.assertTrue(blocks_lock("FATAL", acked=False))
        self.assertTrue(blocks_lock("FATAL", acked=True))  # ack does NOT override FATAL

    def test_blocking_blocks_unless_acked(self):
        self.assertTrue(blocks_lock("BLOCKING", acked=False))
        self.assertFalse(blocks_lock("BLOCKING", acked=True))

    def test_warning_and_info_never_block(self):
        for sev in ("WARNING", "INFO"):
            self.assertFalse(blocks_lock(sev, acked=False))
            self.assertFalse(blocks_lock(sev, acked=True))


if __name__ == "__main__":
    unittest.main()
