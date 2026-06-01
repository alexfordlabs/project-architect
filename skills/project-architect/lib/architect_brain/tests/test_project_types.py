"""Tests for architect_brain.project_types — the project-type registry."""

import unittest

from architect_brain.project_types import (
    AGENTIC_SUBTYPES,
    TOP_LEVEL_TYPES,
    ProjectTypeError,
    is_valid_agentic_subtype,
    is_valid_project_type,
    validate_project_type,
)


class TestProjectTypes(unittest.TestCase):

    def test_agentic_system_is_a_top_level_type(self):
        self.assertIn("agentic_system", TOP_LEVEL_TYPES)

    def test_common_v7_types_present(self):
        for t in ("web_app", "mobile_app", "cli", "library", "mcp_server"):
            self.assertIn(t, TOP_LEVEL_TYPES)

    def test_three_agentic_subtypes(self):
        self.assertEqual(
            set(AGENTIC_SUBTYPES),
            {"single_agent", "multi_agent_orchestrator", "agentic_tool"},
        )

    def test_no_duplicate_top_level_types(self):
        self.assertEqual(len(TOP_LEVEL_TYPES), len(set(TOP_LEVEL_TYPES)))

    def test_is_valid_project_type(self):
        self.assertTrue(is_valid_project_type("agentic_system"))
        self.assertFalse(is_valid_project_type("not_a_type"))

    def test_is_valid_agentic_subtype(self):
        self.assertTrue(is_valid_agentic_subtype("single_agent"))
        self.assertFalse(is_valid_agentic_subtype("rogue_agent"))

    def test_validate_project_type_accepts_known(self):
        validate_project_type("web_app")  # must not raise

    def test_validate_project_type_raises_on_unknown(self):
        with self.assertRaises(ProjectTypeError):
            validate_project_type("not_a_type")


if __name__ == "__main__":
    unittest.main()
