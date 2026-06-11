"""Tests for the TECH_STACK catalog document (v8.0.1).

TECH_STACK is the home for the chosen stack + the resolved `stack.versions.*`
pins, and the real target of document-catalog.md's TECH_STACK references (which
previously pointed at a doc that existed nowhere). It must be a conditional doc
(NOT generate_when:always) so check_27 doesn't require it for stackless projects.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
"""

import unittest
from pathlib import Path

from architect_brain.catalog import detect_cycles, eval_condition, load_catalog

_SKILL_ROOT = Path(__file__).resolve().parents[3]   # skills/project-architect/
_CATALOG = _SKILL_ROOT / "references" / "catalog.json"
_TEMPLATES = _SKILL_ROOT / "references" / "templates"


class TestCatalogTechStack(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog(_CATALOG)        # also asserts schema-validity
        cls.documents = cls.catalog["documents"]

    def test_tech_stack_registered_with_required_shape(self):
        self.assertIn("TECH_STACK", self.documents)
        d = self.documents["TECH_STACK"]
        self.assertEqual(d["template"], "templates/TECH_STACK.md")
        self.assertIn("docs/TECH_STACK.md", d["produces"])
        self.assertIn("PROJECT_OVERVIEW", d["depends_on"])
        self.assertEqual(d["concern"], "stack")
        self.assertEqual(d["produced_by"], "document-author")

    def test_catalog_still_acyclic(self):
        self.assertEqual(detect_cycles(self.documents), [])

    def test_template_exists_and_is_not_always(self):
        tmpl = _TEMPLATES / "TECH_STACK.md"
        self.assertTrue(tmpl.is_file(), "TECH_STACK.md template must exist")
        text = tmpl.read_text(encoding="utf-8")
        # Must NOT be generate_when:always (else check_27 would require it of every project).
        self.assertNotIn('generate_when: "always"', text)
        self.assertIn("generate_when", text)
        # The pins home: the template surfaces the stack.versions.* namespace.
        self.assertIn("stack.versions", text)

    def test_condition_selects_when_stack_present(self):
        cond = self.documents["TECH_STACK"]["conditions"][0]
        self.assertTrue(eval_condition(cond, {"decisions": {"stack.frontend.framework": "next.js"}}))
        self.assertTrue(eval_condition(cond, {"decisions": {"stack.backend.language": "python"}}))
        self.assertFalse(eval_condition(cond, {"decisions": {}}))


if __name__ == "__main__":
    unittest.main()
