"""Tests for architect_brain.detect — situation-router classifier.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
"""

import json
import tempfile
import unittest
from pathlib import Path

from architect_brain.detect import detect_situation


class TestDetect(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.docs_dir = Path(self.tmp.name) / "docs"
        self.docs_dir.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_detect_greenfield_when_state_absent(self):
        result = detect_situation(self.docs_dir)
        self.assertEqual(result["situation"], "greenfield")
        self.assertIsNone(result["schema_version"])
        self.assertIsNone(result["state_layout"])

    def test_detect_v8_project_when_schema_version_file_exists(self):
        state_dir = self.docs_dir / "_architect_state"
        state_dir.mkdir()
        (state_dir / "schema_version").write_text("4.0\n")
        result = detect_situation(self.docs_dir)
        self.assertEqual(result["situation"], "v8_project")
        self.assertEqual(result["schema_version"], "4.0")
        self.assertEqual(result["state_layout"], "v8_multi_file")

    def test_detect_pre_v8_project_with_v7_monolith(self):
        (self.docs_dir / "_architect_state.json").write_text(
            json.dumps({"schema_version": "3.1", "phase": 5})
        )
        result = detect_situation(self.docs_dir)
        self.assertEqual(result["situation"], "pre_v8_project")
        self.assertEqual(result["schema_version"], "3.1")
        self.assertEqual(result["state_layout"], "v7_monolith")

    def test_detect_v7_monolith_without_schema_version_field(self):
        """Pre-schema-3 monoliths may omit the field — must classify, not crash."""
        (self.docs_dir / "_architect_state.json").write_text(json.dumps({"phase": 2}))
        result = detect_situation(self.docs_dir)
        self.assertEqual(result["situation"], "pre_v8_project")
        self.assertIsNone(result["schema_version"])
        self.assertEqual(result["state_layout"], "v7_monolith")

    def test_detect_pre_v8_with_unreadable_monolith(self):
        (self.docs_dir / "_architect_state.json").write_text("not valid json")
        result = detect_situation(self.docs_dir)
        self.assertEqual(result["situation"], "pre_v8_project")
        self.assertIsNone(result["schema_version"])
        self.assertEqual(result["state_layout"], "v7_monolith_unreadable")

    def test_detect_v8_takes_priority_over_v7_monolith(self):
        """If both v8 layout AND v7 monolith exist, v8 wins (post-migration)."""
        # Migrate scenario: v7 monolith kept as backup, new v8 directory created
        (self.docs_dir / "_architect_state.json").write_text(
            json.dumps({"schema_version": "3.1"})
        )
        state_dir = self.docs_dir / "_architect_state"
        state_dir.mkdir()
        (state_dir / "schema_version").write_text("4.0\n")
        result = detect_situation(self.docs_dir)
        self.assertEqual(result["situation"], "v8_project")
        self.assertEqual(result["schema_version"], "4.0")

    def test_detect_schema_version_strips_whitespace(self):
        state_dir = self.docs_dir / "_architect_state"
        state_dir.mkdir()
        (state_dir / "schema_version").write_text("  4.0  \n\n")
        result = detect_situation(self.docs_dir)
        self.assertEqual(result["schema_version"], "4.0")


if __name__ == "__main__":
    unittest.main()
