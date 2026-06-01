"""Tests for architect_brain.ulid — Crockford-base32 monotonic ULIDs.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
"""

import re
import time
import unittest

from architect_brain.ulid import new_ulid, ulid_to_ms


class TestULID(unittest.TestCase):

    def test_length_is_26(self):
        self.assertEqual(len(new_ulid()), 26)

    def test_crockford_charset_only(self):
        valid = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")
        for _ in range(100):
            self.assertRegex(new_ulid(), valid)

    def test_sortable_monotonic_within_same_ms(self):
        # When two ULIDs share the same millisecond, the second is lexicographically greater.
        ms = int(time.time() * 1000)
        a = new_ulid(timestamp_ms=ms)
        b = new_ulid(timestamp_ms=ms)
        self.assertLess(a, b)

    def test_timestamp_recoverable(self):
        ms = 1716859200000  # 2024-05-28T00:00:00Z
        u = new_ulid(timestamp_ms=ms)
        self.assertEqual(ulid_to_ms(u), ms)


if __name__ == "__main__":
    unittest.main()
