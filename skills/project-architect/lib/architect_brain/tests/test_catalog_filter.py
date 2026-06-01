"""Tests for architect_brain.catalog.filter_applicable."""

import unittest

from architect_brain.catalog import filter_applicable


def _doc(conditions, depends_on=None):
    return {
        "conditions": conditions,
        "depends_on": depends_on or [],
        "produces": [], "produced_by": "document-author",
        "template": "t.md", "phase": "doc_generation", "concern": "vision",
    }


CATALOG = {
    "schema_version": "4.0",
    "catalog_version": "8.0.0",
    "documents": {
        "ALWAYS_DOC": _doc(["ALWAYS"]),
        "AI_DOC": _doc(["ai.enabled == true"]),
        "MOBILE_DOC": _doc(["project.type == 'mobile_app'"]),
        "MULTI_LINE_DOC": _doc(["ai.enabled == true", "AND scale > 3"]),
    },
}

FLAT = {"decisions": {"ai.enabled": True, "project.type": "web_app", "scale": 5}}


class TestFilterApplicable(unittest.TestCase):

    def test_keeps_always_and_true_conditions(self):
        applicable = filter_applicable(CATALOG, FLAT)
        self.assertIn("ALWAYS_DOC", applicable)
        self.assertIn("AI_DOC", applicable)
        self.assertIn("MULTI_LINE_DOC", applicable)

    def test_excludes_false_conditions(self):
        applicable = filter_applicable(CATALOG, FLAT)
        self.assertNotIn("MOBILE_DOC", applicable)

    def test_multi_line_conditions_are_space_joined(self):
        # "ai.enabled == true" + "AND scale > 3" → one expression, both true
        self.assertIn("MULTI_LINE_DOC", filter_applicable(CATALOG, FLAT))
        flat_low = {"decisions": {"ai.enabled": True, "scale": 1}}
        self.assertNotIn("MULTI_LINE_DOC", filter_applicable(CATALOG, flat_low))

    def test_preserves_catalog_insertion_order(self):
        applicable = filter_applicable(CATALOG, FLAT)
        self.assertEqual(
            list(applicable.keys()),
            ["ALWAYS_DOC", "AI_DOC", "MULTI_LINE_DOC"],
        )

    def test_returns_full_doc_objects(self):
        applicable = filter_applicable(CATALOG, FLAT)
        self.assertEqual(applicable["AI_DOC"]["produced_by"], "document-author")


if __name__ == "__main__":
    unittest.main()
