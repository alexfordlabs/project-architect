"""Tests for architect_brain.diagrams.gen_c4_container."""

import unittest

from architect_brain.diagrams import gen_c4_container


def _fi(decisions=None):
    return {"schema_version": "4.0", "decisions": decisions or {}, "adrs": []}


class TestGenC4Container(unittest.TestCase):

    def test_starts_with_c4container(self):
        self.assertTrue(gen_c4_container(_fi()).startswith("C4Container"))

    def test_title_includes_name(self):
        self.assertIn("MyApp", gen_c4_container(_fi({"project.name": "MyApp"})))

    def test_has_container_and_rel(self):
        out = gen_c4_container(_fi())
        self.assertIn("Container(", out)
        self.assertIn("Rel(", out)

    def test_framework_shown_as_tech(self):
        out = gen_c4_container(_fi({"stack.frontend.framework": "next.js"}))
        self.assertIn("next.js", out)

    def test_database_adds_containerdb(self):
        out = gen_c4_container(_fi({"stack.database.engine": "postgres"}))
        self.assertIn("ContainerDb(", out)
        self.assertIn("postgres", out)

    def test_no_containerdb_without_database(self):
        self.assertNotIn("ContainerDb(", gen_c4_container(_fi()))

    def test_trailing_newline_and_deterministic(self):
        fi = _fi({"project.name": "X", "stack.frontend.framework": "next.js", "stack.database.engine": "postgres"})
        out = gen_c4_container(fi)
        self.assertTrue(out.endswith("\n"))
        self.assertEqual(gen_c4_container(fi), gen_c4_container(fi))


if __name__ == "__main__":
    unittest.main()
