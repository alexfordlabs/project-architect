"""Tests for architect_brain.catalog.parse_condition — DSL recursive-descent parser."""

import unittest

from architect_brain.catalog import ConditionError, parse_condition


class TestParseCondition(unittest.TestCase):

    def test_always(self):
        self.assertEqual(parse_condition("ALWAYS"), ("always",))

    def test_simple_eq(self):
        self.assertEqual(
            parse_condition("project.type == 'web_app'"),
            ("cmp", "==", "project.type", "web_app"),
        )

    def test_neq_and_numeric(self):
        self.assertEqual(parse_condition("scale != 0"), ("cmp", "!=", "scale", 0))
        self.assertEqual(parse_condition("scale > 5"), ("cmp", ">", "scale", 5))
        self.assertEqual(parse_condition("scale < 5"), ("cmp", "<", "scale", 5))

    def test_in_list(self):
        self.assertEqual(
            parse_condition("project.type IN ['mcp_server', 'agentic_system']"),
            ("cmp", "IN", "project.type", ["mcp_server", "agentic_system"]),
        )

    def test_not_in(self):
        self.assertEqual(
            parse_condition("scale NOT IN ['hobby']"),
            ("cmp", "NOT IN", "scale", ["hobby"]),
        )

    def test_exists_and_not_exists(self):
        self.assertEqual(parse_condition("EXISTS auth.choice"), ("exists", "auth.choice"))
        self.assertEqual(parse_condition("NOT EXISTS auth.choice"), ("not_exists", "auth.choice"))

    def test_and_binds_tighter_than_or(self):
        # a OR b AND c  ==  a OR (b AND c)
        ast = parse_condition("a == 1 OR b == 2 AND c == 3")
        self.assertEqual(ast[0], "or")
        self.assertEqual(ast[1], ("cmp", "==", "a", 1))
        self.assertEqual(ast[2][0], "and")

    def test_explicit_parens_override(self):
        # (a OR b) AND c  →  top node is AND
        ast = parse_condition("(a == 1 OR b == 2) AND c == 3")
        self.assertEqual(ast[0], "and")
        self.assertEqual(ast[1][0], "or")

    def test_empty_raises(self):
        with self.assertRaises(ConditionError):
            parse_condition("")

    def test_trailing_tokens_raise(self):
        with self.assertRaises(ConditionError):
            parse_condition("a == 1 b == 2")  # missing connector

    def test_gt_requires_number(self):
        with self.assertRaises(ConditionError):
            parse_condition("a > 'x'")


if __name__ == "__main__":
    unittest.main()
