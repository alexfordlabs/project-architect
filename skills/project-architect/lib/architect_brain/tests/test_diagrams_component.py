"""Tests for architect_brain.diagrams.gen_c4_component."""

import unittest

from architect_brain.diagrams import gen_c4_component


def _fi(decisions=None):
    return {"schema_version": "4.0", "decisions": decisions or {}, "adrs": []}


class TestGenC4Component(unittest.TestCase):

    def test_starts_with_c4component(self):
        self.assertTrue(gen_c4_component(_fi()).startswith("C4Component"))

    def test_title_includes_name(self):
        self.assertIn("MyApp", gen_c4_component(_fi({"project.name": "MyApp"})))

    def test_has_boundary_and_components(self):
        out = gen_c4_component(_fi())
        self.assertIn("Container_boundary(", out)
        self.assertIn("Component(api", out)
        self.assertIn("Component(svc", out)

    def test_balanced_braces(self):
        out = gen_c4_component(_fi())
        self.assertEqual(out.count("{"), out.count("}"))

    def test_data_access_component_when_database(self):
        out = gen_c4_component(_fi({"stack.database.engine": "postgres"}))
        self.assertIn("Component(repo", out)
        self.assertIn("Rel(svc, repo", out)

    def test_no_data_access_without_database(self):
        self.assertNotIn("Component(repo", gen_c4_component(_fi()))

    def test_trailing_newline_and_deterministic(self):
        fi = _fi({"project.name": "X", "stack.database.engine": "postgres"})
        out = gen_c4_component(fi)
        self.assertTrue(out.endswith("\n"))
        self.assertEqual(gen_c4_component(fi), gen_c4_component(fi))


if __name__ == "__main__":
    unittest.main()
