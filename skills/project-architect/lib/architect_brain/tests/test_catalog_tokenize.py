"""Tests for architect_brain.catalog.tokenize — conditions DSL lexer."""

import unittest

from architect_brain.catalog import ConditionError, Token, tokenize


class TestTokenize(unittest.TestCase):

    def test_key_eq_string(self):
        self.assertEqual(
            tokenize("stack.frontend.framework == 'next.js'"),
            [
                Token("KEY", "stack.frontend.framework"),
                Token("OP", "=="),
                Token("LIT", "next.js"),
            ],
        )

    def test_double_quoted_string(self):
        self.assertEqual(tokenize('a == "x"'), [Token("KEY", "a"), Token("OP", "=="), Token("LIT", "x")])

    def test_bool_and_null_literals(self):
        self.assertEqual(tokenize("ai.enabled == true")[2], Token("LIT", True))
        self.assertEqual(tokenize("ai.enabled == false")[2], Token("LIT", False))
        self.assertEqual(tokenize("ai.enabled == null")[2], Token("LIT", None))

    def test_numbers_int_and_float(self):
        self.assertEqual(tokenize("scale > 5")[2], Token("LIT", 5))
        self.assertEqual(tokenize("ratio < 1.5")[2], Token("LIT", 1.5))

    def test_keywords_uppercase(self):
        self.assertEqual(
            tokenize("a == 1 AND b == 2 OR EXISTS c"),
            [
                Token("KEY", "a"), Token("OP", "=="), Token("LIT", 1),
                Token("KW", "AND"),
                Token("KEY", "b"), Token("OP", "=="), Token("LIT", 2),
                Token("KW", "OR"),
                Token("KW", "EXISTS"), Token("KEY", "c"),
            ],
        )

    def test_in_list_and_parens(self):
        toks = tokenize("(x IN ['a', 'b'])")
        kinds = [t.kind for t in toks]
        self.assertEqual(
            kinds,
            ["LPAREN", "KEY", "KW", "LBRACKET", "LIT", "COMMA", "LIT", "RBRACKET", "RPAREN"],
        )

    def test_not_stays_separate_token(self):
        # 'NOT IN' / 'NOT EXISTS' are combined by the PARSER, not the lexer.
        toks = tokenize("x NOT IN ['a']")
        self.assertEqual(toks[1], Token("KW", "NOT"))
        self.assertEqual(toks[2], Token("KW", "IN"))

    def test_always(self):
        self.assertEqual(tokenize("ALWAYS"), [Token("KW", "ALWAYS")])

    def test_unexpected_character_raises(self):
        with self.assertRaises(ConditionError):
            tokenize("a == @")


if __name__ == "__main__":
    unittest.main()
