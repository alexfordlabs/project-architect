"""Tests for architect_brain.catalog.eval_condition — DSL evaluation."""

import unittest

from architect_brain.catalog import eval_condition


FLAT = {
    "schema_version": "4.0",
    "decisions": {
        "project.type": "web_app",
        "ai.enabled": True,
        "ai.agent": False,
        "scale": 5,
        "auth.choice": "clerk",
        "nullable": None,
    },
    "adrs": [],
}


class TestEvalCondition(unittest.TestCase):

    def test_always(self):
        self.assertTrue(eval_condition("ALWAYS", FLAT))

    def test_eq_true_false(self):
        self.assertTrue(eval_condition("project.type == 'web_app'", FLAT))
        self.assertFalse(eval_condition("project.type == 'mobile_app'", FLAT))

    def test_neq(self):
        self.assertTrue(eval_condition("project.type != 'mobile_app'", FLAT))

    def test_bool_literal(self):
        self.assertTrue(eval_condition("ai.enabled == true", FLAT))
        self.assertTrue(eval_condition("ai.agent == false", FLAT))

    def test_in_and_not_in(self):
        self.assertTrue(eval_condition("project.type IN ['web_app', 'mobile_app']", FLAT))
        self.assertTrue(eval_condition("project.type NOT IN ['mcp_server']", FLAT))

    def test_numeric_compare(self):
        self.assertTrue(eval_condition("scale > 3", FLAT))
        self.assertFalse(eval_condition("scale < 3", FLAT))

    def test_numeric_compare_on_missing_is_false(self):
        self.assertFalse(eval_condition("missing.key > 1", FLAT))

    def test_numeric_compare_on_nonnumber_is_false(self):
        self.assertFalse(eval_condition("project.type > 1", FLAT))

    def test_exists_and_not_exists(self):
        self.assertTrue(eval_condition("EXISTS auth.choice", FLAT))
        self.assertFalse(eval_condition("EXISTS missing.key", FLAT))
        self.assertTrue(eval_condition("NOT EXISTS missing.key", FLAT))
        # a present-but-null key does NOT exist
        self.assertFalse(eval_condition("EXISTS nullable", FLAT))

    def test_and_or_composition(self):
        self.assertTrue(eval_condition("ai.enabled == true AND scale > 3", FLAT))
        self.assertFalse(eval_condition("ai.enabled == true AND scale > 99", FLAT))
        self.assertTrue(eval_condition("ai.agent == true OR scale == 5", FLAT))

    def test_parens(self):
        self.assertTrue(eval_condition("(ai.agent == true OR scale == 5) AND project.type == 'web_app'", FLAT))

    def test_missing_decisions_key_in_flat_index(self):
        # flat_index with no 'decisions' map → everything but ALWAYS/NOT EXISTS is false
        self.assertTrue(eval_condition("ALWAYS", {}))
        self.assertFalse(eval_condition("a == 1", {}))


if __name__ == "__main__":
    unittest.main()
