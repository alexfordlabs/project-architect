"""Contract tests for the authored references/catalog.json."""

import json
import unittest
from pathlib import Path

from architect_brain.catalog import detect_cycles, load_catalog

# parents[0]=tests/, [1]=architect_brain/, [2]=lib/, [3]=project-architect/
_SKILL_ROOT = Path(__file__).resolve().parents[3]   # skills/project-architect/
_CATALOG = _SKILL_ROOT / "references" / "catalog.json"
_TEMPLATES = _SKILL_ROOT / "references" / "templates"

_KNOWN_AGENTS = {
    "document-author", "claude-md-author", "claude-tooling-author",
}
_KNOWN_CONCERNS = {
    "identity", "vision", "architecture", "stack", "cost",
    "ai_agent", "api_contract", "docs", "workflow", "tooling", "handoff",
}


class TestCatalogContent(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog(_CATALOG)        # also asserts schema-validity
        cls.documents = cls.catalog["documents"]

    def test_loads_and_is_acyclic(self):
        self.assertEqual(detect_cycles(self.documents), [])

    def test_project_overview_is_always_and_rootless(self):
        po = self.documents["PROJECT_OVERVIEW"]
        self.assertEqual(po["conditions"], ["ALWAYS"])
        self.assertEqual(po["depends_on"], [])

    def test_core_always_docs_present(self):
        for name in ("PROJECT_OVERVIEW", "PROJECT_REQUIREMENTS", "CLAUDE_MD_ROOT"):
            self.assertIn(name, self.documents)
            self.assertEqual(self.documents[name]["conditions"], ["ALWAYS"])

    def test_every_template_path_exists(self):
        for name, doc in self.documents.items():
            tmpl = _SKILL_ROOT / "references" / doc["template"]
            self.assertTrue(tmpl.exists(), f"{name}: missing template {doc['template']}")

    def test_every_produced_by_is_known_agent(self):
        for name, doc in self.documents.items():
            self.assertIn(doc["produced_by"], _KNOWN_AGENTS, f"{name}: bad produced_by")

    def test_every_concern_is_known(self):
        for name, doc in self.documents.items():
            self.assertIn(doc["concern"], _KNOWN_CONCERNS, f"{name}: bad concern")

    def test_depends_on_targets_exist(self):
        names = set(self.documents)
        for name, doc in self.documents.items():
            for dep in doc["depends_on"]:
                self.assertIn(dep, names, f"{name}: depends_on missing {dep}")

    def test_fragments_excluded(self):
        self.assertNotIn("ADR_TEMPLATE", self.documents)
        self.assertNotIn("REVISION_LOG_FRAGMENT", self.documents)

    def test_all_conditions_parse(self):
        from architect_brain.catalog import parse_condition
        for name, doc in self.documents.items():
            expr = " ".join(doc["conditions"]).strip() or "ALWAYS"
            parse_condition(expr)   # raises ConditionError on a bad expression


if __name__ == "__main__":
    unittest.main()
