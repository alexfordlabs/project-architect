"""Tests for architect_brain.catalog.detect_cycles."""

import unittest

from architect_brain.catalog import detect_cycles


def _doc(depends_on):
    return {"depends_on": depends_on}


class TestDetectCycles(unittest.TestCase):

    def test_acyclic_returns_empty(self):
        docs = {"A": _doc([]), "B": _doc(["A"]), "C": _doc(["A", "B"])}
        self.assertEqual(detect_cycles(docs), [])

    def test_direct_cycle(self):
        docs = {"A": _doc(["B"]), "B": _doc(["A"])}
        cycle = detect_cycles(docs)
        self.assertTrue(cycle)
        # witness starts and ends on the same node
        self.assertEqual(cycle[0], cycle[-1])

    def test_self_loop(self):
        docs = {"A": _doc(["A"])}
        self.assertEqual(detect_cycles(docs), ["A", "A"])

    def test_longer_cycle(self):
        docs = {"A": _doc(["B"]), "B": _doc(["C"]), "C": _doc(["A"])}
        cycle = detect_cycles(docs)
        self.assertEqual(cycle[0], cycle[-1])
        self.assertEqual(set(cycle), {"A", "B", "C"})

    def test_dependency_outside_set_is_not_a_cycle(self):
        docs = {"A": _doc(["external"])}
        self.assertEqual(detect_cycles(docs), [])


if __name__ == "__main__":
    unittest.main()
