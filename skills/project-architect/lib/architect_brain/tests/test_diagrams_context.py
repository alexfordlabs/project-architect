"""Tests for architect_brain.diagrams.gen_c4_context."""

import unittest

from architect_brain.diagrams import gen_c4_context


def _fi(decisions=None):
    return {"schema_version": "4.0", "decisions": decisions or {}, "adrs": []}


class TestGenC4Context(unittest.TestCase):

    def test_starts_with_c4context(self):
        self.assertTrue(gen_c4_context(_fi()).startswith("C4Context"))

    def test_title_includes_name(self):
        out = gen_c4_context(_fi({"project.name": "MyApp"}))
        self.assertIn("MyApp", out)

    def test_has_person_and_system(self):
        out = gen_c4_context(_fi())
        self.assertIn("Person(", out)
        self.assertIn("System(", out)
        self.assertIn("Rel(", out)

    def test_external_database_adds_system_ext(self):
        out = gen_c4_context(_fi({"stack.database.engine": "postgres"}))
        self.assertIn("System_Ext(", out)
        self.assertIn("postgres", out)

    def test_no_system_ext_without_database(self):
        self.assertNotIn("System_Ext(", gen_c4_context(_fi()))

    def test_trailing_newline_and_deterministic(self):
        fi = _fi({"project.name": "X", "stack.database.engine": "postgres"})
        out = gen_c4_context(fi)
        self.assertTrue(out.endswith("\n"))
        self.assertEqual(gen_c4_context(fi), gen_c4_context(fi))


if __name__ == "__main__":
    unittest.main()
