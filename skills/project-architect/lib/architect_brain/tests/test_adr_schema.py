"""Tests for the ADR frontmatter schema (adr-v4-frontmatter.json).

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
"""

import json
import unittest
from pathlib import Path

from architect_brain.validator import validate_schema


SCHEMA_PATH = (
    Path(__file__).resolve().parents[3]
    / "references" / "schemas" / "adr-v4-frontmatter.json"
)


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


VALID_FRONTMATTER = {
    "type": "adr",
    "schema_version": "4.0",
    "id": "0007",
    "title": "Use Next.js 15 over Remix",
    "status": "Accepted",
    "date": "2026-05-27",
    "decision_makers": ["Alexander Ford"],
    "tags": ["stack", "frontend"],
    "phase": "stack",
    "plugin_version": "8.0.0",
    "supersedes": [],
    "superseded_by": [],
    "related": ["0003"],
    "risk": "low",
    "audit": {"required_review_at": None},
}


class TestADRFrontmatterSchema(unittest.TestCase):

    def test_schema_file_exists(self):
        self.assertTrue(SCHEMA_PATH.exists())

    def test_schema_is_valid_json(self):
        _load_schema()

    def test_schema_declares_2020_12(self):
        schema = _load_schema()
        self.assertIn("2020-12", schema.get("$schema", ""))

    def test_full_valid_frontmatter_validates(self):
        schema = _load_schema()
        errors = validate_schema(VALID_FRONTMATTER, schema)
        self.assertEqual(errors, [], f"Expected empty errors, got: {errors}")

    def test_minimal_required_only_validates(self):
        """Only required fields populated should still validate."""
        minimal = {
            "type": "adr",
            "schema_version": "4.0",
            "id": "0007",
            "title": "Test",
            "status": "Accepted",
            "date": "2026-05-27",
            "decision_makers": ["Alexander Ford"],
            "plugin_version": "8.0.0",
        }
        schema = _load_schema()
        errors = validate_schema(minimal, schema)
        self.assertEqual(errors, [])

    def test_wrong_type_rejected(self):
        schema = _load_schema()
        invalid = dict(VALID_FRONTMATTER, type="not-adr")
        errors = validate_schema(invalid, schema)
        self.assertGreater(len(errors), 0)

    def test_wrong_schema_version_rejected(self):
        schema = _load_schema()
        invalid = dict(VALID_FRONTMATTER, schema_version="3.0")
        errors = validate_schema(invalid, schema)
        self.assertGreater(len(errors), 0)

    def test_invalid_id_format_rejected(self):
        schema = _load_schema()
        invalid = dict(VALID_FRONTMATTER, id="abc")
        errors = validate_schema(invalid, schema)
        self.assertGreater(len(errors), 0)

    def test_empty_title_rejected(self):
        schema = _load_schema()
        invalid = dict(VALID_FRONTMATTER, title="")
        errors = validate_schema(invalid, schema)
        self.assertGreater(len(errors), 0)

    def test_unknown_status_rejected(self):
        schema = _load_schema()
        invalid = dict(VALID_FRONTMATTER, status="Bogus")
        errors = validate_schema(invalid, schema)
        self.assertGreater(len(errors), 0)

    def test_reserved_status_accepted(self):
        """Reserved is the v8 placeholder convention."""
        schema = _load_schema()
        reserved = dict(VALID_FRONTMATTER, status="Reserved")
        errors = validate_schema(reserved, schema)
        self.assertEqual(errors, [])

    def test_invalid_date_format_rejected(self):
        schema = _load_schema()
        invalid = dict(VALID_FRONTMATTER, date="May 27, 2026")
        errors = validate_schema(invalid, schema)
        self.assertGreater(len(errors), 0)

    def test_empty_decision_makers_rejected(self):
        schema = _load_schema()
        invalid = dict(VALID_FRONTMATTER, decision_makers=[])
        errors = validate_schema(invalid, schema)
        self.assertGreater(len(errors), 0)

    def test_invalid_plugin_version_rejected(self):
        schema = _load_schema()
        invalid = dict(VALID_FRONTMATTER, plugin_version="v8")
        errors = validate_schema(invalid, schema)
        self.assertGreater(len(errors), 0)

    def test_invalid_supersedes_id_rejected(self):
        schema = _load_schema()
        invalid = dict(VALID_FRONTMATTER, supersedes=["not-an-id"])
        errors = validate_schema(invalid, schema)
        self.assertGreater(len(errors), 0)

    def test_invalid_risk_rejected(self):
        schema = _load_schema()
        invalid = dict(VALID_FRONTMATTER, risk="extreme")
        errors = validate_schema(invalid, schema)
        self.assertGreater(len(errors), 0)

    def test_phase_null_accepted(self):
        schema = _load_schema()
        fm = dict(VALID_FRONTMATTER, phase=None)
        self.assertEqual(validate_schema(fm, schema), [])


if __name__ == "__main__":
    unittest.main()
