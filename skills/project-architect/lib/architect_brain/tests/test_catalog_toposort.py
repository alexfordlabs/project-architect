"""Tests for architect_brain.catalog.topo_sort — Kahn's algorithm."""

import unittest

from architect_brain.catalog import CycleError, topo_sort


def _doc(depends_on):
    return {"depends_on": depends_on}


class TestTopoSort(unittest.TestCase):

    def test_respects_dependencies(self):
        docs = {"B": _doc(["A"]), "A": _doc([]), "C": _doc(["A"])}
        order = topo_sort(docs)
        self.assertLess(order.index("A"), order.index("B"))
        self.assertLess(order.index("A"), order.index("C"))

    def test_alphabetical_tiebreak_among_roots(self):
        docs = {"Z": _doc([]), "A": _doc([]), "M": _doc([])}
        self.assertEqual(topo_sort(docs), ["A", "M", "Z"])

    def test_alphabetical_tiebreak_among_ready_children(self):
        # A unblocks both Y and B; B comes first alphabetically.
        docs = {"A": _doc([]), "Y": _doc(["A"]), "B": _doc(["A"])}
        self.assertEqual(topo_sort(docs), ["A", "B", "Y"])

    def test_deterministic_repeatable(self):
        docs = {"A": _doc([]), "B": _doc(["A"]), "C": _doc(["A", "B"])}
        self.assertEqual(topo_sort(docs), topo_sort(docs))
        self.assertEqual(topo_sort(docs), ["A", "B", "C"])

    def test_dependency_outside_set_is_ignored(self):
        # B depends on A, but A is not in the applicable set → treat B as a root.
        docs = {"B": _doc(["A"]), "C": _doc([])}
        self.assertEqual(topo_sort(docs), ["B", "C"])

    def test_cycle_raises(self):
        docs = {"A": _doc(["B"]), "B": _doc(["A"])}
        with self.assertRaises(CycleError):
            topo_sort(docs)

    def test_empty(self):
        self.assertEqual(topo_sort({}), [])


if __name__ == "__main__":
    unittest.main()
