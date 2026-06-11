"""Tests for the 11 per-concern state schema fragments.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

Wave 2.9 of v8.0. Verifies the JSON Schema 2020-12 fragments under
``skills/project-architect/references/schemas/state-v4-*.json`` exist, parse,
declare 2020-12, require ``schema_version`` + ``concern`` + ``decisions``,
accept the output of ``empty_projections()``, and reject malformed input.
The workflow schema additionally requires the situation-router fields.
"""

import json
import unittest
from pathlib import Path

from architect_brain.projections import CONCERN_NAMES, empty_projections
from architect_brain.validator import validate_schema


# parents[0]=tests/, [1]=architect_brain/, [2]=lib/, [3]=project-architect/
SCHEMAS_DIR = Path(__file__).resolve().parents[3] / "references" / "schemas"


def _load_schema(name: str) -> dict:
    """Load a per-concern schema file (concern name uses underscores)."""
    schema_path = SCHEMAS_DIR / f"state-v4-{name.replace('_', '-')}.json"
    return json.loads(schema_path.read_text())


class TestStateSchemas(unittest.TestCase):

    def test_all_11_concern_schemas_exist(self):
        for concern in CONCERN_NAMES:
            schema_name = f"state-v4-{concern.replace('_', '-')}.json"
            self.assertTrue(
                (SCHEMAS_DIR / schema_name).exists(),
                f"missing schema: {schema_name}",
            )

    def test_each_schema_is_valid_json(self):
        for concern in CONCERN_NAMES:
            try:
                _load_schema(concern)
            except json.JSONDecodeError as e:
                self.fail(f"schema for {concern} is invalid JSON: {e}")

    def test_each_schema_declares_json_schema_2020_12(self):
        for concern in CONCERN_NAMES:
            schema = _load_schema(concern)
            self.assertIn("$schema", schema)
            self.assertIn("2020-12", schema["$schema"])

    def test_each_schema_requires_schema_version_and_concern_and_decisions(self):
        for concern in CONCERN_NAMES:
            schema = _load_schema(concern)
            self.assertIn("required", schema)
            required = set(schema["required"])
            for req in ("schema_version", "concern", "decisions"):
                self.assertIn(
                    req, required,
                    f"{concern} schema missing required: {req}",
                )

    def test_empty_projection_validates_against_schema(self):
        """empty_projections() output must validate against each concern schema."""
        projections = empty_projections()
        for concern in CONCERN_NAMES:
            schema = _load_schema(concern)
            errors = validate_schema(projections[concern], schema)
            self.assertEqual(
                errors, [],
                f"empty {concern} projection failed validation: {errors}",
            )

    def test_workflow_schema_requires_router_fields(self):
        """Workflow schema must require current_phase, substep, locked, audits."""
        schema = _load_schema("workflow")
        required = set(schema["required"])
        self.assertIn("current_phase", required)
        self.assertIn("substep", required)
        self.assertIn("locked", required)
        self.assertIn("audits", required)

    def test_invalid_projection_fails_validation(self):
        """A projection missing required fields must fail validation."""
        schema = _load_schema("stack")
        invalid = {"schema_version": "4.0"}  # missing concern + decisions
        errors = validate_schema(invalid, schema)
        self.assertGreater(len(errors), 0)


if __name__ == "__main__":
    unittest.main()
