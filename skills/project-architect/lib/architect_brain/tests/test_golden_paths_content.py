"""Contract tests for the authored references/golden-paths.json."""

import unittest
from pathlib import Path

from architect_brain.golden_paths import decisions_for, load_golden_paths

_GP = Path(__file__).resolve().parents[3] / "references" / "golden-paths.json"


class TestGoldenPathsContent(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.gp = load_golden_paths(_GP)          # also asserts schema-validity + unique ids
        cls.paths = cls.gp["paths"]

    def test_exactly_nine_paths(self):
        self.assertEqual(len(self.paths), 9)

    def test_modern_saas_matches_spec(self):
        dec = decisions_for("modern_saas_2026", self.gp)
        self.assertEqual(dec["project.type"], "web_app")
        self.assertEqual(dec["stack.frontend.framework"], "next.js")
        self.assertEqual(dec["stack.database.orm"], "drizzle")

    def test_agentic_system_path_present(self):
        dec = decisions_for("agentic_system", self.gp)
        self.assertEqual(dec["project.type"], "agentic_system")
        self.assertTrue(dec.get("ai.agent"))

    def test_every_path_has_at_least_10_decisions(self):
        for p in self.paths:
            self.assertGreaterEqual(
                len(p["decisions"]), 10, f"{p['id']}: only {len(p['decisions'])} decisions"
            )

    def test_every_path_has_project_type(self):
        for p in self.paths:
            self.assertIn("project.type", p["decisions"], f"{p['id']}: no project.type")

    def test_every_path_has_label_and_description(self):
        for p in self.paths:
            self.assertTrue(p["label"], f"{p['id']}: empty label")
            self.assertTrue(p["description"], f"{p['id']}: empty description")

    def test_expected_ids_present(self):
        ids = {p["id"] for p in self.paths}
        expected = {
            "modern_saas_2026", "ai_rag_app", "mobile_cross_platform",
            "high_perf_api", "pl_interpreter", "cli_rust", "cc_plugin",
            "mcp_server", "agentic_system",
        }
        self.assertEqual(ids, expected)


if __name__ == "__main__":
    unittest.main()
